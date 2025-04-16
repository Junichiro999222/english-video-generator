import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.dataset_generator import *
from src.video_generator import *
from src.uploader import *

import os
from typing import List
from pathlib import Path
import multiprocessing



method = input("Type 'songs' to enter specific songs or 'artists' for top songs by artists: ").strip().lower()
created_dirs = []  # ✅ List to track created directories




if __name__ == "__main__":
    print("🚀 Starting full pipeline...")
    # === Step 1: 曲データ構造の構築 ===
    output_base_dir = os.path.join(os.getcwd(), "songs_dataset")
    os.makedirs(output_base_dir, exist_ok=True)
    created_dirs = generate_dataset_structure(output_base_dir, method,created_dirs)



    print("\n📦 Newly created directories:")
    for d in created_dirs:
        print(" -", d)

    # === Step 2: ノートブック実行準備 ===
    base_dir = Path("songs_dataset")
    print("\n📂 Collecting notebook directories...")
    notebook_dirs = [Path(p) for p in created_dirs]
    # notebook_dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    print(f"📁 Found {len(notebook_dirs)} candidate dirs")

    filtered_dirs = []
    for p in notebook_dirs:
        final_video = p / "final_video.mp4"
        first_music = p / "music.mp3"
        errored_file = p / "errored.txt"

        if final_video.exists():
            print(f"✅ Skipping {p} (final_video.mp4 exists)")
        elif errored_file.exists():
            print(f"❌ Skipping {p} (errored.txt exists)")
        elif not first_music.exists():
            print(f"✅ Skipping {p} (music.mp3 doesn't exist)")
        else:
            print(f"🚀 Queued for execution: {p}")
            filtered_dirs.append(p)

    # === Step 3: ノートブック実行 ===
    max_workers = 1
    running_processes = []

    for index, dir_path in enumerate(filtered_dirs):
        while len(running_processes) >= max_workers:
            for proc in running_processes:
                if not proc.is_alive():
                    running_processes.remove(proc)
            time.sleep(1)

        proc = multiprocessing.Process(target=run_notebook_in_dir, args=(index, dir_path))
        proc.start()
        running_processes.append(proc)

    for proc in running_processes:
        proc.join()

    print("🎉 All notebooks done!!")

    # === Step 4: YouTube アップロード ===
    print("🚀 Starting upload process...")
    process_all_videos(filtered_dirs,"songs_dataset")
    print("📤 All videos uploaded!")
