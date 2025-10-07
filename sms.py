# sms.py
import os
from twilio.rest import Client
from datetime import datetime, time as dtime
import pytz
from models import SessionLocal, Message
import json

TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
LOCAL_TZ = os.getenv("LOCAL_TIMEZONE", "Asia/Dhaka")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# The friendly 3-message sequence (owner & service are filled in at runtime)
def build_sequence(owner_name, service_name):
    return [
        f"Hey — this is {owner_name}. Haven’t seen you in a while. Is everything okay with {service_name}?",
        "We really value your feedback. Can I ask what made you stop using our service?",
        "Thanks again for your time — it helps us improve!"
    ]

def local_allowed_now(local_tz_name=LOCAL_TZ, start_hour=10, end_hour=18):
    tz = pytz.timezone(local_tz_name)
    now = datetime.now(tz)
    return start_hour <= now.hour < end_hour

def send_sms(to_number, body, sequence_step=None):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("Twilio credentials are not set in env variables.")
    # send
    msg = client.messages.create(
        body=body,
        from_=TWILIO_NUMBER,
        to=to_number
    )
    # record to DB
    db = SessionLocal()
    m = Message(
        customer_phone=to_number,
        direction="outbound",
        body=body,
        timestamp=datetime.utcnow(),
        sequence_step=sequence_step,
        delivered=True,
        twilio_sid=msg.sid
    )
    db.add(m)
    db.commit()
    db.close()
    return msg.sid

# Helper used before sending: check replies exist to avoid spamming
def has_inbound_reply(phone):
    db = SessionLocal()
    res = db.query(Message).filter(Message.customer_phone==phone, Message.direction=="inbound").first()
    db.close()
    return res is not None
