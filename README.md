# Python Scripts & Utilities Suite

A modular CLI utility suite with subcommands, built using Python's standard library.

## Project Structure

```
python_scripts/
├── main.py                 # Central CLI dispatcher with subcommands
├── play_vlc.py             # Standalone filename-filtered VLC player
├── move_dirs.py            # Move MP3 files one directory level up
├── utils/                  # Modular utilities package
│   ├── __init__.py         # Package exports
│   └── fs_utils.py         # Filesystem tools (e.g., clean-empty-dirs)
└── tests/                  # Automated unit and CLI integration tests
    ├── __init__.py
    ├── test_cli.py         # CLI parsing and command invocation tests
    └── test_fs_utils.py    # Unit tests for filesystem logic
```

## Running Utilities

### 1. Delete Empty Directories (`clean-empty-dirs`)

Recursively deletes empty directories across all subdirectories bottom-up:

```bash
# Preview what would be deleted without making any changes (dry run)
python3 main.py clean-empty-dirs /path/to/folder -n

# Remove empty subdirectories
python3 main.py clean-empty-dirs /path/to/folder

# Remove empty subdirectories quietly (summary only)
python3 main.py clean-empty-dirs /path/to/folder -q

# Also remove the target root directory itself if it ends up empty
python3 main.py clean-empty-dirs /path/to/folder --delete-root
```

*Alias available:* `delete-empty-dirs` can be used in place of `clean-empty-dirs`.

### 2. General Help

```bash
python3 main.py --help
python3 main.py <command> --help
```

### 3. Filter and Play MP3 Files (`play_vlc.py`)

`play_vlc.py` is a standalone script (run directly, not through `main.py`) that
finds MP3 files named `HHMM_DDMMYY.mp3` and opens them in VLC. By default, it
selects files whose filename hour (`HH`) is earlier than the current hour.
Optionally, provide `--play-hour-files HH` to use a specific 24-hour cutoff
(`00`–`23`) instead. The cutoff is exclusive: for example, `--play-hour-files
10` selects files with hours `00` through `09`.

```bash
# See all options
python3 play_vlc.py --help

# Play matching files in this directory (uses the current hour cutoff)
python3 play_vlc.py /path/to/recordings

# Use an explicit hour cutoff
python3 play_vlc.py /path/to/recordings --play-hour-files 10

# Search subdirectories and further filter filenames with a regular expression
python3 play_vlc.py /path/to/recordings --recursive --regex '0101'

# Write the selected paths to an M3U playlist and open it in VLC
python3 play_vlc.py /path/to/recordings --m3u

# Add files to a running VLC instance, or clear its playlist before playing
python3 play_vlc.py /path/to/recordings --enqueue
python3 play_vlc.py /path/to/recordings --clear-and-play

# Stop playback and clear the running VLC playlist
python3 play_vlc.py /path/to/recordings --clear-and-stop

# Enable VLC's HTTP interface when launching VLC
python3 play_vlc.py /path/to/recordings --http --http-password 'your-password'
```

Available arguments:

| Argument | Description |
| --- | --- |
| `directory` | Required directory to search for matching MP3 files. |
| `--play-hour-files HH` | Optional hour cutoff (`00`–`23`); selects filename hours strictly less than `HH`. Defaults to the current hour. |
| `--regex REGEX` | Optional additional regular expression applied to each filename. |
| `--recursive` | Search the directory tree recursively. |
| `--m3u` | Create `filtered_playlist.m3u` and open that playlist in VLC. |
| `--enqueue` | Enqueue matching files into VLC when launching it. |
| `--clear-and-play` | Clear the running VLC playlist, add the matches, and start playback. |
| `--clear-and-stop` | Stop playback and clear the running VLC playlist without adding files. |
| `--rc-host HOST` / `--rc-port PORT` | Set the VLC Remote Control host and port (defaults: `127.0.0.1` and `4212`). |
| `--http` | Enable VLC's HTTP interface when launching VLC. |
| `--http-host HOST` / `--http-port PORT` | Set the HTTP interface bind host and port (default port: `8080`; host defaults to the RC host). |
| `--http-password PASSWORD` | Set the VLC HTTP interface password. |

The script does not modify or delete the source MP3 files. Creating an M3U
playlist writes the playlist file in the current working directory by default.

### 4. Move MP3 Files One Level Up (`move_dirs.py`)

This standalone script recursively finds `.mp3` files below the specified
directory and moves each file into its parent directory (one level up). Files
already directly inside the specified directory are left in place. If a
destination file with the same name already exists, that file is skipped.
Use `--dry-run` to preview moves without changing files.

```bash
# Preview eligible moves
python3 move_dirs.py /path/to/recordings --dry-run

# Move MP3 files one directory level up
python3 move_dirs.py /path/to/recordings

# Show command options
python3 move_dirs.py --help
```

| Argument | Description |
| --- | --- |
| `directory` | Required directory to scan recursively for MP3 files. |
| `--dry-run` | Print planned moves without modifying any files. |

---

## Adding Future Utilities

To add a new utility tool (e.g., text utils, network utils, or media utils):

1. **Create your utility module** inside `utils/` (e.g., `utils/text_utils.py`):
   ```python
   import argparse

   def run_my_tool(args: argparse.Namespace) -> int:
       print("Running tool with", args)
       return 0

   def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
       parser = subparsers.add_parser("my-tool", help="Description of my tool")
       parser.add_argument("--my-flag", action="store_true")
       parser.set_defaults(func=run_my_tool)
   ```

2. **Register the module** in `main.py`:
   ```python
   from utils import fs_utils, text_utils

   COMMAND_MODULES = [
       fs_utils,
       text_utils,
   ]
   ```

3. **Add corresponding tests** in `tests/test_text_utils.py`.

---

## Running Tests

Run all unit and integration tests using Python's standard `unittest`:

```bash
python3 -m unittest discover tests
```
