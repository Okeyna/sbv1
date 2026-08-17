"""Text-to-Speech service for generating audio lessons"""
import os
import wave
import struct
import math
from app.config import Config

# Try to import OpenAI, but don't fail if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _get_client():
    """Get OpenAI client if configured"""
    if Config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        return OpenAI(api_key=Config.OPENAI_API_KEY)
    return None


def generate_audio(text_content: str, file_id: int) -> tuple:
    """
    Generate audio from text content.
    
    Args:
        text_content: The text to convert to speech
        file_id: ID of the source file (for naming)
        
    Returns:
        Tuple of (audio_path, duration_seconds)
    """
    client = _get_client()
    
    # Ensure audio directory exists
    os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    
    # Generate filename
    audio_filename = f"audio_{file_id}.wav"
    audio_path = os.path.join(Config.AUDIO_FOLDER, audio_filename)
    
    if client and Config.OPENAI_API_KEY and Config.TTS_PROVIDER == 'openai':
        try:
            # Use OpenAI TTS
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text_content[:4096]  # OpenAI TTS has character limits
            )
            
            # Save audio file
            response.stream_to_file(audio_path)
            
            # Estimate duration (rough estimate: 150 words per minute)
            word_count = len(text_content.split())
            duration = (word_count / 150) * 60  # seconds
            
            return audio_path, duration
            
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
            # Fall through to mock generation
    
    # Generate silent WAV placeholder
    return _generate_silent_audio(audio_path, text_content)


def _generate_silent_audio(audio_path: str, text_content: str) -> tuple:
    """
    Generate a silent WAV file as placeholder.
    
    Args:
        audio_path: Path to save the WAV file
        text_content: Original text (used to estimate duration)
        
    Returns:
        Tuple of (audio_path, duration_seconds)
    """
    # Estimate duration based on text length
    # Average speaking rate: ~150 words per minute
    word_count = len(text_content.split())
    duration_seconds = max(10, (word_count / 150) * 60)  # At least 10 seconds
    
    # Audio parameters
    sample_rate = 44100  # CD quality
    duration = min(duration_seconds, 30)  # Cap at 30 seconds for placeholder
    num_samples = int(sample_rate * duration)
    
    # Generate silent audio (all zeros)
    frames = b''
    for _ in range(num_samples):
        # Silent sample (value 0)
        frame = struct.pack('<h', 0)  # 16-bit signed integer
        frames += frame
    
    # Write WAV file
    with wave.open(audio_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)
    
    return audio_path, duration


def estimate_duration(text_content: str) -> float:
    """
    Estimate audio duration from text.
    
    Args:
        text_content: The text content
        
    Returns:
        Estimated duration in seconds
    """
    word_count = len(text_content.split())
    # Average speaking rate: 150 words per minute
    return (word_count / 150) * 60
