#!/usr/bin/env python3
"""
Interaction Analytics Tracker — logs every operator interaction with cortana.html
WebSocket server receiving events from visualizer, appending to JSONL log file.
Minimal, non-blocking, append-only design per cybernetic principles.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "interactions.jsonl"
HOST = "localhost"
PORT = 8767  # Separate from projection server's 8766


class InteractionTracker:
    def __init__(self):
        self.clients = set()
        self.session_counter = 0
    
    async def handle_client(self, websocket):
        """Handle individual client connection."""
        self.clients.add(websocket)
        session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_counter}"
        self.session_counter += 1
        
        try:
            async for message in websocket:
                try:
                    event = json.loads(message)
                    event["session_id"] = session_id
                    event["received_at"] = datetime.utcnow().isoformat() + "Z"
                    
                    # Append to log file (append-only pattern)
                    with open(LOG_FILE, "a") as f:
                        f.write(json.dumps(event) + "\n")
                    
                    # Echo acknowledgment back to client
                    await websocket.send(json.dumps({"status": "logged", "event_type": event.get("type")}))
                    
                except json.JSONDecodeError:
                    print(f"[{datetime.now()}] Invalid JSON received")
        
        finally:
            self.clients.discard(websocket)
    
    async def broadcast_state_update(self):
        """Periodic heartbeat to all connected clients (optional)."""
        while True:
            await asyncio.sleep(5)
            state_message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "total_interactions": len(list(Path(LOG_FILE).read_text().strip().split("\n"))),
                "active_clients": len(self.clients)
            }
            if self.clients:
                await asyncio.gather(
                    *[c.send(json.dumps(state_message)) for c in list(self.clients)],
                    return_exceptions=True
                )


async def main():
    tracker = InteractionTracker()
    
    server = await websockets.serve(tracker.handle_client, HOST, PORT)
    print(f"📊 Analytics Tracker listening on ws://{HOST}:{PORT}")
    print(f"📁 Log file: {LOG_FILE.absolute()}")
    
    # Start heartbeat task
    asyncio.create_task(tracker.broadcast_state_update())
    
    await server.wait_closed()


if __name__ == "__main__":
    import websockets
    asyncio.run(main())
