#!/usr/bin/env python3
"""
organize_downloads.py

A smart download folder organizer that:
- On first run, moves existing files in Downloads to an 'old_download' folder
- Watches Downloads folder and organizes new files into dated and categorized folders
- Supports configuration via a settings file
- Provides detailed logging of activities
"""

import time
import shutil
import argparse
import json
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
TEMP_EXTS = {'.crdownload', '.part', '.tmp', '.download'}
MARKER_FILE = ".organized"  # used to mark that first-time setup has already run
CONFIG_FILE = ".organize_config.json"
LOG_FILE = ".organize_log.txt"

# Default file categories and their extensions
DEFAULT_CATEGORIES = {
    "images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    "documents": ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
    "audio": ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
    "video": ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'],
    "archives": ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    "executables": ['.exe', '.msi', '.apk', '.dmg', '.app', '.deb', '.rpm'],
    "code": ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.php', '.rb', '.go', '.json', '.xml', '.sql']
}

# Default configuration
DEFAULT_CONFIG = {
    "organize_by_date": True,
    "organize_by_type": True,
    "delay_seconds": 5.0,
    "excluded_files": ["desktop.ini"],
    "excluded_patterns": [],
    "categories": DEFAULT_CATEGORIES,
    "log_level": "INFO",
    "keep_original_name": True,
    "rename_duplicates": True,
    "max_retry_attempts": 3,
    "retry_delay_seconds": 2
}


def setup_logging(downloads_dir, level="INFO"):
    """Configure logging to both console and file."""
    log_path = downloads_dir / LOG_FILE
    
    # Create a logger
    logger = logging.getLogger("organize_downloads")
    logger.setLevel(getattr(logging, level))
    logger.handlers = []  # Clear existing handlers to avoid duplicates
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    return logger


def load_config(downloads_dir):
    """Load or create configuration file."""
    config_path = downloads_dir / CONFIG_FILE
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        except Exception as e:
            print(f"Error loading config file: {e}. Using defaults.")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"Created default configuration at {config_path}")
        return DEFAULT_CONFIG


def get_category(file_path, categories):
    """Determine the category of a file based on its extension."""
    ext = file_path.suffix.lower()
    
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    
    return "other"


def is_excluded(file_path, config):
    """Check if a file should be excluded from organization."""
    # Check for exact filename match
    if file_path.name in config["excluded_files"]:
        return True
    
    # Check for pattern matches
    for pattern in config["excluded_patterns"]:
        if re.search(pattern, file_path.name, re.IGNORECASE):
            return True
    
    return False


def get_destination_path(src_path, download_dir, config):
    """Determine the destination path for a file based on configuration."""
    date_folder = datetime.now().strftime('%Y-%m-%d')
    
    # Start with download_dir as the base
    dest_dir = download_dir
    
    # Add date folder if configured
    if config["organize_by_date"]:
        dest_dir = dest_dir / date_folder
    
    # Add category folder if configured
    if config["organize_by_type"]:
        category = get_category(src_path, config["categories"])
        dest_dir = dest_dir / category
    
    # Create the directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle file name (with duplicate detection)
    dest_path = dest_dir / src_path.name
    
    if config["rename_duplicates"] and dest_path.exists():
        base_name = dest_path.stem
        extension = dest_path.suffix
        counter = 1
        
        while dest_path.exists():
            new_name = f"{base_name} ({counter}){extension}"
            dest_path = dest_dir / new_name
            counter += 1
    
    return dest_path


class DownloadHandler(FileSystemEventHandler):
    """Handles new file events in the Downloads folder."""

    def __init__(self, download_dir: Path, config: dict, logger):
        super().__init__()
        self.download_dir = download_dir
        self.config = config
        self.logger = logger
        self.delay = config["delay_seconds"]
        self.stats = {"total_organized": 0, "by_category": {}}
    
    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        
        # Skip temporary files
        if src.suffix.lower() in TEMP_EXTS:
            return
        
        # Skip excluded files
        if is_excluded(src, self.config):
            self.logger.info(f"Skipped excluded file: {src.name}")
            return
        
        # Wait for download to complete
        self.logger.debug(f"New file detected: {src.name}. Waiting for download completion...")
        time.sleep(self.delay)
        
        # Check if file is still being written
        prev_size = -1
        while True:
            try:
                curr_size = src.stat().st_size
                if curr_size == prev_size:
                    break
                prev_size = curr_size
                time.sleep(1)
            except FileNotFoundError:
                self.logger.info(f"File disappeared before organizing: {src.name}")
                return
            except PermissionError:
                self.logger.info(f"File is locked by another process: {src.name}. Waiting...")
                time.sleep(2)
        
        # Get destination path
        dest = get_destination_path(src, self.download_dir, self.config)
        
        # Move the file with retry logic
        success = False
        attempts = 0
        max_attempts = self.config["max_retry_attempts"]
        
        while not success and attempts < max_attempts:
            try:
                shutil.move(str(src), str(dest))
                category = get_category(src, self.config["categories"])
                
                # Update statistics
                self.stats["total_organized"] += 1
                self.stats["by_category"][category] = self.stats["by_category"].get(category, 0) + 1
                
                self.logger.info(f"Moved: {src.name} → {dest.relative_to(self.download_dir)}")
                success = True
            except (OSError, PermissionError) as e:
                attempts += 1
                if attempts >= max_attempts:
                    self.logger.error(f"Failed to move {src.name} after {max_attempts} attempts: {e}")
                else:
                    self.logger.warning(f"Error moving {src.name} (attempt {attempts}/{max_attempts}): {e}")
                    time.sleep(self.config["retry_delay_seconds"])


