import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from openai import APITimeoutError, APIStatusError, APIConnectionError
from tasks_api import app
from src.llm.schema import Input, Triage, FALLBACK
from src.llm.client import call_model
from src.llm.parse import parse_output

load_dotenv(Path(__file__).parent / '.env')
app.title = 'Task API with support triage'

@app.exception_handler(APITimeoutError)
async def model_timeout(request, error):
    return JSONResponse({'error':'Model timed out after bounded retries'},status_code=504)

@app.exception_handler(APIStatusError)
async def model_http_error(request, error):
    return JSONResponse({'error':'Model provider rejected the request','provider_status':error.status_code},status_code=503)

@app.exception_handler(APIConnectionError)
async def model_connection_error(request, error):
    return JSONResponse({'error':'Model provider unavailable'},status_code=503)

@app.post('/triage')
async def triage(request: Request):
    try:
        body = Input.model_validate(await request.json())
    except (ValueError,ValidationError) as exc:
        return JSONResponse({'error':'text must be a nonblank string of 1–5000 characters','field':'text'},status_code=400)
    if os.getenv('LLM_STUB') == '1' or os.getenv('LLM_ENABLED','true').lower() == 'false':
        return FALLBACK
    prompt=(Path(__file__).parent/'prompts/triage-v1.md').read_text()
    raw=call_model(prompt,body.text)
    try:
        return parse_output(raw)
    except (ValueError,ValidationError) as error:
        repair_prompt=prompt+'\nYour previous answer was rejected: '+str(error)+'\nPrevious output: '+raw+'\nReturn only corrected JSON matching the schema.'
        corrected=call_model(repair_prompt,body.text,repair=1)
        try:
            return parse_output(corrected)
        except (ValueError,ValidationError) as final_error:
            path=Path(__file__).parent/'logs/quarantine.jsonl'
            path.parent.mkdir(exist_ok=True)
            with path.open('a',encoding='utf8') as handle:
                handle.write(json.dumps({'input':body.text,'raw_output':corrected,'error':str(final_error),'prompt_version':'triage-v1'})+'\n')
            return JSONResponse({'error':'Model output failed validation after one repair'},status_code=422)
