import argparse
import os
import sys
import shutil
import zipfile
import urllib.request
import time
import subprocess
from pathlib import Path
from typing import Any, cast
from yt_dlp import YoutubeDL
import requests

try:
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3
    from mutagen.id3._frames import APIC
    from mutagen.wave import WAVE
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    print("[WARN] 'mutagen' library not found. Metadata tagging will be disabled.")
    print("       Install it with: pip install mutagen")

def tag_audio_metadata(filepath, info, audio_format):
    """Tag MP3 or WAV file with metadata from info dict."""
    if not HAS_MUTAGEN:
        return

    title = info.get('title')
    artist = info.get('artist') or info.get('uploader')
    album = info.get('album') or info.get('playlist_title')
    thumbnail_url = info.get('thumbnail')
    
    try:
        if audio_format == 'mp3':
            try:
                audio = EasyID3(filepath)
            except Exception:
                # File might not have tags yet, save minimal to create them
                audio = EasyID3()
                audio.save(filepath)
                audio = EasyID3(filepath)
                
            if title: audio['title'] = title
            if artist: audio['artist'] = artist
            if album: audio['album'] = album
            audio.save()
            
            # Add album art via ID3 (EasyID3 doesn't support images)
            if thumbnail_url:
                try:
                    img_data = requests.get(thumbnail_url, timeout=10).content
                    audio = ID3(filepath)
                    audio.add(APIC(
                        encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_data
                    ))
                    audio.save()
                except Exception:
                    pass
                    
        elif audio_format == 'wav':
            audio = WAVE(filepath)
            # WAV ID3 tags are non-standard, Mutagen uses specific keys
            if title: audio['TIT2'] = title
            if artist: audio['TPE1'] = artist
            if album: audio['TALB'] = album
            audio.save()
            
    except Exception as e:
        print(f"[WARN] Could not tag {filepath}: {e}")

def check_ffmpeg(ffmpeg_path=None):
    """Check if FFmpeg is available on the system or at a provided path."""
    if ffmpeg_path:
        if os.path.isfile(ffmpeg_path):
            return os.access(ffmpeg_path, os.X_OK) or ffmpeg_path.lower().endswith('.exe')
        if os.path.isdir(ffmpeg_path):
            ffmpeg_exe = os.path.join(ffmpeg_path, 'ffmpeg.exe')
            if os.path.isfile(ffmpeg_exe):
                return os.access(ffmpeg_exe, os.X_OK) or ffmpeg_exe.lower().endswith('.exe')
        try:
            return shutil.which(ffmpeg_path) is not None
        except Exception:
            return False
    return shutil.which("ffmpeg") is not None

def get_local_ffmpeg_path():
    """Get path to locally downloaded ffmpeg in the script directory."""
    script_dir = Path(__file__).parent
    ffmpeg_dir = script_dir / "ffmpeg"
    ffmpeg_exe = ffmpeg_dir / "bin" / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        return str(ffmpeg_dir / "bin")
    return None

def download_ffmpeg():
    """Download and extract FFmpeg static build for Windows."""
    script_dir = Path(__file__).parent
    ffmpeg_dir = script_dir / "ffmpeg"
    ffmpeg_exe = ffmpeg_dir / "bin" / "ffmpeg.exe"
    
    if ffmpeg_exe.exists():
        return str(ffmpeg_dir / "bin")
    
    print("\nFFmpeg not found. Downloading FFmpeg static build for Windows...")
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = script_dir / "ffmpeg-release-essentials.zip"
    
    try:
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(script_dir)
        
        extracted_folders = [f for f in script_dir.iterdir() 
                           if f.is_dir() and f.name.startswith("ffmpeg-") and "essentials" in f.name]
        
        if extracted_folders:
            extracted_folders[0].rename(ffmpeg_dir)
            zip_path.unlink()
            return str(ffmpeg_dir / "bin")
        return None
    except Exception as e:
        print(f"ERROR downloading FFmpeg: {e}")
        if zip_path.exists(): zip_path.unlink()
        return None

