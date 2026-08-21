from typing import Optional

from firebase_admin import messaging


def send_push(
    token: str, title: str, body: str, data: Optional[dict] = None
) -> str:
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    return messaging.send(message)
