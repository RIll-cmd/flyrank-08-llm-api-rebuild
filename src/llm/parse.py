import json
from src.llm.schema import Triage

def parse_output(raw):
    # Accept surrounding prose/fences, but still require exactly one schema-valid object.
    start=raw.find('{')
    if start < 0:
        raise ValueError('No JSON object found')
    result, end=json.JSONDecoder().raw_decode(raw[start:])
    return Triage.model_validate(result).model_dump()
