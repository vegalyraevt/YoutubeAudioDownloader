#!/usr/bin/env python
"""
Audio to MIDI Converter
Uses Spotify's basic-pitch for accurate audio-to-MIDI conversion.
Supports WAV, MP3, OGG, FLAC, M4A formats.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Basic Pitch's saved TensorFlow model expects legacy Keras APIs (Optimizer.add_slot, etc.).
# TensorFlow 2.20 bundles Keras 3 by default, which removes those APIs and breaks model loading.
# Enabling the legacy tf-keras shim restores the older behavior and keeps the model compatible.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

def check_basic_pitch():
    """Check if basic-pitch can actually be used (not just installed)."""
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
        return True
    except Exception:
        return False

def install_basic_pitch():
    """Prompt user to install basic-pitch."""
    print("\n" + "="*60)
    print("basic-pitch is not installed.")
    print("="*60)
    print("\nbasic-pitch is Spotify's audio-to-MIDI converter.")
    print("It's highly accurate and works with any instrument!")
    print("\nInstall it with:")
    print("  pip install basic-pitch")
    print("\nOr install with TensorFlow support:")
    print("  pip install 'basic-pitch[tf]'")
    print("="*60)
    
    response = input("\nInstall basic-pitch now? (y/n): ").strip().lower()
    if response == 'y':
        import subprocess
        try:
            print("\nInstalling basic-pitch...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "basic-pitch"])
            print("\n✅ basic-pitch installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {e}")
            return False
    return False

def convert_audio_to_midi(
    audio_path: str | Path,
    output_dir: str | Path | None = None,
    save_sonification: bool = False,
    save_model_outputs: bool = False,
    save_note_events: bool = False,
    onset_threshold: float = 0.5,
    frame_threshold: float = 0.3,
    minimum_note_length: float = 127.70,
    minimum_frequency: Optional[float] = None,
    maximum_frequency: Optional[float] = None
) -> bool:
    """
    Convert audio file to MIDI using basic-pitch.
    
    Args:
        audio_path: Path to audio file (WAV, MP3, OGG, FLAC, M4A)
        output_dir: Directory to save outputs (default: same as input)
        save_sonification: Save WAV rendering of MIDI
        save_model_outputs: Save raw model output as NPZ
        save_note_events: Save note events as CSV
        onset_threshold: Threshold for note onsets (0.0-1.0, default 0.5)
        frame_threshold: Threshold for note frames (0.0-1.0, default 0.3)
        minimum_note_length: Minimum note length in milliseconds (default 127.70)
        minimum_frequency: Minimum frequency in Hz (optional)
        maximum_frequency: Maximum frequency in Hz (optional)
    
    Returns:
        bool: True if conversion successful
    """
    try:
        from basic_pitch.inference import predict_and_save
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except ImportError:
        print("ERROR: basic-pitch is not installed.")
        return False
    
    # Validate input file
    audio_path = Path(audio_path)
    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        return False
    
    if not audio_path.is_file():
        print(f"ERROR: Not a file: {audio_path}")
        return False
    
    # Set output directory
    if output_dir is None:
        output_dir_path = audio_path.parent
    else:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Converting: {audio_path.name}")
    print(f"Output to:  {output_dir_path}")
    print(f"{'='*60}\n")
    
    try:
        predict_and_save(
            audio_path_list=[str(audio_path)],
            output_directory=str(output_dir_path),
            save_midi=True,
            sonify_midi=save_sonification,
            save_model_outputs=save_model_outputs,
            save_notes=save_note_events,
            model_or_model_path=ICASSP_2022_MODEL_PATH,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_note_length=minimum_note_length,
            minimum_frequency=minimum_frequency,
            maximum_frequency=maximum_frequency,
        )

        midi_output = output_dir_path / f"{audio_path.stem}_basic_pitch.mid"
        print(f"\n✅ Conversion successful!")
        print(f"📝 MIDI file: {midi_output}")
        
        if save_sonification:
            print(f"🔊 Audio render: {output_dir_path / f'{audio_path.stem}_basic_pitch_sonif.wav'}")
        if save_note_events:
            print(f"📊 Note events: {output_dir_path / f'{audio_path.stem}_basic_pitch.csv'}")
        if save_model_outputs:
            print(f"💾 Model output: {output_dir_path / f'{audio_path.stem}_basic_pitch.npz'}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        return False

def batch_convert(
    input_paths: list,
    output_dir: str | Path | None = None,
    **kwargs
) -> tuple:
    """
    Convert multiple audio files to MIDI.
    
    Returns:
        tuple: (successful_count, failed_count)
    """
    successful = 0
    failed = 0
    
    for audio_path in input_paths:
        if convert_audio_to_midi(audio_path, output_dir, **kwargs):
            successful += 1
        else:
            failed += 1
        print()  # Blank line between files
    
    return successful, failed

def main():
    parser = argparse.ArgumentParser(
        description='Convert audio files to MIDI using Spotify\'s basic-pitch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python audio_to_midi.py song.wav

  # Convert multiple files
  python audio_to_midi.py song1.wav song2.mp3 song3.flac

  # Convert and save to specific directory
  python audio_to_midi.py song.wav -o ./midi_output

  # Convert with audio sonification
  python audio_to_midi.py song.wav --sonify

  # Adjust thresholds for better accuracy
  python audio_to_midi.py song.wav --onset-threshold 0.6 --frame-threshold 0.4

Supported formats: WAV, MP3, OGG, FLAC, M4A
        """
    )
    
    parser.add_argument(
        'audio_files',
        nargs='+',
        help='Audio file(s) to convert to MIDI'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: same as input file)'
    )
    
    parser.add_argument(
        '--sonify',
        action='store_true',
        help='Save WAV audio rendering of the MIDI file'
    )
    
    parser.add_argument(
        '--save-model-outputs',
        action='store_true',
        help='Save raw model outputs as NPZ file'
    )
    
    parser.add_argument(
        '--save-notes',
        action='store_true',
        help='Save note events as CSV file'
    )
    
    parser.add_argument(
        '--onset-threshold',
        type=float,
        default=0.5,
        help='Onset threshold (0.0-1.0, default: 0.5). Higher = fewer notes'
    )
    
    parser.add_argument(
        '--frame-threshold',
        type=float,
        default=0.3,
        help='Frame threshold (0.0-1.0, default: 0.3). Higher = shorter notes'
    )
    
    parser.add_argument(
        '--min-note-length',
        type=float,
        default=127.70,
        help='Minimum note length in milliseconds (default: 127.70)'
    )
    
    parser.add_argument(
        '--min-freq',
        type=float,
        help='Minimum frequency in Hz (optional)'
    )
    
    parser.add_argument(
        '--max-freq',
        type=float,
        help='Maximum frequency in Hz (optional)'
    )
    
    args = parser.parse_args()
    
    # Check if basic-pitch is installed
    if not check_basic_pitch():
        if not install_basic_pitch():
            print("\nPlease install basic-pitch manually and try again.")
            sys.exit(1)
        # After installation, check again
        if not check_basic_pitch():
            print("\nInstallation completed but basic-pitch still cannot be imported.")
            print("This may be a compatibility issue. Please try:")
            print("  pip install --no-deps basic-pitch librosa mir-eval pretty-midi resampy scikit-learn scipy")
            sys.exit(1)
    
    print("\n✨ Audio to MIDI Converter (powered by Spotify's basic-pitch) ✨\n")
    
    # Convert files
    successful, failed = batch_convert(
        args.audio_files,
        args.output,
        save_sonification=args.sonify,
        save_model_outputs=args.save_model_outputs,
        save_note_events=args.save_notes,
        onset_threshold=args.onset_threshold,
        frame_threshold=args.frame_threshold,
        minimum_note_length=args.min_note_length,
        minimum_frequency=args.min_freq,
        maximum_frequency=args.max_freq
    )
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Conversion Summary:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed:     {failed}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
