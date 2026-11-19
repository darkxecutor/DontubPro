#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DONTUB Pro v1.0 - Advanced YouTube Downloader
Optimized for long videos (5+ hours) at maximum quality
Compatible with: Termux / Pydroid 3 / Acode / Linux / Windows
"""

import os
import sys
import json
import random
import time
import shutil
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("\033[91m❌ yt-dlp library is not installed!\033[0m")
    print("Run: pip install -U 'yt-dlp[default]'")
    sys.exit(1)

# ==================== Constants ====================
VERSION = "1.0 English Edition"
EMOJIS = ["🖇️", "🧲", "💉", "💊", "🧰", "🧬", "🧪", "🎥", "🎞️", "🎭",
          "🎰", "🎲", "🎃", "🍹", "🍯", "🧋", "☕", "🍾", "🍳", "🥦",
          "🥑", "🍉", "🌶️", "🍅", "🐞", "🐬", "🦚", "🐧", "🐤", "🌑",
          "🌒", "🌌", "🌏", "🌚"]

CONFIG_FILE = Path.home() / ".dontub_config.json"
HISTORY_FILE = Path.home() / ".dontub_history.jsonl"

DEFAULT_CONFIG = {
    "output_dir": "",
    "cookies_file": "",
    "download_thumbnail": False,
    "embed_metadata": True,
    "notifications": True,
    "speed_limit": 0,
    "concurrent_fragments": 8,
}

# ==================== Helper utilities ====================
def colored(text, code):
    return f"\033[{code}m{text}\033[0m"

def emoji():
    return random.choice(EMOJIS)

def is_termux():
    return "com.termux" in os.environ.get("PREFIX", "")

def notify(title, content):
    if not load_config().get("notifications", True):
        return
    if shutil.which("termux-notification"):
        os.system(f'termux-notification --title "{title}" --content "{content}" --priority high 2>/dev/null')

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def human_size(b):
    if not b:
        return "?"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}PB"

def human_time(sec):
    if not sec:
        return "?"
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

# ==================== Configuration management ====================
def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_output_dir():
    cfg = load_config()
    if cfg.get("output_dir"):
        return cfg["output_dir"]
    if is_termux():
        termux_dl = Path.home() / "storage" / "downloads"
        if termux_dl.exists():
            return str(termux_dl / "DONTUB_Downloads")
    return str(Path.home() / "DONTUB_Downloads")

# ==================== Download history ====================
def add_history(title, url, quality):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "url": url,
        "quality": quality,
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def show_history():
    clear()
    print_banner()
    print(f"  {colored('📜 Download History', '96')}\n")
    if not HISTORY_FILE.exists():
        print(f"  {colored('No history yet.', '93')}\n")
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        if not lines:
            print(f"  {colored('No history yet.', '93')}\n")
            return
        for i, e in enumerate(reversed(lines[-20:]), 1):
            print(f"  {colored(str(i).rjust(2), '92')}. {colored(e['date'], '90')} | {colored(e['quality'], '96')}")
            print(f"     └─ {e['title'][:60]}")
        print(f"\n  {colored(f'Total: {len(lines)} downloads', '93')}\n")
    except Exception as ex:
        print(f"  {colored(f'Error reading history: {ex}', '91')}\n")

# ==================== Progress bar (optimized for long videos) ====================
def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        speed = d.get('speed') or 0
        speed_str = f"{speed/1024/1024:.2f} MB/s" if speed else "---"
        eta = d.get('eta') or 0
        if eta and eta > 3600:
            eta_str = f"{eta//3600}h{(eta%3600)//60}m"
        elif eta:
            eta_str = f"{int(eta)//60}:{int(eta)%60:02d}"
        else:
            eta_str = "--:--"

        if total:
            try:
                downloaded = int(d.get('downloaded_bytes', 0))
                total = int(total)
                percent = downloaded / total * 100
                bar_len = 25
                filled = int(bar_len * percent // 100)
                bar = '█' * filled + '░' * (bar_len - filled)
                size_str = f"{human_size(downloaded)}/{human_size(total)}"
                sys.stdout.write(
                    f"\r  {emoji()} {colored(f'[{bar}] {percent:.1f}%', '93')} | "
                    f"{size_str} | {colored(speed_str, '96')} | ⏳ {eta_str}  "
                )
                sys.stdout.flush()
            except (ValueError, TypeError):
                pass
        else:
            # fallback: use the percentage that yt-dlp computes itself
            pct = (d.get('_percent_str') or '').strip()
            if pct and pct != 'N/A':
                sys.stdout.write(
                    f"\r  {emoji()} {colored(pct, '93')} | "
                    f"{colored(speed_str, '96')} | ⏳ {eta_str}  "
                )
                sys.stdout.flush()

    elif d['status'] == 'finished':
        print(f"\n  {colored('✅ Fragment download complete, merging/processing...', '92')} {emoji()}")
    elif d['status'] == 'error':
        print(f"\n  {colored('❌ Download error', '91')}")

# ==================== Building yt-dlp options ====================
def build_opts(quality, output_dir, custom_format=None):
    cfg = load_config()
    opts = {
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'noplaylist': False,

        # === Long video optimizations (5+ hours) ===
        'retries': 30,
        'fragment_retries': 30,
        'extractor_retries': 15,
        'file_access_retries': 15,
        'socket_timeout': 120,
        'http_chunk_size': 10 * 1024 * 1024,
        'concurrent_fragment_downloads': int(cfg.get("concurrent_fragments", 8)),
        'throttledratelimit': 1024,
        'check_formats': False,
        'skip_unavailable_fragments': True,

        # === General settings ===
        'windowsfilenames': True,
        'continuedl': True,
        'overwrites': False,
        'trim_file_name': 200,
        'no_color': False,
        'noprogress': True,
    }

    # cookies
    ck = cfg.get("cookies_file")
    if ck and os.path.exists(ck):
        opts['cookiefile'] = ck

    # speed limit
    if cfg.get("speed_limit", 0) > 0:
        opts['ratelimit'] = cfg['speed_limit'] * 1024 * 1024

    # ===== Format selection =====
    if custom_format:
        opts['format'] = custom_format
        opts['merge_output_format'] = 'mp4/mkv'
    elif quality == 'best':
        # * = allows using full bestvideo (video+audio) if no separate video exists
        opts['format'] = 'bestvideo*+bestaudio/best'
        opts['merge_output_format'] = 'mp4/mkv'
    elif quality == 'audio':
        opts['format'] = 'bestaudio/best'
    elif quality.endswith('p'):
        h = quality.replace('p', '')
        opts['format'] = (
            f'bestvideo[height<={h}]+bestaudio/'
            f'best[height<={h}]/best'
        )
        opts['merge_output_format'] = 'mp4/mkv'

    # postprocessors
    pps = []
    if quality == 'audio' and not custom_format:
        pps.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
    if cfg.get("embed_metadata", True) and check_ffmpeg():
        pps.append({'key': 'FFmpegMetadata', 'add_metadata': True})
    if pps:
        opts['postprocessors'] = pps

    if cfg.get("download_thumbnail", False):
        opts['writethumbnail'] = True

    return opts

# ==================== Show formats ====================
def show_formats(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            formats = info.get('formats', [])
            clear()
            print_banner()
            print(f"  {colored('📊 Available formats:', '96')} {info.get('title', '')[:50]}\n")
            print(f"  {colored('ID', '93'):<10} {colored('Ext', '93'):<6} {colored('Res', '93'):<12} "
                  f"{colored('FPS', '93'):<5} {colored('Size', '93'):<10} {colored('Codec', '93')}")
            print(f"  {'─'*70}")
            for f in formats:
                fid = str(f.get('format_id', '?'))[:8]
                ext = (f.get('ext') or '?')[:5]
                res = f.get('resolution') or f"{f.get('width','?')}x{f.get('height','?')}"
                fps = f.get('fps') or '-'
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_str = human_size(size)
                vcodec = (f.get('vcodec') or 'none')[:10]
                acodec = (f.get('acodec') or 'none')[:10]
                print(f"  {fid:<10} {ext:<6} {res[:12]:<12} {str(fps):<5} {size_str:<10} v:{vcodec} a:{acodec}")
            print()
            return True
    except Exception as ex:
        print(f"\n  {colored(f'❌ Error: {ex}', '91')}")
        return False

# ==================== Search ====================
def search_youtube(query, n=5):
    print(f"\n  {colored('🔍 Searching...', '95')} {emoji()}\n")
    try:
        opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
            return info.get('entries', [])
    except Exception as ex:
        print(f"  {colored(f'❌ Search failed: {ex}', '91')}")
        return []

def search_menu():
    clear()
    print_banner()
    q = input(f"  {emoji()} {colored('Enter video name:', '94')} ").strip()
    if not q:
        return
    results = search_youtube(q, 8)
    if not results:
        print(f"  {colored('No results found.', '91')}")
        return
    print(f"  {colored('Results:', '96')}\n")
    for i, r in enumerate(results, 1):
        title = r.get('title', '?')[:65]
        dur = r.get('duration') or 0
        dur_str = human_time(dur)
        uploader = (r.get('uploader') or '?')[:25]
        print(f"  {colored(str(i).rjust(2), '92')}. {title}")
        print(f"      {colored(dur_str, '93')} | {colored(uploader, '90')}")
    print(f"\n  {colored('0', '92')}. Back\n")
    try:
        ch = int(input(f"  {colored('➤ Choose video number:', '95')} ").strip())
        if 1 <= ch <= len(results):
            vid = results[ch-1]
            url = vid.get('url') or f"https://youtube.com/watch?v={vid.get('id')}"
            download_flow(url)
    except (ValueError, KeyboardInterrupt):
        pass

# ==================== Download ====================
def download_video(url, quality='best', custom_format=None):
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    if not check_ffmpeg():
        print(f"  {colored('⚠️ FFmpeg is not installed! Merging will fail.', '93')}")
        print(f"  {colored('   Run: apk add ffmpeg', '93')}")

    opts = build_opts(quality, output_dir, custom_format)

    print(f"\n  {colored('🔗 URL:', '94')} {url[:80]}")
    print(f"  {emoji()} {colored('Checking...', '95')}\n")

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info and info['entries']:
                first = info['entries'][0] if info['entries'] else {}
                title = first.get('title') or info.get('title') or 'Playlist'
                print(f"  {emoji()} {colored('Type:', '96')} Playlist ({len(info['entries'])} videos)")
            else:
                first = info
                title = info.get('title', 'Video')

            dur = first.get('duration') or 0
            uploader = first.get('uploader') or '?'
            views = first.get('view_count') or 0

            # === Basic info ===
            print(f"  {emoji()} {colored('Title:', '96')} {title[:60]}")
            print(f"  {emoji()} {colored('Channel:', '96')} {uploader}")
            print(f"  {emoji()} {colored('Duration:', '96')} {human_time(dur)}")
            print(f"  {emoji()} {colored('Views:', '96')} {views:,}" if views else f"  {emoji()} {colored('Views:', '96')} ?")
            print(f"  {emoji()} {colored('Saved to:', '96')} {output_dir}")

            # === Warning for long videos ===
            dur_hours = (dur or 0) / 3600
            if dur_hours >= 3:
                print(f"\n  {colored('⚠️ Very long video:', '93')} {dur_hours:.1f} hours")
                print(f"  {colored('   Download + merge may take a long time.', '93')}")
                print(f"  {colored('   Do not close the tool until completion is shown.', '93')}")

            # === Size estimation ===
            requested = [f for f in (first.get('formats') or []) if f.get('format_id') in (custom_format or '')]
            est_bytes = 0
            for f in requested:
                est_bytes += f.get('filesize_approx') or f.get('filesize') or 0
            if not est_bytes:
                fmt_list = first.get('formats') or []
                if quality == 'best' and fmt_list:
                    best_v = max(
                        (f for f in fmt_list if (f.get('vcodec') or 'none') != 'none'),
                        key=lambda x: (x.get('height') or 0, x.get('tbr') or 0),
                        default=None
                    )
                    if best_v:
                        est_bytes += best_v.get('filesize_approx') or best_v.get('filesize') or 0
            if est_bytes > 1024**3:
                print(f"  {emoji()} {colored('Estimated size:', '96')} ~{human_size(est_bytes)}")
                if est_bytes > 8 * 1024**3:
                    print(f"  {colored('⚠️ Huge file (>8GB) - check your storage space.', '93')}")

            print(f"\n  {colored('⬇️ Starting download...', '92')}\n")

            ydl.download([url])

        add_history(title, url, quality)
        notify("DONTUB Pro ✅", f"Completed: {title[:40]}")
        print(f"\n\n  {colored('✨✨✨ Download completed successfully! ✨✨✨', '92')} {emoji()}")
        print(f"  {colored('📁 Path:', '93')} {output_dir}")

    except yt_dlp.utils.DownloadError as ex:
        msg = str(ex)
        print(f"\n  {colored('❌ Download failed:', '91')}")
        if "Private video" in msg:
            print(f"  {colored('Private video. You may need cookies.', '93')}")
        elif "not available" in msg:
            print(f"  {colored('Video not available in your country, or removed.', '93')}")
        elif "HTTP Error 403" in msg:
            print(f"  {colored('Error 403. Try: pip install -U yt-dlp', '93')}")
        elif "Sign in" in msg or "age" in msg.lower():
            print(f"  {colored('Sign-in required. Add cookies from settings.', '93')}")
        elif "ffmpeg" in msg.lower() or "ffprobe" in msg.lower():
            print(f"  {colored('FFmpeg missing! Run: apk add ffmpeg', '93')}")
        else:
            print(f"  {colored(msg[:200], '91')}")
    except KeyboardInterrupt:
        print(f"\n  {colored('⏹️ Cancelled.', '93')}")
    except Exception as ex:
        print(f"\n  {colored(f'❌ Error: {str(ex)[:200]}', '91')}")

# ==================== Quality selection flow ====================
def download_flow(url):
    while True:
        clear()
        print_banner()
        print(f"  {colored('🔗', '94')} {url[:75]}\n")
        print(f"  {emoji()} {colored('Choose quality:', '96')}")
        print(f"     {colored('1', '92')} - Best quality (may be 4K/8K) 🎬")
        print(f"     {colored('2', '92')} - 1080p 🎥")
        print(f"     {colored('3', '92')} - 720p 📺")
        print(f"     {colored('4', '92')} - 480p 📱")
        print(f"     {colored('5', '92')} - 360p 📲")
        print(f"     {colored('6', '92')} - MP3 (audio only) 🎵")
        print(f"     {colored('7', '92')} - Show all formats 📊")
        print(f"     {colored('0', '92')} - Back ⬅️")
        ch = input(f"\n  {colored('➤ Your choice:', '95')} ").strip()

        if ch == '0':
            return
        elif ch == '7':
            if show_formats(url):
                fid = input(f"\n  {colored('Format ID (Enter to go back):', '95')} ").strip()
                if fid:
                    download_video(url, custom_format=fid)
                    input(f"\n  {colored('Press Enter to continue...', '90')}")
        else:
            qmap = {'1':'best','2':'1080p','3':'720p','4':'480p','5':'360p','6':'audio'}
            if ch in qmap:
                download_video(url, quality=qmap[ch])
                input(f"\n  {colored('Press Enter to return...', '90')}")
                return
              # ==================== Settings ====================
def settings_menu():
    while True:
        cfg = load_config()
        clear()
        print_banner()
        print(f"  {colored('⚙️ Settings', '96')}\n")
        out = cfg.get('output_dir') or get_output_dir()
        ck = cfg.get('cookies_file') or 'Not set'
        print(f"  {colored('1', '92')}. Output path: {colored(out, '93')}")
        print(f"  {colored('2', '92')}. Cookies file: {colored(ck, '93')}")
        print(f"  {colored('3', '92')}. Save Thumbnail: {colored('Yes' if cfg.get('download_thumbnail') else 'No', '93')}")
        print(f"  {colored('4', '92')}. Embed Metadata: {colored('Yes' if cfg.get('embed_metadata') else 'No', '93')}")
        print(f"  {colored('5', '92')}. Termux notifications: {colored('Yes' if cfg.get('notifications') else 'No', '93')}")
        sl = cfg.get('speed_limit', 0)
        print(f"  {colored('6', '92')}. Speed limit: {colored(f'{sl} MB/s' if sl else 'Unlimited', '93')}")
        cf = cfg.get('concurrent_fragments', 8)
        print(f"  {colored('7', '92')}. Concurrent downloads: {colored(f'{cf} fragments', '93')}")
        print(f"  {colored('0', '92')}. Back ⬅️")
        ch = input(f"\n  {colored('➤ Your choice:', '95')} ").strip()

        if ch == '0':
            return
        elif ch == '1':
            p = input(f"  New path (Enter for default): ").strip()
            cfg['output_dir'] = p
            save_config(cfg)
        elif ch == '2':
            p = input(f"  Path to cookies.txt (Enter to clear): ").strip()
            cfg['cookies_file'] = p
            save_config(cfg)
        elif ch == '3':
            cfg['download_thumbnail'] = not cfg.get('download_thumbnail', False)
            save_config(cfg)
        elif ch == '4':
            cfg['embed_metadata'] = not cfg.get('embed_metadata', True)
            save_config(cfg)
        elif ch == '5':
            cfg['notifications'] = not cfg.get('notifications', True)
            save_config(cfg)
        elif ch == '6':
            try:
                v = int(input(f"  Speed limit in MB/s (0 = unlimited): ").strip() or "0")
                cfg['speed_limit'] = max(0, v)
                save_config(cfg)
            except ValueError:
                pass
        elif ch == '7':
            try:
                v = int(input(f"  Number of concurrent fragments (1-16, default 8): ").strip() or "8")
                cfg['concurrent_fragments'] = max(1, min(16, v))
                save_config(cfg)
            except ValueError:
                pass

# ==================== System info ====================
def system_info():
    clear()
    print_banner()
    print(f"  {colored('ℹ️ System Information', '96')}\n")
    print(f"  {emoji()} Python: {colored(sys.version.split()[0], '93')}")
    print(f"  {emoji()} yt-dlp: {colored(yt_dlp.version.__version__, '93')}")
    print(f"  {emoji()} FFmpeg: {colored('✅ Installed' if check_ffmpeg() else '❌ Not installed', '92' if check_ffmpeg() else '91')}")
    print(f"  {emoji()} Termux: {colored('Yes' if is_termux() else 'No', '93')}")
    print(f"  {emoji()} Output path: {colored(get_output_dir(), '93')}")
    print(f"  {emoji()} Version: {colored(VERSION, '92')}")

# ==================== Banner ====================
def print_banner():
    clear()
    c = random.choice(["95", "96", "92", "93", "94"])
    print(colored("""    ╔══════════════════════════════════════════════════════════╗
    ║   ██████╗  ██████╗ ███╗   ██╗████████╗██╗   ██╗██████╗   ║
    ║   ██╔══██╗██╔═══██╗████╗  ██║╚══██╔══╝██║   ██║██╔══██╗  ║
    ║   ██║  ██║██║   ██║██╔██╗ ██║   ██║   ██║   ██║██████╔╝  ║
    ║   ██║  ██║██║   ██║██║╚██╗██║   ██║   ██║   ██║██╔══██╗  ║
    ║   ██████╔╝╚██████╔╝██║ ╚████║   ██║   ╚██████╔╝██████╔╝  ║
    ║   ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═════╝   ║
    ║    🚀 The Legendary Downloader - v1.0 Long-Video 🚀       ║
    ║         GitHub: https://github.com/darkxecutor           ║ 
    ║         Instagram: jawad_smlali_                         ║
    ╚══════════════════════════════════════════════════════════╝""", c))
    print(f"  {emoji()} {colored('Ready to download at max quality - even long videos!', '92')} {emoji()}\n")

# ==================== Main menu ====================
def main_menu():
    while True:
        print_banner()
        print(f"  {colored('Main Menu:', '96')}\n")
        print(f"  {colored('1', '92')}. 🔗 Download from URL")
        print(f"  {colored('2', '92')}. 🔍 Search and download")
        print(f"  {colored('3', '92')}. ⚙️  Settings")
        print(f"  {colored('4', '92')}. 📜 Download history")
        print(f"  {colored('5', '92')}. ℹ️  System information")
        print(f"  {colored('0', '92')}. 🚪 Exit")
        ch = input(f"\n  {colored('➤ Your choice:', '95')} ").strip()

        try:
            if ch == '0':
                print(f"\n  {emoji()} {colored('Goodbye!', '92')}\n")
                break
            elif ch == '1':
                clear()
                print_banner()
                url = input(f"  {emoji()} {colored('Paste the URL:', '94')} ").strip()
                if url:
                    download_flow(url)
            elif ch == '2':
                search_menu()
                input(f"\n  {colored('Press Enter to continue...', '90')}")
            elif ch == '3':
                settings_menu()
            elif ch == '4':
                show_history()
                input(f"\n  {colored('Press Enter to continue...', '90')}")
            elif ch == '5':
                system_info()
                input(f"\n  {colored('Press Enter to continue...', '90')}")
            else:
                print(f"  {colored('❌ Invalid choice!', '91')}")
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n  {emoji()} {colored('Goodbye!', '92')}\n")
            break

if __name__ == "__main__":
    if not CONFIG_FILE.exists():
        save_config(dict(DEFAULT_CONFIG))
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {emoji()} {colored('Terminated.', '92')}\n")
