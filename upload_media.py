import requests
import os, json
from dotenv import load_dotenv
load_dotenv()

WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def upload_pdf_to_meta(pdf_path: str):
    url = (
        f"https://graph.facebook.com/v26.0/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/media"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }

    with open(pdf_path, "rb") as pdf_file:
        files = {
            "file": (
                "Strategic_partners.pdf",
                pdf_file,
                "application/pdf"
            )
        }

        data = {
            "messaging_product": "whatsapp",
            "type": "application/pdf"
        }

        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

    print("Upload status:", response.status_code)
    print("Upload response:", response.text)

    response.raise_for_status()
    return response.json()["id"]


print(upload_pdf_to_meta("Strategic_partners.pdf"))