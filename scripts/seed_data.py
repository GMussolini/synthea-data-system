"""
Script to seed the database with sample patient data
"""
import sys
import os

# Add parent directory to path to import from patient-service modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from datetime import datetime, date, timedelta
import random
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Date, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/patient_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models locally since we're running this script independently
class Patient(Base):
    """Patient model"""
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

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize Faker for Brazilian Portuguese
fake = Faker('pt_BR')

# Medical data
MEDICAL_CONDITIONS = [
    "Hipertensão", "Diabetes Tipo 2", "Asma", "Artrite", "Depressão",
    "Ansiedade", "Obesidade", "Hipotireoidismo", "Dislipidemia", "DPOC",
    "Insuficiência Cardíaca", "Arritmia", "Gastrite", "Refluxo", "Enxaqueca",
    "Fibromialgia", "Osteoporose", "Anemia", "Sinusite Crônica", "Apneia do Sono"
]

MEDICATIONS = [
    "Losartana", "Metformina", "Omeprazol", "Sinvastatina", "Levotiroxina",
    "Atenolol", "Captopril", "Enalapril", "Insulina", "Salbutamol",
    "Fluoxetina", "Sertralina", "Rivotril", "Dipirona", "Paracetamol",
    "Ibuprofeno", "Amoxicilina", "Azitromicina", "Prednisona", "Dexametasona"
]

ALLERGIES = [
    "Dipirona", "Penicilina", "Ibuprofeno", "Ácido Acetilsalicílico", "Sulfa",
    "Látex", "Iodo", "Frutos do Mar", "Amendoim", "Leite",
    "Glúten", "Ovo", "Soja", "Pólen", "Ácaros"
]

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def generate_cpf():
    """Generate a valid-looking CPF (for testing only)"""
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])

def generate_phone():
    """Generate a Brazilian phone number"""
    ddd = random.choice(['11', '21', '31', '41', '51', '61', '71', '81', '91'])
    prefix = random.choice(['9', '8'])
    return f"{ddd}9{prefix}{random.randint(1000000, 9999999)}"

def create_sample_patients(n=50):
    """Create n sample patients"""
    db = SessionLocal()
    patients_created = 0
    
    print(f"Creating {n} sample patients...")
    
    for i in range(n):
        try:
            # Generate basic info
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                first_name = fake.first_name_male()
            else:
                first_name = fake.first_name_female()
            
            last_name = fake.last_name()
            full_name = f"{first_name} {last_name}"
            
            # Generate birth date (ages between 18 and 90)
            age = random.randint(18, 90)
            birth_date = date.today() - timedelta(days=age*365 + random.randint(0, 364))
            
            # Generate contact info
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
            phone = generate_phone()
            
            # Generate address
            address = {
                "street": fake.street_name(),
                "number": str(random.randint(1, 9999)),
                "complement": random.choice(["", "Apto 101", "Casa 2", "Bloco B"]),
                "neighborhood": fake.bairro(),
                "city": fake.city(),
                "state": fake.estado_sigla(),
                "zip_code": fake.postcode().replace('-', '')
            }
            
            # Generate medical info
            num_conditions = random.randint(0, 4)
            medical_conditions = random.sample(MEDICAL_CONDITIONS, min(num_conditions, len(MEDICAL_CONDITIONS)))
            
            num_medications = random.randint(0, 5)
            medications = random.sample(MEDICATIONS, min(num_medications, len(MEDICATIONS)))
            
            num_allergies = random.randint(0, 3)
            allergies = random.sample(ALLERGIES, min(num_allergies, len(ALLERGIES)))
            
            # Generate emergency contact
            emergency_contact = {
                "name": fake.name(),
                "relationship": random.choice(["Cônjuge", "Filho(a)", "Pai/Mãe", "Irmão(ã)", "Amigo(a)"]),
                "phone": generate_phone(),
                "email": fake.email()
            }
            
            # Generate insurance info (70% chance of having insurance)
            insurance_info = None
            if random.random() < 0.7:
                insurance_info = {
                    "provider": random.choice(["Unimed", "Amil", "SulAmérica", "Bradesco Saúde", "Porto Seguro", "SUS"]),
                    "plan": random.choice(["Básico", "Standard", "Premium", "Gold", "Platinum"]),
                    "number": str(random.randint(100000000, 999999999)),
                    "validity": (date.today() + timedelta(days=random.randint(30, 730))).isoformat()
                }
            
            # Create patient
            patient = Patient(
                id=uuid.uuid4(),
                name=full_name,
                cpf=generate_cpf(),
                birth_date=birth_date,
                gender=gender,
                email=email,
                phone=phone,
                address=address,
                medical_conditions=medical_conditions,
                medications=medications,
                allergies=allergies,
                emergency_contact=emergency_contact,
                insurance_info=insurance_info,
                notes=fake.text(max_nb_chars=200) if random.random() < 0.3 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                updated_at=datetime.utcnow()
            )
            
            db.add(patient)
            patients_created += 1
            
            if (i + 1) % 10 == 0:
                db.commit()
                print(f"Created {i + 1} patients...")
                
        except Exception as e:
            print(f"Error creating patient {i}: {e}")
            db.rollback()
            continue
    
    db.commit()
    db.close()
    
    print(f"Successfully created {patients_created} patients!")
    return patients_created

