import json
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import app
from src.llm.schema import FALLBACK

def test_input_and_stub(monkeypatch):
    monkeypatch.setenv('LLM_STUB','1')
    with patch('app.call_model') as model:
        client=TestClient(app.app)
        assert client.post('/triage',json={'text':'hello'}).json()==FALLBACK
        for body in [{},{'text':2},{'text':' '},{'text':'x'*5001}]:
            response=client.post('/triage',json=body)
            assert response.status_code==400 and response.json()['field']=='text'
        model.assert_not_called()

def test_repair_once_and_quarantine(monkeypatch):
    monkeypatch.setenv('LLM_STUB','0')
    client=TestClient(app.app)
    with patch('app.call_model',side_effect=['bad',json.dumps(FALLBACK)]) as model:
        response=client.post('/triage',json={'text':'hello'})
        assert response.status_code==200 and model.call_count==2
        assert model.call_args.kwargs['repair']==1
    path=app.Path(app.__file__).parent/'logs/quarantine.jsonl'
    before=len(path.read_text().splitlines()) if path.exists() else 0
    with patch('app.call_model',return_value='{"category":"invented"}') as model:
        response=client.post('/triage',json={'text':'hello'})
        assert response.status_code==422 and model.call_count==2
    assert len(path.read_text().splitlines())==before+1
    assert 'raw_output' in json.loads(path.read_text().splitlines()[-1])

def test_fenced_output():
    from src.llm.parse import parse_output
    assert parse_output('Here is JSON: ```json\n'+json.dumps(FALLBACK)+'\n```')==FALLBACK
