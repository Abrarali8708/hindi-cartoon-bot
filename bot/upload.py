"""Upload to YouTube with the official YouTube Data API (free)."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def client():
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"], scopes=SCOPES)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(path, title, description, tags, cfg):
    body = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:20],
                    "categoryId": str(cfg.get("category_id", "1")),
                    "defaultLanguage": "hi", "defaultAudioLanguage": "hi"},
        "status": {"privacyStatus": cfg.get("privacy", "public"),
                   "selfDeclaredMadeForKids": bool(cfg.get("made_for_kids", False)),
                   "containsSyntheticMedia": bool(cfg.get("ai_disclosure", False))},
    }
    req = client().videos().insert(part="snippet,status", body=body,
                                   media_body=MediaFileUpload(path, mimetype="video/mp4", chunksize=-1,
                                                              resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def set_thumbnail(video_id, path):
    client().thumbnails().set(videoId=video_id, media_body=MediaFileUpload(path, mimetype="image/jpeg")).execute()
