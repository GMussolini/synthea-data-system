"""
Search routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from datetime import datetime, date
import logging

from database import get_db
from models.patient import Patient
from schemas.search import (
    SearchResult, SearchResponse, AdvancedSearchParams, SuggestionsResponse
)
from utils.auth import verify_token
from utils.search import calculate_match_score

# Logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

@router.get("/patients", response_model=SearchResponse)
async def search_patients(
    # General search
    q: Optional[str] = Query(None, description="General search query"),
    
    # Specific field searches
    name: Optional[str] = Query(None, description="Patient name"),
    cpf: Optional[str] = Query(None, description="CPF number"),
    email: Optional[str] = Query(None, description="Email address"),
    phone: Optional[str] = Query(None, description="Phone number"),
    gender: Optional[str] = Query(None, description="Gender (M/F/O)"),
    
    # Age filters
    age_min: Optional[int] = Query(None, ge=0, le=150, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=150, description="Maximum age"),
    
    # Date filters
    birth_date_from: Optional[date] = Query(None, description="Birth date from"),
    birth_date_to: Optional[date] = Query(None, description="Birth date to"),
    
    # Medical filters
    condition: Optional[str] = Query(None, description="Medical condition"),
    medication: Optional[str] = Query(None, description="Medication"),
    allergy: Optional[str] = Query(None, description="Allergy"),
    
    # Address filters
    city: Optional[str] = Query(None, description="City"),
    state: Optional[str] = Query(None, description="State"),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    
    # Sorting
    sort_by: str = Query("name", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Advanced patient search with multiple filters"""
    start_time = datetime.now()
    
    # Build search parameters
    params = AdvancedSearchParams(
        query=q,
        name=name,
        cpf=cpf,
        email=email,
        phone=phone,
        gender=gender,
        age_min=age_min,
        age_max=age_max,
        birth_date_from=birth_date_from,
        birth_date_to=birth_date_to,
        medical_condition=condition,
        medication=medication,
        allergy=allergy,
        city=city,
        state=state
    )
    
    # Build query
    query = db.query(Patient)
    filters_applied = {}
    
    # General search (searches multiple fields)
    if params.query:
        search_term = f"%{params.query}%"
        query = query.filter(
            or_(
                Patient.name.ilike(search_term),
                Patient.cpf.like(search_term),
                Patient.email.ilike(search_term),
                Patient.phone.like(search_term),
                Patient.notes.ilike(search_term) if Patient.notes else False
            )
        )
        filters_applied["general_query"] = params.query
    
    # Specific field filters
    if params.name:
        query = query.filter(Patient.name.ilike(f"%{params.name}%"))
        filters_applied["name"] = params.name
    
    if params.cpf:
        query = query.filter(Patient.cpf.like(f"%{params.cpf}%"))
        filters_applied["cpf"] = params.cpf
    
    if params.email:
        query = query.filter(Patient.email.ilike(f"%{params.email}%"))
        filters_applied["email"] = params.email
    
    if params.phone:
        query = query.filter(Patient.phone.like(f"%{params.phone}%"))
        filters_applied["phone"] = params.phone
    
    if params.gender:
        query = query.filter(Patient.gender == params.gender.upper())
        filters_applied["gender"] = params.gender
    
    # Age filters (calculate from birth_date)
    if params.age_min is not None or params.age_max is not None:
        today = date.today()
        
        if params.age_max is not None:
            min_birth_date = date(today.year - params.age_max - 1, today.month, today.day)
            query = query.filter(Patient.birth_date >= min_birth_date)
            filters_applied["age_max"] = str(params.age_max)
        
        if params.age_min is not None:
            max_birth_date = date(today.year - params.age_min, today.month, today.day)
            query = query.filter(Patient.birth_date <= max_birth_date)
            filters_applied["age_min"] = str(params.age_min)
    
    # Date range filters
    if params.birth_date_from:
        query = query.filter(Patient.birth_date >= params.birth_date_from)
        filters_applied["birth_date_from"] = str(params.birth_date_from)
    
    if params.birth_date_to:
        query = query.filter(Patient.birth_date <= params.birth_date_to)
        filters_applied["birth_date_to"] = str(params.birth_date_to)
    
    # Medical condition filter (searches in JSON array)
    if params.medical_condition:
        query = query.filter(
            func.jsonb_array_elements_text(Patient.medical_conditions).op('ILIKE')(f'%{params.medical_condition}%')
        )
        filters_applied["medical_condition"] = params.medical_condition
    
    # Medication filter
    if params.medication:
        query = query.filter(
            func.jsonb_array_elements_text(Patient.medications).op('ILIKE')(f'%{params.medication}%')
        )
        filters_applied["medication"] = params.medication
    
    # Allergy filter
    if params.allergy:
        query = query.filter(
            func.jsonb_array_elements_text(Patient.allergies).op('ILIKE')(f'%{params.allergy}%')
        )
        filters_applied["allergy"] = params.allergy
    
    # Address filters (searches in JSON object)
    if params.city:
        query = query.filter(
            func.jsonb_extract_path_text(Patient.address, 'city').op('ILIKE')(f'%{params.city}%')
        )
        filters_applied["city"] = params.city
    
    if params.state:
        query = query.filter(
            func.jsonb_extract_path_text(Patient.address, 'state').op('ILIKE')(f'%{params.state}%')
        )
        filters_applied["state"] = params.state
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    if sort_by == "name":
        query = query.order_by(Patient.name.asc() if order == "asc" else Patient.name.desc())
    elif sort_by == "birth_date":
        query = query.order_by(Patient.birth_date.asc() if order == "asc" else Patient.birth_date.desc())
    elif sort_by == "created_at":
        query = query.order_by(Patient.created_at.asc() if order == "asc" else Patient.created_at.desc())
    else:
        query = query.order_by(Patient.name.asc())
    
    # Apply pagination
    offset = (page - 1) * size
    patients = query.offset(offset).limit(size).all()
    
    # Build results with scoring
    results = []
    for patient in patients:
        score = calculate_match_score(patient, params)
        result = SearchResult(
            id=str(patient.id),
            name=patient.name,
            cpf=patient.cpf,
            birth_date=patient.birth_date,
            age=SearchResult.calculate_age(patient.birth_date),
            gender=patient.gender,
            email=patient.email,
            phone=patient.phone,
            medical_conditions=patient.medical_conditions or [],
            medications=patient.medications or [],
            allergies=patient.allergies or [],
            match_score=score
        )
        results.append(result)
    
    # Sort by relevance score if we have search criteria
    if params.query or params.medical_condition or params.medication:
        results.sort(key=lambda x: x.match_score, reverse=True)
    
    # Calculate query time
    query_time = (datetime.now() - start_time).total_seconds() * 1000
    
    logger.info(f"Search completed: {total} results, {query_time:.2f}ms")
    
    return SearchResponse(
        results=results,
        total=total,
        query_time_ms=query_time,
        filters_applied=filters_applied
    )

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    field: str = Query(..., description="Field to get suggestions for"),
    prefix: str = Query("", description="Prefix to filter suggestions"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Get autocomplete suggestions for search fields"""
    suggestions = []
    
    if field == "medical_conditions":
        # Get all unique medical conditions
        all_conditions = db.query(func.jsonb_array_elements_text(Patient.medical_conditions)).distinct().all()
        conditions = [c[0] for c in all_conditions if c[0]]
        
        if prefix:
            conditions = [c for c in conditions if c.lower().startswith(prefix.lower())]
        
        suggestions = sorted(conditions)[:limit]
    
    elif field == "medications":
        # Get all unique medications
        all_meds = db.query(func.jsonb_array_elements_text(Patient.medications)).distinct().all()
        meds = [m[0] for m in all_meds if m[0]]
        
        if prefix:
            meds = [m for m in meds if m.lower().startswith(prefix.lower())]
        
        suggestions = sorted(meds)[:limit]
    
    elif field == "allergies":
        # Get all unique allergies
        all_allergies = db.query(func.jsonb_array_elements_text(Patient.allergies)).distinct().all()
        allergies = [a[0] for a in all_allergies if a[0]]
        
        if prefix:
            allergies = [a for a in allergies if a.lower().startswith(prefix.lower())]
        
        suggestions = sorted(allergies)[:limit]
    
    elif field == "cities":
        # Get unique cities from addresses
        cities = db.query(
            func.jsonb_extract_path_text(Patient.address, 'city')
        ).distinct().all()
        cities = [c[0] for c in cities if c[0]]
        
        if prefix:
            cities = [c for c in cities if c.lower().startswith(prefix.lower())]
        
        suggestions = sorted(cities)[:limit]
    
    return SuggestionsResponse(
        field=field,
        suggestions=suggestions,
        count=len(suggestions)
    )