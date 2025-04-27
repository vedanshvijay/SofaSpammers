import asyncio
import httpx
import websockets
import json
import time

class CommClient:
    def __init__(self, username, server_url="http://localhost:8001", ws_url="ws://localhost:8001/ws"):
        self.username = username
        self.server_url = server_url
        self.ws_url = f"{ws_url}/{username}"
        self.ws = None
        self.on_message = None
        self.on_status = None
        self.on_typing = None
        self._reconnect_delay = 2
        self._stop = False

    async def send_message(self, recipient, content, msg_id=None):
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.server_url}/send_message", json={
                "sender": self.username,
                "recipient": recipient,
                "content": content,
                "timestamp": time.time(),
                "msg_id": msg_id or f"{self.username}_{recipient}_{time.time()}"
            })

    async def connect_ws(self):
        while not self._stop:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    print(f"Connected to websocket as {self.username}")
                    async for msg in ws:
                        print("Raw websocket message:", msg)
                        data = json.loads(msg)
                        if data.get("type") == "message" and self.on_message:
                            print("Calling on_message handler")
                            await self.on_message(data)
                        elif data.get("type") == "status" and self.on_status:
                            print("Calling on_status handler")
                            await self.on_status(data)
                        elif data.get("type") == "typing" and self.on_typing:
                            print("Calling on_typing handler")
                            await self.on_typing(data)
            except Exception as e:
                print(f"Websocket error: {e}. Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)

    async def send_typing(self, is_typing=True):
        """Send typing status with rate limiting"""
        if self.ws:
            # Rate limit typing events 
            current_time = time.time()
            if not hasattr(self, '_last_typing_sent'):
                self._last_typing_sent = 0
                
            # Only send at most once per second, but always send when typing stops
            if not is_typing or (current_time - self._last_typing_sent > 1.0):
                try:
                    await self.ws.send(json.dumps({"type": "typing", "is_typing": is_typing}))
                    self._last_typing_sent = current_time
                except Exception as e:
                    print(f"Error sending typing status: {e}")

    def stop(self):
        self._stop = True

# Example usage:
# client = CommClient("alice")
# asyncio.run(client.connect_ws()) 