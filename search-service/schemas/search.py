"""
Pydantic schemas for search service
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date

class SearchResult(BaseModel):
    """Search result schema"""
    id: str
    name: str
    cpf: str
    birth_date: date
    age: int
    gender: str
    email: Optional[str]
    phone: Optional[str]
    medical_conditions: List[str]
    medications: List[str]
    allergies: List[str]
    match_score: float = 1.0
    
    @staticmethod
    def calculate_age(birth_date: date) -> int:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

class SearchResponse(BaseModel):
    """Search response schema"""
    results: List[SearchResult]
    total: int
    query_time_ms: float
    filters_applied: Dict[str, str]

class AdvancedSearchParams(BaseModel):
    """Advanced search parameters"""
    query: Optional[str] = None
    name: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    birth_date_from: Optional[date] = None
    birth_date_to: Optional[date] = None
    medical_condition: Optional[str] = None
    medication: Optional[str] = None
    allergy: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class SuggestionsResponse(BaseModel):
    """Suggestions response schema"""
    field: str
    suggestions: List[str]
    count: int