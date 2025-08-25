"""
Patient routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
import uuid
import logging
from datetime import datetime

from database import get_db
from models.patient import Patient
from schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    PaginatedResponse, ImportResponse, StatsResponse
)
from utils.auth import verify_token

# Logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)

@router.get("", response_model=PaginatedResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """List all patients with pagination"""
    offset = (page - 1) * size
    
    query = db.query(Patient)
    total = query.count()
    patients = query.offset(offset).limit(size).all()
    
    return PaginatedResponse(
        items=[PatientResponse.from_orm_model(p) for p in patients],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

@router.get("/stats/summary", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Get patient statistics"""
    total = db.query(Patient).count()
    
    # Get all patients for statistics
    patients = db.query(Patient).all()
    
    if not patients:
        return StatsResponse(
            total_patients=0,
            age_distribution={},
            gender_distribution={},
            top_conditions={},
            average_age=0
        )
    
    # Age distribution
    ages = [PatientResponse.calculate_age(p.birth_date) for p in patients]
    
    age_groups = {
        "0-18": sum(1 for a in ages if a <= 18),
        "19-30": sum(1 for a in ages if 19 <= a <= 30),
        "31-50": sum(1 for a in ages if 31 <= a <= 50),
        "51-70": sum(1 for a in ages if 51 <= a <= 70),
        "70+": sum(1 for a in ages if a > 70)
    }
    
    # Gender distribution
    gender_dist = {
        "M": db.query(Patient).filter(Patient.gender == "M").count(),
        "F": db.query(Patient).filter(Patient.gender == "F").count(),
        "O": db.query(Patient).filter(Patient.gender == "O").count()
    }
    
    # Common conditions
    all_conditions = []
    for p in patients:
        if p.medical_conditions:
            all_conditions.extend(p.medical_conditions)
    
    condition_counts = {}
    for condition in all_conditions:
        condition_counts[condition] = condition_counts.get(condition, 0) + 1
    
    top_conditions = dict(sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return StatsResponse(
        total_patients=total,
        age_distribution=age_groups,
        gender_distribution=gender_dist,
        top_conditions=top_conditions,
        average_age=sum(ages) / len(ages) if ages else 0
    )

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return PatientResponse.from_orm_model(patient)

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Create a new patient"""
    # Check if CPF already exists
    existing = db.query(Patient).filter(Patient.cpf == patient.cpf).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF already registered"
        )
    
    # Prepare data
    patient_data = patient.dict()
    
    # Convert nested models to dict
    if patient.address:
        patient_data['address'] = patient.address.dict()
    if patient.emergency_contact:
        patient_data['emergency_contact'] = patient.emergency_contact.dict()
    if patient.insurance_info:
        patient_data['insurance_info'] = patient.insurance_info.dict()
    
    # Convert gender enum to string
    patient_data['gender'] = patient.gender.value
    
    # Create patient
    db_patient = Patient(**patient_data)
    # db_patient.created_by = auth.get("username")
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    logger.info(f"Patient created: {db_patient.id}")
    
    return PatientResponse.from_orm_model(db_patient)

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    update_data = patient_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "address" and value:
            value = value.dict()
        elif field == "emergency_contact" and value:
            value = value.dict()
        elif field == "insurance_info" and value:
            value = value.dict()
        elif field == "gender" and value:
            value = value.value
        
        setattr(patient, field, value)
    
    patient.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(patient)
    
    logger.info(f"Patient updated: {patient_id}")
    
    return PatientResponse.from_orm_model(patient)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Delete a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    db.delete(patient)
    db.commit()
    
    logger.info(f"Patient deleted: {patient_id}")
    
    return None

@router.post("/import", response_model=ImportResponse)
async def import_patients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # auth: dict = Depends(verify_token)
):
    """Import patients from JSON file"""
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported"
        )
    
    content = await file.read()
    
    try:
        data = json.loads(content)
        
        # Handle both array and object with 'entry' field (Synthea format)
        if isinstance(data, dict) and 'entry' in data:
            patients_data = data['entry']
        elif isinstance(data, list):
            patients_data = data
        else:
            raise ValueError("Invalid JSON format")
        
        imported_count = 0
        errors = []
        
        for item in patients_data:
            try:
                # Extract patient data (adapt based on format)
                if 'resource' in item:  # Synthea FHIR format
                    resource = item['resource']
                    patient_data = {
                        'name': f"{resource.get('name', [{}])[0].get('given', [''])[0]} {resource.get('name', [{}])[0].get('family', '')}".strip(),
                        'cpf': resource.get('identifier', [{}])[0].get('value', str(uuid.uuid4())[:11]),
                        'birth_date': resource.get('birthDate', '2000-01-01'),
                        'gender': resource.get('gender', 'other')[0].upper(),
                        'email': f"{resource.get('id', uuid.uuid4())}@example.com",
                        'phone': resource.get('telecom', [{}])[0].get('value', '11999999999'),
                    }
                else:  # Custom format
                    patient_data = item
                
                # Validate and create patient
                patient_create = PatientCreate(**patient_data)
                
                # Check if CPF already exists
                existing = db.query(Patient).filter(Patient.cpf == patient_create.cpf).first()
                if not existing:
                    # Prepare data
                    db_patient_data = patient_create.dict()
                    
                    # Convert nested models
                    if patient_create.address:
                        db_patient_data['address'] = patient_create.address.dict()
                    if patient_create.emergency_contact:
                        db_patient_data['emergency_contact'] = patient_create.emergency_contact.dict()
                    if patient_create.insurance_info:
                        db_patient_data['insurance_info'] = patient_create.insurance_info.dict()
                    
                    # Convert gender
                    db_patient_data['gender'] = patient_create.gender.value
                    
                    db_patient = Patient(**db_patient_data)
                    # db_patient.created_by = auth.get("username")
                    
                    db.add(db_patient)
                    imported_count += 1
                
            except Exception as e:
                errors.append(str(e))
                continue
        
        db.commit()
        
        return ImportResponse(
            message="Import completed",
            imported=imported_count,
            errors=len(errors),
            error_details=errors[:10] if errors else []
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )