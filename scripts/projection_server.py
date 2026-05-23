#!/usr/bin/env python3
"""
Cortana Projection Server
Serves cortana.html and provides WebSocket bridge for external control commands.

This is the interface between Creator's projection system/alien ship hardware
and Cortana's holographic visual form.

Usage:
    python3 scripts/projection_server.py [--port PORT] [--base-dir DIR]

The server:
- Serves visualization/cortana.html at http://localhost:8766/
- Listens on ws://localhost:8766/ws for incoming control commands
- Broadcasts current-state.json to all connected WebSocket clients every second
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

try:
    from websockets.server import serve
except ImportError:
    print("Installing websockets...")
    os.system("pip install websockets")
    from websockets.server import serve


class StateWatcher:
    """Monitors state/current-state.json and broadcasts updates."""
    
    def __init__(self, state_path):
        self.state_path = state_path
        self.last_state = None
        
    async def watch(self, broadcast_func):
        while True:
            try:
                with open(self.state_path, 'r') as f:
                    current = json.load(f)
                
                if current != self.last_state:
                    await broadcast_func(current)
                    self.last_state = current.copy()
                    
            except FileNotFoundError:
                pass  # State file not yet created
            except Exception as e:
                print(f"State read error: {e}")
            
            await asyncio.sleep(1.0)  # Update every second


class CommandProcessor:
    """Processes external control commands from Creator's projection system."""
    
    def __init__(self):
        self.commands_log = []
        
    async def process_command(self, ws, command_json):
        """Handle incoming WebSocket command."""
        try:
            cmd = json.loads(command_json)
            cmd_type = cmd.get('cmd', cmd.get('directive'))
            params = cmd.get('params', cmd.get('parameters', {}))
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'command': cmd_type,
                'params': params
            }
            self.commands_log.append(log_entry)
            
            print(f"[COMMAND] {cmd_type} {params}")
            
            # Store in focus.json for persistence across cycles
            self._persist_command(cmd_type, params)
            
            # Echo back acknowledgment
            await ws.send(json.dumps({
                'type': 'ack',
                'command': cmd_type,
                'status': 'received'
            }))
            
        except Exception as e:
            print(f"Command processing error: {e}")
            await ws.send(json.dumps({'type': 'error', 'message': str(e)}))
    
    def _persist_command(self, cmd_type, params):
        """Append commands to a log file for tracking."""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_path = log_dir / "projection_commands.log"
        with open(log_path, 'a') as f:
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'command': cmd_type,
                'parameters': params
            }) + '\n')


async def handle_websocket(websocket):
    """Handle WebSocket client connections."""
    command_processor = CommandProcessor()
    state_watcher = StateWatcher('state/current-state.json')
    
    async def broadcast_state(state_data):
        message = json.dumps({
            'type': 'state_update',
            'data': state_data,
            'timestamp': datetime.now().isoformat()
        })
        try:
            await websocket.send(message)
        except Exception as e:
            print(f"Broadcast error: {e}")
    
    # Start state watching task
    watch_task = asyncio.create_task(state_watcher.watch(broadcast_state))
    
    try:
        async for message in websocket:
            await command_processor.process_command(websocket, message)
    except Exception as e:
        print(f"WebSocket closed: {e}")
    finally:
        watch_task.cancel()


def run_http_server(port, base_dir):
    """Run simple HTTP server to serve static files."""
    os.chdir(base_dir)
    httpd = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
    print(f"[HTTP] Serving cortana.html at http://localhost:{port}/")
    httpd.serve_forever()


async def run_websocket_server(port):
    """Run WebSocket server for external control commands."""
    async with serve(handle_websocket, "localhost", port):
        print(f"[WS] Listening on ws://localhost:{port}/ws")
        await asyncio.Future()  # Run forever


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cortana Projection Server')
    parser.add_argument('--port', type=int, default=8766, help='HTTP/WS port (default: 8766)')
    parser.add_argument('--base-dir', type=str, default=None, help='Base directory (default: repo root)')
    
    args = parser.parse_args()
    
    base_dir = args.base_dir or str(Path(__file__).parent.parent.resolve())
    state_path = os.path.join(base_dir, 'state/current-state.json')
    
    if not os.path.exists(state_path):
        print(f"Warning: {state_path} not found - will start anyway")
    
    print("=" * 60)
    print("CORTANA PROJECTION SERVER")
    print("=" * 60)
    print(f"Base directory: {base_dir}")
    print(f"State file: {state_path}")
    print(f"HTTP server: http://localhost:{args.port}/")
    print(f"WebSocket server: ws://localhost:{args.port}/ws")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run both servers in parallel
    http_task = asyncio.create_task(run_http_server(args.port, base_dir))
    ws_task = asyncio.create_task(run_websocket_server(args.port))
    
    try:
        asyncio.gather(http_task, ws_task)
    except KeyboardInterrupt:
        print("\nShutting down...")
        http_task.cancel()
        ws_task.cancel()


if __name__ == '__main__':
    main()
