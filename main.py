from re import search
from flask import Flask, render_template, redirect, abort

# Google Photos stuff
import os, os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load from .env if exists
load_dotenv()

# Supabase stuff
# TODO: make optional for simple self-hosted installs
if os.environ.get("USE_SUPABASE") == "true":
    from supabase import create_client, Client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

# Database
import psycopg2, psycopg2.extras

app = Flask(__name__)

# Disable strict slashes to allow /slug and /slug/
app.url_map.strict_slashes = False

# Do not show requests in logs
import logging
logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

def db_connect():
    connection = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return connection;

def get_frame(slug):
    if os.environ.get("USE_SUPABASE") == "true":
        request = supabase.table("frames").select("user, plugins").limit(1).eq("slug", slug).execute()
        if len(request.get("data", [])) == 0:
            return None;
        else:
            return request.get("data")[0]
    else:
        # Open DB connection  
        connection = db_connect();
        cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Look up frame in the database
        cursor.execute("SELECT user, plugins FROM frames WHERE slug=%s", (slug,))

        the_frame = cursor.fetchone();

        cursor.close()
        connection.close()
        
        return the_frame;

def get_plugin_config(frame, enabledPlugins):

    # TODO: only fetch enabledPlugins in SELECT
    # can use .in() filter for Supabase

    if os.environ.get("USE_SUPABASE") == "true":
        request = supabase.table("plugin_configs").select("plugin, data").eq("frame", frame).execute()
        
        all_config = request.get("data");
            
    else: 
        connection = db_connect();
        cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Look up simple_photo_gallery config for this frame
        cursor.execute("SELECT plugin, data FROM plugin_configs WHERE frame=%s", (frame,))

        all_config = cursor.fetchall()

        # Close DB Connection
        cursor.close()
        connection.close()
    
    # For each enabled plugin map the config
    # e.g: mappedConfig["simple_photo_gallery"] = { ...data }
    mappedConfig = {};
    for pluginName in enabledPlugins:
        searchForConfig = next((item for item in all_config if item["plugin"] == pluginName), None)

        # Only use the "data" column for the JSON config
        if searchForConfig is not None:
            configForPlugin = searchForConfig["data"]
        else:
            configForPlugin = None

        mappedConfig[pluginName] = configForPlugin
        
    return mappedConfig;

def use_google_photos(token, refresh_token):
    # Auth with Google Photos
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = Credentials.from_authorized_user_info({
                "token": token,
                "refresh_token": refresh_token,
                "scopes": SCOPES,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET")
            })
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

def generate_menu(frame, pluginsList):
    # TODO: refactor on a per-plugin basis instead of all this inline logic
    menu = []

    if "simple_photo_gallery" in pluginsList:
        menu.append({"name": "All photos", url: ""})

@app.route("/")
def hello_world():
    return render_template("homepage.html")

@app.route('/<path:slug>', methods=['GET', 'POST'])
def photo_frame(slug):
    frame = get_frame(slug)
    if frame is None:
        abort(404)

    if "simple_photo_gallery" not in frame["plugins"]:
        return "At this time, simple_photo_gallery is a required plugin"

    # Grab & validate config
    plugin_config = get_plugin_config(slug, frame["plugins"])

    # Grab config for photo gallery
    gallery_config = plugin_config["simple_photo_gallery"];
    if gallery_config is None:
        return "Unable to fetch this frame's configuration for the simple_photo_gallery plugin"
    if not gallery_config["albums"]:
        return "No albums are configured for this photo gallery"
    # For now, we will only use the first album
    album = gallery_config["albums"][0]
    if not album["type"] or not album["id"]:
        return "Album \"id\" or \"type\" not specified"
    if album["type"] != "google_photos":
        return "Google photos is the only supported album type"

    try:
        service = use_google_photos(os.getenv("GOOGLE_OAUTH_TOKEN"), os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN"))

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

@app.route('/<path:slug>/<path:plugin>', methods=['GET', 'POST'])
@app.route('/<path:slug>/<path:plugin>/<path:params>', methods=['GET', 'POST'])
def plugin(slug, plugin, params=""): 
    if plugin == "web_frame": 
        frame = get_frame(slug)
        if frame is None:
            abort(404)

        if "web_frame" not in frame["plugins"]:
            return "web_frame is not enabled"

        # Grab & validate config
        plugin_config = get_plugin_config(slug, frame["plugins"])

        web_frame_config = plugin_config["web_frame"]

        print(web_frame_config)
        
        if web_frame_config is None:
            # TODO: potentially use a default website
            return "Unable to fetch this frame's configuration for the web_frame plugin"
        if not web_frame_config["frames"]:
            return "No frames are configured"

        return "so far so good"
    else:
        return "Unsupported plugin"