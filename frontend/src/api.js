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
  
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    form.append('grant_type', 'password');

    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  
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

export const uploadFile = async (file) => {
  const response = await filesAPI.upload(file);
  return response.data;
};
export const getFiles = async () => {
  const response = await filesAPI.getAll();
  return response.data.files ?? response.data;
};
export const getFile = async (id) => {
  const response = await filesAPI.getById(id);
  return response.data;
};
export const deleteFile = async (id) => {
  const response = await filesAPI.delete(id);
  return response.data;
};
export const generateSummary = async (id) => {
  const response = await filesAPI.regenerateSummary(id);
  return response.data.summary ?? response.data;
};
export const generateAudio = async (fileId) => {
  const response = await audioAPI.generate(fileId);
  return response.data;
};
export const updateAudioPosition = async (id, position) => {
  const response = await audioAPI.updatePosition(id, position);
  return response.data;
};
export const generateQuiz = async (fileId, difficulty = 'medium') => {
  const response = await quizzesAPI.generate(fileId, difficulty);
  return response.data;
};
export const submitQuiz = async (id, answers) => {
  const response = await quizzesAPI.submit(id, answers);
  return response.data;
};
export const getChatHistory = async (fileId) => {
  const response = await chatAPI.getHistory(fileId);
  return response.data.messages ?? response.data;
};
export const sendMessage = async (fileId, message) => {
  const response = await chatAPI.sendMessage(fileId, message);
  const payload = response.data ?? response;
  if (typeof payload === 'string') return payload;
  return payload.response ?? payload.message ?? payload;
};
export const getProgress = async () => {
  const response = await progressAPI.getProgress();
  return response.data;
};

export default api;
