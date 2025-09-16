# initialize_database.py

from app import app, db
import models  # Import all models to ensure they are registered

def initialize_database():
    """Initialize the database by creating all tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    initialize_database()