import os
import smtplib
import sys
import json
from email.message import EmailMessage
from prompts.email_prompt import get_email_prompt
from typing import Optional

SENDER_EMAIL = os.getenv("GMAIL_USER")
SENDER_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def generate_email_from_prompt(prompt: str, contacts) -> Optional[dict]:
    try:
        response, error = get_email_prompt(prompt, contacts)
        print(response)
        if not error:
            return response
        else:
            print("❌ LLM did not return a valid email response.")
            return None
    except Exception as e:
        print(f"❌ Error generating email: {e}")
        return None

def send_email(contact: str, subject: str, body: str):
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        print("❌ Missing GMAIL_USER or GMAIL_APP_PASSWORD in environment.")
        sys.exit(1)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = contact

    plain_body = f"Hi there,\n\n{body}\n\nBest regards,\n{SENDER_EMAIL}"
    html_body = body.replace('\n', '<br>\n')

    msg.set_content(plain_body)
    msg.add_alternative(f"""\
    <html>
      <body>
        <p>Hi there,</p>
        <p>{html_body}</p>
        <p><br>Best regards,<br>{SENDER_EMAIL}</p>
      </body>
    </html>
    """, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)
            print(f"✅ Email sent to {contact}")
    except Exception as e:
        print(f"❌ Failed to send email to {contact}: {e}")

        