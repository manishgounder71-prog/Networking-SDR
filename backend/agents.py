"""
agents.py — AI agent for generating personalized outreach suggestions.
Uses Lyzr AI if configured, otherwise falls back to a heuristic engine.
"""

import os
from typing import Optional

LYZR_API_KEY = os.getenv("LYZR_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Try Lyzr SDK ───────────────────────────────────────────────────────────
_lyzr_available = False
try:
    from lyzr_automata import Agent, Task, Pipeline
    from lyzr_automata.ai_models.openai import OpenAIModel
    _lyzr_available = True
    print("[Agents] OK: Lyzr SDK loaded.")
except ImportError:
    print("[Agents] INFO: lyzr-automata not installed. Will attempt direct OpenAI fallback.")

# ── Try OpenAI fallback ────────────────────────────────────────────────────
_openai_available = False
try:
    import openai
    _openai_available = True
    print("[Agents] OK: OpenAI library loaded.")
except ImportError:
    print("[Agents] INFO: OpenAI library not installed.")


async def generate_suggestions(
    name: str,
    company: Optional[str],
    research: dict,
    memory: Optional[dict],
) -> dict:
    """
    Generates personalized networking/outreach suggestions for a lead.
    Returns a dict with: subject, opener, value_prop, call_to_action, tags.
    """
    articles = research.get("articles", [])
    is_returning = memory is not None

    # Prioritize specialized keys
    active_key = OPENAI_API_KEY or LYZR_API_KEY
    
    try:
        if active_key and active_key != "your_lyzr_api_key_here":
            if _lyzr_available:
                return await _lyzr_suggestions(name, company, articles, is_returning, active_key)
            elif _openai_available:
                return await _openai_fallback_suggestions(name, company, articles, is_returning, active_key)
    except Exception as e:
        print(f"[Agents] AI Suggestion failed: {str(e)}. Falling back to heuristic.")
    
    return _heuristic_suggestions(name, company, articles, is_returning)


async def _openai_fallback_suggestions(
    name: str,
    company: Optional[str],
    articles: list,
    is_returning: bool,
    api_key: str,
) -> dict:
    """Fallback using direct OpenAI calls if Lyzr SDK is unavailable."""
    try:
        from openai import OpenAI
        import json
        
        client = OpenAI(api_key=api_key)
        
        news_context = "\n".join(
            [f"- {a['title']} ({a['source']})" for a in articles[:3]]
        )
        
        prompt = f"""
You are an expert B2B networking assistant. Generate a personalized outreach message for:
Name: {name}
Company: {company or 'Unknown'}
Recent News:
{news_context or 'No recent news found.'}
Returning Contact: {'Yes' if is_returning else 'No'}

Return ONLY a valid JSON object:
{{
  "subject": "Email subject line",
  "opener": "First 2 sentences",
  "value_prop": "One sentence value prop",
  "call_to_action": "Short CTA",
  "tags": ["Tag1", "Tag2", "Tag3"],
  "score": 85,
  "sentiment": "Bullish"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[Agents] OpenAI Fallback error: {e}")
        return _heuristic_suggestions(name, company, articles, is_returning)


async def _lyzr_suggestions(
    name: str,
    company: Optional[str],
    articles: list,
    is_returning: bool,
    api_key: str,
) -> dict:
    """Use Lyzr automata to generate intelligent outreach."""
    try:
        news_context = "\n".join(
            [f"- {a['title']} ({a['source']})" for a in articles[:3]]
        )
        prompt = f"""
You are an expert B2B networking assistant. Based on the following context, 
generate a personalized outreach message for:

Name: {name}
Company: {company or 'Unknown'}
Recent News:
{news_context or 'No recent news found.'}
Returning Contact: {'Yes (follow up warmly)' if is_returning else 'No (cold outreach)'}

Return a JSON object with these exact keys:
- subject: email subject line (max 10 words)
- opener: first 2 sentences of the email
- value_prop: one sentence on why you're reaching out
- call_to_action: short CTA (e.g., "Book a 15-min call")
- tags: list of 3 relevant tags (e.g., ["Series B", "AI", "SaaS"])
- score: integer from 0-100 (Lead quality based on news/growth)
- sentiment: one-word string (Bullish, Neutral, Bearish)
"""
        model = OpenAIModel(
            api_key=api_key,
            parameters={"model": "gpt-4o-mini", "temperature": 0.7},
        )
        agent = Agent(role="SDR Outreach Specialist", prompt_persona=prompt)
        task = Task(
            name="Generate Outreach",
            agent=agent,
            instructions=prompt,
            input_type=str,
            input_value=f"{name} at {company}",
            output_type=str,
            model=model,
        )
        pipeline = Pipeline(tasks=[task])
        result = pipeline.run()
        import json
        return json.loads(result.output)
    except Exception as e:
        print(f"[Agents] Lyzr error: {e}. Falling back to heuristics.")
        return _heuristic_suggestions(name, company, [], is_returning)


def _heuristic_suggestions(
    name: str,
    company: Optional[str],
    articles: list,
    is_returning: bool,
) -> dict:
    """Rule-based suggestion generator when AI is not available."""
    first_name = name.split()[0] if name else "there"
    co = company or "your company"

    # Find a news hook
    hook = ""
    tags = ["Networking", "B2B", "Outreach"]
    if articles:
        first = articles[0]
        hook = f"I noticed that {first.get('snippet', f'{co} has been in the news recently')} "
        title = first.get("title", "")
        if "funding" in title.lower() or "series" in title.lower():
            tags = ["Funded", "Growth Stage", "Investor Ready"]
        elif "partner" in title.lower():
            tags = ["Partnership", "Expansion", "Strategic"]
        elif "award" in title.lower() or "30 under 30" in title.lower():
            tags = ["Thought Leader", "Award Winner", "Influencer"]

    if is_returning:
        subject = f"Following up — {co} x [Your Company]"
        opener = (
            f"Hi {first_name}, great to reconnect! "
            f"I've been following {co}'s progress and it's impressive. "
        )
    else:
        subject = f"Quick question for {first_name} at {co}"
        opener = (
            f"Hi {first_name}, {hook}"
            f"I came across your profile and thought there might be a strong synergy "
            f"between what you're building at {co} and what we do."
        )

    return {
        "subject": subject,
        "opener": opener,
        "value_prop": (
            f"We help companies like {co} accelerate their growth "
            "with AI-powered outreach and relationship intelligence."
        ),
        "call_to_action": "Would you be open to a 15-min intro call this week?",
        "tags": tags,
        "score": 75 if articles else 50,
        "sentiment": "Bullish" if "funding" in str(articles).lower() else "Neutral",
    }
