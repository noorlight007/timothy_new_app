import httpx
import json
import os
from dotenv import load_dotenv
load_dotenv()

WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def get_template_info(template_name: str):
    url = (
        f"https://graph.facebook.com/"
        f"v26.0/2472096733287820/message_templates"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    params = {
        "name": template_name
    }

    response = httpx.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:")
    print(
        json.dumps(
            response.json(),
            indent=2
        )
    )

    return response.json()


get_template_info("req_to_connect")