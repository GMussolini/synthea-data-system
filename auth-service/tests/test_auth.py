"""
Tests for Patient Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
import sys
import os
import json
import io


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patients.db"
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

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

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
        assert data["age"] >= 0
        return data["id"]
    
    def test_get_patient(self, sample_patient):
        """Test getting a patient by ID"""
        
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        
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
        
        for i in range(5):
            patient = sample_patient.copy()
            patient["cpf"] = f"9876543210{i}"
            patient["name"] = f"Patient {i}"
            client.post("/patients", json=patient)
        
        
        response = client.get("/patients?page=1&size=3")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 3
        assert data["total"] == 5
    
    def test_update_patient(self, sample_patient):
        """Test updating patient information"""
        
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        
        update_data = {
            "name": "João Silva Santos",
            "phone": "11888888888"
        }
        response = client.put(f"/patients/{patient_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "João Silva Santos"
        assert data["phone"] == "11888888888"
        
        assert data["cpf"] == sample_patient["cpf"]
    
    def test_delete_patient(self, sample_patient):
        """Test deleting a patient"""
        
        create_response = client.post("/patients", json=sample_patient)
        patient_id = create_response.json()["id"]
        
        
        response = client.delete(f"/patients/{patient_id}")
        assert response.status_code == 204
        
        
        get_response = client.get(f"/patients/{patient_id}")
        assert get_response.status_code == 404
    
    def test_patient_validation(self):
        """Test patient data validation"""
        invalid_patient = {
            "name": "Jo",  
            "cpf": "123",  
            "birth_date": "invalid-date",
            "gender": "X",  
            "email": "invalid-email"
        }
        response = client.post("/patients", json=invalid_patient)
        assert response.status_code == 422
    
    def test_duplicate_cpf(self, sample_patient):
        """Test that duplicate CPF is not allowed"""
        
        response1 = client.post("/patients", json=sample_patient)
        assert response1.status_code == 201
        
        
        response2 = client.post("/patients", json=sample_patient)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_cpf_validation(self):
        """Test CPF validation"""
        patient = {
            "name": "Test Patient",
            "cpf": "111.111.111-11",  
            "birth_date": "1990-01-01",
            "gender": "M"
        }
        response = client.post("/patients", json=patient)
        assert response.status_code == 422  
    
    def test_phone_validation(self, sample_patient):
        """Test phone number validation"""
        
        patient = sample_patient.copy()
        patient["cpf"] = "98765432100"
        patient["phone"] = "(11) 98765-4321"
        response = client.post("/patients", json=patient)
        assert response.status_code == 201
        assert response.json()["phone"] == "11987654321"
    
    def test_zip_code_validation(self, sample_patient):
        """Test ZIP code validation"""
        patient = sample_patient.copy()
        patient["cpf"] = "55555555555"
        patient["address"]["zip_code"] = "12345-678"
        response = client.post("/patients", json=patient)
        assert response.status_code == 201
        assert response.json()["address"]["zip_code"] == "12345678"

class TestPatientStats:
    """Test patient statistics endpoints"""
    
    def test_get_stats_empty(self):
        """Test getting stats with no patients"""
        response = client.get("/patients/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_patients"] == 0
        assert data["average_age"] == 0
    
    def test_get_stats(self, sample_patient):
        """Test getting patient statistics"""
        
        for i in range(3):
            patient = sample_patient.copy()
            patient["cpf"] = f"1111111111{i}"
            client.post("/patients", json=patient)
        
        response = client.get("/patients/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_patients"] == 3
        assert "age_distribution" in data
        assert "gender_distribution" in data
        assert data["gender_distribution"]["M"] == 3
        assert "top_conditions" in data
        assert "Hipertensão" in data["top_conditions"]
        assert data["average_age"] > 0

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
        
        json_file = io.BytesIO(json.dumps(import_data).encode())
        
        response = client.post(
            "/patients/import",
            files={"file": ("patients.json", json_file, "application/json")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2
        assert data["errors"] == 0
    
    def test_import_invalid_file(self):
        """Test importing non-JSON file"""
        text_file = io.BytesIO(b"This is not JSON")
        
        response = client.post(
            "/patients/import",
            files={"file": ("patients.txt", text_file, "text/plain")}
        )
        assert response.status_code == 400
        assert "Only JSON files are supported" in response.json()["detail"]
    
    def test_import_with_errors(self):
        """Test importing with some invalid data"""
        import_data = [
            {
                "name": "Valid Patient",
                "cpf": "44444444444",
                "birth_date": "1990-01-01",
                "gender": "M"
            },
            {
                "name": "In",  
                "cpf": "555",  
                "birth_date": "invalid",
                "gender": "X"
            }
        ]
        
        json_file = io.BytesIO(json.dumps(import_data).encode())
        
        response = client.post(
            "/patients/import",
            files={"file": ("patients.json", json_file, "application/json")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1
        assert data["errors"] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])