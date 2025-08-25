"""
Tests for Patient Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patient_service.main import app, get_db, Base, Patient

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def sample_patient():
    return {
        "name": "João Silva",
        "cpf": "12345678901",
        "birth_date": "1990-01-01",
        "gender": "M",
        "email": "joao@example.com",
        "phone": "11999999999",
        "address": {
            "street": "Rua Teste",
            "number": "123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01234-567"
        },
        "medical_conditions": ["Hipertensão", "Diabetes"],
        "medications": ["Losartana", "Metformina"],
        "allergies": ["Dipirona"]
    }

class TestPatientEndpoints:
    """Test patient CRUD operations"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_create_patient(self, sample_patient):
        """Test creating a new patient"""
        response = client.post("/patients", json=sample_patient)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_patient["name"]
        assert data["cpf"] == sample_patient["cpf"]
        assert "id" in data
        return data["id"]
    
    def test_get_patient(self, sample_patient):
        """Test getting a patient by ID"""
        # First create a patient
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        # Then get the patient
        response = client.get(f"/patients/{patient_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["name"] == sample_patient["name"]
    
    def test_get_nonexistent_patient(self):
        """Test getting a patient that doesn't exist"""
        response = client.get("/patients/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_list_patients(self, sample_patient):
        """Test listing patients with pagination"""
        # Create multiple patients
        for i in range(5):
            patient = sample_patient.copy()
            patient["cpf"] = f"9876543210{i}"
            patient["name"] = f"Patient {i}"
            client.post("/patients", json=patient)
        
        # List patients
        response = client.get("/patients?page=1&size=3")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 3
    
    def test_update_patient(self, sample_patient):
        """Test updating patient information"""
        # Create patient
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        # Update patient
        update_data = {
            "name": "João Silva Santos",
            "phone": "11888888888"
        }
        response = client.put(f"/patients/{patient_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "João Silva Santos"
        assert data["phone"] == "11888888888"
    
    def test_delete_patient(self, sample_patient):
        """Test deleting a patient"""
        # Create patient
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        # Delete patient
        response = client.delete(f"/patients/{patient_id}")
        assert response.status_code == 204
        
        # Verify patient is deleted
        get_response = client.get(f"/patients/{patient_id}")
        assert get_response.status_code == 404
    
    def test_patient_validation(self):
        """Test patient data validation"""
        invalid_patient = {
            "name": "Jo",  # Too short
            "cpf": "123",  # Invalid CPF
            "birth_date": "invalid-date",
            "gender": "X",  # Invalid gender
            "email": "invalid-email"
        }
        response = client.post("/patients", json=invalid_patient)
        assert response.status_code == 422
    
    def test_duplicate_cpf(self, sample_patient):
        """Test that duplicate CPF is not allowed"""
        # Create first patient
        response1 = client.post("/patients", json=sample_patient)
        assert response1.status_code == 201
        
        # Try to create another with same CPF
        response2 = client.post("/patients", json=sample_patient)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

class TestPatientStats:
    """Test patient statistics endpoints"""
    
    def test_get_stats(self, sample_patient):
        """Test getting patient statistics"""
        # Create some patients
        for i in range(3):
            patient = sample_patient.copy()
            patient["cpf"] = f"1111111111{i}"
            client.post("/patients", json=patient)
        
        response = client.get("/patients/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_patients" in data
        assert "age_distribution" in data
        assert "gender_distribution" in data
        assert "top_conditions" in data

class TestPatientImport:
    """Test patient import functionality"""
    
    def test_import_json(self):
        """Test importing patients from JSON"""
        import_data = [
            {
                "name": "Maria Santos",
                "cpf": "22222222222",
                "birth_date": "1985-05-15",
                "gender": "F",
                "email": "maria@example.com",
                "medical_conditions": ["Asma"],
                "medications": ["Salbutamol"]
            },
            {
                "name": "Pedro Oliveira",
                "cpf": "33333333333",
                "birth_date": "1975-10-20",
                "gender": "M",
                "email": "pedro@example.com",
                "medical_conditions": ["Hipertensão"],
                "medications": ["Enalapril"]
            }
        ]
        
        import json
        import io
        
        json_file = io.BytesIO(json.dumps(import_data).encode())
        
        response = client.post(
            "/patients/import",
            files={"file": ("patients.json", json_file, "application/json")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])