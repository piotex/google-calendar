import datetime
import os.path

import googleapiclient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

service: googleapiclient.discovery.Resource = None
time_zone_eu = "Europe/Warsaw"
tz_parser = '%Y-%m-%dT%H:%M:%S+01:00'
zero_datatime: datetime.timedelta = None


def init():
    global zero_datatime
    zero_datatime = datetime.datetime.strptime("0:0:0", "%H:%M:%S")
    zero_datatime = datetime.timedelta(hours=zero_datatime.hour, minutes=zero_datatime.minute,
                                       seconds=zero_datatime.second)


def get_create_creds():
    scopes = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def init_service(creds) -> googleapiclient.discovery.Resource:
    global service
    if service is None:
        service = build('calendar', 'v3', credentials=creds)
    return service


def get_events():
    global service, time_zone_eu
    day_start = datetime.datetime.now().strftime("%Y-%m-%dT0:0:0Z")  # 'Z' indicates UTC time
    day_end_t = datetime.datetime.now().strftime("%Y-%m-%dT23:59:59Z")  # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='primary', timeMin=day_start,
                                          timeMax=day_end_t, singleEvents=True,
                                          orderBy='startTime', timeZone=time_zone_eu).execute()

    events = events_result.get('items', [])
    return events


def insert_event(break_time, start, end_t):
    global service, time_zone_eu
    event = {
        "colorId": "8",
        'summary': f'--break: {break_time}',
        'start': {
            'dateTime': start,
            'timeZone': time_zone_eu,
        },
        'end': {
            'dateTime': end_t,
            'timeZone': time_zone_eu,
        }
    }
    event = service.events().insert(calendarId='primary', body=event).execute()


def get_first_ok_i(events):
    global service, time_zone_eu, tz_parser, zero_datatime

    does_except = False
    first_ok_i = 0

    for i in range(0, len(events)):
        try:
            event = events[i]
            end_t = event['start'].get('dateTime')
            datetime.datetime.strptime(end_t, tz_parser)
            if does_except:
                first_ok_i = i
                does_except = False
        except:
            does_except = True
            continue
    return first_ok_i


def add_breaks_time(events):
    counter_datatime = zero_datatime
    start = events[0]['end'].get('dateTime')
    first_ok_i = get_first_ok_i(events)

    for i in range(first_ok_i, len(events)):
        event = events[i]
        end_t = event['start'].get('dateTime')
        try:
            a1 = datetime.datetime.strptime(end_t, tz_parser)
            a2 = datetime.datetime.strptime(start, tz_parser)
            break_time = a1 - a2
            if break_time > zero_datatime:
                counter_datatime += break_time
                insert_event(break_time, start, end_t)
                print(break_time, start, end_t)

        except Exception as eee:
            print(eee)
            continue

        event = events[i]
        start = event['end'].get('dateTime')


def add_total_break_time(events):
    global service, time_zone_eu, tz_parser, zero_datatime
    counter_datatime = zero_datatime
    start = events[0]['end'].get('dateTime')
    first_ok_i = get_first_ok_i(events)

    for i in range(first_ok_i, len(events)):
        event = events[i]
        end_t = event['start'].get('dateTime')
        try:
            a1 = datetime.datetime.strptime(end_t, tz_parser)
            a2 = datetime.datetime.strptime(start, tz_parser)
            break_time = a1 - a2
            if break_time > zero_datatime:
                counter_datatime += break_time

        except Exception as eee:
            print(eee)
            continue

        event = events[i]
        start = event['end'].get('dateTime')

    time_format = "%Y-%m-%dT"
    day_start = datetime.datetime.now().strftime(time_format)  # 'Z' indicates UTC time
    print(counter_datatime)

    insert_event(counter_datatime,
                 datetime.datetime.strptime(day_start, time_format).strftime(tz_parser),
                 (datetime.datetime.strptime(day_start, time_format) + datetime.timedelta(days=1)).strftime(tz_parser))



def main():
    global service
    init()
    creds = get_create_creds()
    init_service(creds)
    events = get_events()
    add_breaks_time(events)
    add_total_break_time(events)


if __name__ == '__main__':
    main()
