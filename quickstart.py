from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    load_dotenv()

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, use environment variables
    # this will happen if it is a fresh deploy
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = Credentials.from_authorized_user_info({
                "token": os.getenv("GOOGLE_OAUTH_TOKEN"),
                "refresh_token": os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN"),
                "scopes": SCOPES,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET")
            })
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

        # List all albums (if necessary)
        # results = service.albums().list(
        #     pageSize=50).execute()
        # items = results.get('albums', [])
        # if not items:
        #     print('No albums found.')
        # else:
        #     print('Albums:')
        #     for item in items:
        #         print('{0} ({1})'.format(item['title'].encode('utf8'), item['id']))

        results = service.mediaItems().search(
            body={"albumId": "AEP_oUT4Jk6Fuz_xl5ww0zXtjgvqJsBg8xugikeEaztxnlk0wtehgMqeYpuON61V63GeFpK-M0uzAMV-zXDmdFMtGks63us8gA", "pageSize": 100}).execute()
        items = results.get('mediaItems', [])

        nextpagetoken = results.get('nextPageToken', '')

        urls = []

        for item in items:
            urls.append(item["baseUrl"] + "=w1280")

        print(urls[56])

    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()
