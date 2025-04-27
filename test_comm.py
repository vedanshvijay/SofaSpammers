import asyncio
from comm_client import CommClient

async def on_message(name):
    async def handler(data):
        print(f"[{name} RECEIVED MESSAGE] {data}")
    return handler

async def on_status(name):
    async def handler(data):
        print(f"[{name} STATUS] {data}")
    return handler

async def on_typing(name):
    async def handler(data):
        print(f"[{name} TYPING] {data}")
    return handler

async def alice_actions(alice):
    await asyncio.sleep(1)
    print("[ALICE] Sending message to Bob...")
    await alice.send_message("bob", "Hello Bob! This is Alice.")
    await asyncio.sleep(1)
    print("[ALICE] Typing...")
    await alice.send_typing(True)
    await asyncio.sleep(2)
    print("[ALICE] Stopped typing.")
    await alice.send_typing(False)

async def bob_actions(bob):
    await asyncio.sleep(2)
    print("[BOB] Sending message to Alice...")
    await bob.send_message("alice", "Hi Alice! Bob here.")
    await asyncio.sleep(1)
    print("[BOB] Typing...")
    await bob.send_typing(True)
    await asyncio.sleep(2)
    print("[BOB] Stopped typing.")
    await bob.send_typing(False)

async def main():
    alice = CommClient("alice")
    bob = CommClient("bob")

    alice.on_message = await on_message("ALICE")
    alice.on_status = await on_status("ALICE")
    alice.on_typing = await on_typing("ALICE")

    bob.on_message = await on_message("BOB")
    bob.on_status = await on_status("BOB")
    bob.on_typing = await on_typing("BOB")

    # Run both websocket connections and actions concurrently
    await asyncio.gather(
        alice.connect_ws(),
        bob.connect_ws(),
        alice_actions(alice),
        bob_actions(bob),
    )

if __name__ == "__main__":
    asyncio.run(main())