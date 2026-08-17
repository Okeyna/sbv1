import React, { useState, useRef, useEffect } from 'react';
import * as api from '../api';

const AudioPlayer = ({ audio }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(audio?.duration || 0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const audioRef = useRef(null);

  useEffect(() => {
    if (audio?.position_seconds) {
      setCurrentTime(audio.position_seconds);
      if (audioRef.current) {
        audioRef.current.currentTime = audio.position_seconds;
      }
    }
  }, [audio]);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      // Save position when paused
      api.updateAudioPosition(audio.id, audioRef.current.currentTime).catch(console.error);
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const handleSpeedChange = (e) => {
    const speed = parseFloat(e.target.value);
    setPlaybackRate(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-player">
      <h3>Audio Lesson</h3>
      <audio
        ref={audioRef}
        src={audio.audio_url}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
      />
      
      <div className="audio-controls">
        <button className="btn-play" onClick={togglePlay}>
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        
        <div className="progress-container">
          <span className="time-display">{formatTime(currentTime)}</span>
          <input
            type="range"
            className="progress-bar"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
          />
          <span className="time-display">{formatTime(duration)}</span>
        </div>

        <div className="speed-control">
          <label>Speed:</label>
          <select value={playbackRate} onChange={handleSpeedChange}>
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
        </div>
      </div>

      <div className="audio-info">
        <p>Voice: {audio.voice_type || 'Default'}</p>
      </div>
    </div>
  );
};

export default AudioPlayer;
