from celery_app import celery

import os, json
from dotenv import load_dotenv
load_dotenv()
import httpx
from message_ids import add_message_id
from utils import (extract_message_fields, get_businesses_by_industry, business_carousel_payload,
                   get_business_by_id, get_business_details_check_payload, get_businesses_by_category,
                   send_notification_talk_live_advisor, send_notification_interested_payload)

WHATSAPP_PHONE_NUMBER_ID=os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = "6984125oO!"

import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)



def send_whatsapp_message(sender: str, payload: dict, headers: dict, url: str):
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


def state_key(sender): 
    return f"wa:state:{sender}"

def data_key(sender):
    return f"wa:data:{sender}"

# State related
###############################
def get_state(sender):
    return r.get(state_key(sender))

def set_state(sender, state):
    r.setex(state_key(sender), 60*60, state)  # 60 minutes TTL

def clear_state(sender) -> bool:
    return r.delete(state_key(sender)) == 1
###############################

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

########  @@@@@@@  #######
def error_message_payload(sender):
    text = "Wrong keyword. Please try again."
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "text",
        "text": {
            "body": text.strip()
        }
    }

    return payload

def welcome_message_payload(sender):
    text = "👋 Welcome to MK Timothy & Company"
    text+= "\n\n🌍 Your next business opportunity starts here."
    text+= "\n\nPLooking to buy a business, invest or find the right partner in Uganda and East Africa? Let’s connect you."
    text+= "\n\nChoose your next move: 👇"

    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text.strip()},
            "footer": {
                "text": "🤝 Big opportunities begin with strong partnerships. Meet ours."
            },
            # "footer": {"text": footer_text},
            "action": {
                "button": "MENU",
                "sections": [
                    {
                        "title": "Seleccione desde aquí",
                        "rows": [
                            {
                            "id": "wlc_1",
                            "title": "Explore Businesses"
                            },
                            # {
                            # "id": "wlc_2",
                            # "title": "Investment Opportunities"
                            # },
                            {
                            "id": "wlc_3",
                            "title": "Our Solutions"
                            },
                            {
                            "id": "wlc_4",
                            "title": "Strategic Partners"
                            },
                            {
                            "id": "wlc_5",
                            "title": "Speak to an Advisor"
                            },
                            {
                            "id": "about_timothy",
                            "title": "MK Timothy & Business"
                            }


                        ],
                    }
                ]
            },
        },
    }

    return payload

def join_venture_starting_payload(sender):
    text= "You have chosen *Join Ventures*.\n\nNow please select an industry to continue."
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text.strip()},
            # "footer": {"text": footer_text},
            "action": {
                "button": "SELECT INDUSTRY",
                "sections": [
                    {
                        "title": "uuu",
                        "rows": [
                            {
                                "id": "Infrastructure",
                                "title": "Infrastructure"
                            },
                            {
                                "id": "Energy & Natural",
                                "title": "Energy & Natural"
                            },
                            {
                                "id": "Real Estate",
                                "title": "Real Estate"
                            },
                            {
                                "id": "ICT & Innovation",
                                "title": "ICT & Innovation"
                            },
                            {
                                "id": "Manufacturing",
                                "title": "Manufacturing"
                            },
                            {
                                "id": "go_back",
                                "title": "Back"
                            },
                            {
                                "id": "back_home",
                                "title": "Back to Home"
                            }

                        ],
                    }
                ]
            },
        },
    }

    return payload

