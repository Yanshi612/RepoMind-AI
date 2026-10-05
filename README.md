# 🧠 RepoMind AI

> **AI-powered GitHub Repository Analysis & Code Understanding Platform**

RepoMind AI helps developers understand large GitHub repositories faster by analyzing repository structure, source code, and documentation, and providing an AI-powered interface for exploring the codebase.

## 🚀 Live Demo

👉 **[Open RepoMind AI](https://repo-mind-ai-ivory.vercel.app/)**

## 📌 Project Overview

Understanding an unfamiliar GitHub repository can be time-consuming, especially when the project contains multiple folders, source files, dependencies, and configuration files.

**RepoMind AI** is designed to simplify this process by analyzing a GitHub repository and creating a searchable context that can be used to understand the project through AI-assisted queries.

### What RepoMind AI Can Do

- 🔗 Analyze a GitHub repository
- 📁 Understand repository structure and source files
- 🧩 Process relevant code and project files
- 🔎 Build searchable context from the repository
- 🤖 Ask questions about the analyzed codebase
- 💬 Get AI-assisted explanations and answers
- ⚡ Provide a developer-friendly interface for repository exploration

## ✨ Key Features

### 🔍 Repository Analysis
Enter a GitHub repository URL and let RepoMind AI analyze its contents and structure.

### 🧠 AI-Powered Code Understanding
Ask questions about the repository and receive contextual responses based on the analyzed codebase.

### 📚 Repository-Aware Search
Relevant repository information is processed into a searchable knowledge context for better answers.

### ⚙️ Full-Stack Architecture
The project contains both frontend and backend components in the same GitHub repository.

### 🎨 Modern Web Interface
Responsive React-based interface with a clean dashboard for interacting with the repository analysis system.

## 🏗️ Architecture

```text
                    ┌─────────────────────────┐
                    │      User / Developer   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     React Frontend      │
                    │       (Vite)            │
                    └────────────┬────────────┘
                                 │ API Requests
                                 ▼
                    ┌─────────────────────────┐
                    │      FastAPI Backend    │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        GitHub Repository    Repository        AI / RAG
           Content           Processing        Pipeline
                                  │
                                  ▼
                            ChromaDB / Vector
                              Search Context
```

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- JavaScript
- Modern CSS / UI components

### Backend
- Python
- FastAPI
- REST APIs

### AI / Data Processing
- Retrieval-Augmented Generation (RAG)
- ChromaDB
- Repository parsing and code processing
- Generative AI integration

### Deployment
- Frontend: Vercel
- Backend: FastAPI-compatible deployment environment

## 📂 Project Structure

```text
RepoMind-AI/
│
├── backend/
│   ├── ai_engine/
│   ├── routes/
│   ├── services/
│   ├── main.py
│   └── requirements.txt
│
├── src/
│   ├── components/
│   ├── pages/
│   └── ...
│
├── public/
├── package.json
├── vite.config.js
├── .gitignore
└── README.md
```

## 🔄 How It Works

```text
1. User enters a GitHub repository URL
                    ↓
2. RepoMind AI fetches and processes repository content
                    ↓
3. Relevant files and code are analyzed
                    ↓
4. Repository context is prepared for retrieval
                    ↓
5. User asks questions about the repository
                    ↓
6. AI generates a context-aware response
```

## 💻 Local Setup

### Prerequisites

Make sure the following are installed:

- Node.js
- npm
- Python 3.x
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Yanshi612/RepoMind-AI.git
cd RepoMind-AI
```

### 2. Frontend Setup

```bash
npm install
npm run dev
```

The frontend will start on the local Vite development server.

### 3. Backend Setup

Open a new terminal:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

## 🔐 Environment Variables

Create a `.env` file inside the backend directory and configure the required API credentials used by the application.

Example:

```env
API_KEY=your_api_key_here
```

> Never commit secret keys, passwords, or private credentials to GitHub.

## 🔌 Backend API

The backend exposes API endpoints for repository analysis, application health/status, and AI-assisted interaction.

Typical endpoints include:

```text
GET  /health
GET  /status
POST /analyze
POST /ask
```

## 🎯 Use Cases

RepoMind AI can be useful for:

- 👨‍💻 Developers exploring unfamiliar repositories
- 🎓 Students learning from open-source projects
- 🧑‍💼 Teams onboarding new developers
- 🔍 Codebase exploration and understanding
- 🤖 AI-assisted repository documentation and Q&A

## 🔒 Security & Best Practices

- Do not commit `.env` files containing secrets.
- Use environment variables for API credentials.
- Only analyze repositories that you are authorized to access or that are publicly available.
- Keep generated data and temporary files outside version control where appropriate.

## 🚧 Future Improvements

Possible future enhancements include:

- Multi-language code analysis
- Improved repository dependency mapping
- Advanced code quality analysis
- Authentication and user accounts
- Persistent vector storage
- Repository comparison
- Better code visualization
- More advanced AI reasoning over large repositories

## 👩‍💻 Author

**Yanshi**

GitHub:  
👉 https://github.com/Yanshi612

## 📄 License

This project is intended for educational and demonstration purposes.