def perform_first_time_cleanup(downloads: Path, config: dict, logger):
    """
    If this is the first time the script is run, move all existing items
    into a folder named 'old_download'.
    """
    marker = downloads / MARKER_FILE
    if marker.exists():
        logger.info("Already initialized. Skipping first-time setup.")
        return

    logger.info("First run detected. Moving existing items to 'old_download'...")

    old_download_folder = downloads / "old_download"
    old_download_folder.mkdir(exist_ok=True)

    # Count files moved for reporting
    file_count = 0
    
    for item in downloads.iterdir():
        if item.name in {"old_download", MARKER_FILE, CONFIG_FILE, LOG_FILE}:
            continue  # Skip self and config files
        
        if is_excluded(item, config):
            logger.info(f"Skipping excluded item during initial cleanup: {item.name}")
            continue
            
        try:
            shutil.move(str(item), str(old_download_folder / item.name))
            logger.info(f"Moved: {item.name} → old_download/")
            file_count += 1
        except (OSError, PermissionError) as e:
            logger.error(f"Error moving {item.name}: {e}")

    # Create a marker so we don't do this again
    marker.touch()
    logger.info(f"Initial organization complete. Moved {file_count} items to old_download/")


def display_config_info(config, logger):
    """Display current configuration information."""
    logger.info("=== Current Configuration ===")
    logger.info(f"Organize by date: {config['organize_by_date']}")
    logger.info(f"Organize by type: {config['organize_by_type']}")
    logger.info(f"Wait delay: {config['delay_seconds']} seconds")
    logger.info(f"Excluded files: {len(config['excluded_files'])} items")
    logger.info(f"Excluded patterns: {len(config['excluded_patterns'])} patterns")
    logger.info(f"File categories: {len(config['categories'])} categories")
    logger.info("===========================")


def main():
    """Set up the Downloads watcher and organize existing files if first run."""
    parser = argparse.ArgumentParser(
        description="Watch and organize your Downloads folder by date and file type."
    )
    parser.add_argument(
        "--downloads", "-d",
        type=Path,
        default=Path.home() / "Downloads",
        help="Path to your Downloads folder (default: ~/Downloads)"
    )
    parser.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset configuration to defaults"
    )
    args = parser.parse_args()

    downloads = args.downloads.expanduser().resolve()
    if not downloads.is_dir():
        print(f"Error: {downloads} is not a directory.")
        return
    
    # Reset config if requested
    if args.reset_config:
        config_path = downloads / CONFIG_FILE
        if config_path.exists():
            os.remove(config_path)
            print("Configuration reset to defaults.")
    
    # Load or create configuration
    config = load_config(downloads)
    
    # Setup logging
    logger = setup_logging(downloads, config["log_level"])
    
    logger.info(f"Starting Download Organizer for: {downloads}")
    display_config_info(config, logger)
    
    # Perform first-time cleanup if needed
    perform_first_time_cleanup(downloads, config, logger)

    # Setup and start the watcher
    logger.info(f"Watching for new files...")
    event_handler = DownloadHandler(downloads, config, logger)
    observer = Observer()
    observer.schedule(event_handler, str(downloads), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(60)  # Check stats periodically
            stats = event_handler.stats
            if stats["total_organized"] > 0:
                logger.info(f"Stats: Organized {stats['total_organized']} files so far.")
    except KeyboardInterrupt:
        logger.info("Stopping organizer. Final stats:")
        stats = event_handler.stats
        logger.info(f"Total organized: {stats['total_organized']} files")
        for category, count in stats["by_category"].items():
            logger.info(f"  - {category}: {count} files")
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    main()
