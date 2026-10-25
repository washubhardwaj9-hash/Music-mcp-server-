import asyncio
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import websockets

ENDPOINT = os.environ["MCP_ENDPOINT"]
SCRIPT = sys.argv[1] if len(sys.argv) > 1 else "main.py"


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def start_health():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()


async def bridge():
    async with websockets.connect(ENDPOINT) as ws:
        print("Connected to XiaoZhi", file=sys.stderr, flush=True)
        proc = await asyncio.create_subprocess_exec(
            sys.executable, SCRIPT,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,
            limit=10 * 1024 * 1024,
        )

        async def ws_to_proc():
            async for msg in ws:
                if isinstance(msg, bytes):
                    msg = msg.decode()
                proc.stdin.write((msg.strip() + "\n").encode())
                await proc.stdin.drain()

        async def proc_to_ws():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    await ws.send(text)

        tasks = [asyncio.create_task(ws_to_proc()), asyncio.create_task(proc_to_ws())]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in tasks:
            t.cancel()
        try:
            proc.kill()
        except ProcessLookupError:
            pass


async def main():
    delay = 2
    while True:
        try:
            await bridge()
            delay = 2
        except Exception as e:
            print(f"Disconnected: {e}", file=sys.stderr, flush=True)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 60)


if __name__ == "__main__":
    threading.Thread(target=start_health, daemon=True).start()
    asyncio.run(main())