def create_test_users():
    """Create test users for authentication"""
    db = SessionLocal()
    
    test_users = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "Administrator",
            "password": "admin123",
            "is_admin": True
        },
        {
            "email": "user@example.com",
            "username": "user",
            "full_name": "Test User",
            "password": "user123",
            "is_admin": False
        },
        {
            "email": "doctor@example.com",
            "username": "doctor",
            "full_name": "Dr. Test",
            "password": "doctor123",
            "is_admin": False
        }
    ]
    
    print("Creating test users...")
    
    for user_data in test_users:
        try:
            # Check if user already exists
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if existing:
                print(f"User {user_data['username']} already exists, skipping...")
                continue
            
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                username=user_data["username"],
                full_name=user_data["full_name"],
                hashed_password=get_password_hash(user_data["password"]),
                is_admin=user_data["is_admin"],
                is_active=True
            )
            
            db.add(user)
            print(f"Created user: {user_data['username']}")
            
        except Exception as e:
            print(f"Error creating user {user_data['username']}: {e}")
            db.rollback()
            continue
    
    db.commit()
    db.close()
    
    print("Test users created successfully!")
    print("\nYou can now login with:")
    for user in test_users:
        print(f"  Username: {user['username']}, Password: {user['password']}")

def export_sample_data():
    """Export sample data to JSON file for import testing"""
    db = SessionLocal()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get first 10 patients
    patients = db.query(Patient).limit(10).all()
    
    export_data = []
    for patient in patients:
        export_data.append({
            "name": patient.name,
            "cpf": patient.cpf,
            "birth_date": patient.birth_date.isoformat(),
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone,
            "address": patient.address,
            "medical_conditions": patient.medical_conditions,
            "medications": patient.medications,
            "allergies": patient.allergies
        })
    
    # Save to file
    with open('data/sample_patients.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    db.close()
    print(f"Exported {len(export_data)} patients to data/sample_patients.json")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument("--patients", type=int, default=50, help="Number of patients to create")
    parser.add_argument("--users", action="store_true", help="Create test users")
    parser.add_argument("--export", action="store_true", help="Export sample data to JSON")
    parser.add_argument("--all", action="store_true", help="Do everything")
    
    args = parser.parse_args()
    
    if args.all or args.users:
        create_test_users()
    
    if args.all or args.patients > 0:
        create_sample_patients(args.patients)
    
    if args.all or args.export:
        export_sample_data()
    
    if not any([args.all, args.users, args.patients > 0, args.export]):
        print("No action specified. Use --help for options.")
        print("Example: python seed_data.py --all")