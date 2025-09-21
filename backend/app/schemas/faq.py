# backend/app/schemas/faq.py
from pydantic import BaseModel, Field
from typing import List

class FAQ(BaseModel):
    question: str = Field(..., max_length=200)
    answer: str = Field(..., max_length=1000)

class FAQUpdate(BaseModel):
    faqs: List[FAQ]