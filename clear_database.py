# clear_database.py

# from app import app, db
# from models import (
#     Notification, Message, Application, Opportunity, Award, Skill,
#     Technology, Publication, Experience, Education, CSRFund, SponsorRequest,
#     TeamMember, Project, ResearchFacility, PIProfile, StudentProfile,
#     VendorProfile, IndustryProfile, Profile, User, Department, Institute,
#     department_institute
# )

# with app.app_context():
#     print("Deleting all data from tables...")

#     # Clear the many-to-many association table first
#     db.session.execute(department_institute.delete())

#     models_in_order = [
#         Notification, Message, Application, Opportunity, Award,
#         Skill, Technology, Publication, Experience, Education,
#         CSRFund, SponsorRequest, TeamMember, Project, ResearchFacility,
#         PIProfile, StudentProfile, VendorProfile, IndustryProfile,
#         Profile, User, Department, Institute
#     ]

#     for model in models_in_order:
#         records = db.session.query(model).all()
#         for record in records:
#             db.session.delete(record)

#     db.session.commit()
#     print("All data deleted successfully.")



from app import app, db
from sqlalchemy import text  # <-- yeh import zaroori hai

with app.app_context():
    print(" Truncating all tables and resetting IDs...")

    # Clear many-to-many association table first
    db.session.execute(text("TRUNCATE department_institute RESTART IDENTITY CASCADE;"))

    db.session.execute(text("""
        TRUNCATE TABLE 
            notifications, messages, applications, opportunities,
            awards, skills, technologies, publications, experience, education,
            csr_funds, sponsor_requests,
            team_members, projects, research_facilities,
            pi_profiles, student_profiles, vendor_profiles, industry_profiles,
            profiles, users, institutes, departments
        RESTART IDENTITY CASCADE;
    """))

    db.session.commit()
    print(" All data truncated and identity reset.")

