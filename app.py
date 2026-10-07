import os, json, asyncio

from typing import Any, Dict
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Query, UploadFile, File, Form, HTTPException
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
import httpx
import logging
from pathlib import Path
from uuid import uuid4
import mimetypes

from tasks import process_webhook  # your Celery task
from message_ids import add_message_id
from utils import extract_message_fields
from users_db import store_user, store_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-bot")

VERIFY_TOKEN = "6984125oO!"  # keep exactly as your Flask code
WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
STATIC_DIR = Path("static/whatsapp_media")

http_client: httpx.AsyncClient | None = None

ALLOWED_MEDIA = {
    "image": {
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
    },
    "video": {
        "video/mp4": [".mp4"],
        "video/3gpp": [".3gp"],
    },
    "audio": {
        "audio/aac": [".aac"],
        "audio/mpeg": [".mp3"],
        "audio/mp4": [".m4a"],
        "audio/ogg": [".ogg"],
        "audio/amr": [".amr"],
    },
    "document": {
        "application/pdf": [".pdf"],
        "application/msword": [".doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
        "application/vnd.ms-excel": [".xls"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
        "application/vnd.ms-powerpoint": [".ppt"],
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
        "text/plain": [".txt"],
    },
}

def validate_media_file(
    media_type: str,
    filename: str,
    content_type: str,
):
    if media_type not in ALLOWED_MEDIA:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported media type: {media_type}"
        )

    allowed_types = ALLOWED_MEDIA[media_type]

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}"
        )

    extension = Path(filename).suffix.lower()

    if extension not in allowed_types[content_type]:
        raise HTTPException(
            status_code=400,
            detail="File extension does not match the file MIME type."
        )


def create_media_payload(
    sender: str,
    media_type: str,
    media_url: str,
    caption: str | None = None,
):
    if media_type not in ["image", "video", "audio", "document"]:
        raise ValueError(
            "Invalid media type. "
            "Allowed: image, video, audio, document"
        )

    media_data = {
        "link": media_url
    }
    text_payload = None
    if media_type == "audio":
        if caption:
            # Send text message first, then audio
            # because WhatsApp Cloud API does not support caption for audio
            text_payload = {
                "messaging_product": "whatsapp",
                "to": sender,
                "type": "text",
                "text": {"body": caption.strip()}
            }

    if caption and media_type in ["image", "video", "document"]:
        media_data["caption"] = caption.strip()

    return text_payload,{
        "messaging_product": "whatsapp",
        "to": sender,
        "type": media_type,
        media_type: media_data
    }


def save_whatsapp_media(file: UploadFile, media_type: str):
    validate_media_file(
        media_type=media_type,
        filename=file.filename,
        content_type=file.content_type,
    )

    STATIC_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    extension = Path(file.filename).suffix.lower()

    filename = f"{uuid4().hex}{extension}"

    file_path = STATIC_DIR / filename

    with open(file_path, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)

            if not chunk:
                break

            buffer.write(chunk)

    return filename


def send_whatsapp_message(payload: dict, headers: dict, url: str):
    """Helper function to send WhatsApp messages"""
    with httpx.Client() as client:
        resp = client.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print("\n========== WHATSAPP DEBUG ==========")
        print("URL:")
        print(url)

        print("\nSTATUS:")
        print(resp.status_code)

        print("\nREQUEST PAYLOAD:")
        print(json.dumps(payload, indent=2))

        print("\nMETA RESPONSE BODY:")
        print(resp.text)

        try:
            print("\nMETA RESPONSE JSON:")
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            pass

        print("====================================\n")

        if not resp.is_success:
            return {
                "success": False,
                "status_code": resp.status_code,
                "response": resp.text
            }

        return resp.json()

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

        profile_name = None
        sender = None

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
    
                # Profile name (if present)
                profile_name = None
                try:
                    profile_name = value["contacts"][0]["profile"]["name"]
                    print(f"Profile name = {profile_name}")
                except Exception:
                    pass
    
                messages = value.get("messages")
                if not messages:
                    continue  # could be a status/event update
    
                msg = messages[0]
                print(msg)
                msg_id = msg.get("id")
    
                new_msg_check = add_message_id(msg_id)
                if not new_msg_check:
                    print("🔁 Duplicate message. Skipping.")
                    return "okay", 200     
    
                # Sender WhatsApp ID (phone number in international format without +)
                sender = msg.get("from")
                print(f"👤 Sender = {sender}")
    
                # clear_data(sender)
    
                msg_type, list_msg_id, button_msg_id, text_body, media_id, latitude, longitude = extract_message_fields(msg)
                
                if button_msg_id:
                    text_body = button_msg_id

        user = store_user(
            wp_number=sender,
            wp_name=profile_name
        )

        store_message(
            wp_number=sender,
            role="user",
            content=text_body
        )

        if user.auto_bot_reply:
            print("Auto bot reply is enabled. Sending auto reply...")
            # Keep your Celery async processing
            process_webhook.delay(data)
            print("sent")
        # print(data)

        return PlainTextResponse(content="okay", status_code=200)

    except Exception as e:
        logger.exception("Error processing webhook: %s", str(e))
        return PlainTextResponse(content="okay", status_code=500)


## Send Admin message to user
@app.post("/admin/whatsapp/send")
async def admin_send_whatsapp(
    wp_number: str = Form(...),
    message_type: str = Form(...),
    message: str | None = Form(None),
    media_type: str | None = Form(None),
    media: UploadFile | None = File(None),
):
    """
    message_type:
        text
        media
    """

    if message_type == "text":

        if not message:
            raise HTTPException(
                status_code=400,
                detail="Message is required."
            )

        # Send text through WhatsApp Cloud API
        # await send_whatsapp_text(wp_number, message)

        # Store admin message
        store_message(
            wp_number=wp_number,
            role="admin",
            content=message
        )

        return {
            "success": True,
            "message": "Text message sent successfully."
        }

    elif message_type == "media":

        if not media:
            raise HTTPException(
                status_code=400,
                detail="Media file is required."
            )

        if not media_type:
            raise HTTPException(
                status_code=400,
                detail="media_type is required."
            )

        filename = save_whatsapp_media(
            file=media,
            media_type=media_type
        )

        # Public URL
        base_url = os.getenv("PUBLIC_BASE_URL")

        if not base_url:
            raise HTTPException(
                status_code=500,
                detail="PUBLIC_BASE_URL is not configured."
            )

        media_url = (
            f"{base_url.rstrip('/')}"
            f"/static/whatsapp_media/{filename}"
        )

        # Send through WhatsApp Cloud API
        url = f"https://graph.facebook.com/v26.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        

        text_msg_payload , media_payload = create_media_payload(wp_number, media_type, media_url, caption=message)

        if text_msg_payload:
            # Send text message first
            send_whatsapp_message(text_msg_payload, headers, url)

        if media_payload:
            send_whatsapp_message(media_payload, headers, url)

        history_content = media_url

        if message:
            history_content = f"{message}\n{media_url}"

        store_message(
            wp_number=wp_number,
            role="admin",
            content=history_content
        )

        return {
            "success": True,
            "message": "Media message sent successfully.",
            "media_url": media_url
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="message_type must be 'text' or 'media'."
        )


## Get all whatsapp contacts from the database
@app.get("/get_all_contacts")
async def get_all_contacts(request: Request):
    return "okay"


## Turn off or On auto bot reply for a user
@app.post("/turn_off_on_auto_bot")
async def turn_off_on_auto_bot(request: Request):
    return "okay"