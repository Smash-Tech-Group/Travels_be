from pydantic import BaseModel

class TranslationRequest(BaseModel):
    summary: str
    target_language: str