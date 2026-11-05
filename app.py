import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from tasks_api import app
from src.llm.schema import Input, Triage, FALLBACK

load_dotenv(Path(__file__).parent / '.env')
app.title = 'Task API with support triage'

@app.post('/triage')
async def triage(request: Request):
    try:
        body = Input.model_validate(await request.json())
    except (ValueError,ValidationError) as exc:
        return JSONResponse({'error':'text must be a nonblank string of 1–5000 characters','field':'text'},status_code=400)
    if os.getenv('LLM_STUB') == '1':
        return FALLBACK
    return JSONResponse({'error':'Live model integration is not wired yet'},status_code=503)
