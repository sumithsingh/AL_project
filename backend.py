import logging
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Request, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from chatbot import FreeMedicalChatbot
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator
from email_validator import validate_email, EmailNotValidError
import os
from PIL import Image
import numpy as np
import io
from dotenv import load_dotenv
from model_handler import ModelHandler


# Load environment variables
load_dotenv()

# App Configuration
class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/blood_cancer_db")

settings = Settings()

# FastAPI app setup
app = FastAPI(
    title="Blood Cancer Detection API",
    description="Backend API for blood cancer detection system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize ML model handler
router = APIRouter()
model_handler = ModelHandler()

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "doctor" or "patient"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")  # Add this line here
    # Patient appointments
    patient_appointments = relationship(
        "Appointment",
        back_populates="patient",
        foreign_keys="Appointment.patient_id"
    )
    # Doctor appointments
    doctor_appointments = relationship(
        "Appointment",
        back_populates="doctor",
        foreign_keys="Appointment.doctor_id"
    )

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    results = Column(JSON)
    risk_level = Column(String)
    doctor_notes = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analyses")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    status = Column(String)  # "scheduled", "completed", "cancelled"
    notes = Column(String, nullable=True)
    
    # Relationships with explicit foreign keys
    patient = relationship(
        "User",
        back_populates="patient_appointments",
        foreign_keys=[patient_id]
    )
    doctor = relationship(
        "User",
        back_populates="doctor_appointments",
        foreign_keys=[doctor_id]
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserBase(BaseModel):
    username: str
    email: str
    role: str

    @validator('email')
    def validate_email(cls, v):
        try:
            validate_email(v)
            return v
        except EmailNotValidError:
            raise ValueError('Invalid email address')
    
    @validator('role')
    def validate_role(cls, v):
        if v.lower() not in ['doctor', 'patient']:
            raise ValueError('Role must be either doctor or patient')
        return v.lower()

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
        
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="chat_logs")

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

class AnalysisCreate(BaseModel):
    results: dict
    risk_level: str
    doctor_notes: Optional[str] = None

class AnalysisResponse(AnalysisCreate):
    id: int
    user_id: int
    date: datetime

    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    doctor_id: int
    date: datetime
    notes: Optional[str] = None

class AppointmentResponse(AppointmentCreate):
    id: int
    patient_id: int
    status: str

    class Config:
        from_attributes = True

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check existing username
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check existing email
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        role=user.role,
        hashed_password=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }


@app.post("/analyze-batch")
async def analyze_batch(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes multiple images in a single batch,
    aggregates the cell counts, computes a single risk level,
    and returns one final analysis result.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # 1) Initialize accumulators
        total_cell_counts = {
            "monocyte": 0.0,
            "myeloblast": 0.0,
            "erythroblast": 0.0,
            "segmented_neutrophil": 0.0,
            "basophil": 0.0
        }
        num_images = len(files)

        # 2) Process each image
        for file in files:
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not an image"
                )

            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))

            processed_image = model_handler.preprocess_image(image)
            predictions = model_handler.get_predictions(processed_image)

            # Convert predictions -> cell_counts
            cell_counts = {
                cell: float(prob * 100)
                for cell, prob in zip(model_handler.classes, predictions)
            }
            # Accumulate
            for cell, val in cell_counts.items():
                total_cell_counts[cell] += val

        # 3) Average the cell counts across all images
        for cell in total_cell_counts:
            total_cell_counts[cell] /= num_images

        # 4) Determine final risk based on aggregated myeloblast, etc.
        aggregated_myeloblast = total_cell_counts["myeloblast"]
        aggregated_erythroblast = total_cell_counts["erythroblast"]

        if aggregated_myeloblast > 20 or aggregated_erythroblast > 10:
            risk_level = "High"
            risk_message = "Immediate medical attention required"
        elif aggregated_myeloblast > 10 or aggregated_erythroblast > 5:
            risk_level = "Moderate"
            risk_message = "Further evaluation recommended"
        else:
            risk_level = "Low"
            risk_message = "Regular monitoring advised"

        # 5) Generate recommendations
        recommendations = model_handler.generate_recommendations(risk_level)

        final_analysis_data = {
            "cell_counts": total_cell_counts,
            "risk_assessment": f"{risk_level} - {risk_message}",
            "recommendations": recommendations,
            "details": {
                "analysis_date": datetime.utcnow().isoformat(),
                # confidence_score might not make sense aggregated,
                # but you can do an average if you want
                "confidence_score": 0.0
            }
        }

        # 6) Create one Analysis entry for entire batch
        analysis = Analysis(
            user_id=current_user.id,
            results=final_analysis_data,
            risk_level=risk_level,
            date=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        # Return final aggregated analysis
        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "date": analysis.date.isoformat(),
            "risk_level": analysis.risk_level,
            "results": analysis.results
        }

    except Exception as e:
        logging.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail="Batch image processing error")
    
