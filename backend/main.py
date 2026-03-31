import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load configuration
load_dotenv()

# Import internal modules
from research import fetch_lead_research
from memory import check_memory, store_lead, get_all_leads, delete_lead
from agents import generate_suggestions
from storage import save_lead, get_storage_status

app = FastAPI(
    title="Real-Time Networking SDR API",
    description="AI-powered lead research and outreach suggestion engine.",
    version="1.0.0",
)

# Allow frontend dev server to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────────────

class LeadRequest(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    status: str
    lead_name: Optional[str]
    company: Optional[str]
    is_returning: bool
    research: dict
    suggestions: dict
    storage: dict


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Networking SDR API is live 🚀",
        "status": "ok",
        "version": "1.0.0",
        "storage": get_storage_status(),
    }


@app.get("/leads")
async def list_leads():
    """Retrieve all leads stored in memory."""
    leads = get_all_leads()
    return {"count": len(leads), "leads": leads}


@app.delete("/leads")
async def remove_lead(name: str, company: Optional[str] = None):
    """Remove a lead from memory."""
    success = delete_lead(name, company)
    return {"status": "success" if success else "error"}


@app.post("/process-lead", response_model=LeadResponse)
async def process_lead(lead: LeadRequest):
    """
    Full pipeline:
    1. Validate input
    2. Check memory for returning lead
    3. Fetch real-time research (SerpAPI)
    4. Generate AI suggestions (Lyzr / heuristic)
    5. Store in memory (Qdrant)
    6. Save to Google Sheets / CSV
    """
    if not lead.name and not lead.company:
        raise HTTPException(
            status_code=400,
            detail="Provide at least a name or company.",
        )

    name = lead.name or lead.company
    company = lead.company

    # 1. Check memory
    existing = check_memory(name, company)
    is_returning = existing is not None

    # 2. Research
    research = await fetch_lead_research(name, company)

    # 3. Generate AI suggestions
    suggestions = await generate_suggestions(name, company, research, existing)

    # 4. Store in memory
    lead_data = {
        "linkedin_url": lead.linkedin_url,
        "notes": lead.notes,
        "last_researched": research.get("summary", ""),
        "tags": suggestions.get("tags", []),
    }
    store_lead(name, company, lead_data)

    # 5. Save to Sheets / CSV
    storage_result = save_lead(
        name=name,
        company=company,
        linkedin_url=lead.linkedin_url,
        suggestions=suggestions,
        research=research,
        is_returning=is_returning,
        notes=lead.notes,
    )

    return LeadResponse(
        status="success",
        lead_name=name,
        company=company,
        is_returning=is_returning,
        research=research,
        suggestions=suggestions,
        storage=storage_result,
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "storage": get_storage_status()}


@app.get("/status")
async def get_detailed_status():
    """Returns detailed connectivity status of all integrations."""
    # We import inside to avoid circular dependencies if any
    from research import SERPAPI_KEY
    from memory import _use_qdrant
    from agents import LYZR_API_KEY, OPENAI_API_KEY, _lyzr_available, _openai_available

    return {
        "research": {
            "connected": bool(SERPAPI_KEY),
            "provider": "Zenserp" if (len(SERPAPI_KEY) == 36 and "-" in SERPAPI_KEY) else "SerpAPI",
            "fallback": not bool(SERPAPI_KEY)
        },
        "memory": {
            "connected": _use_qdrant,
            "provider": "Qdrant",
            "fallback": not _use_qdrant
        },
        "ai": {
            "connected": bool(LYZR_API_KEY or OPENAI_API_KEY),
            "lyzr_enabled": _lyzr_available and bool(LYZR_API_KEY),
            "openai_enabled": _openai_available and bool(OPENAI_API_KEY),
            "fallback": not bool(LYZR_API_KEY or OPENAI_API_KEY)
        },
        "storage": get_storage_status()
    }



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
