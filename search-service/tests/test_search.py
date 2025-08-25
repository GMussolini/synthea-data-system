"""
Tests for Search Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta
import sys
import os
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db
from models.patient import Patient

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_search.db"
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
def sample_patients():
    """Create sample patients in database"""
    db = TestingSessionLocal()
    patients = [
        Patient(
            id=uuid.uuid4(),
            name="João Silva",
            cpf="12345678901",
            birth_date=date(1990, 1, 1),
            gender="M",
            email="joao@example.com",
            phone="11999999999",
            address={"city": "São Paulo", "state": "SP"},
            medical_conditions=["Hipertensão", "Diabetes"],
            medications=["Losartana", "Metformina"],
            allergies=["Dipirona"]
        ),
        Patient(
            id=uuid.uuid4(),
            name="Maria Santos",
            cpf="98765432100",
            birth_date=date(1985, 5, 15),
            gender="F",
            email="maria@example.com",
            phone="21888888888",
            address={"city": "Rio de Janeiro", "state": "RJ"},
            medical_conditions=["Asma"],
            medications=["Salbutamol"],
            allergies=["Penicilina"]
        ),
        Patient(
            id=uuid.uuid4(),
            name="Pedro Oliveira",
            cpf="55555555555",
            birth_date=date(2000, 10, 20),
            gender="M",
            email="pedro@example.com",
            phone="31777777777",
            address={"city": "Belo Horizonte", "state": "MG"},
            medical_conditions=["Diabetes"],
            medications=["Insulina"],
            allergies=[]
        )
    ]
    
    for patient in patients:
        db.add(patient)
    db.commit()
    
    yield patients
    
    # Cleanup
    db.query(Patient).delete()
    db.commit()
    db.close()

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_search_by_name(self, sample_patients):
        """Test searching by patient name"""
        response = client.get("/search/patients?name=João")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "João Silva"
        assert "name" in data["filters_applied"]
    
    def test_search_by_cpf(self, sample_patients):
        """Test searching by CPF"""
        response = client.get("/search/patients?cpf=123456")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["cpf"] == "12345678901"
    
    def test_search_by_medical_condition(self, sample_patients):
        """Test searching by medical condition"""
        response = client.get("/search/patients?condition=Diabetes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # João and Pedro have Diabetes
        
        names = [r["name"] for r in data["results"]]
        assert "João Silva" in names
        assert "Pedro Oliveira" in names
    
    def test_search_by_medication(self, sample_patients):
        """Test searching by medication"""
        response = client.get("/search/patients?medication=Salbutamol")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "Maria Santos"
    
    def test_search_by_allergy(self, sample_patients):
        """Test searching by allergy"""
        response = client.get("/search/patients?allergy=Dipirona")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "João Silva"
    
    def test_search_by_city(self, sample_patients):
        """Test searching by city"""
        response = client.get("/search/patients?city=São Paulo")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "João Silva"
    
    def test_search_by_state(self, sample_patients):
        """Test searching by state"""
        response = client.get("/search/patients?state=RJ")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "Maria Santos"
    
    def test_search_by_gender(self, sample_patients):
        """Test searching by gender"""
        response = client.get("/search/patients?gender=F")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["name"] == "Maria Santos"
    
    def test_search_by_age_range(self, sample_patients):
        """Test searching by age range"""
        # Calculate ages for proper filtering
        response = client.get("/search/patients?age_min=20&age_max=30")
        assert response.status_code == 200
        data = response.json()
        # Pedro was born in 2000, so he should be in this range
        assert any(r["name"] == "Pedro Oliveira" for r in data["results"])
    
    def test_general_search(self, sample_patients):
        """Test general search across multiple fields"""
        response = client.get("/search/patients?q=maria")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(r["name"] == "Maria Santos" for r in data["results"])
    
    def test_combined_filters(self, sample_patients):
        """Test searching with multiple filters"""
        response = client.get("/search/patients?gender=M&condition=Diabetes")
        assert response.status_code == 200
        data = response.json()
        # João and Pedro are male with Diabetes
        assert data["total"] == 2
    
    def test_pagination(self, sample_patients):
        """Test pagination in search results"""
        response = client.get("/search/patients?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2
        
        # Second page
        response2 = client.get("/search/patients?page=2&size=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["results"]) <= 2
    
    def test_sorting(self, sample_patients):
        """Test sorting search results"""
        # Sort by name ascending
        response = client.get("/search/patients?sort_by=name&order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [r["name"] for r in data["results"]]
        assert names == sorted(names)
        
        # Sort by name descending
        response = client.get("/search/patients?sort_by=name&order=desc")
        assert response.status_code == 200
        data = response.json()
        names = [r["name"] for r in data["results"]]
        assert names == sorted(names, reverse=True)
    
    def test_empty_search(self):
        """Test search with no results"""
        response = client.get("/search/patients?name=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["results"]) == 0
    
    def test_search_response_time(self, sample_patients):
        """Test that search response includes query time"""
        response = client.get("/search/patients?name=João")
        assert response.status_code == 200
        data = response.json()
        assert "query_time_ms" in data
        assert data["query_time_ms"] >= 0

class TestSuggestionsEndpoint:
    """Test autocomplete suggestions"""
    
    def test_medical_conditions_suggestions(self, sample_patients):
        """Test getting medical condition suggestions"""
        response = client.get("/search/suggestions?field=medical_conditions")
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "medical_conditions"
        assert "Diabetes" in data["suggestions"]
        assert "Hipertensão" in data["suggestions"]
        assert "Asma" in data["suggestions"]
    
    def test_medications_suggestions(self, sample_patients):
        """Test getting medication suggestions"""
        response = client.get("/search/suggestions?field=medications")
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "medications"
        assert "Losartana" in data["suggestions"]
        assert "Metformina" in data["suggestions"]
        assert "Salbutamol" in data["suggestions"]
    
    def test_allergies_suggestions(self, sample_patients):
        """Test getting allergy suggestions"""
        response = client.get("/search/suggestions?field=allergies")
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "allergies"
        assert "Dipirona" in data["suggestions"]
        assert "Penicilina" in data["suggestions"]
    
    def test_cities_suggestions(self, sample_patients):
        """Test getting city suggestions"""
        response = client.get("/search/suggestions?field=cities")
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "cities"
        assert "São Paulo" in data["suggestions"]
        assert "Rio de Janeiro" in data["suggestions"]
        assert "Belo Horizonte" in data["suggestions"]
    
    def test_suggestions_with_prefix(self, sample_patients):
        """Test suggestions with prefix filtering"""
        response = client.get("/search/suggestions?field=medical_conditions&prefix=Dia")
        assert response.status_code == 200
        data = response.json()
        assert "Diabetes" in data["suggestions"]
        assert "Hipertensão" not in data["suggestions"]
    
    def test_suggestions_limit(self, sample_patients):
        """Test suggestions limit"""
        response = client.get("/search/suggestions?field=medical_conditions&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 2

class TestSearchScoring:
    """Test search relevance scoring"""
    
    def test_exact_match_higher_score(self, sample_patients):
        """Test that exact matches get higher scores"""
        # Create a patient with exact name match
        db = TestingSessionLocal()
        exact_patient = Patient(
            id=uuid.uuid4(),
            name="Silva",
            cpf="11111111111",
            birth_date=date(1990, 1, 1),
            gender="M"
        )
        db.add(exact_patient)
        db.commit()
        
        response = client.get("/search/patients?name=Silva")
        assert response.status_code == 200
        data = response.json()
        
        # The exact match should have higher score
        results = sorted(data["results"], key=lambda x: x["match_score"], reverse=True)
        assert results[0]["name"] == "Silva"
        
        db.query(Patient).filter(Patient.cpf == "11111111111").delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])