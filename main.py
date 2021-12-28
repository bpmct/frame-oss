from flask import Flask, render_template, redirect, abort

# Google Photos stuff
import os, os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# Supabase stuff
# TODO: make optional for simple self-hosted installs
if os.environ.get("USE_SUPABASE"):
    from supabase import create_client, Client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

# Database
import psycopg2
import json

app = Flask(__name__)

# Do not show requests in logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


@app.route("/")
def hello_world():
    # Generate "Login with Google" link for Supabase
    google_url = "https://tkcpbdawrrhatvriturr.supabase.co/auth/v1/callback"

    return render_template("homepage.html")

@app.route('/<path:text>', methods=['GET', 'POST'])
def all_routes(text):
    if text.startswith('f'):  

        # Open DB connection  
        connection = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = connection.cursor()

        # Look up frame in the database
        cursor.execute("SELECT user, plugins, id FROM frames WHERE slug=%s", (text,))
        frame = cursor.fetchone()

        if frame is None:    
            abort(404)
        
        user = frame[0]
        plugins = frame[1]
        frame_uuid = frame[2]

        if "simple_photo_gallery" not in plugins:
            return "At this time, simple_photo_gallery is a required plugin"

        # Look up simple_photo_gallery config for this frame
        cursor.execute("SELECT data FROM plugin_configs WHERE frame=%s", (frame_uuid,))
        gallery_config = cursor.fetchone()[0]

        # Config validation
        if gallery_config is None:
            return "Unable to fetch configuration for the simple_photo_gallery plugin"
        if not gallery_config["albums"]:
            return "No albums are configured for this photo gallery"
        # For now, we will only use the first album
        album = gallery_config["albums"][0]
        if not album["type"] or not album["id"]:
            return "Album \"id\" or \"type\" not specified"
        if album["type"] != "google_photos":
            return "Google phtoos is the only supported album type"
    
        # Close DB Connection
        if (connection):
            cursor.close()
            connection.close()

        # Authenticater with Google Photos
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
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
                body={"albumId": album["id"], "pageSize": 100}).execute()
            items = results.get('mediaItems', [])

            # TODO: load more items if necessary
            nextpagetoken = results.get('nextPageToken', '')

            # Collect list of photo URLs
            urls = []
            for item in items:
                urls.append(item["baseUrl"] + "=w1280")

        except HttpError as err:
            print(err)

        return render_template("photo_frame.html", google_photos=urls)
        # elif text == "fjsyDoKNNo_ferry_cam":
        #     return render_template("iframe.html", frame_url="//video.nest.com/embedded/live/WsP35hLv1f?autoplay=1");
        # elif text == "fjsyDoKNNo_palms_village_cam":
        #     return render_template("iframe.html", frame_url="//video.nest.com/embedded/live/oRHGqamzOS?autoplay=1");
        # elif text == "fjsyDoKNNo_cjs_central_cam":
        #     return render_template("iframe.html", frame_url="//video.nest.com/embedded/live/cwPe1SFdep?autoplay=1");
        # else:
        #     abort(404)
    else:
        abort(404)