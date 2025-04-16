import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
from google.auth.transport.requests import Request
import time

def authenticate_youtube():
    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube"
    ]
    creds = None
    token_path = "token.pickle"

    # 🔄 トークンの読み込み
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # 🔁 トークンが期限切れならリフレッシュ
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # ← これで更新できる！！

    # 🆕 なければ新規認証
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", scopes)
        for port in [8080, 8081, 8082, 8888]:
            try:
                creds = flow.run_local_server(port=port, open_browser=False)
                break
            except OSError:
                print(f"⚠️ Port {port} already in use, trying next...")
        else:
            raise RuntimeError("😢 No available ports for OAuth redirect.")

    # 💾 保存
    with open(token_path, "wb") as token:
        pickle.dump(creds, token)

    youtube = build("youtube", "v3", credentials=creds)
    return youtube


def upload_video(youtube, video_path, title, description, category_id="22", privacy_status="unlisted"):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response["id"]

def mark_as_uploaded(path):
    with open(path, "w") as f:
        f.write("uploaded\n")

def load_text_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def add_to_playlist(youtube, video_id, playlist_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    response = request.execute()
    return response


def process_all_videos(filtered_dirs, base_dir="songs_dataset"):
    youtube = authenticate_youtube()
    for dir_name in filtered_dirs:
        subdir = dir_name
        if not os.path.isdir(subdir):
            continue

        uploaded_path = os.path.join(subdir, "uploaded.txt")
        if os.path.exists(uploaded_path):
            print(f"✅ Skipping {subdir}, already uploaded.")
            continue

        video_path = os.path.join(subdir, "final_video.mp4")
        title_path = os.path.join(subdir, "title.txt")
        description_path = os.path.join(subdir, "description.txt")

        if not os.path.exists(video_path):
            print(f"⚠️ No video found in {subdir}, skipping.")
            continue

        title = load_text_file(title_path)
        description = load_text_file(description_path)

        print(f"🔼 Uploading video from: {subdir}")

        video_id = upload_video(youtube, os.path.join(subdir, "final_video.mp4"), title, description)
        add_to_playlist(youtube, video_id, "PLQ_36MSwXUhoOhtsRYX8zEpnzoMKaEkTT")

        video_id = upload_video(youtube, os.path.join(subdir, "final_output.mp3"), title, description)
        add_to_playlist(youtube, video_id, "PLQ_36MSwXUhoU1VbOFnRPxj30e2cAyTZ0")
        mark_as_uploaded(uploaded_path)  # ✅ 成功時にマーク！
        print(f"🍅 Video uploaded!! : {subdir}")
        print(f"⌛ Waiting for next upload...")
        time.sleep(300)  # ← 5分休憩（状況に応じて調整）


__all__ = [
    "authenticate_youtube",
    "upload_video",
    "mark_as_uploaded",
    "load_text_file",
    "add_to_playlist",
    "process_all_videos"   
    
]
