from mongoengine import *
from datetime import datetime


# MongoDB connection
connect(
    host="mongodb://127.0.0.1:27017/timothy?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.7.0"
)


class MessageHistory(EmbeddedDocument):
    role = StringField(
        required=True,
        choices=["user", "bot", "admin"]
    )
    content = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)


class WpUser(Document):
    id = SequenceField(primary_key=True)

    wp_name = StringField(required=True)
    wp_number = StringField(required=True, unique=True)

    auto_bot_reply = BooleanField(default=True)

    message_history = ListField(
        EmbeddedDocumentField(MessageHistory),
        default=list
    )
    last_user_message_datetime = DateTimeField()

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "indexes": [
            "wp_name",
            "wp_number",
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


# ============================================================
# USER FUNCTIONS
# ============================================================

def store_user(wp_name, wp_number):
    """
    Create and store a new WhatsApp user.

    If the WhatsApp number already exists, the existing user
    will be returned instead of creating a duplicate.
    """

    user = WpUser.objects(wp_number=wp_number).first()

    if user:
        return user

    user = WpUser(
        wp_name=wp_name,
        wp_number=wp_number
    )

    user.save()

    return user


def find_user(wp_number=None, wp_name=None):
    """
    Find a WhatsApp user by WhatsApp number or username.

    Priority:
        1. wp_number
        2. wp_name

    Returns:
        WpUser object or None
    """

    if wp_number:
        user = WpUser.objects(wp_number=wp_number).first()

        if user:
            return user

    if wp_name:
        return WpUser.objects(wp_name=wp_name).first()

    return None


def delete_user(wp_number=None, wp_name=None):
    """
    Delete a user by WhatsApp number or username.

    Returns:
        True if deleted
        False if user was not found
    """

    user = find_user(
        wp_number=wp_number,
        wp_name=wp_name
    )

    if not user:
        return False

    user.delete()

    return True


def update_user(
    wp_number,
    wp_name=None,
    new_wp_number=None,
    auto_bot_reply=None
):
    """
    Update user information.

    Only the values that are not None will be updated.

    Returns:
        Updated WpUser object or None
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    if wp_name is not None:
        user.wp_name = wp_name

    if new_wp_number is not None:
        user.wp_number = new_wp_number

    if auto_bot_reply is not None:
        user.auto_bot_reply = auto_bot_reply

    user.save()

    return user


def store_message(
    wp_number,
    role,
    content
):
    """
    Store a new message in the user's message history.

    role must be:
        user
        bot
        admin

    If role == 'admin':
        auto_bot_reply will automatically be disabled.
    """

    if role not in ["user", "bot", "admin"]:
        raise ValueError(
            "Invalid role. Role must be 'user', 'bot', or 'admin'."
        )

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    message = MessageHistory(
        role=role,
        content=content,
        created_at=datetime.utcnow()
    )

    user.message_history.append(message)


    # Admin has taken over the conversation.
    if role == "admin":
        user.auto_bot_reply = False

    if role == "user":
        user.last_user_message_datetime = datetime.utcnow()

    user.save()

    return user


def turn_on_auto_bot(wp_number):
    """
    Turn ON automatic bot replies for a user.
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    user.auto_bot_reply = True
    user.save()

    return user


def turn_off_auto_bot(wp_number):
    """
    Turn OFF automatic bot replies for a user.
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    user.auto_bot_reply = False
    user.save()

    return user

def check_auto_bot_status(wp_number):
    """
    Check if automatic bot replies are ON or OFF for a user.

    Returns:
        True if ON
        False if OFF
        None if user not found
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    return user.auto_bot_reply


def get_message_history(wp_number):
    """
    Get the message history for a user.

    Returns:
        List of MessageHistory objects or None if user not found
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    return user.message_history


def clear_message_history(wp_number):
    """
    Clear the message history for a user.

    Returns:
        True if cleared
        False if user not found
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return False

    user.message_history = []
    user.save()

    return True

def check_if_last_message_within_timeframe(wp_number, timeframe_minutes):
    """
    Check if the last user message was sent within a specified timeframe.

    Returns:
        True if the last message was sent within the timeframe
        False if it was sent outside the timeframe or if no messages exist
        None if user not found
    """

    user = find_user(wp_number=wp_number)

    if not user:
        return None

    last_message_time = user.last_user_message_datetime

    if not last_message_time:
        return False  # No messages have been sent by the user

    current_time = datetime.utcnow()
    time_difference = current_time - last_message_time

    return time_difference.total_seconds() <= (timeframe_minutes * 60)