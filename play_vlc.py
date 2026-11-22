import argparse
import os
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Matches filenames in format HHMM_DDMMYY.mp3 (captures HH in group 1)
FILENAME_REGEX = re.compile(r"^(\d{2})\d{2}_\d{6}\.mp3$")


def get_files_before_current_hour(
    directory: str,
    extra_pattern: str | None = None,
    recursive: bool = False,
    current_time: datetime | None = None,
    play_hour: int | None = None,
) -> list[Path]:
    """
    Find .mp3 files named HHMM_DDMMYY.mp3.
    When play_hour is provided, match only files with that exact HH prefix.
    Otherwise, preserve the default behavior and match hours strictly before
    the current hour.
    Read-only: never modifies or deletes any files.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    now = current_time or datetime.now()
    current_hour = play_hour if play_hour is not None else now.hour

    extra_regex = re.compile(extra_pattern) if extra_pattern else None
    iterator = root.rglob("*") if recursive else root.iterdir()

    matched = [
        path.resolve()
        for path in iterator
        if path.is_file()
        and (m := FILENAME_REGEX.match(path.name)) is not None
        and (
            int(m.group(1)) == play_hour
            if play_hour is not None
            else int(m.group(1)) < current_hour
        )
        and (extra_regex is None or extra_regex.search(path.name))
    ]

    return sorted(matched, key=lambda p: p.name)


def create_m3u_playlist(files: list[Path], playlist_path: str = "filtered_playlist.m3u") -> Path:
    """Write matching file paths into an M3U playlist file."""
    out = Path(playlist_path).resolve()
    with open(out, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for file_path in files:
            f.write(f"{file_path}\n")
    return out


def find_vlc_executable() -> str:
    """Locate the VLC binary on Windows, macOS, or Linux."""
    vlc_in_path = shutil.which("vlc")
    if vlc_in_path:
        return vlc_in_path

    common_paths = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        "/Applications/VLC.app/Contents/MacOS/VLC",
        "/usr/bin/vlc",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("Could not find VLC executable. Ensure VLC is installed or in your PATH.")


def is_rc_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if VLC's TCP Remote Control (rc) socket is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def send_rc_commands(host: str, port: int, commands: list[str], timeout: float = 3.0) -> None:
    """Send commands to VLC's TCP Remote Control (rc) interface."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        for cmd in commands:
            sock.sendall((cmd.strip() + "\n").encode("utf-8"))
            time.sleep(0.05)


def clear_playlist_and_stop(host: str = "127.0.0.1", port: int = 4212) -> bool:
    """Stop playback and clear the current VLC playlist via RC (never touches disk files)."""
    if not is_rc_listening(host, port):
        print(f"VLC RC interface is not listening on {host}:{port}. Nothing to clear/stop.")
        return False

    send_rc_commands(host, port, ["stop", "clear"])
    print(f"Stopped playback and cleared VLC playlist via RC ({host}:{port}).")
    return True


def build_vlc_launch_args(
    vlc_cmd: str,
    items: list[Path],
    host: str = "127.0.0.1",
    port: int = 4212,
    enqueue: bool = False,
    http: bool = False,
    http_host: str | None = None,
    http_port: int = 8080,
    http_password: str = "",
) -> list[str]:
    """Build command-line arguments to launch VLC with RC (and optional HTTP interface)."""
    args = [
        vlc_cmd,
        "--extraintf", "http:rc" if http else "rc",
        "--rc-host", f"{host}:{port}",
    ]
    if http:
        bind_host = http_host or host
        args += ["--http-host", bind_host, "--http-port", str(http_port)]
        if http_password:
            args += ["--http-password", http_password]
    if enqueue:
        args.append("--playlist-enqueue")
    args.extend(str(item) for item in items)
    return args


