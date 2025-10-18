# Agentic Collaboration Platform — AI-Ready (CrewAI + LangChain)

This version is **API-key-ready** for integrating **CrewAI** (agent orchestration) and **LangChain/OpenAI** (conversational AI).
It provides a friendly two-way chat experience tied to tasks so users can communicate interactively with the assigned agent(s).

## Environment Variables (required for real integrations)
- `CREWAI_API_KEY` = your CrewAI API key (leave empty to use heuristic fallback)
- `OPENAI_API_KEY` = your OpenAI API key used by LangChain (leave empty to use a simulated assistant)

## Install & Run
1. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate    # Windows PowerShell
   ```
2. Install dependencies:
   ```bash
   cd backend
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
3. Set environment variables (example):
   ```powershell
   $env:CREWAI_API_KEY = "your_crewai_key"
   $env:OPENAI_API_KEY = "your_openai_key"
   ```
   or on macOS/Linux:
   ```bash
   export CREWAI_API_KEY=your_crewai_key
   export OPENAI_API_KEY=your_openai_key
   ```
4. Run the backend:
   ```bash
   python -m uvicorn main:app --reload
   ```
5. Open `frontend/index.html` in your browser.

## How it works
- **CrewAI integration**: backend will call the CrewAI HTTP API at `/assign` when `CREWAI_API_KEY` is present. Replace the placeholder URL in `backend/main.py` with your actual CrewAI endpoint.
- **LangChain/OpenAI integration**: when `OPENAI_API_KEY` is present and LangChain is installed, the `/chat/{task_id}` endpoint will use LangChain to generate model responses and persist them to `chat_logs`.
- If API keys or libs are missing, the system uses heuristics and simulated responses so the demo stays functional offline.

## Next steps I can implement for you
- Real CrewAI endpoint URL and example request/response handling (if you provide API docs).
- More advanced LangChain chains (tool-using chains, retrieval-augmented generation with embeddings and vector DB).
- WebSocket-based streaming chat for real-time feel.
- Dockerfile and docker-compose for easy deployment.

