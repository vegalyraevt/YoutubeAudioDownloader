# YouTube Downloader & Audio-to-MIDI Converter

A collection of tools for downloading YouTube videos/audio and converting audio to MIDI format.

## 📦 Installation

### 1. Install Python Dependencies

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt

# Install basic-pitch for audio-to-MIDI conversion (optional)
pip install basic-pitch
```

### 2. FFmpeg (Required for WAV conversion)

FFmpeg is automatically downloaded when you first run `yt_downloader.py` with `--wav`. Alternatively:

- **Via script auto-download**: Run the script and choose 'y' when prompted
- **Manual download**: https://ffmpeg.org/download.html

---

## 🎵 YouTube Downloader (`yt_downloader.py`)


Download YouTube videos or extract audio as WAV, MP3, or native formats. Now supports advanced features for large-scale, robust, and organized downloads.

### Basic Usage

```powershell
# Activate venv first!
.\.venv\Scripts\Activate.ps1

# Download video at 1080p 60fps
python yt_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Download audio only as WAV
python yt_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --wav

# Save to specific directory
python yt_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --wav -o ./music

# Save to Warudo Sounds directory
python yt_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --wav --warudo
```

### Advanced Options

```powershell
# Specify FFmpeg location (if not in PATH)
python yt_downloader.py "URL" --wav --ffmpeg-path "C:\ffmpeg\bin"
 
# Download audio as MP3 at CD quality
python yt_downloader.py "URL" --mp3

# Download best native audio format (no transcoding, preserves Opus/AAC)
python yt_downloader.py "URL" --best-native

# Add a delay between downloads (for playlists)
python yt_downloader.py "PLAYLIST_URL" --wav --delay 5 --max-delay 15

# Use a download archive to skip already-downloaded videos
python yt_downloader.py "PLAYLIST_URL" --wav --download-archive archive.txt

# Custom output file naming template
python yt_downloader.py "URL" --wav --output-template "%(uploader)s - %(title)s.%(ext)s"

# Ignore errors and continue downloading
python yt_downloader.py "PLAYLIST_URL" --wav --ignore-errors

# List all available formats for a video
python yt_downloader.py "URL" --list-formats
```

### Features

✅ **Auto-retry logic** - Retries up to 3 times on YouTube blocking  
✅ **Auto-FFmpeg download** - First-time download and setup  
✅ **1080p 60fps** - High quality video downloads  
✅ **WAV/MP3/native audio extraction** - Choose your preferred format  
✅ **Robust metadata tagging** - Title, artist, album, and thumbnail embedded in MP3/WAV  
✅ **Download archive** - Skips already-downloaded videos for massive playlists  
✅ **Delay between downloads** - Prevents IP bans on large playlists  
✅ **Custom output templates** - Advanced file naming for organization  
✅ **Native format preservation** - No transcoding with --best-native  
✅ **Error resilience** - Continue on errors, strict cleanup of temp files  
✅ **Interactive format selection** - List all available formats if a download fails

---

## 🎹 Audio-to-MIDI Converter (`audio_to_midi.py`)

Convert any audio file to MIDI using Spotify's **basic-pitch** - a highly accurate, instrument-agnostic transcription model.

### ⚠️ Python Version Requirement

**Note**: `basic-pitch` currently requires **Python 3.11 or 3.12**. It is not yet compatible with Python 3.13.

If you're using Python 3.13, you have two options:
1. **Use Python 3.11 or 3.12** in a separate virtual environment for audio-to-MIDI conversion
2. **Use an alternative tool** like `audio-to-midi` (simpler but less accurate)

To check your Python version:
```powershell
python --version
```

### Basic Usage

```powershell
# Activate venv first!
.\.venv\Scripts\Activate.ps1

# Convert single file
python audio_to_midi.py song.wav

# Convert multiple files at once
python audio_to_midi.py song1.wav song2.mp3 song3.flac

# Save to specific directory
python audio_to_midi.py song.wav -o ./midi_files
```

### Advanced Options

```powershell
# Include audio sonification (hear what the MIDI sounds like)
python audio_to_midi.py song.wav --sonify

# Save additional outputs
python audio_to_midi.py song.wav --save-notes --save-model-outputs

# Adjust sensitivity for better accuracy
python audio_to_midi.py song.wav --onset-threshold 0.6 --frame-threshold 0.4

# Set frequency range (e.g., for bass guitar 40-400 Hz)
python audio_to_midi.py bass.wav --min-freq 40 --max-freq 400
```

### Supported Audio Formats

✅ WAV, MP3, OGG, FLAC, M4A

### Output Files

- `filename_basic_pitch.mid` - MIDI file
- `filename_basic_pitch_sonif.wav` - Audio rendering (if `--sonify`)
- `filename_basic_pitch.csv` - Note events (if `--save-notes`)
- `filename_basic_pitch.npz` - Raw model output (if `--save-model-outputs`)

### Tuning Parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `--onset-threshold` | 0.5 | Higher = fewer notes detected |
| `--frame-threshold` | 0.3 | Higher = shorter note durations |
| `--min-note-length` | 127.70 ms | Minimum note duration |
| `--min-freq` | None | Filter out low frequencies |
| `--max-freq` | None | Filter out high frequencies |

---

## 🔄 Complete Workflow Example

**Download YouTube audio and convert to MIDI:**

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Step 1: Download audio from YouTube
python yt_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --wav

# Step 2: Convert to MIDI
python audio_to_midi.py "Never Gonna Give You Up.wav" --sonify

# Done! You'll have:
# - Never Gonna Give You Up.wav (original audio)
# - Never Gonna Give You Up_basic_pitch.mid (MIDI file)
# - Never Gonna Give You Up_basic_pitch_sonif.wav (MIDI audio render)
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'yt_dlp'"

Activate your virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

### "FFmpeg is required but was not found"

Run with `--wav` flag and choose 'y' when prompted to auto-download FFmpeg.

### "ERROR: Download failed after 3 attempts"

1. Wait a few minutes and try again
2. Update yt-dlp: `pip install --upgrade yt-dlp`
3. Try a different video

### "basic-pitch is not installed"

The script will prompt you to install it automatically, or:
```powershell
pip install basic-pitch
```

---

## 📝 Tips for Best Results

### MIDI Conversion

- **Use clean audio** - Less background noise = better transcription
- **One instrument at a time** - basic-pitch works best on single instruments
- **Adjust thresholds** - Piano might need lower thresholds
- **Set frequency ranges** for specific instruments:
  - Bass: `--min-freq 40 --max-freq 400`
  - Vocals: `--min-freq 80 --max-freq 1000`

### YouTube Downloads

- **Always wrap URLs in quotes** to handle special characters
- **Use --wav for music** to get highest quality audio
- **Check virtual environment** - look for `(.venv)` in your prompt

---

## 📚 Resources

- **basic-pitch**: https://github.com/spotify/basic-pitch
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **FFmpeg**: https://ffmpeg.org/


- Downloads YouTube videos at 1080p 60fps quality (if available)
- Falls back to best available quality if the requested quality is not available
- Option to extract audio and convert to WAV format
- Quick shortcut to save files to Warudo's Sounds directory
