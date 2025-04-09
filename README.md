# Downloads Organizer

A Python utility that automatically organizes your Downloads folder by date.

## Features

- **First-run cleanup**: Moves existing files in Downloads to an 'old_download' folder
- **Continuous monitoring**: Watches for new files and organizes them into dated folders (YYYY-MM-DD)
- **Smart handling**: Ignores temporary/partial download files (.crdownload, .part, .tmp)
- **Download completion detection**: Waits for downloads to complete before organizing
- **Simple setup**: Just run the script and it handles the rest

## Requirements

- Python 3.6+
- watchdog library (`pip install watchdog`)

## Usage

```bash
# Basic usage (watches default Downloads folder)
python organize_download.py

# Specify a different Downloads folder
python organize_download.py --downloads /path/to/downloads

# Adjust the delay before moving files (in seconds)
python organize_download.py --delay 10
```

## How It Works

1. **First-time setup**: When run for the first time, the script moves all existing files in your Downloads folder to a subfolder called 'old_download'
2. **Monitoring**: The script then continuously watches for new files in your Downloads folder
3. **Organization**: When a new file appears, the script:
   - Waits for the download to complete
   - Creates a folder with today's date (if it doesn't exist)
   - Moves the file into that folder

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

The `.spec` file included suggests you can build this into a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller organize_download.spec
```

The executable will be created in the `dist` directory.
