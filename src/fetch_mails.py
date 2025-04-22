import os
import base64
import email
from email.header import decode_header
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import imaplib

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = '../credentials.json'
TOKEN_FILE = '../token.json'

def get_oauth_credentials():
    """
    Retrieves OAuth2 credentials for accessing Gmail.
    If no valid credentials are found, initiates the OAuth2 flow.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Initiating OAuth2 flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def fetch_last_unread_email(credentials):
    try:
        auth_string = f"user={credentials.token}\x01auth=Bearer {credentials.token}\x01\x01"
        mail = imaplib.IMAP4_SSL('imap.gmail.com')

        mail.authenticate('XOAUTH2', lambda x: auth_string)

        mail.select('inbox')
        status, messages = mail.search(None, '(UNSEEN)')
        if status != 'OK' or not messages[0]:
            print("No unread emails found.")
            return

        email_ids = messages[0].split()
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')

        if status != 'OK':
            print("Failed to fetch email.")
            return

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or 'utf-8')

                from_ = msg.get('From')
                date = msg.get('Date')

                print(f"Subject: {subject}")
                print(f"From: {from_}")
                print(f"Date: {date}")

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            print(f"Body:\n{body}")
                else:
                    body = msg.get_payload(decode=True).decode()
                    print(f"Body:\n{body}")

        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    creds = get_oauth_credentials()
    fetch_last_unread_email(creds)