def download_youtube_video(url, output_path=None, audio_format=None, ffmpeg_path=None, 
                         auto_download_ffmpeg=True, delay=None, max_delay=None, 
                         download_archive=None, best_native=False, output_template=None, 
                         ignore_errors=False, list_formats=False):
    
    # 1. Handle List Formats
    if list_formats:
        ydl_opts = {'listformats': True, 'quiet': False}
        with YoutubeDL(cast(Any, ydl_opts)) as ydl:
            ydl.download([url])
        return True

    # 2. Check FFmpeg Requirement (Required for WAV *and* MP3)
    needs_conversion = audio_format in ('wav', 'mp3')
    
    if needs_conversion:
        if not check_ffmpeg(ffmpeg_path):
            local_ffmpeg = get_local_ffmpeg_path()
            if local_ffmpeg:
                ffmpeg_path = local_ffmpeg
            elif auto_download_ffmpeg:
                print("\nFFmpeg is required for conversion. Downloading...")
                downloaded_path = download_ffmpeg()
                if downloaded_path:
                    ffmpeg_path = downloaded_path
                else:
                    return False
            else:
                print("ERROR: FFmpeg is required for WAV/MP3 conversion.")
                return False

    if not output_path:
        output_path = os.getcwd()
    os.makedirs(output_path, exist_ok=True)

    # 3. Configure yt-dlp Options
    # Determine Output Template
    if output_template:
        outtmpl = os.path.join(output_path, output_template)
    else:
        outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')

    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': False,
        'progress': True,
        'ignoreerrors': ignore_errors,
        'no_warnings': ignore_errors,
        'extractor_args': {
            'youtube': {'player_client': ['android', 'web']},
        },
    }

    # Add advanced options
    if delay is not None: ydl_opts['sleep_interval'] = delay
    if max_delay is not None: ydl_opts['max_sleep_interval'] = max_delay
    if download_archive: ydl_opts['download_archive'] = download_archive
    if ffmpeg_path: ydl_opts['ffmpeg_location'] = ffmpeg_path

    # Configure Format / Post-processing
    if best_native:
        # Download best audio without transcoding (usually opus/webm or m4a)
        ydl_opts['format'] = 'bestaudio/best'
    elif audio_format == 'wav':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }]
    elif audio_format == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    else:
        # Video download
        ydl_opts['format'] = 'bestvideo[height=1080][fps=60]+bestaudio/best[height=1080][fps=60]/best'

    # 4. Execute Download with Retry Logic
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with YoutubeDL(cast(Any, ydl_opts)) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Apply Metadata Tags if using MP3/WAV
                if needs_conversion and not ignore_errors:
                    # If it's a playlist, 'entries' will be present, and tags are handled per-file internally by yt-dlp or skipped here.
                    # We focus on single video tagging for now to avoid complexity with playlist iterators.
                    if 'entries' not in info:
                         # Calculate final filename to tag it
                        ext = audio_format
                        filename = ydl.prepare_filename(info)
                        base, _ = os.path.splitext(filename)
                        final_filename = f"{base}.{ext}"
                        
                        if os.path.exists(final_filename):
                            tag_audio_metadata(final_filename, info, audio_format)
                
                return True

        except Exception as e:
            if attempt < max_retries:
                print(f"\n[Retry {attempt}/{max_retries}] Error: {e}")
                time.sleep(attempt * 2)
            else:
                print(f"\n[Error] Failed to download {url}: {e}")
                return False
    return False

def convert_local_file_to_wav(input_file, output_path=None, ffmpeg_path=None):
    """Convert local file to WAV."""
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found.")
        return False
        
    # FFmpeg resolution logic
    ffmpeg_cmd = "ffmpeg"
    if ffmpeg_path and os.path.exists(os.path.join(ffmpeg_path, 'ffmpeg.exe')):
        ffmpeg_cmd = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    elif check_ffmpeg(): 
        ffmpeg_cmd = "ffmpeg"
    else:
        local = get_local_ffmpeg_path()
        if local: ffmpeg_cmd = os.path.join(local, 'ffmpeg.exe')
    
    if not output_path: output_path = input_path.parent
    else: Path(output_path).mkdir(parents=True, exist_ok=True)
    
    output_file = Path(output_path) / f"{input_path.stem}.wav"
    
    cmd = [ffmpeg_cmd, '-i', str(input_path), '-vn', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2', '-y', str(output_file)]
    try:
        subprocess.run(cmd, check=True)
        print(f"Converted: {output_file}")
        return True
    except Exception as e:
        print(f"Conversion failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='YouTube Audio/Video Downloader')
    
    # URL Argument: Changed to '*' so it is OPTIONAL (allows running --local without a URL)
    parser.add_argument('url', nargs='*', help='YouTube video URL(s)')
    
    # Mode Arguments
    parser.add_argument('--local', metavar='FILE', help='Convert local file to WAV')
    parser.add_argument('--wav', action='store_true', help='Download as WAV')
    parser.add_argument('--mp3', action='store_true', help='Download as MP3 (320kbps)')
    parser.add_argument('--best-native', action='store_true', help='Download best native audio (Opus/M4A)')
    
    # Path Arguments
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--warudo', action='store_true', help='Save to Warudo Sounds folder')
    parser.add_argument('--ffmpeg-path', help='Path to FFmpeg')
    
    # Advanced / Playlist Arguments
    parser.add_argument('--delay', type=int, default=None, help='Min sleep (sec) between downloads')
    parser.add_argument('--max-delay', type=int, default=None, help='Max sleep (sec) between downloads')
    parser.add_argument('--download-archive', type=str, help='File to track downloaded IDs')
    parser.add_argument('--output-template', type=str, help='Custom filename template')
    parser.add_argument('--ignore-errors', action='store_true', help='Ignore errors in playlists')
    parser.add_argument('--list-formats', action='store_true', help='List formats only')

    args = parser.parse_args()

    # Determine Output Path
    output_path = args.output or os.getcwd()
    if args.warudo:
        output_path = r'D:\SteamLibrary\steamapps\common\Warudo\Warudo_Data\StreamingAssets\Sounds'

    # 1. Local File Conversion Mode
    if args.local:
        convert_local_file_to_wav(args.local, output_path, args.ffmpeg_path)
        sys.exit(0)

    # 2. YouTube Download Mode
    if not args.url:
        print("Error: No URL provided. Please provide a URL or use --local.")
        sys.exit(1)

    # Determine Audio Format
    audio_fmt = None
    if args.wav: audio_fmt = 'wav'
    elif args.mp3: audio_fmt = 'mp3'

    # Loop through all provided URLs (Batching)
    for link in args.url:
        print(f"\nProcessing: {link}")
        download_youtube_video(
            link,
            output_path=output_path,
            audio_format=audio_fmt,
            ffmpeg_path=args.ffmpeg_path,
            delay=args.delay,
            max_delay=args.max_delay,
            download_archive=args.download_archive,
            best_native=args.best_native,
            output_template=args.output_template,
            ignore_errors=args.ignore_errors,
            list_formats=args.list_formats
        )

if __name__ == '__main__':
    main()