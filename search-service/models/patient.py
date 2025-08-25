"""
Patient model for search service (read-only mirror)
"""
from sqlalchemy import Column, String, Date, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from database import Base

class Patient(Base):
    """Patient model (read-only for search service)"""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(JSON, nullable=True)
    medical_conditions = Column(JSON, default=list)
    medications = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    emergency_contact = Column(JSON, nullable=True)
    insurance_info = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)