import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]  # bijv. "whatsapp:+14155238886"

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MAIL_FROM = os.environ["MAIL_FROM"]          # bijv. jouw Gmail-adres
MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]  # Gmail App Password
MAIL_RECIPIENTS = [
    addr.strip()
    for addr in os.environ.get("MAIL_RECIPIENTS", "").split(",")
    if addr.strip()
]

DATABASE_PATH = os.environ.get("DATABASE_PATH", "waste_tracker.db")

WEEKLY_REPORT_DAY = "mon"
WEEKLY_REPORT_HOUR = 8
WEEKLY_REPORT_MINUTE = 0
