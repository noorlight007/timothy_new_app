import json

def get_businesses_by_industry(industry: str) -> list:
    """
    Get businesses from the JSON catalogue by industry.

    Matching is case-insensitive.

    Example:
        get_businesses_by_industry(
            "mk_timothy_business_catalogue_recategorized.json",
            "Tourism & Hospitality"
        )
    """

    json_file_path = "businesses.json"

    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            businesses = json.load(file)

        search_industry = industry.strip().lower()

        results = [
            business
            for business in businesses["businesses"]
            if str(business.get("industry", "")).strip().lower()
            == search_industry or search_industry in str(business.get("industry", "")).strip().lower()
        ]

        return results

    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")
        return []

    except json.JSONDecodeError:
        print("Invalid JSON file.")
        return []

    except Exception as e:
        print(f"Error reading catalogue: {e}")
        return []

def get_businesses_by_category(category: str) -> list:
    """
    Get businesses from the JSON catalogue by industry.

    Matching is case-insensitive.

    Example:
        get_businesses_by_industry(
            "mk_timothy_business_catalogue_recategorized.json",
            "Tourism & Hospitality"
        )
    """

    json_file_path = "businesses.json"

    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            businesses = json.load(file)

        search_category = category.strip().lower()

        results = [
            business
            for business in businesses["businesses"]
            if str(business.get("category", "")).strip().lower()
            == search_category or search_category in str(business.get("category", "")).strip().lower()
        ]

        return results

    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")
        return []

    except json.JSONDecodeError:
        print("Invalid JSON file.")
        return []

    except Exception as e:
        print(f"Error reading catalogue: {e}")
        return []


def get_business_by_id(business_id: int):
    """
    Return a specific business from the JSON catalogue by its internal ID.

    Returns:
        dict  -> if business is found
        None  -> if no matching business exists
    """
    json_file_path = "businesses.json"
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            businesses = json.load(file)

        business_id = int(business_id)

        for business in businesses['businesses']:
            if business.get("id") == business_id:
                return business

        return None

    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")
        return None

    except json.JSONDecodeError:
        print("Invalid JSON file.")
        return None

    except (TypeError, ValueError):
        print(f"Invalid business ID: {business_id}")
        return None

    except Exception as e:
        print(f"Error loading business: {e}")
        return None


def extract_message_fields(msg: dict):
    """
    Extract commonly used fields from a WhatsApp Cloud API message.

    Returns:
        (
            msg_type,
            list_msg_id,
            button_msg_id,
            text_body,
            media_id,
            latitude,
            longitude,
        )
    """

    msg_type = msg.get("type")

    list_msg_id = None
    button_msg_id = None
    text_body = None
    media_id = None
    latitude = None
    longitude = None

    # --------------------------------------------------
    # TEXT MESSAGE
    # --------------------------------------------------
    if msg_type == "text":
        text_body = msg.get("text", {}).get("body")

    # --------------------------------------------------
    # INTERACTIVE MESSAGE
    # List reply / Reply button
    # --------------------------------------------------
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        interactive_type = interactive.get("type")

        # User clicked a list item
        if interactive_type == "list_reply":
            msg_type = "interactive_list_reply"
            list_reply = interactive.get("list_reply", {})

            list_msg_id = list_reply.get("id")

            # Optional: useful if you want the visible title too
            text_body = list_reply.get("title")

        # User clicked an interactive reply button
        elif interactive_type == "button_reply":
            msg_type = "interactive_button_reply"
            button_reply = interactive.get("button_reply", {})

            button_msg_id = button_reply.get("id")

            # Visible button text
            text_body = button_reply.get("title")

    # --------------------------------------------------
    # OLD / TEMPLATE BUTTON MESSAGE
    # --------------------------------------------------
    elif msg_type == "interactive_button_reply":
        button = msg.get("button", {})

        # Button payload is normally what you should use
        button_msg_id = button.get("payload")

        # Visible button text
        text_body = button.get("text")

    # --------------------------------------------------
    # IMAGE
    # --------------------------------------------------
    elif msg_type == "image":
        image = msg.get("image", {})

        media_id = image.get("id")
        text_body = image.get("caption")

    # --------------------------------------------------
    # VIDEO
    # --------------------------------------------------
    elif msg_type == "video":
        video = msg.get("video", {})

        media_id = video.get("id")
        text_body = video.get("caption")

    # --------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------
    elif msg_type == "document":
        document = msg.get("document", {})

        media_id = document.get("id")

        # Prefer caption, otherwise filename
        text_body = (
            document.get("caption")
            or document.get("filename")
        )

    # --------------------------------------------------
    # AUDIO
    # --------------------------------------------------
    elif msg_type == "audio":
        audio = msg.get("audio", {})
        media_id = audio.get("id")

    # --------------------------------------------------
    # STICKER
    # --------------------------------------------------
    elif msg_type == "sticker":
        sticker = msg.get("sticker", {})
        media_id = sticker.get("id")

    # --------------------------------------------------
    # LOCATION
    # --------------------------------------------------
    elif msg_type == "location":
        location = msg.get("location", {})

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        # Optional descriptive location information
        location_name = location.get("name")
        location_address = location.get("address")

        if location_name and location_address:
            text_body = f"{location_name} - {location_address}"
        elif location_name:
            text_body = location_name
        elif location_address:
            text_body = location_address

    # --------------------------------------------------
    # CONTACT MESSAGE
    # --------------------------------------------------
    elif msg_type == "contacts":
        contacts = msg.get("contacts", [])

        if contacts:
            contact = contacts[0]

            name = contact.get("name", {})
            text_body = name.get("formatted_name")

    # --------------------------------------------------
    # REACTION
    # --------------------------------------------------
    elif msg_type == "reaction":
        reaction = msg.get("reaction", {})

        # Emoji itself
        text_body = reaction.get("emoji")

        # Message being reacted to
        button_msg_id = reaction.get("message_id")

    elif msg_type == "button":
        button_reply = msg.get("button", {})
        button_msg_id = button_reply["payload"]
        text_body = button_reply["text"]


    # --------------------------------------------------
    # UNKNOWN / UNSUPPORTED
    # --------------------------------------------------
    else:
        print(f"⚠️ Unsupported message type: {msg_type}")

    return (
        msg_type,
        list_msg_id,
        button_msg_id,
        text_body,
        media_id,
        latitude,
        longitude,
    )


