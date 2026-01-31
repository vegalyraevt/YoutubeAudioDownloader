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
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.wave import WAVE
import requests

def tag_audio_metadata(filepath, info, audio_format):
    """Tag MP3 or WAV file with metadata from info dict."""
    title = info.get('title')
    artist = info.get('artist') or info.get('uploader')
    album = info.get('album') or info.get('playlist_title')
    thumbnail_url = info.get('thumbnail')
    try:
        if audio_format == 'mp3':
            audio = EasyID3(filepath)
            if title:
                audio['title'] = title
            if artist:
                audio['artist'] = artist
            if album:
                audio['album'] = album
            audio.save()
            # Add album art
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
            if title:
                audio['TIT2'] = title
            if artist:
                audio['TPE1'] = artist
            if album:
                audio['TALB'] = album
            audio.save()
    except Exception as e:
        print(f"[WARN] Could not tag {filepath}: {e}")
from yt_dlp import YoutubeDL

def check_ffmpeg(ffmpeg_path=None):
    """Check if FFmpeg is available on the system or at a provided path.

    Args:
        ffmpeg_path: Optional path to an ffmpeg executable or directory containing it.
    Returns:
        bool: True if ffmpeg is found, False otherwise.
    """
    # If user provided a specific path, validate it first
    if ffmpeg_path:
        # If it's a file path to an executable
        if os.path.isfile(ffmpeg_path):
            return os.access(ffmpeg_path, os.X_OK) or ffmpeg_path.lower().endswith('.exe')

        # If it's a directory, check for ffmpeg.exe inside (Windows)
        if os.path.isdir(ffmpeg_path):
            ffmpeg_exe = os.path.join(ffmpeg_path, 'ffmpeg.exe')
            if os.path.isfile(ffmpeg_exe):
                return os.access(ffmpeg_exe, os.X_OK) or ffmpeg_exe.lower().endswith('.exe')

        # Try to resolve via shutil.which if the provided value might be executable name
        try:
            return shutil.which(ffmpeg_path) is not None
        except Exception:
            return False

    # Fall back to searching PATH
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
    """Download and extract FFmpeg static build for Windows.
    
    Returns:
        str: Path to the extracted ffmpeg bin directory, or None if failed.
    """
    script_dir = Path(__file__).parent
    ffmpeg_dir = script_dir / "ffmpeg"
    ffmpeg_exe = ffmpeg_dir / "bin" / "ffmpeg.exe"
    
    # Check if already downloaded
    if ffmpeg_exe.exists():
        print(f"FFmpeg already exists at: {ffmpeg_dir / 'bin'}")
        return str(ffmpeg_dir / "bin")
    
    print("\nFFmpeg not found. Downloading FFmpeg static build for Windows...")
    print("This is a one-time download (~100-150 MB).")
    
    # Using gyan.dev essentials build (smaller, commonly used)
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = script_dir / "ffmpeg-release-essentials.zip"
    
    try:
        # Download with progress
        print(f"Downloading from: {ffmpeg_url}")
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        print("Download complete. Extracting...")
        
        # Extract the zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # The zip contains a folder like ffmpeg-X.X.X-essentials_build/
            # We need to extract and rename it
            zip_ref.extractall(script_dir)
        
        # Find the extracted folder (it has a version number in the name)
        extracted_folders = [f for f in script_dir.iterdir() 
                           if f.is_dir() and f.name.startswith("ffmpeg-") and "essentials" in f.name]
        
        if extracted_folders:
            # Rename to just "ffmpeg"
            extracted_folders[0].rename(ffmpeg_dir)
            print(f"FFmpeg installed successfully to: {ffmpeg_dir / 'bin'}")
            
            # Clean up zip file
            zip_path.unlink()
            
            return str(ffmpeg_dir / "bin")
        else:
            print("ERROR: Could not find extracted FFmpeg folder.")
            return None
            
    except Exception as e:
        print(f"ERROR downloading FFmpeg: {e}")
        # Clean up partial downloads
        if zip_path.exists():
            zip_path.unlink()
        return None

