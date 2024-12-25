import os
import requests
import time

PUSH_API_KEY = os.getenv("PUSH_API_KEY")
PUSH_USER_KEY = os.getenv("PUSH_USER_KEY")


last_send = time.time() - 6 * 3600


def send_push_notification(message: str):
    try:
        print(f"Sending push notification: {message}")
        url = "https://api.pushover.net/1/messages.json"
        requests.post(url, data={
            'token': PUSH_API_KEY,
            'user': PUSH_USER_KEY,
            'message': message,
        }, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        global last_send
        last_send = time.time()
    except Exception as e:
        print(f"Failed to send push notification: {e}")

def send_notification_if_needed():
    if time.time() - last_send > 6 * 3600:
        send_push_notification('Still going strong!')
