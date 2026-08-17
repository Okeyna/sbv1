import os
import wave
import struct
from typing import Tuple, Optional
from .config import settings


def generate_audio_from_text(text: str, output_path: str, voice_type: str = "alloy") -> Tuple[str, float]:
    """
    Generate audio from text using TTS.
    
    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file
        voice_type: Voice type to use (for OpenAI TTS)
        
    Returns:
        Tuple of (audio_path, duration_seconds)
    """
    # Check if OpenAI TTS is configured
    if settings.tts_provider == "openai" and settings.openai_api_key:
        try:
            return _generate_openai_tts(text, output_path, voice_type)
        except Exception as e:
            print(f"OpenAI TTS failed: {e}, generating placeholder audio")
    
    # Generate placeholder silent audio
    return _generate_placeholder_audio(text, output_path)


def _generate_openai_tts(text: str, output_path: str, voice_type: str) -> Tuple[str, float]:
    """Generate audio using OpenAI TTS API."""
    from openai import OpenAI
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Truncate text if too long (OpenAI has limits)
    max_chars = 4096
    if len(text) > max_chars:
        text = text[:max_chars]
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice_type,
        input=text
    )
    
    # Save the audio file
    response.stream_to_file(output_path)
    
    # Estimate duration (rough estimate: ~150 words per minute)
    word_count = len(text.split())
    duration = (word_count / 150) * 60  # seconds
    
    return output_path, duration


def _generate_placeholder_audio(text: str, output_path: str) -> Tuple[str, float]:
    """
    Generate a silent WAV file as a placeholder.
    
    This creates a valid WAV file with silence, useful for testing
    when TTS credentials are not available.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Calculate duration based on text length
    # Rough estimate: 150 words per minute, 2 bytes per sample, 44.1kHz
    word_count = len(text.split())
    duration_seconds = max(5.0, (word_count / 150) * 60)  # At least 5 seconds
    
    # Audio parameters
    sample_rate = 44100  # Hz
    duration = duration_seconds  # seconds
    num_samples = int(sample_rate * duration)
    
    # Create silent audio data (all zeros)
    # Mono channel, 16-bit samples
    audio_data = struct.pack('<' + 'h' * num_samples, *[0] * num_samples)
    
    # Write WAV file
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16 bits)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    
    return output_path, duration_seconds


def estimate_duration(text: str) -> float:
    """
    Estimate audio duration from text.
    
    Args:
        text: The text content
        
    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    # Average speaking rate: ~150 words per minute
    return (word_count / 150) * 60


def get_audio_info(audio_path: str) -> Optional[dict]:
    """
    Get information about an audio file.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary with audio info or None if file doesn't exist
    """
    if not os.path.exists(audio_path):
        return None
    
    try:
        with wave.open(audio_path, 'r') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            
            return {
                "duration": duration,
                "channels": wav_file.getnchannels(),
                "sample_rate": rate,
                "frames": frames
            }
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return None