def download_youtube_video(url, output_path=None, audio_format=None, ffmpeg_path=None, auto_download_ffmpeg=True, delay=None, max_delay=None, download_archive=None, best_native=False, output_template=None):
        # Check download archive for already-downloaded IDs
        downloaded_ids = set()
        if download_archive and os.path.exists(download_archive):
            with open(download_archive, 'r', encoding='utf-8') as f:
                for line in f:
                    downloaded_ids.add(line.strip())
    """
    Download a YouTube video at 1080p 60fps or as WAV audio.
    
    Args:
        url: YouTube video URL
        output_path: Optional path to save the video (default: current directory)
        wav_only: If True, download audio only and convert to WAV
        ffmpeg_path: Optional path to ffmpeg executable or directory
        auto_download_ffmpeg: If True, automatically download ffmpeg if not found
    
    if audio_format in ('wav', 'mp3'):
        bool: True if download was successful, False otherwise
    """
    # Check for FFmpeg if WAV conversion is requested
    if wav_only:
        # First check if ffmpeg is available
        if not check_ffmpeg(ffmpeg_path):
            # Try to find locally downloaded ffmpeg
            local_ffmpeg = get_local_ffmpeg_path()
            if local_ffmpeg:
                print(f"Using locally installed FFmpeg from: {local_ffmpeg}")
                ffmpeg_path = local_ffmpeg
            elif auto_download_ffmpeg:
                # Offer to download ffmpeg automatically
                response = input("\nFFmpeg is required but not found. Download it automatically? (y/n): ").strip().lower()
                if response == 'y':
                    downloaded_path = download_ffmpeg()
                    if downloaded_path:
                        ffmpeg_path = downloaded_path
                    else:
                        print("Failed to download FFmpeg. Please install manually.")
                        return False
                else:
                    print("\nTo use --wav, you need FFmpeg. Install options:")
                    print("1. Run this script again and choose 'y' to auto-download")
                    print("2. Download from: https://ffmpeg.org/download.html")
                    print("3. Use --ffmpeg-path to specify location")
                    return False
            else:
                print("ERROR: FFmpeg is required for WAV conversion but was not found.")
                print("Note: 'pip install ffmpeg-python' only installs a Python wrapper — it does NOT provide the ffmpeg binary.")
                print("Please install the FFmpeg binary (one of):")
                print("1. Run this script again without --no-auto-download to auto-download")
                print("2. Download from: https://ffmpeg.org/download.html")
                print("3. Use --ffmpeg-path to specify location")
                return False
    
    # Set the output path to current directory if not specified
    if not output_path:
        output_path = os.getcwd()
    
    # Make sure the output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Set YoutubeDL options
    # Set output template if provided
    if output_template:
        outtmpl = os.path.join(output_path, output_template)
    else:
        outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': False,
        'progress': True,
        # Use alternative clients to bypass YouTube's SSAP experiment issues
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
    }

    # Add sleep interval options if provided
    if delay is not None:
        ydl_opts['sleep_interval'] = delay
    if max_delay is not None:
        ydl_opts['max_sleep_interval'] = max_delay
def download_youtube_video(url, output_path=None, audio_format=None, ffmpeg_path=None, auto_download_ffmpeg=True, delay=None, max_delay=None, download_archive=None, best_native=False, output_template=None, ignore_errors=False, list_formats=False):
    if list_formats:
        # List all available formats for the video and exit
        from yt_dlp import YoutubeDL
        ydl_opts = {'listformats': True, 'quiet': False}
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True

    if best_native:
        # Download best native audio (Opus/webm or AAC/m4a, no transcoding)
        ydl_opts['format'] = 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio'
    elif audio_format == 'wav':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        })
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
    elif audio_format == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        })
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
    else:
        ydl_opts['format'] = 'bestvideo[height=1080][fps=60]+bestaudio/best[height=1080][fps=60]/best'
    
    # Retry logic for YouTube's SSAP and signature extraction issues
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        # Check if this video is already downloaded (by ID)
        # Only works for single video, not playlist at this call level
        if download_archive:
            # Try to extract video ID from URL
            import re
            id_match = re.search(r'(?:v=|be/|embed/|shorts/|list=)?([\w-]{11})', url)
            video_id = None
            if id_match:
                video_id = id_match.group(1)
            # If video_id is in archive, skip
            if video_id and video_id in downloaded_ids:
                print(f"[SKIP] Video ID {video_id} already in archive {download_archive}")
                return True
        try:
            with YoutubeDL(cast(Any, ydl_opts)) as ydl:
                info = ydl.extract_info(url, download=True)
                print(f"\nDownload successful! File saved to: {output_path}")
                # Tag MP3/WAV with metadata if applicable
                if audio_format in ("mp3", "wav"):
                    # Find the output file path
                    outtmpl = ydl_opts['outtmpl']
                    ext = audio_format
                    if 'ext' in info:
                        ext = info['ext']
                    filename = outtmpl % info if '%' in outtmpl else outtmpl
                    if not filename.endswith(f'.{ext}'):
                        filename = os.path.splitext(filename)[0] + f'.{ext}'
                    if os.path.exists(filename):
                        tag_audio_metadata(filename, info, audio_format)
                # Log video ID to archive if requested
                if download_archive and 'id' in info:
                    with open(download_archive, 'a', encoding='utf-8') as f:
                        f.write(info['id'] + '\n')
            return True
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a YouTube SSAP/signature/fragment issue
            is_youtube_blocking = any(phrase in error_msg.lower() for phrase in [
                'ssap', 'signature extraction', 'nsig extraction', 
                'fragment not found', 'downloaded file is empty',
                'formats have been skipped', 'missing a url'
            ])
            
            if is_youtube_blocking and attempt < max_retries:
                wait_time = attempt * 2  # Exponential backoff: 2s, 4s
                print(f"\nAttempt {attempt}/{max_retries} failed due to YouTube restrictions.")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            elif is_youtube_blocking and attempt == max_retries:
                print(f"\n{'='*60}")
                print(f"ERROR: Download failed after {max_retries} attempts.")
                print(f"{'='*60}")
                print("\nYouTube is currently blocking downloads with SSAP (Server-Side Ads) experiment.")
                print("\nPossible solutions:")
                print("1. Try again in a few minutes (YouTube's blocking can be temporary)")
                print("2. Update yt-dlp: pip install --upgrade yt-dlp")
                print("3. Try a different video")
                print("4. Use a VPN to change your IP address")
                print(f"\nOriginal error: {e}")
                return False
            else:
                # Different error, report it
                print(f"Error downloading video: {e}")
                
                if "ffmpeg" in error_msg.lower():
                    print("\nFFmpeg is required for audio conversion. Please install FFmpeg:")
                    print("1. Run this script again and choose 'y' to auto-download")
                    print("2. Download from: https://ffmpeg.org/download.html")
                    print("3. Use --ffmpeg-path to specify location")
                else:
                    print("Tip: If your URL contains an '&' character, wrap the URL in quotes, e.g.:")
                    print('  python yt_downloader.py "https://www.youtube.com/watch?v=xxxx&t=123s"')
                return False
    
    return False

