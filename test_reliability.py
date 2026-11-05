import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIStatusError, APITimeoutError
import app
from src.llm import client
from src.llm.schema import FALLBACK


def response(value):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=value))],usage=SimpleNamespace(model_dump=lambda:{'prompt_tokens':12,'completion_tokens':5}))


def error(status, headers=None):
    return APIStatusError('provider error',response=httpx.Response(status,headers=headers,request=httpx.Request('POST','http://provider')),body={})


def setup(monkeypatch,tmp_path):
    monkeypatch.setenv('LLM_BASE_URL','http://127.0.0.1:11434/v1')
    monkeypatch.setenv('LLM_API_KEY','local-test')
    monkeypatch.setenv('LLM_MODEL','test-model')
    monkeypatch.setenv('LLM_LOG_PATH',str(tmp_path/'calls.jsonl'))
    monkeypatch.setattr(client.random,'uniform',lambda a,b:0)


def test_timeout_retry_policy_and_cost_logs(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    create=Mock(side_effect=[APITimeoutError(request=httpx.Request('POST','http://provider')),error(429,{'Retry-After':'3'}),error(500),response('{}')])
    sdk=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with patch.object(client,'OpenAI',return_value=sdk) as factory,patch.object(client.time,'sleep') as sleep:
        assert client.call_model('system','input')=='{}'
        assert [x.args[0] for x in sleep.call_args_list]==[1,3,4]
        assert factory.call_args.kwargs['timeout']==30.0 and factory.call_args.kwargs['max_retries']==0
    rows=[json.loads(x) for x in (tmp_path/'calls.jsonl').read_text().splitlines()]
    assert len(rows)==4 and rows[-1]['input_tokens']==12 and rows[-1]['output_tokens']==5


@pytest.mark.parametrize('status',[400,401,403])
def test_bad_requests_and_credentials_never_retry(monkeypatch,tmp_path,status):
    setup(monkeypatch,tmp_path)
    create=Mock(side_effect=error(status))
    sdk=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with patch.object(client,'OpenAI',return_value=sdk),patch.object(client.time,'sleep') as sleep:
        with pytest.raises(APIStatusError):client.call_model('system','input')
        assert create.call_count==1
        sleep.assert_not_called()


def test_kill_switch_and_timeout_http_status(monkeypatch):
    monkeypatch.setenv('LLM_STUB','0');monkeypatch.setenv('LLM_ENABLED','false')
    with patch('app.call_model') as call:
        assert TestClient(app.app).post('/triage',json={'text':'hello'}).json()==FALLBACK
        call.assert_not_called()
    monkeypatch.setenv('LLM_ENABLED','true')
    with patch('app.call_model',side_effect=APITimeoutError(request=httpx.Request('POST','http://provider'))):
        assert TestClient(app.app).post('/triage',json={'text':'hello'}).status_code==504
