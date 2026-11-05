import json
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from openai import OpenAI, APITimeoutError, APIStatusError, APIConnectionError


def log_call(model, started, repair, outcome, usage=None):
    path = Path(os.getenv('LLM_LOG_PATH', 'logs/model-calls.jsonl'))
    path.parent.mkdir(parents=True, exist_ok=True)
    usage = usage or {}
    row = {'prompt_version':'triage-v1', 'model':model,
           'input_tokens':usage.get('prompt_tokens'), 'output_tokens':usage.get('completion_tokens'),
           'duration_ms':round((time.monotonic()-started)*1000), 'repair':repair,
           'outcome':outcome, 'api_cost_usd':0 if '127.0.0.1' in os.environ['LLM_BASE_URL'] or 'localhost' in os.environ['LLM_BASE_URL'] else None}
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(row)+'\n')


def retry_delay(error, attempt):
    if isinstance(error, APIStatusError) and error.status_code == 429:
        value = error.response.headers.get('Retry-After')
        if value:
            try:
                return max(0, float(value))
            except ValueError:
                try:
                    return max(0, (parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds())
                except (TypeError, ValueError):
                    pass
    return 2**attempt + random.uniform(0, .2)

def call_model(prompt, text, repair=0):
    client=OpenAI(base_url=os.environ['LLM_BASE_URL'],api_key=os.environ['LLM_API_KEY'],timeout=30.0,max_retries=0)
    model=os.environ['LLM_MODEL']
    for attempt in range(4):
        started=time.monotonic()
        try:
            response=client.chat.completions.create(model=model,temperature=0,messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'text':text})}])
            log_call(model,started,repair,'ok',response.usage.model_dump() if response.usage else None)
            return response.choices[0].message.content or ''
        except APITimeoutError as error:
            log_call(model,started,repair,'timeout')
            if attempt == 3:
                raise
            time.sleep(retry_delay(error,attempt))
        except APIStatusError as error:
            log_call(model,started,repair,'http_'+str(error.status_code))
            if (error.status_code != 429 and error.status_code < 500) or attempt == 3:
                raise
            time.sleep(retry_delay(error,attempt))
        except APIConnectionError:
            log_call(model,started,repair,'connection_error')
            raise
