# Networking SDR | AI Intelligence Command Center ⊡

**Networking SDR** is a high-performance, AI-driven lead intelligence and automated outreach platform built for elite sales engineering. It automates the entire lead acquisition lifecycle: from real-time research and memory indexing to strategic outreach generation.

![Preview](C:/Users/manis/.gemini/antigravity/brain/dc7314d1-d4af-4a0f-8a1b-f019f56dd8ed/final_demo_dashboard_1774977155990.png)

## 📡 Core Intelligence Engine

The platform is powered by a multi-agent orchestration layer:
- **🧠 Memory Scan**: Leverages **Qdrant Vector DB** to maintain longitudinal lead history and context.
- **🔍 Intelligence Extraction**: Real-time news & funding research via **Zenserp/SerpAPI**.
- **✨ Agent Strategy**: Deep lead scoring and sentiment analysis using **OpenAI GPT-4o**.
- **💾 CRM Sync**: Automated data persistence to Google Sheets or local CSV fallback.

## 🚀 Key Features

- **Demo Mode**: One-click population of high-quality lead targets (Jensen Huang, Satya Nadella).
- **Intelligence Log**: Chronologically sorted sidebar of all past research cycles.
- **Lead Score Meter**: Visual assessment of lead viability based on recent news and sentiment.
- **Strategic Directives**: AI-generated email subject lines, openers, and value propositions.
- **Micro-animations**: Premium glassmorphic UI with real-time pipeline progress indicators.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Pydantic, Python-dotenv, Httpx, Qdrant-client.
- **Frontend**: React (Vite), Vanilla CSS, Lucide Icons.
- **AI/LLM**: OpenAI GPT models.
- **Search**: SerpAPI / Zenserp.

## 🚦 Getting Started

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Environment Variables
Create a `.env` file in the `backend/` directory:
```env
OPENAI_API_KEY=your_key
SERPAPI_API_KEY=your_key
QDRANT_URL=:memory:
```

## 📜 License
MIT License - 2026 मनीष गौंडर
