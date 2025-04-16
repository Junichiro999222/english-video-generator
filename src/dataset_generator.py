import papermill as pm
import os
import shutil
import subprocess
import openai
import json
import csv
from typing import List
from pathlib import Path



def file_found(path: Path, exts=[".mp3", ".m4a"]):
    return any((path / f"music{ext}").exists() for ext in exts)

def extract_reference_url(path: Path):
    for file in path.glob("music.*.info.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("webpage_url", "")
                if url.startswith("http"):
                    return url
        except Exception as e:
            print(f"❌ Failed to read {file.name}: {e}")
    return ""

def download_mp3(search_query: str, target_path: str):
    os.makedirs(target_path, exist_ok=True)
    path = Path(target_path)
    for n in [1, 3, 5, 7]:
        print(f"🔍 Trying: scsearch{n}:{search_query}")
        command = ["yt-dlp", f"scsearch{n}:{search_query} full", "-x", "--audio-format", "mp3", "--write-info-json", "-o", os.path.join(target_path, "music.%(id)s.%(ext)s")]
        subprocess.run(command, check=False)
        mp3_files = list(path.glob("music.*.mp3"))
        if mp3_files:
            downloaded_file = mp3_files[0]
            downloaded_file.rename(path / "music.mp3")
            print(f"✅ Success with scsearch{n}")
            return
    print(f"❌ Failed to get good audio for: {search_query}")

def copy_notebook_template(target_path: str, notebook_template_path: str):
    shutil.copy(os.path.join(notebook_template_path, "../notebooks/Video_generate.ipynb"), os.path.join(target_path, "Video_generate.ipynb"))

def generate_info_csv(dataset_dir: str, artist: str, song: str, output_csv: str):
    reference = extract_reference_url(Path(dataset_dir))
    entry = {"artist": artist, "song": song, "reference": reference}
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["artist", "song", "reference"])
        writer.writeheader()
        writer.writerow(entry)

def fill_templates(info_csv: str, base_dir: str, song_dir: str):
    title_tpl = Path(base_dir, "../src/templates/title.txt").read_text(encoding="utf-8")
    desc_tpl = Path(base_dir, "../src/templates/description.txt").read_text(encoding="utf-8")
    with open(info_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = title_tpl.format(artist=row["artist"], music=row["song"], reference=row["reference"])
            desc = desc_tpl.format(artist=row["artist"], music=row["song"], reference=row["reference"])
            Path(song_dir, "title.txt").write_text(title, encoding="utf-8")
            Path(song_dir, "description.txt").write_text(desc, encoding="utf-8")

# === Step 3: Orchestrate ===
def generate_dataset_structure(base_dir: str,method,created_dirs):
    get_top_songs,artists = get_top_songs_for_mode(method)
    for x, artist in enumerate(artists):
        try:
            top_songs = get_top_songs(artist)
            for song in top_songs:
                song_dir = os.path.join(base_dir, f"{artist.replace(' ', '_')}_{song.replace(' ', '_')}")
                os.makedirs(song_dir, exist_ok=True)
                created_dirs.append(song_dir)  # ✅ Save directory
                download_mp3(f"{artist} {song}", song_dir)
                copy_notebook_template(song_dir, base_dir)
                info_csv = os.path.join(song_dir, "info.csv")
                generate_info_csv(song_dir, artist, song, info_csv)
                fill_templates(info_csv, base_dir, song_dir)
        except Exception as e:
            print(f"❌ Error processing {artist}: {e}")
    return created_dirs

def get_top_songs_for_mode(method: str):
    if method == "songs":
        all_songs = {}
        while True:
            artist = input("Enter artist name (or leave blank to finish): ").strip()
            if not artist:
                break
            songs = input(f"Enter songs by {artist}, comma separated: ").split(',')
            all_songs[artist] = [s.strip() for s in songs if s.strip()]
        artists = list(all_songs.keys())
        def get_top_songs(artist):
            return all_songs.get(artist, [])[:1]
    
    elif method == "artists":
        artists = []
        while True:
            artist = input("Enter artist name (or leave blank to finish): ").strip()
            if not artist:
                break
            artists.append(artist)
    
        def get_top_songs(artist: str) -> List[str]:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"List 3 of the most famous songs by {artist}. Only return a plain numbered list of song titles."}
                ]
            )
            text = response.choices[0].message.content
            print(text)
            songs = [line.split(". ", 1)[-1].strip() for line in text.split("\n") if line.strip()]
            return songs[:3]

       
    else:
        print("❌ Invalid choice. Exiting...")
        exit()
    return get_top_songs,artists

__all__ = [
    "file_found",
    "extract_reference_url",
    "generate_dataset_structure",
    "download_mp3",
    "generate_info_csv",
    "fill_templates",
    "copy_notebook_template",
    "get_top_songs_for_mode"
]

