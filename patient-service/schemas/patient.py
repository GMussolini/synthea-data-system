"""
Pydantic schemas for patient service
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum
import re

class Gender(str, Enum):
    """Gender enum"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

class Address(BaseModel):
    """Address schema"""
    street: str
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str
    state: str
    zip_code: str
    
    @validator('zip_code')
    def validate_zip_code(cls, v):
        if not re.match(r'^\d{5}-?\d{3}$', v):
            raise ValueError('CEP inválido')
        return v.replace('-', '')

class EmergencyContact(BaseModel):
    """Emergency contact schema"""
    name: str
    relationship: str
    phone: str
    email: Optional[EmailStr] = None

class InsuranceInfo(BaseModel):
    """Insurance information schema"""
    provider: str
    plan: str
    number: str
    validity: Optional[date] = None

class PatientBase(BaseModel):
    """Base patient schema"""
    name: str = Field(..., min_length=3, max_length=200)
    birth_date: date
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[Address] = None
    medical_conditions: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    emergency_contact: Optional[EmergencyContact] = None
    insurance_info: Optional[InsuranceInfo] = None
    notes: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone = re.sub(r'\D', '', v)
            if len(phone) < 10 or len(phone) > 11:
                raise ValueError('Telefone inválido')
            return phone
        return v

class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    cpf: str
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove non-numeric characters
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        # Basic CPF validation (simplified)
        if cpf == cpf[0] * 11:
            raise ValueError('CPF inválido')
        
        return cpf

class PatientUpdate(BaseModel):
    """Schema for updating a patient"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    birth_date: Optional[date] = None
    gender: Optional[Gender] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[Address] = None
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[EmergencyContact] = None
    insurance_info: Optional[InsuranceInfo] = None
    notes: Optional[str] = None

class PatientResponse(BaseModel):
    """Schema for patient response"""
    id: str
    name: str
    cpf: str
    birth_date: date
    gender: str
    age: int
    email: Optional[str]
    phone: Optional[str]
    address: Optional[Dict]
    medical_conditions: List[str]
    medications: List[str]
    allergies: List[str]
    emergency_contact: Optional[Dict]
    insurance_info: Optional[Dict]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def calculate_age(birth_date: date) -> int:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    @classmethod
    def from_orm_model(cls, patient):
        """Create response from ORM model"""
        return cls(
            id=str(patient.id),
            name=patient.name,
            cpf=patient.cpf,
            birth_date=patient.birth_date,
            gender=patient.gender,
            age=cls.calculate_age(patient.birth_date),
            email=patient.email,
            phone=patient.phone,
            address=patient.address,
            medical_conditions=patient.medical_conditions or [],
            medications=patient.medications or [],
            allergies=patient.allergies or [],
            emergency_contact=patient.emergency_contact,
            insurance_info=patient.insurance_info,
            notes=patient.notes,
            created_at=patient.created_at,
            updated_at=patient.updated_at
        )
    
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    """Schema for paginated response"""
    items: List[PatientResponse]
    total: int
    page: int
    size: int
    pages: int

class ImportResponse(BaseModel):
    """Schema for import response"""
    message: str
    imported: int
    errors: int
    error_details: List[str] = []

class StatsResponse(BaseModel):
    """Schema for statistics response"""
    total_patients: int
    age_distribution: Dict[str, int]
    gender_distribution: Dict[str, int]
    top_conditions: Dict[str, int]
    average_age: float