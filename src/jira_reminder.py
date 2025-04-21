import logging
import os
import re
import sys
from dotenv import load_dotenv
from jira import JIRA
from jira.exceptions import JIRAError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPException

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

required_vars = ['JIRA_SERVER', 'JIRA_EMAIL', 'JIRA_API_KEY', 'GMAIL_USER', 'GMAIL_APP_PASSWORD']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    sys.exit(f"❌ Missing required environment variables: {', '.join(missing)}")

JIRA_SERVER = os.getenv('JIRA_SERVER')
EMAIL = os.getenv('JIRA_EMAIL')
API_TOKEN = os.getenv('JIRA_API_KEY')

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('GMAIL_USER')
SENDER_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

try:
    jira = JIRA(server=JIRA_SERVER, basic_auth=(EMAIL, API_TOKEN), options={'timeout': 10})
except JIRAError as je:
    sys.exit(f"❌ Failed to connect to JIRA: {je.text}")
except Exception as e:
    sys.exit(f"❌ An unexpected error occurred: {e}")

jql_query = 'duedate >= startOfDay() AND duedate <= startOfDay(2d) AND assignee IS NOT EMPTY'

issues = []
start_at = 0
while True:
    batch = jira.search_issues(jql_str=jql_query, startAt=start_at, maxResults=50)
    if not batch:
        break
    issues.extend(batch)
    start_at += len(batch)

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

sent_emails = []

def send_reminder_email(recipient_email, issue_key, summary, due_date):
    subject = f"Reminder: Issue {issue_key} is Due on {due_date}"
    body = f"""
    Hello,

    This is a reminder that the following issue is assigned to you and is due soon:

    Issue Key: {issue_key}
    Summary: {summary}
    Due Date: {due_date}

    Please ensure you complete it before the deadline.

    Best regards,
    Your Project Management Team
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        logging.info("✅ Reminder email sent to %s for issue %s.", recipient_email, issue_key)
        print(f"✅ Reminder email sent to {recipient_email} for issue {issue_key}.")
        sent_emails.append(recipient_email)
    
    except SMTPException as se:
        logging.error("❌ SMTP error: %s", se)
        print(f"❌ Failed to send email to {recipient_email}: {se}")
    except Exception as e:
        logging.error("❌ Unexpected error while sending email: %s", e)
        print(f"❌ Failed to send email to {recipient_email}: {e}")

for issue in issues:
    issue_key = issue.key
    summary = issue.fields.summary
    due_date = getattr(issue.fields, 'duedate', None)
    assignee = issue.fields.assignee

    if not due_date:
        logging.warning("⚠️ Issue %s has no due date. Skipping.", issue_key)
        continue

    if assignee and hasattr(assignee, 'emailAddress') and assignee.emailAddress:
        recipient_email = assignee.emailAddress
        if not is_valid_email(recipient_email):
            logging.warning("⚠️ Invalid email address %s for issue %s. Skipping.", recipient_email, issue_key)
            continue
        send_reminder_email(recipient_email, issue_key, summary, due_date)
    else:
        logging.warning("⚠️ No valid email found for issue %s (assignee: %s).", issue_key, getattr(assignee, 'displayName', 'Unknown'))

if sent_emails:
    print("\n=== List of Emails Sent ===")
    for email in sent_emails:
        print(email)
else:
    print("\n❌ No emails were sent.")