import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle logout on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  register: (email, password) => 
    api.post('/auth/register', { email, password }),
  
  login: (email, password) => 
    api.post('/auth/login', null, {
      params: { username: email, password, grant_type: 'password' }
    }),
  
  logout: () => api.post('/auth/logout'),
  
  getMe: () => api.get('/auth/me'),
  
  updateMe: (data) => api.patch('/auth/me', data),
};

// File endpoints
export const filesAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getAll: () => api.get('/files'),
  
  getById: (id) => api.get(`/files/${id}`),
  
  delete: (id) => api.delete(`/files/${id}`),
  
  regenerateSummary: (id) => api.post(`/files/${id}/summary`),
};

// Audio endpoints
export const audioAPI = {
  generate: (fileId) => api.post(`/audio/generate/${fileId}`),
  
  getByFile: (fileId) => api.get(`/audio/file/${fileId}`),
  
  getById: (id) => api.get(`/audio/${id}`),
  
  delete: (id) => api.delete(`/audio/${id}`),
  
  updatePosition: (id, position) => 
    api.post(`/audio/${id}/position`, { position_seconds: position }),
};

// Quiz endpoints
export const quizzesAPI = {
  generate: (fileId, difficulty = 'medium') => 
    api.post(`/quizzes/generate/${fileId}`, null, { params: { difficulty } }),
  
  getByFile: (fileId) => api.get(`/quizzes/file/${fileId}`),
  
  getById: (id) => api.get(`/quizzes/${id}`),
  
  submit: (id, answers) => api.post(`/quizzes/${id}/submit`, { answers }),
};

// Chat endpoints
export const chatAPI = {
  sendMessage: (fileId, message) => 
    api.post('/chat/message', { file_id: fileId, message }),
  
  getHistory: (fileId) => api.get(`/chat/${fileId}`),
};

// Progress endpoints
export const progressAPI = {
  getProgress: () => api.get('/progress'),
  
  updateListening: (fileId, seconds) => 
    api.post('/progress/listening', { file_id: fileId, seconds }),
  
  updateCompletion: (fileId, completion) => 
    api.post('/progress/completion', { file_id: fileId, completion }),
  
  getWeakTopics: () => api.get('/progress/weak-topics'),
};

export const uploadFile = (file) => filesAPI.upload(file);
export const getFiles = () => filesAPI.getAll();
export const getFile = (id) => filesAPI.getById(id);
export const deleteFile = (id) => filesAPI.delete(id);
export const generateSummary = (id) => filesAPI.regenerateSummary(id);
export const generateAudio = (fileId) => audioAPI.generate(fileId);
export const updateAudioPosition = (id, position) => audioAPI.updatePosition(id, position);
export const generateQuiz = (fileId, difficulty = 'medium') => quizzesAPI.generate(fileId, difficulty);
export const submitQuiz = (id, answers) => quizzesAPI.submit(id, answers);
export const getChatHistory = (fileId) => chatAPI.getHistory(fileId);
export const sendMessage = (fileId, message) => chatAPI.sendMessage(fileId, message);
export const getProgress = () => progressAPI.getProgress();

export default api;
