# StudyBuddy - AI-Powered Study Assistant

## Project Overview

StudyBuddy is an AI-powered study assistant that helps students and professionals convert static study materials (PDFs) into active, engaging learning sessions.

### MVP Features

1. **User Authentication** - Register, login, logout with JWT tokens
2. **PDF Upload** - Upload study materials (max 20MB)
3. **Text Extraction** - Automatically extract text from PDFs
4. **AI Summaries** - Generate concise 5-bullet summaries
5. **Audio Lessons** - Convert text to audio using TTS
6. **Quiz Generation** - Create 5-question multiple-choice quizzes
7. **AI Chat Tutor** - Chat with AI using uploaded files as context
8. **Progress Dashboard** - Track study progress and weak topics

### Tech Stack

**Backend:**
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic v2
- JWT Authentication (python-jose)
- Password hashing (passlib + bcrypt)
- PyPDF2 for PDF extraction
- OpenAI SDK (optional)
- pytest for testing

**Frontend:**
- React 18
- Vite
- React Router
- Axios
- Custom CSS

**Database:**
- PostgreSQL (production via Docker)
- SQLite (local development fallback)

## Folder Structure

```
studybuddy/
├── README.md
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── deps.py
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── files.py
│   │   │   ├── audio.py
│   │   │   ├── quizzes.py
│   │   │   ├── chat.py
│   │   │   └── progress.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── pdf_service.py
│   │       ├── ai_service.py
│   │       └── tts_service.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_api.py
│   ├── uploads/
│   └── audio/
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── .env.example
    ├── Dockerfile
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        ├── AuthContext.jsx
        ├── index.css
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   └── Dashboard.jsx
        └── components/
            ├── Navbar.jsx
            ├── FileUploader.jsx
            ├── AudioPlayer.jsx
            ├── QuizEngine.jsx
            ├── ChatInterface.jsx
            └── ProgressCards.jsx
```

## Local Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for PostgreSQL)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Edit `.env` and configure your settings (optional: add OpenAI key)

6. Run the backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs will be available at: http://localhost:8000/docs

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

### Database Setup with Docker

To use PostgreSQL instead of SQLite:

1. Start the database container:
```bash
docker-compose up -d db
```

2. Update `backend/.env`:
```
DATABASE_URL=postgresql://studybuddy:studybuddy@localhost:5432/studybuddy
```

3. Restart the backend

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | Database connection string | sqlite:///./studybuddy.db |
| SECRET_KEY | JWT secret key | change-this |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration time | 1440 |
| OPENAI_API_KEY | OpenAI API key (optional) | |
| OPENAI_MODEL | OpenAI model to use | gpt-4o-mini |
| TTS_PROVIDER | TTS provider (openai/mock) | mock |
| FRONTEND_ORIGIN | Frontend URL for CORS | http://localhost:5173 |
| ALLOWED_ORIGINS | Comma-separated allowed origins | http://localhost:5173 |

### Frontend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000 |

## Running Tests

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get token |
| POST | /auth/logout | Logout (invalidate token) |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Get current user |
| PATCH | /auth/me | Update current user |

### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /files/upload | Upload PDF file |
| GET | /files | List all files |
| GET | /files/{id} | Get file details |
| DELETE | /files/{id} | Delete file |
| POST | /files/{id}/summary | Generate summary |

### Audio

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /audio/generate/{file_id} | Generate audio lesson |
| GET | /audio/file/{file_id} | Get audio for file |
| GET | /audio/{id} | Get audio details |
| DELETE | /audio/{id} | Delete audio |
| POST | /audio/{id}/position | Save playback position |

### Quizzes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /quizzes/generate/{file_id} | Generate quiz |
| GET | /quizzes/file/{file_id} | Get quizzes for file |
| GET | /quizzes/{id} | Get quiz details |
| POST | /quizzes/{id}/submit | Submit quiz answers |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /chat/message | Send chat message |
| GET | /chat/{file_id} | Get chat history |

### Progress

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /progress | Get overall progress |
| POST | /progress/listening | Log listening time |
| POST | /progress/completion | Update completion status |
| GET | /progress/weak-topics | Get weak topics |

## Manual Testing Checklist

1. [ ] Register a new account
2. [ ] Login with credentials
3. [ ] Upload a PDF file
4. [ ] View file summary
5. [ ] Generate audio lesson
6. [ ] Play audio lesson
7. [ ] Generate quiz
8. [ ] Complete quiz
9. [ ] Chat with AI tutor
10. [ ] View progress dashboard
11. [ ] Logout

## Deployment Notes

### Backend (Render/Railway)

1. Set build command: `pip install -r backend/requirements.txt`
2. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables
4. Connect PostgreSQL database

### Frontend (Vercel/Netlify)

1. Set build command: `npm run build`
2. Set output directory: `dist`
3. Add environment variable: `VITE_API_URL`
4. Deploy

## Phase 2 Future Features

- Voice conversations with AI tutor
- Mobile app (React Native)
- Flashcards system
- Study groups and collaboration
- AI tutor memory across sessions
- AI career coaching
- University partnerships
- Enterprise learning solutions
- Certification marketplaces
- Spaced repetition algorithms
- Calendar integration
- Note-taking features
- Collaborative whiteboard

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
