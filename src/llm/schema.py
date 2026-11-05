from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    text: str = Field(min_length=1, max_length=5000)
    @field_validator('text')
    @classmethod
    def not_blank(cls,value):
        if not value.strip():
            raise ValueError('text must not be blank')
        return value

class Triage(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    category: Literal['billing','technical','account','other']
    urgency: Literal['low','medium','high']
    suggested_team: Literal['billing','support','accounts','general']
    confidence: float = Field(ge=0,le=1)
    summary: str = Field(min_length=1,max_length=200)

FALLBACK = Triage(category='other',urgency='medium',suggested_team='general',confidence=0.0,summary='Manual review required').model_dump()
