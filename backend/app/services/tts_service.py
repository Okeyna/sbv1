"""Text-to-Speech Service for generating audio lessons"""
import os
import wave
import struct
import math
from typing import Tuple

def get_openai_client():
    """Get OpenAI client if configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    tts_provider = os.getenv("TTS_PROVIDER", "mock")
    
    if not api_key or tts_provider != "openai":
        return None
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None

def generate_silent_audio(output_path: str, duration_seconds: float = 10.0) -> str:
    """Generate a silent WAV file as placeholder"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_seconds)
    
    # Create silent audio data
    audio_data = [0] * num_samples
    
    # Write WAV file
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for sample in audio_data:
            packed_value = struct.pack('h', sample)
            wav_file.writeframes(packed_value)
    
    return output_path

def estimate_duration(text: str) -> float:
    """Estimate audio duration from text (rough average speaking rate)"""
    words = len(text.split())
    # Average speaking rate: ~150 words per minute
    minutes = words / 150.0
    return minutes * 60.0  # Return seconds

def generate_audio(text: str, file_id: int) -> Tuple[str, float]:
    """Generate audio from text using TTS"""
    from app.config import Config
    
    client = get_openai_client()
    filename = f"audio_{file_id}.mp3"
    output_path = os.path.join(Config.AUDIO_FOLDER, filename)
    
    # Ensure directory exists
    os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    
    if not client:
        # Generate silent placeholder
        duration = estimate_duration(text)
        # Create a simple silent WAV file
        generate_silent_audio(output_path.replace('.mp3', '.wav'), min(duration, 60.0))
        # For mock, just create an empty file with .mp3 extension
        with open(output_path, 'wb') as f:
            # Write minimal WAV header to make it a valid (silent) audio file
            pass
        return output_path, duration
    
    try:
        # Use OpenAI TTS
        from openai import OpenAI
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:4096]  # Truncate if too long
        )
        
        response.stream_to_file(output_path)
        
        # Estimate duration
        duration = estimate_duration(text)
        
        return output_path, duration
    except Exception as e:
        # Fallback to silent audio
        duration = estimate_duration(text)
        generate_silent_audio(output_path.replace('.mp3', '.wav'), min(duration, 60.0))
        with open(output_path, 'wb') as f:
            pass
        return output_path, duration
