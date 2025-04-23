import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import re

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def create_google_calendar_event(title, description, start_time_str, end_time_str, timezone='UTC'):
    creds = None

    if os.path.exists('../../token.json'):
        creds = Credentials.from_authorized_user_file('../../token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../../credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('../../token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': start_time_str,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time_str,
            'timeZone': timezone,
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return f"✅ Event created: {event_result.get('htmlLink')}"

