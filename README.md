# Smart SMS Re-engagement Demo

A Streamlit + Flask demo to run a human-sounding SMS re-engagement campaign for former customers. Reads the Kaggle Telco churn dataset and demonstrates:
- sending friendly 3-message sequences via Twilio
- receiving replies via a webhook (Flask) and classifying reason + sentiment via OpenAI
- storing messages & tags in SQLite and exporting CSV
- a simple Streamlit dashboard to view replies & counts

## Files
- `app.py` — Streamlit app (main). Use this as the entrypoint for Streamlit Cloud.
- `webhook.py` — Flask webhook that Twilio calls on inbound SMS (deploy separately)
- `sms.py` — Twilio send helper
- `models.py` — SQLAlchemy models + DB initialization
- `utils.py` — OpenAI classification wrapper
- `requirements.txt` — packages
- `example.env` — example environment variables

## Setup (local / VS Code)
1. Create a virtualenv with Python 3.11.0:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
