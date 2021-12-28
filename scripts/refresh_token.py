from __future__ import print_function

import os, os.path

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

def main():
    load_dotenv()

    creds = None

    print(os.getenv("GOOGLE_CLIENT_ID"))

    flow = InstalledAppFlow.from_client_config({'installed': {
      'client_id': os.getenv("GOOGLE_CLIENT_ID"),
      'client_secret': os.getenv("GOOGLE_CLIENT_SECRET"),
      'redirect_uris': ['http://localhost:57339'],
      'auth_uri': 'https://accounts.google.com/o/oauth2/v2/auth',
      'token_uri': 'https://oauth2.googleapis.com/token',
      'prompt': "consent"
      }
    }, SCOPES)

    creds = flow.run_local_server(port=57339)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print("----")

    print("Token: ", creds.token)
    print("Refresh token: ", creds.refresh_token)


if __name__ == '__main__':
    main()
