from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from typing import Dict, List, Set
import time
import json

app = FastAPI()

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory structures
connected_users: Dict[str, WebSocket] = {}
online_users: Set[str] = set()
typing_users: Set[str] = set()
message_queues: Dict[str, asyncio.Queue] = {}

@app.post("/send_message")
async def send_message(request: Request):
    data = await request.json()
    sender = data["sender"]
    recipient = data["recipient"]
    content = data["content"]
    msg_id = data.get("msg_id", f"{sender}_{recipient}_{time.time()}")
    
    msg = {
        "sender": sender,
        "content": content,
        "msg_id": msg_id
    }
    
    # Queue message for recipient
    if recipient not in message_queues:
        message_queues[recipient] = asyncio.Queue()
    await message_queues[recipient].put(msg)
    
    # If recipient is online, push via websocket
    if recipient in connected_users:
        await connected_users[recipient].send_json({"type": "message", **msg})
    
    return JSONResponse({"status": "ok"})

@app.get("/online_users")
async def get_online_users():
    return list(online_users)

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connected_users[username] = websocket
    online_users.add(username)
    try:
        # Notify others user is online
        await broadcast_status()
        # Send queued messages
        if username in message_queues:
            while not message_queues[username].empty():
                msg = await message_queues[username].get()
                try:
                    await websocket.send_json({"type": "message", **msg})
                except Exception as e:
                    print(f"Error sending queued message: {e}")
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "typing":
                    if data.get("is_typing"):
                        typing_users.add(username)
                    else:
                        typing_users.discard(username)
                    await broadcast_typing()
            except json.JSONDecodeError as e:
                print(f"Invalid JSON received from {username}: {e}")
            except Exception as e:
                print(f"Error processing message from {username}: {e}")
    except WebSocketDisconnect:
        pass
    finally:
        connected_users.pop(username, None)
        online_users.discard(username)
        typing_users.discard(username)
        await broadcast_status()
        await broadcast_typing()

async def broadcast_status():
    for ws in connected_users.values():
        await ws.send_json({"type": "status", "online": list(online_users)})

async def broadcast_typing():
    for ws in connected_users.values():
        await ws.send_json({"type": "typing", "users": list(typing_users)})

if __name__ == "__main__":
    uvicorn.run("comm_server:app", host="0.0.0.0", port=8001, reload=True) 