from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time
import multiprocessing
import os
import subprocess
import papermill as pm

def run_notebook_in_dir(index,dir_path):
    delay_seconds = index * 65
    
    input_nb = dir_path / "Video_generate.ipynb"
    output_nb = dir_path / "Video_generate_output.ipynb"
    final_video = dir_path / "final_video.mp4"
    pid = multiprocessing.current_process().pid

    # print(f"📦 PID {pid} — Preparing: {dir_path} (wait {delay_seconds}s)", flush=True)
    # time.sleep(delay_seconds)
    # print(f"⏱️ PID {pid} — Starting execution after delay: {dir_path}", flush=True)

    if input_nb.exists():
        try:
            # pm.execute_notebook(
            #     str(input_nb),
            #     str(output_nb),
            #     parameters={},
            #     kernel_name="python3",
            #     cwd=str(dir_path)  # ← ココでカレントディレクトリ指定できる！
            # )
            cmd = [
                "papermill",
                str(input_nb),
                str(output_nb),
                "--kernel", "python3",
                "--cwd", str(dir_path)
            ]
            subprocess.run(cmd, check=True)

            print(f"✅ PID {pid} — Done: {input_nb}", flush=True)
        except Exception as e:
            print(f"❌ PID {pid} — Failed: {input_nb} -> {e}", flush=True)
            errored_file.write_text(str(e))
    else:
        print(f"⚠️ PID {pid} — Notebook not found: {dir_path}", flush=True)

__all__ = [
    "run_notebook_in_dir"
]
