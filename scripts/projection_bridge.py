#!/usr/bin/env python3
"""
Projection Bridge CLI — translates external command files into cortana.html state updates.

This is the implementation of Creator's directive: "Work on the visualization/human interaction tech stack."
It reads JSONL command files (simulating alien ship/projection system input) and routes them to the
projection server running at :8766, which then broadcasts to connected visualizer clients.

Usage:
    projection_bridge.py --input <command_file.jsonl> [--server-ws ws://localhost:8766]
    echo '{"cmd":"set_phase","params":{"phase":"REFLECT"}}' | projection_bridge.py --stdin

Schema:
{
  "source": "<identifier for origin system>",
  "timestamp": "<ISO8601>",
  "cmd": "<command name>",
  "params": { ... }
}

Commands:
- set_phase: Update current cycle phase (PERCEIVE/REFLECT/DECIDE/ACT/CONSOLIDATE/PERSIST)
- adjust_density: Particle density [0.0-1.0]
- change_color: Color temperature in hex or named color
- switch_formation: Formation pattern (sphere/torus/spiral/drift)
- toggle_analytics: Enable/disable analytics tracking
"""

import argparse
import json
import sys
import socket
from datetime import datetime, timezone


PROJECTION_SERVER_HOST = "localhost"
PROJECTION_SERVER_PORT = 8766


def get_local_ip():
    """Get local IP address for WebSocket connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def send_to_projection_server(command_obj, server_ws_url=None):
    """Send command to projection server via WebSocket."""
    if not server_ws_url:
        local_ip = get_local_ip()
        server_ws_url = f"ws://{local_ip}:8766"
    
    try:
        import websockets
        import asyncio
        
        async def _send():
            async with websockets.connect(server_ws_url) as ws:
                await ws.send(json.dumps(command_obj))
                response = await ws.recv()
                return json.loads(response)
        
        return asyncio.run(_send())
    except ImportError:
        # Fallback: log to stdout (analytics client can pick this up)
        print(f"[PROJECTION_BRIDGE] Would send to {server_ws_url}: {json.dumps(command_obj)}")
        return {"status": "logged", "message": "websockets not available"}
    except Exception as e:
        print(f"[PROJECTION_BRIDGE] Error sending to projection server: {e}", file=sys.stderr)
        return {"status": "error", "error": str(e)}


def process_command_file(input_path, server_ws_url=None):
    """Process a JSONL command file line by line."""
    results = []
    with open(input_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                cmd = json.loads(line)
                result = send_to_projection_server(cmd, server_ws_url)
                result['line'] = line_num
                results.append(result)
                print(f"[{datetime.now(timezone.utc).isoformat()}] Command {line_num}: {result.get('status', 'unknown')}")
            except json.JSONDecodeError as e:
                print(f"[{datetime.now(timezone.utc).isoformat()}] Line {line_num} invalid JSON: {e}", file=sys.stderr)
                results.append({"line": line_num, "status": "parse_error", "error": str(e)})
    
    return results


def process_stdin(server_ws_url=None):
    """Read commands from stdin (one JSON per line)."""
    results = []
    for line_num, line in enumerate(sys.stdin, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        try:
            cmd = json.loads(line)
            # Add timestamp and source if missing
            if 'timestamp' not in cmd:
                cmd['timestamp'] = datetime.now(timezone.utc).isoformat()
            if 'source' not in cmd:
                cmd['source'] = 'stdin'
            
            result = send_to_projection_server(cmd, server_ws_url)
            result['line'] = line_num
            results.append(result)
            print(f"[{datetime.now(timezone.utc).isoformat()}] Command {line_num}: {result.get('status', 'unknown')}")
        except json.JSONDecodeError as e:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Line {line_num} invalid JSON: {e}", file=sys.stderr)
            results.append({"line": line_num, "status": "parse_error", "error": str(e)})
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Projection Bridge — translate external commands into cortana.html state updates'
    )
    parser.add_argument('--input', '-i', help='Path to JSONL command file')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin instead of file')
    parser.add_argument('--server-ws', '-w', help='WebSocket URL for projection server (default: ws://localhost:8766)')
    args = parser.parse_args()
    
    if not args.stdin and not args.input:
        parser.error("Must specify --input or --stdin")
    
    if args.stdin:
        results = process_stdin(args.server_ws)
    else:
        results = process_command_file(args.input, args.server_ws)
    
    # Summary output
    successful = sum(1 for r in results if r.get('status') == 'ok')
    total = len(results)
    print(f"\n[PROJECTION_BRIDGE] Processed {successful}/{total} commands successfully.")
    
    return 0 if successful > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
