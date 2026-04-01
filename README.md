# Networking SDR | AI Intelligence Command Center

AI-powered lead research and outreach suggestion engine for elite sales development teams.

## Features

- **Real-time Lead Research** - News, funding, and company intelligence via SerpAPI/Zenserp
- **AI-Powered Outreach** - GPT-4o generates personalized email templates
- **Memory System** - Lead history tracking with vector database
- **CRM Integration** - Google Sheets or CSV backup
- **Beautiful UI** - Obsidian-themed command center interface

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment to Render

### 1. Fork/Clone Repository
```bash
git clone https://github.com/manishgounder71-prog/Networking-SDR.git
cd Networking-SDR
```

### 2. Create Render Account
Sign up at [render.com](https://render.com) and connect your GitHub repository.

### 3. Deploy Services

**Backend API:**
1. Create a new **Web Service**
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `OPENAI_API_KEY` (your key)
   - `SERPAPI_API_KEY` (optional)
   - `QDRANT_URL=:memory:`
   - `PORT=10000`

**Frontend:**
1. Create a **Static Site**
2. Set root directory to `frontend`
3. Build command: `npm install && npm run build`
4. Publish directory: `frontend/dist`
5. Add redirect rule: `/* → /index.html`

### 4. Configure API URL
For production, set `VITE_API_URL` environment variable in the frontend to your backend URL (e.g., `https://networking-sdr-api.onrender.com`).

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `LYZR_API_KEY` | Lyzr AI key | No |
| `SERPAPI_API_KEY` | SerpAPI/Zenserp key | No |
| `QDRANT_URL` | Qdrant Cloud URL | No |
| `QDRANT_API_KEY` | Qdrant API key | No |

## Architecture

```
Frontend (React/Vite) → Backend (FastAPI) → OpenAI/SerpAPI
                              ↓
                        Memory (In-Memory/Qdrant)
                              ↓
                        Storage (CSV/Google Sheets)
```

## License

MIT - 2026 Manish Gounder
