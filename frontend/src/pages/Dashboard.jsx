import React, { useState, useEffect } from 'react';
import { useAuth } from '../useAuth';
import * as api from '../api';
import Navbar from '../components/Navbar';
import FileUploader from '../components/FileUploader';
import AudioPlayer from '../components/AudioPlayer';
import QuizEngine from '../components/QuizEngine';
import ChatInterface from '../components/ChatInterface';
import ProgressCards from '../components/ProgressCards';

const Dashboard = () => {
  const { user } = useAuth();
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [filesData, progressData] = await Promise.all([
        api.getFiles(),
        api.getProgress()
      ]);
      const normalizedFiles = Array.isArray(filesData) ? filesData : filesData?.files ?? [];
      setFiles(normalizedFiles);
      setProgress(progressData);
      if (normalizedFiles.length > 0 && !selectedFile) {
        setSelectedFile(normalizedFiles[0]);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  const handleFileUploaded = (newFile) => {
    setFiles([...files, newFile]);
    setSelectedFile(newFile);
  };

  const handleFileDeleted = (fileId) => {
    setFiles(files.filter(f => f.id !== fileId));
    if (selectedFile && selectedFile.id === fileId) {
      setSelectedFile(files.length > 1 ? files.find(f => f.id !== fileId) : null);
    }
  };

  const handleSummaryRegenerated = (updatedFile) => {
    setFiles(files.map(f => f.id === updatedFile.id ? updatedFile : f));
    setSelectedFile(updatedFile);
  };

  const handleAudioGenerated = (audioData) => {
    if (selectedFile) {
      setSelectedFile({ ...selectedFile, audio: audioData });
    }
  };

  const handleQuizGenerated = (quizData) => {
    if (selectedFile) {
      setSelectedFile({ ...selectedFile, quiz: quizData });
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <Navbar />
        <div className="loading-container">
          <div className="loading-spinner">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <Navbar />
      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>Welcome, {user?.email}</h1>
          <p>Your AI-powered study assistant</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <ProgressCards progress={progress} />

        <div className="dashboard-grid">
          <div className="dashboard-sidebar">
            <h2>Your Files</h2>
            <FileUploader onFileUploaded={handleFileUploaded} />
            <div className="files-list">
              {files.length === 0 ? (
                <p className="empty-state">No files uploaded yet.</p>
              ) : (
                files.map(file => (
                  <div
                    key={file.id}
                    className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                    onClick={() => handleFileSelect(file)}
                  >
                    <span className="file-name">{file.filename}</span>
                    <button
                      className="btn-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        api.deleteFile(file.id).then(() => handleFileDeleted(file.id));
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="dashboard-main">
            {selectedFile ? (
              <>
                <div className="file-section">
                  <h2>{selectedFile.filename}</h2>
                  <div className="file-actions">
                    {!selectedFile.summary && (
                      <button
                        className="btn-secondary"
                        onClick={async () => {
                          const updated = await api.generateSummary(selectedFile.id);
                          handleSummaryRegenerated(updated);
                        }}
                      >
                        Generate Summary
                      </button>
                    )}
                    {!selectedFile.audio && (
                      <button
                        className="btn-secondary"
                        onClick={async () => {
                          const audio = await api.generateAudio(selectedFile.id);
                          handleAudioGenerated(audio);
                        }}
                      >
                        Generate Audio
                      </button>
                    )}
                    {!selectedFile.quiz && (
                      <button
                        className="btn-secondary"
                        onClick={async () => {
                          const quiz = await api.generateQuiz(selectedFile.id);
                          handleQuizGenerated(quiz);
                        }}
                      >
                        Generate Quiz
                      </button>
                    )}
                  </div>

                  {selectedFile.summary && (
                    <div className="summary-section">
                      <h3>Summary</h3>
                      <div className="summary-content">
                        {selectedFile.summary.split('\n').map((line, i) => (
                          <p key={i}>{line}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {selectedFile.audio && (
                  <AudioPlayer audio={selectedFile.audio} />
                )}

                {selectedFile.quiz && (
                  <QuizEngine quiz={selectedFile.quiz} fileId={selectedFile.id} />
                )}

                <ChatInterface fileId={selectedFile.id} />
              </>
            ) : (
              <div className="empty-state">
                <p>Select a file or upload a new PDF to get started.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
