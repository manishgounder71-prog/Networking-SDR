"""
memory.py — Qdrant vector database integration for lead memory.
Stores and retrieves lead profiles using semantic embeddings.
Falls back to a simple in-memory dict if qdrant-client is unavailable.
"""

import os
import hashlib
import json
import time
from typing import Optional

QDRANT_URL = os.getenv("QDRANT_URL", ":memory:")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "sdr_leads"
VECTOR_SIZE = 128  # Small dummy size for fallback

# ── In-memory simple store (always available as fallback) ──────────────────
_simple_store: dict[str, dict] = {}


def _lead_key(name: str, company: Optional[str]) -> str:
    raw = f"{name.lower().strip()}|{(company or '').lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _dummy_vector(key: str) -> list[float]:
    """Generate a deterministic pseudo-vector from a key (for demo)."""
    import struct
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
    result = []
    for i in range(VECTOR_SIZE):
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        result.append((seed % 1000) / 1000.0)
    return result


# ── Try to load Qdrant ─────────────────────────────────────────────────────
_qdrant_client = None
_use_qdrant = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    if QDRANT_URL == ":memory:":
        _qdrant_client = QdrantClient(":memory:")
    else:
        _qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)

    # Ensure collection exists
    existing = [c.name for c in _qdrant_client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        _qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    _use_qdrant = True
    print("[Memory] OK: Qdrant connected.")
except Exception as e:
    _use_qdrant = False
    print(f"[Memory] INFO: Using in-memory dict (Qdrant: {type(e).__name__})")


# ── Public API ─────────────────────────────────────────────────────────────

def check_memory(name: str, company: Optional[str] = None) -> Optional[dict]:
    """
    Returns stored lead data if this lead has been seen before, else None.
    """
    key = _lead_key(name, company)

    if _use_qdrant:
        try:
            from qdrant_client.models import QueryRequest
            results = _qdrant_client.query_points(
                collection_name=COLLECTION_NAME,
                query=_dummy_vector(key),
                limit=1,
                score_threshold=0.99,
            )
            points = results.points if hasattr(results, 'points') else results
            if points:
                return points[0].payload
        except Exception as e:
            print(f"[Memory] Qdrant search error: {e}")

    # Fallback to simple dict
    return _simple_store.get(key)


def store_lead(name: str, company: Optional[str], data: dict) -> bool:
    """
    Stores a lead profile in memory (Qdrant or in-memory dict).
    Returns True on success.
    """
    key = _lead_key(name, company)
    payload = {
        "name": name, 
        "company": company, 
        "timestamp": time.time(),
        **data
    }

    if _use_qdrant:
        try:
            from qdrant_client.models import PointStruct
            import uuid
            _qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, key)),
                        vector=_dummy_vector(key),
                        payload=payload,
                    )
                ],
            )
            return True
        except Exception as e:
            print(f"[Memory] Qdrant store error: {e}")

    # Fallback
    _simple_store[key] = payload
    return True


def get_all_leads() -> list[dict]:
    """Returns all stored leads (for listing/dashboard)."""
    if _use_qdrant:
        try:
            result = _qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                with_payload=True,
            )
            # scroll() returns a tuple (points, next_page_offset)
            points = result[0] if isinstance(result, tuple) else result
            return [r.payload for r in points]
        except Exception as e:
            print(f"[Memory] Qdrant scroll error: {e}")

    # Fallback: If cache is empty, try loading from CSV
    if not _simple_store:
        _load_from_csv()

    return list(_simple_store.values())


def _load_from_csv():
    """Helper to populate _simple_store from the storage CSV."""
    from pathlib import Path
    import csv
    csv_path = Path(__file__).parent / "leads_fallback.csv"
    if not csv_path.exists():
        return

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Name")
                company = row.get("Company")
                if not name: continue
                
                key = _lead_key(name, company)
                if key not in _simple_store:
                    # Map CSV columns back to the structure expected by memory.py
                    _simple_store[key] = {
                        "name": name,
                        "company": company,
                        "linkedin_url": row.get("LinkedIn URL"),
                        "notes": row.get("Notes"),
                        "last_researched": row.get("News Summary"),
                        "tags": [t.strip() for t in row.get("Tags", "").split(",") if t.strip()],
                        "suggestions": {
                            "subject": row.get("Email Subject"),
                            "opener": row.get("Opener"),
                            "value_prop": row.get("Value Prop"),
                            "call_to_action": row.get("CTA")
                        }
                    }
        print(f"[Memory] Loaded {len(_simple_store)} leads from CSV fallback.")
    except Exception as e:
        print(f"[Memory] Error loading CSV: {e}")


def delete_lead(name: str, company: Optional[str] = None) -> bool:
    """Removes a lead from memory."""
    key = _lead_key(name, company)

    if _use_qdrant:
        try:
            from qdrant_client.models import PointIdList
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, key))
            _qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdList(points=[point_id]),
            )
        except Exception as e:
            print(f"[Memory] Qdrant delete error: {e}")

    if key in _simple_store:
        del _simple_store[key]
    
    return True
