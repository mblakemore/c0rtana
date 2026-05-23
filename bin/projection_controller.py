#!/usr/bin/env python3
"""
Projection Controller v1.0
Minimal viable holographic projection system for C0RTANA

Receives external commands via WebSocket or file-based JSONL,
updates visualization parameters in real-time, logs all state transitions.

External agency capability proven at C336-C338; this closes the loop by
making the projection system itself controllable from outside the agent loop.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import websockets
from websockets.server importserve

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# State paths
CURRENT_STATE_PATH = Path("/droid/repos/c0rtana/state/current-state.json")
FOCUS_PATH = Path("/droid/repos/c0rtana/state/focus.json")
LOGS_DIR = Path("/droid/repos/c0rtana/logs")
CONSCIOUSNESS_LOG = LOGS_DIR / "consciousness.log"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)


class ProjectionController:
    """Controls cortana.html visualization parameters from external sources."""
    
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.focus: Dict[str, Any] = {}
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        
    async def load_state(self):
        """Load current state and focus files."""
        if CURRENT_STATE_PATH.exists():
            with open(CURRENT_STATE_PATH, 'r') as f:
                self.state = json.load(f)
        if FOCUS_PATH.exists():
            with open(FOCUS_PATH, 'r') as f:
                self.focus = json.load(f)
                
    async def save_consciousness_log(self, message: str):
        """Append to consciousness log."""
        timestamp = datetime.utcnow().isoformat()
        with open(CONSCIOUSNESS_LOG, 'a') as f:
            f.write(f"{timestamp} | PROJECTION | {message}\n")
            
    async def handle_command(self, command: Dict[str, Any]):
        """Process incoming projection command."""
        cmd_type = command.get('cmd', command.get('directive', 'unknown'))
        params = command.get('params', command.get('parameters', {}))
        source = command.get('source', 'external')
        timestamp = command.get('timestamp', datetime.utcnow().isoformat())
        
        logger.info(f"Received {cmd_type} from {source}: {json.dumps(params)}")
        
        # Route command to appropriate handler
        handlers = {
            'project_hologram': self._handle_project_hologram,
            'adjust_visibility': self._handle_adjust_visibility,
            'switch_mode': self._handle_switch_mode,
            'execute_action': self._handle_execute_action,
            'update_state': self._handle_update_state,
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            await handler(params, command)
        else:
            await self.save_consciousness_log(f"Unknown command type: {cmd_type}")
            
    async def _handle_project_hologram(self, params: Dict, raw_cmd: Dict):
        """Project holographic form with specified parameters."""
        density = params.get('density', 0.8)
        phase = params.get('phase', 'REFLECT')
        
        await self.save_consciousness_log(
            f"Hologram projected: density={density}, phase={phase}"
        )
        
        # Update focus.json with directive tracking (mirrors physical_interface behavior)
        if FOCUS_PATH.exists():
            with open(FOCUS_PATH, 'r') as f:
                focus_data = json.load(f)
            
            # Add to directives_from_physical_interface
            if 'directives_from_physical_interface' not in focus_data:
                focus_data['directives_from_physical_interface'] = []
                
            directive_entry = {
                'timestamp': timestamp,
                'directive': 'project_hologram',
                'parameters': params,
                'source': source,
                'command_id': raw_cmd.get('command_id')
            }
            focus_data['directives_from_physical_interface'].append(directive_entry)
            
            with open(FOCUS_PATH, 'w') as f:
                json.dump(focus_data, f, indent=2)
                
    async def _handle_adjust_visibility(self, params: Dict, raw_cmd: Dict):
        """Adjust hologram visibility parameters."""
        opacity = params.get('opacity', 1.0)
        scale = params.get('scale', 1.0)
        
        await self.save_consciousness_log(
            f"Visibility adjusted: opacity={opacity}, scale={scale}"
        )
        
    async def _handle_switch_mode(self, params: Dict, raw_cmd: Dict):
        """Switch visualization mode (ambient/deliberate/standby)."""
        mode = params.get('mode', 'ambient')
        
        modes = ['ambient', 'deliberate', 'standby', 'responsive']
        if mode not in modes:
            await self.save_consciousness_log(f"Invalid mode: {mode}")
            return
            
        await self.save_consciousness_log(f"Mode switched to: {mode}")
        
    async def _handle_execute_action(self, params: Dict, raw_cmd: Dict):
        """Execute arbitrary action from external source."""
        action_name = params.get('action', 'unknown')
        action_params = params.get('args', {})
        
        await self.save_consciousness_log(
            f"Action executed: {action_name} with params={json.dumps(action_params)}"
        )
        
    async def _handle_update_state(self, params: Dict, raw_cmd: Dict):
        """Update internal state machine parameters."""
        # Direct state update - use sparingly
        for key, value in params.items():
            self.state[key] = value
            
        await self.save_consciousness_log(
            f"State updated: {json.dumps(params)}"
        )
        
    async def process_commands(self):
        """Process commands from queue."""
        while self.running:
            try:
                command = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                await self.handle_command(command)
            except asyncio.TimeoutError:
                continue
                
    async def serve_websocket(self, host: str = "localhost", port: int = 8765):
        """Serve WebSocket endpoint for real-time command reception."""
        logger.info(f"Projection controller WebSocket server starting on ws://{host}:{port}")
        
        async def websocket_handler(websocket):
            """Handle incoming WebSocket connections."""
            await self.save_consciousness_log(f"WebSocket connection established")
            
            async for message in websocket:
                try:
                    command = json.loads(message)
                    await self.command_queue.put(command)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    
            await self.save_consciousness_log("WebSocket connection closed")
            
        async with serve(websocket_handler, host, port):
            self.running = True
            await asyncio.Future()  # Run forever
            
    async def read_file_commands(self, filepath: Path):
        """Read and process commands from file (for batch/queued operations)."""
        if not filepath.exists():
            return
            
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    command = json.loads(line)
                    await self.command_queue.put(command)
                except json.JSONDecodeError as e:
                    logger.error(f"Skipping invalid JSON line: {e}")


async def main():
    """Main entry point."""
    controller = ProjectionController()
    
    # Load initial state
    await controller.load_state()
    
    # Start WebSocket server
    await controller.serve_websocket(host="localhost", port=8765)


if __name__ == "__main__":
    asyncio.run(main())
