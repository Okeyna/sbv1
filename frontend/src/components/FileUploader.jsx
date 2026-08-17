import React, { useState, useRef } from 'react';
import * as api from '../api';

const FileUploader = ({ onFileUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = async (file) => {
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Only PDF files are allowed.');
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError('File size must be less than 20MB.');
      return;
    }

    setError('');
    setUploading(true);

    try {
      const uploadedFile = await api.uploadFile(file);
      onFileUploaded(uploadedFile);
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  return (
    <div className="file-uploader">
      <div
        className={`upload-area ${uploading ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={handleClick}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleInputChange}
          accept=".pdf,application/pdf"
          style={{ display: 'none' }}
        />
        {uploading ? (
          <div className="upload-status">
            <div className="upload-spinner">Uploading...</div>
          </div>
        ) : (
          <>
            <div className="upload-icon">📁</div>
            <p>Drag & drop a PDF here or click to select</p>
            <p className="upload-hint">Max file size: 20MB</p>
          </>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default FileUploader;
