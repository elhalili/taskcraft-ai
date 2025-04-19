import datetime
import os.path
import argparse
import pickle
import pytz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil.parser import parse as dateutil_parse
from tzlocal import get_localzone


SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_FILE = '../../../cred.json'
TOKEN_FILE = 'token.pickle'
APPLICATION_NAME = 'Google Reminder CLI'
DEFAULT_REMINDER_DURATION_MINUTES = 5


# الحصول على خدمة تقويم Google مع التعامل مع المصادقة
def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: Credentials file '{CREDENTIALS_FILE}' not found.")
                exit(1)
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080)
            except Exception as e:
                print(f"Error during authentication flow: {e}")
                exit(1)

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print(f"Authentication successful. Token saved to {TOKEN_FILE}")

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An API error occurred: {error}')
        if error.resp.status in [401, 403] and os.path.exists(TOKEN_FILE):
            print(f"Authentication error. Deleting {TOKEN_FILE} and exiting.")
            os.remove(TOKEN_FILE)
        exit(1)
    except Exception as e:
        print(f"Failed to build calendar service: {e}")
        exit(1)

# إنشاء حدث تذكير على التقويم الأساسي للمستخدم
def create_reminder_event(service, subject, start_time, end_time, timezone_str):
    event = {
        'summary': subject,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': timezone_str,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': timezone_str,
        },
    }

    try:
        print(f"Creating event: '{subject}' at {start_time.strftime('%Y-%m-%d %I:%M %p')}")
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Reminder created successfully!")
        print(f"Event Link: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as error:
        print(f'An API error occurred while creating event: {error}')
        try:
            print(f"Details: {error.content.decode()}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"An unexpected error occurred during event creation: {e}")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a Google Calendar reminder.')
    parser.add_argument('remindersubject', help='The subject/title of the reminder.')
    parser.add_argument('date', help='The date for the reminder (e.g., "YYYY-MM-DD", "today", "tomorrow", "next Friday", "Oct 25").')
    parser.add_argument('hour', type=int, help='The hour for the reminder (1-12).')
    parser.add_argument('ampm', choices=['AM', 'PM', 'am', 'pm'], help='AM or PM for the hour.')

    args = parser.parse_args()

    if not (1 <= args.hour <= 12):
        print("Error: Hour must be between 1 and 12.")
        exit(1)

    time_str = f"{args.hour}:00 {args.ampm.upper()}"
    datetime_str = f"{args.date} {time_str}"

    try:
        parsed_dt = dateutil_parse(datetime_str, fuzzy=False)
        local_tz = get_localzone()
        if hasattr(local_tz, "localize"):
            aware_dt_start = local_tz.localize(parsed_dt)
        else:
            aware_dt_start = parsed_dt.replace(tzinfo=local_tz)

        timezone_iana_str = str(local_tz)

    except ValueError:
        print(f"Error: Could not parse the date/time string: '{datetime_str}'")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during date/time parsing: {e}")
        exit(1)

    aware_dt_end = aware_dt_start + datetime.timedelta(minutes=DEFAULT_REMINDER_DURATION_MINUTES)

    print("Authenticating with Google Calendar...")
    service = get_calendar_service()

    if service:
        create_reminder_event(service, args.remindersubject, aware_dt_start, aware_dt_end, timezone_iana_str)
    else:
        print("Failed to get Google Calendar service. Exiting.")
        exit(1)