def open_in_vlc(
    files: list[Path],
    use_m3u: bool = False,
    enqueue: bool = False,
    clear_and_play: bool = False,
    clear_and_stop: bool = False,
    host: str = "127.0.0.1",
    port: int = 4212,
    http: bool = False,
    http_host: str | None = None,
    http_port: int = 8080,
    http_password: str = "",
    playlist_name: str = "filtered_playlist.m3u",
) -> None:
    """Launch VLC or control a running VLC instance with the matched files."""
    if clear_and_stop:
        clear_playlist_and_stop(host=host, port=port)
        return

    vlc_cmd = find_vlc_executable()
    target_items: list[Path] = [create_m3u_playlist(files, playlist_name)] if (use_m3u and files) else files

    if clear_and_play:
        if is_rc_listening(host, port):
            if target_items:
                commands = (
                    ["stop", "clear"]
                    + [f"add {item.as_uri()}" for item in target_items]
                    + ["play"]
                )
                send_rc_commands(host, port, commands)
                print(f"Cleared playlist and started playing {len(files)} file(s) via VLC RC.")
            else:
                send_rc_commands(host, port, ["stop", "clear"])
                print("Stopped playback and cleared VLC playlist (no eligible files found).")
            return

        if not files:
            print("No eligible files found.")
            return

        print(f"Launching VLC with {len(files)} file(s) (clear-and-play)...")
        subprocess.Popen(
            build_vlc_launch_args(
                vlc_cmd=vlc_cmd,
                items=target_items,
                host=host,
                port=port,
                http=http,
                http_host=http_host,
                http_port=http_port,
                http_password=http_password,
            )
        )
        return

    if not files:
        print("No eligible files found.")
        return

    if use_m3u:
        print(f"Created playlist '{target_items[0]}' with {len(files)} file(s).")

    print(f"Launching VLC with {len(files)} file(s)...")
    subprocess.Popen(
        build_vlc_launch_args(
            vlc_cmd=vlc_cmd,
            items=target_items,
            host=host,
            port=port,
            enqueue=enqueue,
            http=http,
            http_host=http_host,
            http_port=http_port,
            http_password=http_password,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter HHMM_DDMMYY.mp3 files by exact selected hour or before the current hour and control VLC."
    )
    parser.add_argument("directory", help="Path to directory containing HHMM_DDMMYY.mp3 files")
    parser.add_argument(
        "--play-hour-files",
        metavar="HH",
        type=parse_hour,
        help="Match only filenames starting with HH (for example, 07 matches 0719_221126.mp3)",
    )
    parser.add_argument("--regex", default=None, help="Optional extra regex to match against filename")
    parser.add_argument("--recursive", action="store_true", help="Search subdirectories recursively")
    parser.add_argument("--m3u", action="store_true", help="Generate and open an .m3u playlist file")
    parser.add_argument("--enqueue", action="store_true", help="Enqueue into an existing VLC instance")
    parser.add_argument(
        "--clear-and-play",
        action="store_true",
        help="Clear the current VLC playlist, add matching files, and start playing",
    )
    parser.add_argument(
        "--clear-and-stop",
        action="store_true",
        help="Stop playback and clear the current VLC playlist without adding files",
    )
    parser.add_argument("--rc-host", default="127.0.0.1", help="VLC RC host (default: 127.0.0.1)")
    parser.add_argument("--rc-port", type=int, default=4212, help="VLC RC port (default: 4212)")
    parser.add_argument("--http", action="store_true", help="Also enable VLC HTTP web interface when launching VLC")
    parser.add_argument(
        "--http-host",
        default=None,
        help="VLC HTTP bind host (default: same as --rc-host; use 0.0.0.0 to listen on all interfaces)",
    )
    parser.add_argument("--http-port", type=int, default=8080, help="VLC HTTP port (default: 8080)")
    parser.add_argument("--http-password", default="", help="VLC HTTP interface password")
    return parser.parse_args()


def parse_hour(value: str) -> int:
    """Parse an hour in 24-hour HH format."""
    if not re.fullmatch(r"\d{2}", value):
        raise argparse.ArgumentTypeError("hour must be in HH format (00-23)")

    hour = int(value)
    if hour > 23:
        raise argparse.ArgumentTypeError("hour must be in HH format (00-23)")
    return hour


def main() -> None:
    args = parse_args()

    if args.clear_and_stop:
        open_in_vlc(
            files=[],
            clear_and_stop=True,
            host=args.rc_host,
            port=args.rc_port,
        )
        return

    now = datetime.now()
    matches = get_files_before_current_hour(
        directory=args.directory,
        extra_pattern=args.regex,
        recursive=args.recursive,
        current_time=now,
        play_hour=args.play_hour_files,
    )

    if args.play_hour_files is not None:
        print(
            f"Selected hour: {args.play_hour_files:02d}:xx | "
            f"Matching files starting with {args.play_hour_files:02d}: {len(matches)}"
        )
    else:
        print(
            f"Current hour: {now.hour:02d}:xx | "
            f"Matching files with hour < {now.hour:02d}: {len(matches)}"
        )
    for m in matches:
        print("  Matched:", m.name)

    open_in_vlc(
        files=matches,
        use_m3u=args.m3u,
        enqueue=args.enqueue,
        clear_and_play=args.clear_and_play,
        host=args.rc_host,
        port=args.rc_port,
        http=args.http,
        http_host=args.http_host,
        http_port=args.http_port,
        http_password=args.http_password,
    )


if __name__ == "__main__":
    main()