def convert_local_file_to_wav(input_file, output_path=None, ffmpeg_path=None, auto_download_ffmpeg=True):
    """
    Convert a local video/audio file to WAV format without quality loss.
    
    Args:
        input_file: Path to local video or audio file
        output_path: Optional directory to save the WAV file (default: same as input)
        ffmpeg_path: Optional path to ffmpeg executable or directory
        auto_download_ffmpeg: If True, automatically download ffmpeg if not found
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    input_path = Path(input_file)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return False
    
    if not input_path.is_file():
        print(f"ERROR: Not a file: {input_file}")
        return False
    
    # Check for FFmpeg
    ffmpeg_cmd = None
    if ffmpeg_path:
        # User provided a specific path
        if os.path.isfile(ffmpeg_path):
            ffmpeg_cmd = ffmpeg_path
        elif os.path.isdir(ffmpeg_path):
            ffmpeg_exe = os.path.join(ffmpeg_path, 'ffmpeg.exe')
            if os.path.isfile(ffmpeg_exe):
                ffmpeg_cmd = ffmpeg_exe
    
    if not ffmpeg_cmd:
        # Try to find ffmpeg in PATH
        ffmpeg_cmd = shutil.which("ffmpeg")
    
    if not ffmpeg_cmd:
        # Try to find locally downloaded ffmpeg
        local_ffmpeg = get_local_ffmpeg_path()
        if local_ffmpeg:
            print(f"Using locally installed FFmpeg from: {local_ffmpeg}")
            ffmpeg_cmd = os.path.join(local_ffmpeg, 'ffmpeg.exe')
        elif auto_download_ffmpeg:
            # Offer to download ffmpeg automatically
            response = input("\nFFmpeg is required but not found. Download it automatically? (y/n): ").strip().lower()
            if response == 'y':
                downloaded_path = download_ffmpeg()
                if downloaded_path:
                    ffmpeg_cmd = os.path.join(downloaded_path, 'ffmpeg.exe')
                else:
                    print("Failed to download FFmpeg. Please install manually.")
                    return False
            else:
                print("\nTo convert files, you need FFmpeg. Install options:")
                print("1. Run this script again and choose 'y' to auto-download")
                print("2. Download from: https://ffmpeg.org/download.html")
                print("3. Use --ffmpeg-path to specify location")
                return False
        else:
            print("ERROR: FFmpeg is required but was not found.")
            print("Please install FFmpeg or use --ffmpeg-path to specify location.")
            return False
    
    # Set output directory
    if output_path:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_path.parent
    
    # Generate output filename
    output_file = output_dir / f"{input_path.stem}.wav"
    
    # Check if output already exists
    if output_file.exists():
        response = input(f"\nOutput file already exists: {output_file}\nOverwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Conversion cancelled.")
            return False
    
    print(f"\n{'='*60}")
    print(f"Converting: {input_path.name}")
    print(f"Output to:  {output_file}")
    print(f"{'='*60}\n")
    
    # FFmpeg command for lossless WAV conversion
    # Using PCM signed 16-bit little-endian (s16le) which is the standard WAV format
    # -ar 48000 sets sample rate to 48kHz (you can use 44100 for CD quality)
    # -ac 2 ensures stereo output
    cmd = [
        ffmpeg_cmd,
        '-i', str(input_path),      # Input file
        '-vn',                       # No video
        '-acodec', 'pcm_s16le',     # PCM 16-bit (lossless)
        '-ar', '48000',              # 48kHz sample rate
        '-ac', '2',                  # Stereo
        '-y',                        # Overwrite output file
        str(output_file)
    ]
    
    try:
        # Run FFmpeg conversion
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ Conversion successful!")
        print(f"📝 WAV file: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Conversion failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
                            if args.list_formats:
                                # Only list formats and exit
                                download_youtube_video(
                                    args.url,
                                    output_path,
                                    audio_format=None,
                                    ffmpeg_path=args.ffmpeg_path,
                                    delay=None,
                                    max_delay=None,
                                    download_archive=None,
                                    best_native=False,
                                    output_template=args.output_template,
                                    ignore_errors=False,
                                    list_formats=True
                                )
                                sys.exit(0)
                        parser.add_argument('--list-formats', action='store_true', help='List all available formats for a video and exit')
                    parser.add_argument('--ignore-errors', action='store_true', help='Continue downloading even if some videos fail (for playlists)')
                parser.add_argument('--output-template', type=str, default=None, help='Custom output file naming template (e.g., "%(uploader)s - %(title)s.%(ext)s")')
            parser.add_argument('--best-native', action='store_true', help='Download the best native audio format (Opus/AAC) without transcoding')
        parser.add_argument('--download-archive', type=str, default=None, help='Path to a file to log downloaded video IDs and skip already-downloaded videos')
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description='Download YouTube videos at 1080p 60fps or convert local files to WAV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download YouTube video
  python yt_downloader.py "https://www.youtube.com/watch?v=xxxx"
  
  # Download as WAV audio
  python yt_downloader.py "https://www.youtube.com/watch?v=xxxx" --wav
  
  # Convert local file to WAV
  python yt_downloader.py --local "video.mp4"
  
  # Convert local file with custom output directory
  python yt_downloader.py --local "video.mp4" -o ./output
        """
    )
    parser.add_argument('url', nargs='?', help='YouTube video URL (not needed with --local)')
    parser.add_argument('--local', metavar='FILE', help='Convert local video/audio file to WAV')
    parser.add_argument('-o', '--output', help='Output directory (default: current directory for YouTube, same directory as input for local files)')
    parser.add_argument('--wav', action='store_true', help='Download audio only in WAV format (YouTube only)')
    parser.add_argument('--mp3', action='store_true', help='Download audio only in MP3 format at 320kbps (YouTube only)')
    parser.add_argument('--delay', type=int, default=None, help='Minimum seconds to sleep between downloads (for playlists)')
    parser.add_argument('--max-delay', type=int, default=None, help='Maximum seconds to sleep between downloads (for playlists)')
    parser.add_argument('--ffmpeg-path', help='Path to ffmpeg executable or directory containing ffmpeg.exe')
    parser.add_argument('--warudo', action='store_true', help='Save to Warudo Sounds directory')
    args = parser.parse_args()
    
    # Handle local file conversion
    if args.local:
        # Set output path based on arguments
        output_path = args.output
        if args.warudo:
            output_path = r'D:\SteamLibrary\steamapps\common\Warudo\Warudo_Data\StreamingAssets\Sounds'
        
        success = convert_local_file_to_wav(args.local, output_path, args.ffmpeg_path)
        sys.exit(0 if success else 1)
    
    # Handle YouTube download
    if not args.url:
        parser.error('YouTube URL is required (or use --local for local file conversion)')
    
    # Set output path based on arguments
    output_path = args.output
    if args.warudo:
        output_path = r'D:\SteamLibrary\steamapps\common\Warudo\Warudo_Data\StreamingAssets\Sounds'
    
    # Download the video
    # Determine audio format
    audio_format = None
    if args.wav:
        audio_format = 'wav'
    elif args.mp3:
        audio_format = 'mp3'

    # Pass delay options
    success = download_youtube_video(
        args.url,
        output_path,
        audio_format=audio_format,
        ffmpeg_path=args.ffmpeg_path,
        delay=args.delay,
        max_delay=args.max_delay,
        download_archive=args.download_archive,
        best_native=args.best_native,
        output_template=args.output_template,
        ignore_errors=args.ignore_errors
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
