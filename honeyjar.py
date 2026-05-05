"""HoneyJar - lightweight honeypot.

Listens on configured ports, logs first bytes received, and POSTs structured
events to a webhook. Designed to run on a tiny VPS.

Configuration via environment (or .env via python-dotenv if installed):

    HONEYJAR_PORTS=22,23,80,445
    HONEYJAR_WEBHOOK_URL=https://discord.com/api/webhooks/...
    HONEYJAR_HOSTNAME=honeyjar-prod
    HONEYJAR_LOG_FILE=honeyjar.log
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import os
import socket
import urllib.request
from dataclasses import asdict, dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


PORTS = [int(p) for p in os.getenv("HONEYJAR_PORTS", "2222,2323,8080,4445").split(",") if p.strip()]
WEBHOOK_URL = os.getenv("HONEYJAR_WEBHOOK_URL", "").strip()
HOSTNAME = os.getenv("HONEYJAR_HOSTNAME", socket.gethostname())
LOG_FILE = os.getenv("HONEYJAR_LOG_FILE", "honeyjar.log")
MAX_BYTES = 256

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("honeyjar")


@dataclass
class Event:
    ts: str
    host: str
    src_ip: str
    src_port: int
    dst_port: int
    payload_preview: str
    payload_bytes: int


def post_webhook(event: Event) -> None:
    if not WEBHOOK_URL:
        return
    body = {
        "username": "honeyjar",
        "content": f"`{event.dst_port}` from `{event.src_ip}:{event.src_port}` "
                   f"({event.payload_bytes} bytes)\n```\n{event.payload_preview[:500]}\n```",
        "embeds": [{"title": f"connection :{event.dst_port}", "fields": [
            {"name": k, "value": str(v), "inline": True} for k, v in asdict(event).items()
            if k not in ("payload_preview",)
        ]}],
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        WEBHOOK_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "honeyjar/0.1"},
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        log.warning("webhook post failed: %s", e)


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("?", 0)
    try:
        data = await asyncio.wait_for(reader.read(MAX_BYTES), timeout=3.0)
    except asyncio.TimeoutError:
        data = b""
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    preview = data.decode("utf-8", errors="replace") if data else ""
    event = Event(
        ts=dt.datetime.now(dt.timezone.utc).isoformat(),
        host=HOSTNAME,
        src_ip=peer[0],
        src_port=peer[1],
        dst_port=port,
        payload_preview=preview,
        payload_bytes=len(data),
    )
    log.info("HIT %s:%d -> :%d (%d bytes)", peer[0], peer[1], port, len(data))
    post_webhook(event)


async def serve_port(port: int) -> None:
    server = await asyncio.start_server(
        lambda r, w: handle(r, w, port), host="0.0.0.0", port=port
    )
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    log.info("listening on %s", addrs)
    async with server:
        await server.serve_forever()


async def main() -> None:
    log.info("HoneyJar starting. ports=%s webhook=%s", PORTS, "yes" if WEBHOOK_URL else "no")
    await asyncio.gather(*[serve_port(p) for p in PORTS])


if __name__ == "__main__":
    asyncio.run(main())
