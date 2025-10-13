import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Profile, StudentProfile, PIProfile, IndustryProfile, VendorProfile

def create_demo_users():
    """Create demo users with different roles"""
    with app.app_context():
        print("Creating demo users...")

        # Create a student user
        student = User(
            email="student@example.com",
            user_type="Student",
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        student.password_hash = generate_password_hash("password123")

        # Create a PI user
        pi = User(
            email="pi@example.com",
            user_type="PI",
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        pi.password_hash = generate_password_hash("password123")

        # Create an Industry user
        industry = User(
            email="industry@example.com",
            user_type="Industry",
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        industry.password_hash = generate_password_hash("password123")

        # Create a Vendor user
        vendor = User(
            email="vendor@example.com",
            user_type="Vendor",
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        vendor.password_hash = generate_password_hash("password123")

        # Create an admin user
        admin = User(
            email="admin@example.com",
            user_type="Admin",
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        admin.password_hash = generate_password_hash("admin123")

        # Add the users
        db.session.add(student)
        db.session.add(pi)
        db.session.add(industry)
        db.session.add(vendor)
        db.session.add(admin)

        try:
            db.session.commit()
            print("Users created successfully!")

            # Create profiles for each user
            create_profiles(student, pi, industry, vendor)

            print("\nLogin Credentials:")
            print("------------------")
            print("Student: student@example.com / password123")
            print("PI: pi@example.com / password123")
            print("Industry: industry@example.com / password123")
            print("Vendor: vendor@example.com / password123")
            print("Admin: admin@example.com / admin123")

        except Exception as e:
            db.session.rollback()
            print(f"Error creating users: {e}")

def create_profiles(student, pi, industry, vendor):
    """Create profiles for demo users"""
    try:
        # Student profile
        student_profile = Profile(
            user_id=student.id,
            profile_type="Student",
            profile_completeness=90,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(student_profile)
        db.session.commit()

        student_specific = StudentProfile(
            profile_id=student_profile.id,
            name="Alex Johnson",
            affiliation="Stanford University",
            contact_email="alex.johnson@stanford.edu",
            contact_phone="(555) 123-4567",
            gender="Other",
            address="Stanford, CA 94305",
            research_interests="Machine Learning, Artificial Intelligence, Data Science, Computational Biology",
            why_me="I am a motivated graduate student with a strong background in computer science and biology. I have experience in implementing machine learning algorithms for biological data analysis.",
            current_status="PhD Student"
        )
        db.session.add(student_specific)

        # PI profile
        pi_profile = Profile(
            user_id=pi.id,
            profile_type="Scientist",
            profile_completeness=95,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(pi_profile)
        db.session.commit()

        pi_specific = PIProfile(
            profile_id=pi_profile.id,
            name="Dr. Sarah Williams",
            department="Computer Science",
            affiliation="MIT",
            gender="Female",
            current_designation="Associate Professor",
            email="sarah.williams@mit.edu",
            contact_phone="(555) 987-6543",
            address="77 Massachusetts Ave, Cambridge, MA 02139",
            current_message="Welcome to the Williams Lab! We are always looking for talented students to join our research on artificial intelligence and robotics.",
            current_focus="Robotics, Computer Vision, Reinforcement Learning",
            expectations_from_students="Strong programming skills, background in machine learning or robotics, willingness to learn and collaborate.",
            why_join_lab="Our lab has cutting-edge facilities and collaborations with leading tech companies. We publish regularly in top-tier conferences and journals."
        )
        db.session.add(pi_specific)

        # Industry profile
        industry_profile = Profile(
            user_id=industry.id,
            profile_type="Industry",
            profile_completeness=85,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(industry_profile)
        db.session.commit()

        industry_specific = IndustryProfile(
            profile_id=industry_profile.id,
            company_name="InnovateTech Solutions",
            contact_person="Michael Chen",
            email="michael.chen@innovatetech.com",
            contact_phone="(555) 456-7890",
            gst="GST123456789",
            pan="ABCDE1234F",
            address="123 Innovation Park, San Francisco, CA 94105",
            vision="Pioneering technological solutions to solve global challenges through research and innovation.",
            sector="Technology, Healthcare",
            team_size=250,
            annual_turnover="$50M"
        )
        db.session.add(industry_specific)

        # Vendor profile
        vendor_profile = Profile(
            user_id=vendor.id,
            profile_type="Vendor",
            profile_completeness=80,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(vendor_profile)
        db.session.commit()

        vendor_specific = VendorProfile(
            profile_id=vendor_profile.id,
            company_name="LabSupply Pro",
            contact_person="Jennifer Lee",
            dealing_categories="Laboratory Equipment, Research Chemicals, Scientific Instruments",
            email="jennifer.lee@labsupplypro.com",
            contact_phone="(555) 789-0123",
            gst="GST987654321",
            pan="ZYXWV9876G",
            address="456 Science Park, Boston, MA 02210",
            product_categories="Microscopes, Centrifuges, Spectrophotometers, PCR Equipment",
            why_me="We provide high-quality lab equipment with excellent customer service and technical support. Academic discounts available!",
            region="North America, Europe"
        )
        db.session.add(vendor_specific)

        db.session.commit()
        print("Profiles created successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"Error creating profiles: {e}")

if __name__ == "__main__":
    create_demo_users()
