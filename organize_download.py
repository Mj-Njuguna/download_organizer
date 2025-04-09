#!/usr/bin/env python3
"""
organize_downloads.py

- On first run, moves existing files in Downloads to an 'old_download' folder.
- Then watches Downloads folder and organizes new files into dated folders.
"""

import time
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

TEMP_EXTS = {'.crdownload', '.part', '.tmp'}
MARKER_FILE = ".organized"  # used to mark that first-time setup has already run


class DownloadHandler(FileSystemEventHandler):
    """Handles new file events in the Downloads folder."""

    def __init__(self, download_dir: Path, delay: float = 5.0):
        super().__init__()
        self.download_dir = download_dir
        self.delay = delay

    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        if src.suffix.lower() in TEMP_EXTS:
            return

        time.sleep(self.delay)

        prev_size = -1
        while True:
            try:
                curr_size = src.stat().st_size
            except FileNotFoundError:
                return
            if curr_size == prev_size:
                break
            prev_size = curr_size
            time.sleep(1)

        date_folder = self.download_dir / datetime.now().strftime('%Y-%m-%d')
        date_folder.mkdir(exist_ok=True)

        dest = date_folder / src.name
        try:
            shutil.move(str(src), str(dest))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Moved: {src.name} → {date_folder.name}")
        except (OSError, PermissionError) as e:
            print(f"Error moving {src.name}: {e}")


def perform_first_time_cleanup(downloads: Path):
    """
    If this is the first time the script is run, move all existing items
    into a folder named 'old_download'.
    """
    marker = downloads / MARKER_FILE
    if marker.exists():
        return  # Already initialized before

    print("First run detected. Moving existing items to 'old_download'...")

    old_download_folder = downloads / "old_download"
    old_download_folder.mkdir(exist_ok=True)

    for item in downloads.iterdir():
        if item.name in {"old_download", MARKER_FILE}:
            continue  # Skip self
        try:
            shutil.move(str(item), str(old_download_folder / item.name))
            print(f"Moved: {item.name} → old_download/")
        except (OSError, PermissionError) as e:
            print(f"Error moving {item.name}: {e}")

    # Create a marker so we don't do this again
    marker.touch()
    print("Initial organization complete.")


def main():
    """Set up the Downloads watcher and organize existing files if first run."""
    parser = argparse.ArgumentParser(
        description="Watch and organize your Downloads folder into dated subfolders."
    )
    parser.add_argument(
        "--downloads",
        "-d",
        type=Path,
        default=Path.home() / "Downloads",
        help="Path to your Downloads folder (default: ~/Downloads)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait after file creation before moving (default: 5)"
    )
    args = parser.parse_args()

    downloads = args.downloads.expanduser().resolve()
    if not downloads.is_dir():
        print(f"Error: {downloads} is not a directory.")
        return

    perform_first_time_cleanup(downloads)

    print(f"Watching folder: {downloads}")
    event_handler = DownloadHandler(downloads, delay=args.delay)
    observer = Observer()
    observer.schedule(event_handler, str(downloads), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
