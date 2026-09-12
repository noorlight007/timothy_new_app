from celery_app import celery

import os, json
from dotenv import load_dotenv
load_dotenv()

WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = "6984125oO!"

import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def process_webhook(self, payload: dict):
    """
    Do slow work here: DB writes, API calls, business logic
    """
    # print(payload)
    # your processing logic
    data = payload
    print(data)

    url = f"https://graph.facebook.com/v26.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    return 0