# print(get_businesses_by_industry("Energy & Natural"))

def business_carousel_payload(sender, businesses):
    """
    Send an interactive WhatsApp media carousel.

    businesses:
        Maximum 10 records.
        Minimum 2 records.
    """

    if len(businesses) < 2:
        raise ValueError("Carousel requires at least 2 businesses.")

    # WhatsApp allows max 10 cards
    businesses = businesses[:10]

    cards = []

    for index, business in enumerate(businesses):

        # Keep body short:
        # max 160 chars and max 2 line breaks
        card_body = (
            f"*{business['name']}*\n"
            f"📍 {business['country']} · {business['category']}\n"
            f"💰 {business['price']}"
        )

        card = {
            "card_index": index,

            # Current carousel schema uses this card-level type
            "type": "cta_url",

            "header": {
                "type": "image",
                "image": {
                    "link": business["image_url"]
                }
            },

            "body": {
                "text": card_body
            },

            "action": {
                "buttons": [

                    # --------------------------------
                    # INTERESTED
                    # --------------------------------
                    {
                        "type": "quick_reply",
                        "quick_reply": {
                            "id": f"pp_interest_{business['id']}",
                            "title": "Interested"
                        }
                    },

                    # --------------------------------
                    # VIEW MORE
                    # --------------------------------
                    {
                        "type": "quick_reply",
                        "quick_reply": {
                            "id": f"see_details_{business['id']}",
                            "title": "See Details"
                        }
                    }

                ]
            }
        }

        cards.append(card)

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "carousel",

            "body": {
                "text": (
                    "🏢 *Explore Business Opportunities*\n\n"
                    "Swipe through the available opportunities below."
                )
            },

            "action": {
                "cards": cards
            }
        }
    }

    return payload


def get_business_details_check_payload(sender, business):
    text = f"Name: {business['name']}"
    text+= f"\nCountry: {business['country']}"
    text+= f"\nBusiness Category: {business['category']}"
    text+= f"\nIndustry: {business['industry']}"
    text+= f"\nOpportunity type: {business['opportunity_type']}"
    text+= f"\nBudget: {business['price']}"
    text+= f"\n\nFor more details, check the website link: {business['details_url']}"
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",

        "interactive": {
            "type": "button",

            "header": {
                "type": "image",
                "image": {
                    "link": business['image_url']
                }
            },

            "body": {
                "text": text.strip()
            },
            "footer": {
                "text": "M.K. Timothy & Company"
            },

            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"pp_interest_{business['id']}",
                            "title": "Interested"
                        }
                    }
                ]
            }
        }
    }

    return payload


# Talk to live advisor - send notification to the admins

def send_notification_talk_live_advisor(receipient_whatsApp, user_name, user_whatsapp):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": receipient_whatsApp,
        "type": "template",

        "template": {
            "name": "req_to_connect",

            "language": {
                "code": "en"
            },

            "components": [
                {
                    "type": "body",

                    "parameters": [
                        # {{1}}
                        {
                            "type": "text",
                            "text": user_name
                        },

                        # {{2}}
                        {
                            "type": "text",
                            "text": user_whatsapp
                        }
                    ]
                }
            ]
        }
    }

    return payload



def send_notification_interested_payload(receipient_whatsApp, user_name, user_whatsapp, business_details : dict):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": receipient_whatsApp,
        "type": "template",

        "template": {
            "name": "inter_busi",

            "language": {
                "code": "en"
            },

            "components": [
                {
                    "type": "body",

                    "parameters": [
                        # {{1}}
                        {
                            "type": "text",
                            "text": user_name
                        },

                        # {{2}}
                        {
                            "type": "text",
                            "text": user_whatsapp
                        },

                        # {{3}}
                        {
                            "type": "text",
                            "text": business_details['name']
                        },

                        # {{4}}
                        {
                            "type": "text",
                            "text": business_details['country']
                        },

                        # {{5}}
                        {
                            "type": "text",
                            "text": business_details['category']
                        }
                    ]
                }
            ]
        }
    }

    return payload