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

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        processed_image = model_handler.preprocess_image(image)
        predictions = model_handler.get_predictions(processed_image)

        risk_level, risk_message = model_handler.assess_risk(predictions)
        recommendations = model_handler.generate_recommendations(risk_level)

        analysis_data = {
            "cell_counts": {cell: float(pred * 100) for cell, pred in zip(model_handler.classes, predictions)},
            "risk_assessment": risk_message if risk_message else "Unknown",
            "recommendations": recommendations if recommendations else ["No recommendations available"],
            "details": {
                "myeloblast_percentage": float(predictions[model_handler.classes.index('myeloblast')] * 100),
                "analysis_date": datetime.utcnow().isoformat(),
                "confidence_score": float(np.max(predictions) * 100)
            }
        }

        analysis = Analysis(
            user_id=current_user.id,
            results=analysis_data,
            risk_level=risk_level,
            date=datetime.utcnow()
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "date": analysis.date.isoformat(),
            "results": analysis.results,
            "risk_level": analysis.risk_level
        }

    except Exception as e:
        logging.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Image processing error")
    
global_chatbot = FreeMedicalChatbot()

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