# create_users.py
from backend import SessionLocal, User, get_password_hash
from sqlalchemy import create_engine, MetaData

def create_test_users():
    db = SessionLocal()
    try:
        # First, clear existing users (optional, remove if you want to keep existing users)
        db.query(User).delete()
        db.commit()
        
        # Create test users
        test_users = [
            {
                "username": "doctor",
                "email": "doctor@example.com",
                "password": "doctor123",
                "role": "doctor"
            },
            {
                "username": "patient",
                "email": "patient@example.com",
                "password": "patient123",
                "role": "patient"
            }
        ]

        for user_data in test_users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=True
            )
            db.add(user)
        
        db.commit()
        
        # Verify users were created
        users = db.query(User).all()
        print("\nCreated users:")
        for user in users:
            print(f"Username: {user.username}, Role: {user.role}")
        
        print("\nTest credentials:")
        print("Doctor - username: doctor, password: doctor123")
        print("Patient - username: patient, password: patient123")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()