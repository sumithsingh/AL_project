from backend import User, SessionLocal, get_password_hash

def create_test_user():
    db = SessionLocal()
    
    # Create a doctor user
    doctor = User(
        username="doctor",
        email="doctor@example.com",
        hashed_password=get_password_hash("doctor123"),
        role="doctor",
        is_active=True
    )
    
    try:
        db.add(doctor)
        db.commit()
        print("Test user created successfully!")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()