import json
import os
from openai import OpenAI

def call_model(prompt, text, repair=0):
    client=OpenAI(base_url=os.environ['LLM_BASE_URL'],api_key=os.environ['LLM_API_KEY'],timeout=30.0,max_retries=0)
    response=client.chat.completions.create(model=os.environ['LLM_MODEL'],temperature=0,messages=[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'text':text})}])
    return response.choices[0].message.content or ''
