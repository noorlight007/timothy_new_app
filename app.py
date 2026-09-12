import os, json, asyncio

from typing import Any, Dict
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Query
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-bot")

VERIFY_TOKEN = "6984125oO!?"  # keep exactly as your Flask code

app = FastAPI()

http_client: httpx.AsyncClient | None = None

@app.on_event("startup")
async def startup():
    global http_client
    http_client = httpx.AsyncClient(timeout=30)
    logger.info("✅ FastAPI startup complete")


@app.on_event("shutdown")
async def shutdown():
    global http_client
    if http_client:
        await http_client.aclose()
        logger.info("🛑 http_client closed")

def is_inbound_message_event(data: dict) -> bool:
    """
    Same logic as your Flask version:
    if payload has 'statuses' under entry[0].changes[0].value -> not inbound message
    """
    value = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
    if "statuses" in value:
        return False
    return True

@app.get("/webhook")
async def verify(
    mode: str | None = Query(None, alias="hub.mode"),
    token: str | None = Query(None, alias="hub.verify_token"),
    challenge: str | None = Query(None, alias="hub.challenge"),
):
    token_ok = (token == VERIFY_TOKEN)
    logger.info("VERIFY hit mode=%s token_ok=%s", mode, token_ok)

    if mode == "subscribe" and token_ok:
        # Meta expects the plain challenge string
        return PlainTextResponse(content=challenge or "", status_code=200)

    return PlainTextResponse(content="Forbidden", status_code=403)


@app.post("/webhook")
async def receive(request: Request):
    logger.info("POST /webhookone hit. headers=%s", dict(request.headers))

    try:
        data: Dict[str, Any] = await request.json()
    except Exception:
        data = {}

    # print(data)

    try:
        if not is_inbound_message_event(data):
            logger.info("Not a valid message event (likely statuses).")
            return PlainTextResponse(content="ok", status_code=200)

        # Keep your Celery async processing
        # process_webhook.delay(data)
        print(data)

        return PlainTextResponse(content="okay", status_code=200)

    except Exception as e:
        logger.exception("Error processing webhook: %s", str(e))
        return PlainTextResponse(content="okay", status_code=500)
