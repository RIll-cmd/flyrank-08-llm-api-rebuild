"""Measure the real endpoint against labels fixed before this evaluation run."""
import json
import os
from pathlib import Path
import time
import httpx
from dotenv import load_dotenv

root=Path(__file__).resolve().parent
load_dotenv(root.parent/'.env')
base=os.getenv('BASE_URL','http://127.0.0.1:8108').rstrip('/')
cases=json.loads((root/'cases.json').read_text())
results=[]
with httpx.Client(timeout=180) as client:
    for index,case in enumerate(cases,1):
        started=time.monotonic()
        response=client.post(base+'/triage',json={'text':case['text']})
        answer=response.json()
        category_match=response.status_code==200 and answer.get('category')==case['category']
        fields_match=category_match and all(answer.get(k)==case[k] for k in ['urgency','suggested_team'])
        if case.get('unsure'):
            fields_match=fields_match and answer.get('confidence',1)<.5
        results.append({'case':index,'input':case['text'],'expected':{k:case[k] for k in ['category','urgency','suggested_team']},'status':response.status_code,'response':answer,'category_match':category_match,'closed_fields_match':fields_match,'seconds':round(time.monotonic()-started,2)})
        print(f'Case {index}: HTTP {response.status_code}; category={category_match}; closed fields={fields_match}',flush=True)
score=sum(row['category_match'] for row in results)
report={'date':'2026-11-05','prompt_version':'triage-v1','model':os.getenv('LLM_MODEL'),'category_correct':score,'total':len(cases),'category_accuracy':score/len(cases),'closed_fields_correct':sum(row['closed_fields_match'] for row in results),'results':results}
(root/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'Category: {score}/{len(cases)} ({score/len(cases):.1%}); closed fields: {report["closed_fields_correct"]}/{len(cases)}')
print('Failed category cases:',[row['case'] for row in results if not row['category_match']])