global_chatbot = FreeMedicalChatbot()

@app.get("/reports", response_model=List[AnalysisResponse])
async def get_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches all blood cancer analysis reports for the logged-in user.
    """
    try:
        # Retrieve all reports for the logged-in user
        reports = db.query(Analysis).filter(Analysis.user_id == current_user.id).order_by(Analysis.date.desc()).all()

        if not reports:
            logging.warning("⚠ No reports found for user!")
            return []
        formatted_reports = []

        for report in reports:
            formatted_reports.append(
                {
                    "id": report.id,
                    "user_id": report.user_id,
                    "date": report.date.isoformat(),
                    "risk_level": report.risk_level,
                    "results": report.results,
                    "doctor_notes": report.doctor_notes if report.doctor_notes else "No notes available",
                }
            )

        logging.info(f"📊 {len(reports)} reports fetched from the database")
        return reports

    except Exception as e:
        logging.error(f"❌ Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports.")


@app.post("/chat")
async def chat(
    message: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        response = global_chatbot.get_response(
            query=message["text"],
            language=message.get("language", "English")
        )
        
        # Log chat with user context
        chat_log = ChatLog(
            user_id=current_user.id,
            message=message["text"],
            response=response["response"],
            timestamp=datetime.utcnow()
        )
        db.add(chat_log)
        db.commit()
        
        return response
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/patients", response_model=List[UserResponse])
async def get_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(User).filter(User.role == "patient").all()

@app.get("/patient/{patient_id}/history", response_model=List[AnalysisResponse])
async def get_patient_history(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "doctor" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(Analysis).filter(Analysis.user_id == patient_id).all()

@app.post("/appointment", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify doctor exists and is active
    doctor = db.query(User).filter(
        User.id == appointment.doctor_id,
        User.role == "doctor",
        User.is_active == True
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Create appointment
    db_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=appointment.doctor_id,
        date=appointment.date,
        status="scheduled",
        notes=appointment.notes
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment

@app.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "doctor":
        return db.query(Appointment).filter(Appointment.doctor_id == current_user.id).all()
    else:
        return db.query(Appointment).filter(Appointment.patient_id == current_user.id).all()

@app.get("/doctors")
async def get_doctors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a list of doctors (users with role='doctor').
    """
    try:
        # Optionally, you can restrict to only patients
        if current_user.role != "patient":
            raise HTTPException(status_code=403, detail="Not authorized to view doctors")

        doctors = db.query(User).filter(User.role == "doctor", User.is_active == True).all()
        return [{"id": doc.id, "username": doc.username} for doc in doctors]
    except Exception as e:
        logging.error(f"Error fetching doctors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve doctors.")


@app.get("/active-patients", response_model=List[UserResponse])
async def get_active_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return (
        db.query(User)
        .join(Analysis)
        .filter(User.role == "patient")
        .filter(Analysis.risk_level.contains("High"))
        .distinct()
        .all()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)