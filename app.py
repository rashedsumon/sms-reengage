# app.py
import streamlit as st
import pandas as pd
import os
from models import init_db, SessionLocal, Customer, Message, ReplyTag
from sms import build_sequence, send_sms, local_allowed_now, has_inbound_reply
from datetime import datetime
from sqlalchemy.exc import IntegrityError

st.set_page_config(page_title="Re-engage - SMS Campaign", layout="wide")
init_db()

# config / env
OWNER_NAME = os.getenv("OWNER_NAME", "Owner")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Service")
LOCAL_TZ = os.getenv("LOCAL_TIMEZONE", "Asia/Dhaka")

st.title("💬 Smart SMS Re-engagement — Demo")

st.sidebar.header("Campaign settings")
owner_name = st.sidebar.text_input("Owner name", OWNER_NAME)
service_name = st.sidebar.text_input("Service name", SERVICE_NAME)
send_test_number = st.sidebar.text_input("Test number (E.164)", "")
start_campaign = st.sidebar.button("Start campaign for selected customers")
export_csv = st.sidebar.button("Export tags CSV")

# Load dataset
st.header("1) Load dataset")
csv_path = st.text_input("Path to CSV", "/kaggle/input/telco-customer-churn/WA_Fn-UseC_-Telco-Customer-Churn.csv")
if st.button("Load CSV"):
    try:
        df = pd.read_csv(csv_path)
        st.success(f"Loaded {len(df)} rows")
        st.session_state["df"] = df
    except Exception as e:
        st.error(f"Failed to load CSV: {e}")

if "df" in st.session_state:
    df = st.session_state["df"]

    st.markdown("### Preview")
    st.dataframe(df.head(50))

    # Identify churned customers (Telco dataset has 'Churn' column yes/no)
    if "Churn" in df.columns:
        churned = df[df["Churn"].astype(str).str.lower()=="yes"].copy()
    else:
        churned = df.copy()  # fallback

    st.markdown(f"**Found {len(churned)} churned customers**")
    # Map dataset columns to minimal fields
    st.markdown("### Map columns")
    phone_col = st.selectbox("Phone column (choose column with phone numbers)", options=[""] + list(df.columns))
    name_col = st.selectbox("Name column (optional)", options=[""] + list(df.columns))
    email_col = st.selectbox("Email column (optional)", options=[""] + list(df.columns))

    # show preview of the churn list
    st.markdown("### Churn list preview (mapped)")
    sample = churned.head(200).copy()
    def _map_row(r):
        return {
            "customer_id": r.get("customerID", ""),
            "name": r.get(name_col, "") if name_col else "",
            "phone": r.get(phone_col, ""),
            "email": r.get(email_col, "")
        }
    mapped = []
    for _, r in sample.iterrows():
        mapped.append(_map_row(r))
    mapped_df = pd.DataFrame(mapped)
    st.dataframe(mapped_df)

    # Bulk import mapped customers into local DB
    if st.button("Import mapped churned customers to DB"):
        db = SessionLocal()
        added = 0
        for idx, row in mapped_df.iterrows():
            phone = str(row["phone"]) if row["phone"] is not None else ""
            if not phone or phone.strip()=="":
                continue
            cust = Customer(customer_id=row.get("customer_id",""), name=row.get("name",""), phone=phone, email=row.get("email",""), meta="")
            db.add(cust)
            try:
                db.commit()
                added += 1
            except IntegrityError:
                db.rollback()
        db.close()
        st.success(f"Imported {added} customers")

# Campaign controls & dashboard
st.header("2) Campaign & Dashboard")
db = SessionLocal()
customers = db.query(Customer).all()
st.write(f"Customers in DB: {len(customers)}")

col1, col2 = st.columns([2,1])
with col1:
    sel = st.multiselect("Select customers (phone) to send now", [c.phone for c in customers], max_selections=50)
    if st.button("Send first message now (selected)"):
        seq = build_sequence(owner_name, service_name)
        sent = 0
        failures = []
        for phone in sel:
            # skip if inbound already exists
            if has_inbound_reply(phone):
                failures.append((phone, "already replied — skipping"))
                continue
            # respect local allowed hours
            if not local_allowed_now():
                failures.append((phone, "outside allowed send hours"))
                continue
            try:
                sid = send_sms(phone, seq[0], sequence_step=1)
                sent += 1
            except Exception as e:
                failures.append((phone, str(e)))
        st.success(f"Sent first message to {sent} numbers.")
        if failures:
            st.table(pd.DataFrame(failures, columns=["phone","reason"]))

with col2:
    st.markdown("### Quick actions")
    if st.button("Send test message (to test number)"):
        if not send_test_number:
            st.error("Enter test number in sidebar.")
        else:
            try:
                sid = send_sms(send_test_number, build_sequence(owner_name, service_name)[0], sequence_step=1)
                st.success(f"Test SMS sent (sid {sid})")
            except Exception as e:
                st.error(f"Failed: {e}")

# Show messages & tags
st.markdown("### Messages & Tags")
msgs = db.query(Message).order_by(Message.timestamp.desc()).limit(200).all()
if msgs:
    df_msgs = pd.DataFrame([{"phone":m.customer_phone,"dir":m.direction,"body":m.body,"time":m.timestamp,"step":m.sequence_step} for m in msgs])
    st.dataframe(df_msgs)
tags = db.query(ReplyTag).order_by(ReplyTag.timestamp.desc()).limit(200).all()
if tags:
    df_tags = pd.DataFrame([{"phone":t.customer_phone,"reason":t.reason,"sentiment":t.sentiment,"note":t.note,"time":t.timestamp} for t in tags])
    st.dataframe(df_tags)

# Simple analytics
st.markdown("### Simple Dashboard")
if tags:
    df_tags_all = pd.DataFrame([{"reason":t.reason,"sentiment":t.sentiment} for t in db.query(ReplyTag).all()])
    counts = df_tags_all.groupby("reason").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(counts.set_index("reason"))
    st.write(df_tags_all["sentiment"].value_counts())

# Export CSV of tags
if export_csv:
    df_export = pd.DataFrame([{"phone":t.customer_phone,"reason":t.reason,"sentiment":t.sentiment,"note":t.note,"time":t.timestamp} for t in db.query(ReplyTag).all()])
    csv_bytes = df_export.to_csv(index=False).encode()
    st.download_button("Download tags CSV", data=csv_bytes, file_name="reply_tags.csv", mime="text/csv")

db.close()
