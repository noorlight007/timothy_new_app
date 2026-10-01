from celery_app import celery

import os, json
from dotenv import load_dotenv
load_dotenv()
import httpx
from message_ids import add_message_id
from utils import (extract_message_fields, get_businesses_by_industry, business_carousel_payload,
                   get_business_by_id, get_business_details_check_payload, get_businesses_by_category,
                   send_notification_talk_live_advisor, send_notification_interested_payload)

from instructions import get_the_instruction
import json

WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = "6984125oO!"
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

import anthropic
deepseek_client = anthropic.Anthropic(
    api_key= ANTHROPIC_API_KEY,
    base_url= ANTHROPIC_BASE_URL
)


def data_key(sender):
    return f"wa:data:{sender}"

# Data related
###############################
def get_data(sender) -> dict:
    """Get stored conversation data for a user"""
    data = r.get(data_key(sender))
    if data:
        return json.loads(data)
    return {}

def set_data(sender, data: dict):
    """Store conversation data for a user"""
    r.setex(data_key(sender), 60*60, json.dumps(data))  # 60 minutes TTL

def update_data(sender, key: str, value: any):
    """Update a specific field in user's conversation data"""
    data = get_data(sender)
    data[key] = value
    set_data(sender, data)

def clear_data(sender) -> bool:
    """Clear all stored data for a user"""
    return r.delete(data_key(sender)) == 1
###############################

# Conversation history
###############################

def get_history(sender) -> list:
    """Get conversation history for a WhatsApp user."""

    data = get_data(sender)

    return data.get("messages", [])


def add_message(sender, role: str, text_content: str):
    """Add a message to the user's conversation history."""

    data = get_data(sender)

    messages = data.get("messages", [])

    messages.append({
        "role": role,
        "content": [
            {
                "type": "text",
                "text": text_content
            }
        ]
    })

    data["messages"] = messages

    set_data(sender, data)


def clear_history(sender) -> bool:
    """Clear only the conversation history."""

    data = get_data(sender)

    if "messages" not in data:
        return False

    del data["messages"]

    set_data(sender, data)

    return True

###############################

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

# Get deepseek generated response
def get_deepseek_response_text(message) -> str:
    """Extract text content from an Anthropic API response."""

    for block in message.content:
        if block.type == "text":
            return block.text

    return ""


tools = [
    {
        "name": "show_catalog_business",
        "description": (
            "Use this tool ONLY when the user wants to see, browse, "
            "explore, or get information about businesses that MK Timothy "
            "and Company offers. When the user selects a business category, "
            "you MUST provide the selected category as the 'topic' parameter. "
            "The topic must be exactly one of the allowed values. "
            "Do NOT use this tool for strategic partners or speaking to an advisor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [
                        "Infrastructure",
                        "Energy & Natural",
                        "Real Estate",
                        "ICT & Innovation",
                        "Manufacturing",
                        "Health Care",
                        "Businesses for Sale",
                        "Tourism & Hospitality",
                        "Investment Projects"
                    ],
                    "description": (
                        "The business category selected by the user. "
                        "Must be exactly one of the allowed topic values."
                    )
                }
            },
            "required": ["topic"]
        }
    },

    {
        "name": "fetch_partners",
        "description": (
            "Use this tool ONLY when the user wants to see, browse, or get "
            "information about MK Timothy and Company's strategic partners. "
            "Examples include 'show me your strategic partners', "
            "'who are your partners', or 'I want to see your partners'. "
            "Do NOT use this tool for businesses, investment sectors, "
            "or speaking to an advisor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    {
        "name": "speak_direct",
        "description": (
            "Use this tool when the user wants to speak directly with an "
            "advisor or wants an advisor to contact them. The user must "
            "provide their name before this tool is called. Extract the "
            "user's name and provide it as the 'name' parameter. "
            "If the user wants to speak with an advisor but has not provided "
            "their name, DO NOT call this tool; ask the user for their name first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The user's name."
                }
            },
            "required": ["name"]
        }
    }
]


def serialize_content_blocks(content_blocks):
    serialized = []

    for block in content_blocks:
        if block.type == "thinking":
            serialized.append({
                "type": "thinking",
                "thinking": block.thinking,
                "signature": block.signature
            })

        elif block.type == "text":
            serialized.append({
                "type": "text",
                "text": block.text
            })

        elif block.type == "tool_use":
            serialized.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input
            })

    return serialized

def add_message_raw(sender, role, content):
    data = get_data(sender)
    messages = data.get("messages", [])

    messages.append({
        "role": role,
        "content": content
    })

    data["messages"] = messages
    set_data(sender, data)



def add_tool_results(sender, tool_results):
    data = get_data(sender)

    messages = data.get("messages", [])

    messages.append({
        "role": "user",
        "content": tool_results
    })

    data["messages"] = messages

    set_data(sender, data)

@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def process_webhook(self, payload: dict):
    
    
    data = payload
    # print(data)

    url = f"https://graph.facebook.com/v26.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

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

            add_message(sender, "user", text_body)

            message = deepseek_client.messages.create(
                model="deepseek-flash",
                max_tokens=1000,
                system= get_the_instruction(),
                tools = tools,
                messages= get_history(sender)
            )

            tool_results = []

            # Convert SDK objects -> JSON-compatible dictionaries
            assistant_content = serialize_content_blocks(message.content)

            for block in message.content:
                if block.type != "tool_use":
                    continue
                # print(block)

                if block.name == "show_catalog_business":
                    topic = block.input.get("topic")
                    print(f"Topic: {topic}")
                    result = {
                        "is_active": True
                    }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"sent": "okay"}, ensure_ascii=False)
                })

            # Store DeepSeek's complete response:
            # thinking + text + tool_use
            add_message_raw(
                sender,
                "assistant",
                assistant_content
            )

            if tool_results:

                # IMPORTANT:
                # Save DeepSeek's complete response containing tool_use
                add_message_raw(
                    sender,
                    "user",
                    tool_results
                )

                # # Save tool results as actual tool_result blocks
                # add_tool_results(
                #     sender,
                #     tool_results
                # )
                

                



            deepseek_resposne = message
            final_response = get_deepseek_response_text(deepseek_resposne)
            print(final_response)

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": sender,
                "type": "text",
                "text": {
                    "body": final_response
                }
            }

            
            send_whatsapp_message(payload, headers, url)

            # add_message(sender, "assistant", final_response)

            return "okay"