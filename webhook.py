# webhook.py
import os
from flask import Flask, request, Response
from models import SessionLocal, Message, ReplyTag, init_db
from utils import classify_reply
from datetime import datetime

app = Flask(__name__)
init_db()

@app.route("/incoming-sms", methods=["POST"])
def incoming_sms():
    # Twilio sends form-encoded data
    from_number = request.form.get("From")
    body = request.form.get("Body", "")
    ts = datetime.utcnow()

    db = SessionLocal()
    msg = Message(
        customer_phone=from_number,
        direction="inbound",
        body=body,
        timestamp=ts
    )
    db.add(msg)
    db.commit()

    # classify reply
    classification = classify_reply(body)
    tag = ReplyTag(
        customer_phone=from_number,
        reason=classification.get("reason","other"),
        sentiment=classification.get("sentiment","neutral"),
        note=classification.get("note","")
    )
    db.add(tag)
    db.commit()
    db.close()

    # Respond to Twilio quickly with a friendly phrase (Optional)
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?><Response><Message>Thanks — we got your message. Someone will review this shortly.</Message></Response>"""
    return Response(twiml, mimetype="application/xml")

if __name__ == "__main__":
    # for local debug
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
