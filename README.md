# Downloads Organizer

A smart Python utility that automatically organizes your Downloads folder by date and file type.

## Features

- **File categorization**: Automatically sorts files into categories (images, documents, video, etc.)
- **First-run cleanup**: Moves existing files in Downloads to an 'old_download' folder
- **Continuous monitoring**: Watches for new files and organizes them
- **Smart handling**: Ignores temporary/partial download files
- **Download completion detection**: Waits for downloads to complete before organizing
- **Duplicate file handling**: Automatically renames files that would overwrite existing ones
- **Configurable settings**: JSON configuration file for customizing behavior
- **Exclusion patterns**: Skip files you don't want organized
- **Detailed logging**: Logs all activity to both console and a log file
- **Statistics tracking**: Keeps count of files moved by category

## Requirements

- Python 3.6+
- watchdog library (`pip install watchdog`)

## Usage

```bash
# Basic usage (watches default Downloads folder)
python organize_download.py

# Specify a different Downloads folder
python organize_download.py --downloads /path/to/downloads

# Reset configuration to defaults
python organize_download.py --reset-config
```

## How It Works

1. **First-time setup**: When run for the first time, the script moves all existing files in your Downloads folder to a subfolder called 'old_download'
2. **Configuration**: Creates a `.organize_config.json` file with default settings that you can customize
3. **Monitoring**: Continuously watches for new files in your Downloads folder
4. **Organization**: When a new file appears, the script:
   - Waits for the download to complete
   - Determines the file category based on extension
   - Creates appropriate date and category folders (if they don't exist)
   - Moves the file, handling duplicates if needed
   - Updates statistics and logs the activity

## Configuration Options

The `.organize_config.json` file lets you customize:

- `organize_by_date`: Whether to create date folders (YYYY-MM-DD)
- `organize_by_type`: Whether to create category folders (images, documents, etc.)
- `delay_seconds`: Time to wait after a file appears before processing
- `excluded_files`: List of specific filenames to ignore
- `excluded_patterns`: Regular expression patterns for files to ignore
- `categories`: Customize file categories and their extensions
- `log_level`: Set logging verbosity (INFO, DEBUG, etc.)
- `rename_duplicates`: Whether to rename files that would overwrite existing ones
- `max_retry_attempts`: Number of times to retry moving a locked file
- `retry_delay_seconds`: Time to wait between retry attempts

## File Categories

Files are automatically sorted into these categories:

- **images**: jpg, jpeg, png, gif, etc.
- **documents**: pdf, doc, docx, txt, etc.
- **audio**: mp3, wav, flac, etc.
- **video**: mp4, avi, mkv, etc.
- **archives**: zip, rar, 7z, etc.
- **executables**: exe, msi, apk, etc.
- **code**: py, js, html, css, etc.
- **other**: Any file type not in the above categories

## Ready-to-Use Executable

For Windows users who don't want to install Python or any dependencies, a ready-to-use executable is provided:

1. Go to the [Releases](https://github.com/Mj-Njuguna/download_organizer/releases) section of this repository
2. Download the latest `organize_download.exe` file
3. Run the executable on your Windows computer
4. The program will start organizing your Downloads folder immediately
5. To keep it running in the background, you may want to:
   - Create a shortcut in your Startup folder
   - Run it as a scheduled task at login

No installation or Python knowledge required!

## Building an Executable (Optional)

The `.spec` file included allows you to build this into a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller organize_download.spec
```

The executable will be created in the `dist` directory.
