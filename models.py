# models.py
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, Boolean)
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reengage.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=False, index=True)  # from dataset
    name = Column(String, nullable=True)
    phone = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    meta = Column(Text, nullable=True)  # JSON string for any extra fields
    added_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, index=True)
    direction = Column(String)  # "outbound" or "inbound"
    body = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence_step = Column(Integer, nullable=True)  # which message in the 3-message seq
    delivered = Column(Boolean, default=False)
    twilio_sid = Column(String, nullable=True)

class ReplyTag(Base):
    __tablename__ = "reply_tags"
    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, index=True)
    reason = Column(String, index=True)  # price, moved, service quality, etc.
    sentiment = Column(String)  # positive/negative/neutral
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