def explore_business_payload(sender):
    text = "Thank you for your interest in checking the investment opportunities we are currently offering from MK Timothy & Company.\n\nPlease select the category first to continue."
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text.strip()},
            # "footer": {"text": footer_text},
            "action": {
                "button": "CATEGORIES",
                "sections": [
                    {
                        "title": "uuu",
                        "rows": [
                            {
                                "id": "sector_1",
                                "title": "Joint Venture"
                            },
                            {
                                "id": "sector_2",
                                "title": "Businesses for Sale"
                            },
                            {
                                "id": "sector_3",
                                "title": "Health Care"
                            },
                            {
                                "id": "sector_4",
                                "title": "Tourism & Hospitality"
                            },
                            {
                                "id": "sector_5",
                                "title": "Investment Projects"
                            },
                            {
                                "id": "back_home",
                                "title": "Back to Home"
                            }

                        ],
                    }
                ]
            },
        },
    }

    return payload

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



            msg_type, list_msg_id, button_msg_id, text_body, media_id, latitude, longitude = extract_message_fields(msg)
            # clear_state(sender)

            ########## Exceptional Flows ....
            print(button_msg_id)
            if button_msg_id: 
                if button_msg_id.startswith("pp_interest_"):
                    # interested in a property
                    business_id_str = button_msg_id.replace("pp_interest_", "")
                    business_id = business_id_str.strip()
                    business_info = get_business_by_id(business_id)
                    
                    set_data(sender, {"interested_business_info": business_info})

                    text = f"Thank you for showing interest for *{business_info['name']}*.\n\nIn order to continue to the next stage, please type in your name."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",

                        "interactive": {
                            "type": "button",

                            "body": {
                                "text": text.strip()
                            },

                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    set_state(sender, f"interested_name_asking")

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                elif button_msg_id.startswith("see_details_"):
                    business_id_str = button_msg_id.replace("see_details_", "")
                    business_id = business_id_str.strip()
                    business_info = get_business_by_id(business_id)
                    print("**** Business info: ")
                    # print(business_info)
                    # Media card
                    payload_new = get_business_details_check_payload(sender, business_info)

                    clear_state(sender)

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload_new, headers, url)
                    return "Okay"

                elif button_msg_id.startswith("back_home"):
                    payload = welcome_message_payload(sender)

                    # Update state for next step
                    set_state(sender, "welcome_message")
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                elif button_msg_id.startswith("back_about_timothy"):
                    text = f"Invest in Uganda now - a goldmine of growth, resources and unbeatable returns you can't afford to miss!\n\nClick on the button below to explore more about Mk Timothy & Company."
                                
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",
                        "interactive": {
                            "type": "list",
                            "body": {"text": text.strip()},
                            # "footer": {"text": footer_text},
                            "action": {
                                "button": "EXPLORE MORE",
                                "sections": [
                                    {
                                        "title": "uuu",
                                        "rows": [
                                            {
                                            "id": "about_1_1",
                                            "title": "Our Legacy"
                                            },
                                            {
                                            "id": "about_1_2",
                                            "title": "Invest in Uganda"
                                            },
                                            {
                                            "id": "about_1_3",
                                            "title": "Office locations"
                                            },
                                            {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                            }
            
                                        ],
                                    }
                                ]
                            },
                        },
                    }
            
                    # Update state for next step
                    set_state(sender, "about_timothy")
                    # clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"
                
                elif button_msg_id.startswith("speak_to_advisor"):
                    text = "Thank you for choosing Mk Timothy & Company.\n\n Sure. To proceed, type in your name please."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",

                        "interactive": {
                            "type": "button",

                            "body": {
                                "text": text.strip()
                            },

                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    set_state(sender, "live_agent_1_1")

                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

            ######################################
            ####### Welcome flow
            if not get_state(sender):

                payload = welcome_message_payload(sender)

                # Update state for next step
                set_state(sender, "welcome_message")

                # Send message to WhatsApp (sync httpx client)
                send_whatsapp_message(sender, payload, headers, url)
                return "Okay"
            ######################################
            ####### End of Welcome flow

            elif get_state(sender) == "welcome_message":

                print("Yes we are in")

                # Souce of explore businesses
                if msg_type == "interactive_list_reply" and list_msg_id == "wlc_1":
                    payload = explore_business_payload(sender)

                    # Update state for next step
                    set_state(sender, "explore_business")
                    # clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                # Our solutions and end of it
                elif msg_type == "interactive_list_reply" and list_msg_id == "wlc_3":
                    text = "We support companies, investors, governments, and development agencies to understand African markets, manage risk, access opportunities, and achieve sustainable growth."
                    text += "\n\n*Business Intelligence*"
                    text += "\nWe provide market insights, risk analysis, tailored intelligence, and opportunity and partner identification to help clients make informed decisions across Africa."
                    text += "\n\n*Stakeholder Engagement*"
                    text += "\nUsing our strong public and private sector networks, we help clients identify and engage key stakeholders, build partnerships, and support investment and expansion."
                    text += "\n\n*Sustainability Advisory*"
                    text += "\nWe help clients create and protect long-term value through ESG strategy, due diligence, sustainability consulting, auditing, and non-financial reporting."

                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",

                        "interactive": {
                            "type": "button",

                            "body": {
                                "text": text.strip()
                            },

                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "speak_to_advisor",
                                            "title": "Speak to an Advisor"
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    clear_state(sender)
                    
                    send_whatsapp_message(sender, payload, headers, url)
                    
                    return "Okay"
                
                # Source of Strategic Partners and end of it
                elif msg_type == "interactive_list_reply" and list_msg_id == "wlc_4":
                    text= "Here is the list of strategic partners of Mk Timothy & Business till today.\n\nThank you!"

                    payload = {
                        "messaging_product": "whatsapp",
                        
                        "to": sender,
                        "type": "document",
                        "document": {
                            "id": "1092247616611464",
                            "filename": "strategic partners.pdf",
                            "caption": text
                        }
                    }

                    clear_state(sender)

                    send_whatsapp_message(sender, payload, headers, url)
                    
                    return "Okay"

                # Source of Speak to an advisor
                elif msg_type == "interactive_list_reply" and list_msg_id == "wlc_5":
                    text = "Thank you, we will connect you with an advisor shortly.\n\nTo proceed, type in your name please."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",

                        "interactive": {
                            "type": "button",

                            "body": {
                                "text": text.strip()
                            },

                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    set_state(sender, "live_agent_1_1")

                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Source of About Mk Timothy
                elif msg_type == "interactive_list_reply" and list_msg_id == "about_timothy":
                    text = f"Invest in Uganda now - a goldmine of growth, resources and unbeatable returns you can't afford to miss!\n\nClick on the button below to explore more about Mk Timothy & Company."
            
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",
                        "interactive": {
                            "type": "list",
                            "body": {"text": text.strip()},
                            # "footer": {"text": footer_text},
                            "action": {
                                "button": "EXPLORE MORE",
                                "sections": [
                                    {
                                        "title": "uuu",
                                        "rows": [
                                            {
                                            "id": "about_1_1",
                                            "title": "Our Legacy"
                                            },
                                            {
                                            "id": "about_1_2",
                                            "title": "Invest in Uganda"
                                            },
                                            {
                                            "id": "about_1_3",
                                            "title": "Office locations"
                                            },
                                            {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                            }
            
                                        ],
                                    }
                                ]
                            },
                        },
                    }
            
                    # Update state for next step
                    set_state(sender, "about_timothy")
                    # clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

            
            ######################################
            ####### Explore Business flow
            elif get_state(sender) == "explore_business":

                # Join venture starting flow
                if msg_type == "interactive_list_reply" and list_msg_id == "sector_1":

                    payload = join_venture_starting_payload(sender)

                    # Update state for next step
                    set_state(sender, "explore_business_sector_1_industry")
                    # clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                # Business for Sale, Tourism and Investment starting flow
                elif msg_type == "interactive_list_reply" and (list_msg_id == "sector_2" or list_msg_id == "sector_4" or list_msg_id == "sector_5"):
                
                    real_category = ""
                    if list_msg_id == "sector_2":
                        real_category = "Businesses for Sale"
                    elif list_msg_id == "sector_4":
                        real_category = "Tourism & Hospitality"
                    else:
                        real_category = "Investment Projects"
                    
                    items = get_businesses_by_category(real_category)
                    payload = business_carousel_payload(sender, items)

                    # Update state for next step
                                        
                    clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                # Health Care
                elif msg_type == "interactive_list_reply" and list_msg_id == "sector_3":
                    # Exceptional
                    # Health Care
                    business_info = get_business_by_id(18)
                    payload = get_business_details_check_payload(sender, business_info)

                    clear_state(sender)
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"
                    

                # back to home
                elif msg_type == "interactive_list_reply" and list_msg_id == "back_home":

                    payload = welcome_message_payload(sender)

                    # Update state for next step
                    set_state(sender, "welcome_message")
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Error input
                else:
                    payload = error_message_payload(sender)
                                        
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

            ####### End of Explore business flow

            # Join Venture flow
            elif get_state(sender) == "explore_business_sector_1_industry":
                items = {}
                if msg_type == "interactive_list_reply" and list_msg_id != "go_back" and list_msg_id != "back_home":

                    if list_msg_id == "ICT & Innovation":
                        business_info = get_business_by_id(9)
                        payload = get_business_details_check_payload(sender, business_info)

                    else:

                        items = get_businesses_by_industry(list_msg_id)
                        payload = business_carousel_payload(sender, items)

                    # Update state for next step
                    
                    clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                elif msg_type == "interactive_list_reply" and list_msg_id == "go_back":
                    payload = explore_business_payload(sender)
                    
                    # Update state for next step
                    set_state(sender, "explore_business")
                    # clear_state(sender)
            
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"
                
                elif msg_type == "interactive_list_reply" and list_msg_id == "back_home":
                    payload = welcome_message_payload(sender)

                    # Update state for next step
                    set_state(sender, "welcome_message")
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Error input
                else:
                    payload = error_message_payload(sender)
                    
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"
                
            ####### End of Join Venture flow

            ######################################
            ####### Talk to Live agent flow
            elif get_state(sender) == "live_agent_1_1":
                user_name = text_body
                if not user_name or len(user_name) ==1:
                    text = "Name cannot be empty or one character only. Please write your name again."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {
                            "body": text.strip()
                        }
                    }

                    set_state(sender, "live_agent_1_1")

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                else:
                    text= f"Thank you {user_name}, one of our advisors will contact you shortly.\n\nIn the meantime, you can explore our business website. Thank you!"
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",
                        "interactive": {
                            "type": "cta_url",
                            "header": {
                                "type": "text",
                                "text": "Connecting an Advisor"
                            },
                            "body": {
                                "text": text.strip()
                            },
                            "footer": {
                                "text": "M.K. Timothy & Company"
                            },
                            "action": {
                                "name": "cta_url",
                                "parameters": {
                                    "display_text": "Explore Website",
                                    "url": "https://www.mktimothy.com/"
                                }
                            }
                        }
                    }
                    
                    # Sending the Notification message to Timothy first
                    timothy_notification_payload = send_notification_talk_live_advisor("12568881990", user_name, sender)
                    print("@@@@@@@@@@@@@@@@@@@@@@@@@")
                    print(timothy_notification_payload)
                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, timothy_notification_payload, headers, url)

                    clear_state(sender)

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"
                    
            ####### End of Talk to live agent flow

            ######################################
            ####### About Timothy flow
            elif get_state(sender) == "about_timothy":
                # our Legacy
                if msg_type == "interactive_list_reply" and list_msg_id == "about_1_1":
                    text = "Founded in 2016 by Ugandan-born Japanese angel investor and venture capitalist Musasizi Timothy Karubanga, Mk Timothy & Company supports investors and corporations operating in Uganda and worldwide. The company promotes Africa as a destination where profitable business opportunities can also create meaningful and sustainable development."
                    text+= "\nAs Africa's commercial landscape has evolved, Mk Timothy & Company has expanded its services across key industries shaping the continent's future. It supports respected investors and partners in sectors such as development finance, renewable energy, telecommunications, transportation, and logistics."
                    text+= "\nDespite its growing reach and diverse portfolio, the company remains committed to delivering exceptional service, helping clients achieve their operational and investment goals while generating lasting value for investors and African communities."
                    text+= "\nMk Timothy & Company's mission is to advance sustainable and equitable investment across Africa while encouraging international entrepreneurs to explore the many opportunities available in Uganda. It is where Africa's potential connects with global ambition."

                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",

                        "interactive": {
                            "type": "button",

                            "body": {
                                "text": text.strip()
                            },

                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "back_about_timothy",
                                            "title": "Back"
                                        }
                                    },
                                    {
                                        "type": "reply",
                                        "reply": {
                                            "id": "back_home",
                                            "title": "Back to Home"
                                        }
                                    }
                                ]
                            }
                        }
                    }

                    clear_state(sender)
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Invest in Uganda
                elif msg_type == "interactive_list_reply" and list_msg_id == "about_1_2":
                    text = "*Why Invest in Uganda?*"
                    text += "\nUganda offers a secure, inclusive free-market environment, a young population, abundant natural resources, and a rapidly expanding economy. Priority sectors include agriculture, infrastructure, oil and natural resources, and technology, aligned with sustainable development goals."

                    text += "\n\n*Favorable Legislation and Policy*"
                    text += "\nThe Public-Private Partnership Act of 2015 encourages foreign and local investment. Supportive government policies strengthen Uganda's potential to become an important economic hub in Africa."

                    text += "\n\n*Ready Markets*"
                    text += "\nUganda provides access to growing domestic, regional, and international markets. Regional integration, including the African Continental Free Trade Area, supports increased trade, job creation, poverty reduction, and sustainable economic growth."

                    text += "\n\n*Fast-Growing Economy*"
                    text += "\nUganda has demonstrated strong long-term growth, with GDP approximately doubling each decade between 1990 and 2010. Stable macroeconomic policies, private-sector support, and resilience to global shocks continue to create opportunities across multiple sectors."

                    text += "\n\n*Investment Incentives*"
                    text += "\nQualifying foreign investors making capital investments of at least $500,000 may receive reduced import duties on machinery, equipment, vehicles, and construction materials; exemptions for eligible personal imports; tax and customs benefits for start-ups; and duty drawbacks on imported inputs used to produce export goods."

                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {
                            "body": text.strip()
                        }
                    }

                    clear_state(sender)
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Office Locations
                elif msg_type == "interactive_list_reply" and list_msg_id == "about_1_3":

                    text = "We are operating in multiple locations around the world, especially in Africa.\n\n*Uganda*\nHome and Office complex\n\n*Kenya*\n308-8988 Fraserton Court\n\n*South Sudan*\nHai Malakal, Juba, South Sudan\n\n*South Africa*\nBlack River Park, Fir St\n\n*Japan*\nMetropolitan Road 319, Kanjo"
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {
                            "body": text.strip()
                        }
                    }

                    clear_state(sender)
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Back to Home
                elif msg_type == "interactive_list_reply" and list_msg_id == "back_home":

                    payload = welcome_message_payload(sender)
                    # Update state for next step
                    set_state(sender, "welcome_message")
                    # Send message to WhatsApp
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"

                # Error input
                else:
                    payload = error_message_payload(sender)

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)

                    return "Okay"
            ####### End of About Timothy flow

            elif get_state(sender) == "interested_name_asking":
                name = text_body
                if not name or len(name) == 1:
                    text = "Wrong method of writing a name. Please type in your name again."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {
                            "body": text.strip()
                        }
                    }

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

                else:
                    # TODO - Send User info and the selected business info to the Admin's whatsApp
                    text = f"*Thank you {name} for submitting your interest!*\n\nOne of our advisors will contact with you soon."
                    text+= f"\n\nIn the meantime, you can explore our website for more business offers."
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "interactive",
                        "interactive": {
                            "type": "cta_url",
                            "header": {
                                "type": "text",
                                "text": "Connecting an Advisor"
                            },
                            "body": {
                                "text": text.strip()
                            },
                            "footer": {
                                "text": "M.K. Timothy & Company"
                            },
                            "action": {
                                "name": "cta_url",
                                "parameters": {
                                    "display_text": "Explore Website",
                                    "url": "https://www.mktimothy.com/"
                                }
                            }
                        }
                    }

                    notification_payload = send_notification_interested_payload("8801571238110", name, sender, get_data(sender).get("interested_business_info"))
                    send_whatsapp_message("12568881990", notification_payload, headers, url)

                    clear_data(sender)
                    clear_state(sender)

                    # Send message to WhatsApp (sync httpx client)
                    send_whatsapp_message(sender, payload, headers, url)
                    return "Okay"

            else:
                print("Don't understand")
                clear_state(sender)
                return "Okay"




