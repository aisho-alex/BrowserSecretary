"""Q&A API router with LLM integration."""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import httpx

from config import get_settings

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    context_ids: Optional[List[str]] = None
    max_context: int = 5


class QuestionResponse(BaseModel):
    answer: str
    sources: List[dict]
    model: str


@router.post("/", response_model=QuestionResponse)
async def ask_question(data: QuestionRequest, request=None):
    """Ask question using LLM with knowledge base context."""
    kb = request.app.state.kb_client
    settings = get_settings()
    
    # 1. Search relevant knowledge
    context_entries = kb.search_knowledge(data.question, data.project_id, data.max_context)
    
    # If specific IDs provided, add those too
    if data.context_ids:
        for entry_id in data.context_ids:
            entry = kb.get_knowledge(entry_id)
            if entry and entry not in context_entries:
                context_entries.append(entry)
    
    # 2. Build context
    context_text = ""
    sources = []
    for i, entry in enumerate(context_entries, 1):
        context_text += f"\n[{i}] {entry['title']}\n{entry['content']}\n"
        sources.append({
            "id": entry["id"],
            "title": entry["title"],
            "tags": entry.get("tags", [])
        })
    
    if not context_text:
        context_text = "No relevant information found in knowledge base."
    
    # 3. Build prompt
    system_prompt = """You are a helpful assistant that answers questions based on the provided knowledge base context.
Answer the question using ONLY the information from the context.
If the context doesn't contain enough information, say so clearly.
Be concise and accurate. Reference sources by number [1], [2], etc."""

    user_prompt = f"""Context from knowledge base:
{context_text}

Question: {data.question}

Answer:"""

    # 4. Call LLM API
    if not settings.llm_api_key:
        return QuestionResponse(
            answer="LLM API key not configured. Please set LLM_API_KEY in .env file.",
            sources=sources,
            model="none"
        )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                settings.llm_api_url,
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    return QuestionResponse(
        answer=answer,
        sources=sources,
        model=settings.llm_model
    )
