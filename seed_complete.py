import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Profile, StudentProfile, PIProfile, IndustryProfile, VendorProfile, Opportunity

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        print("Database reset complete!")

def create_seed_data():
    """Create seed data for the application"""
    with app.app_context():
        print("Creating seed users...")
        
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
        db.session.add(student)
        db.session.commit()
        
        # Create student profile
        student_profile = Profile(
            user_id=student.id,
            profile_type="Student",
            profile_completeness=90,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(student_profile)
        db.session.commit()
        
        # Create student specific profile
        student_specific = StudentProfile(
            profile_id=student_profile.id,
            name="Alex Johnson",
            affiliation="Stanford University",
            contact_email="alex.johnson@stanford.edu",
            contact_phone="(555) 123-4567",
            gender="Prefer not to say",
            address="Stanford, CA 94305",
            research_interests="Machine Learning, Artificial Intelligence, Data Science, Computational Biology",
            why_me="I am a motivated graduate student with a strong background in computer science and biology. I have experience in implementing machine learning algorithms for biological data analysis. Published: Johnson A, et al. (2024) Machine Learning Applications in Genomics. Nature AI 5: 123-130.",
            current_status="PhD Student"
        )
        db.session.add(student_specific)
        
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
        db.session.add(pi)
        db.session.commit()
        
        # Create PI profile
        pi_profile = Profile(
            user_id=pi.id,
            profile_type="PI",
            profile_completeness=95,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(pi_profile)
        db.session.commit()
        
        # Create PI specific profile
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
        db.session.add(industry)
        db.session.commit()
        
        # Create Industry profile
        industry_profile = Profile(
            user_id=industry.id,
            profile_type="Industry",
            profile_completeness=85,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(industry_profile)
        db.session.commit()
        
        # Create Industry specific profile
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
        db.session.add(vendor)
        db.session.commit()
        
        # Create Vendor profile
        vendor_profile = Profile(
            user_id=vendor.id,
            profile_type="Vendor",
            profile_completeness=80,
            visibility_settings="Public",
            last_updated=datetime.utcnow()
        )
        db.session.add(vendor_profile)
        db.session.commit()
        
        # Create Vendor specific profile
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
        
        print("Creating seed opportunities...")
        
        # Create opportunities from PI
        opportunities = [
            # PI opportunities
            Opportunity(
                creator_profile_id=pi_profile.id,
                type="PhD",
                title="PhD Position in Machine Learning for Robotics",
                domain="Machine Learning, Robotics",
                eligibility="Master's degree in Computer Science, Electrical Engineering, or related field. Strong programming skills in Python and experience with machine learning frameworks.",
                deadline=datetime.utcnow() + timedelta(days=90),
                description="""
                The Williams Lab at MIT is looking for a motivated PhD student to join our research on machine learning approaches for robotic manipulation and navigation. The successful candidate will work on developing new algorithms for robot learning and contribute to our ongoing projects in collaboration with industry partners.
                
                Research Focus:
                - Deep reinforcement learning for robotic manipulation
                - Computer vision for scene understanding
                - Human-robot interaction
                
                The position is fully funded for 4 years, with opportunities for conference travel and internships at partner companies.
                """,
                location="MIT, Cambridge, MA",
                duration="4 years",
                compensation="$35,000/year + tuition waiver",
                keywords="Machine Learning, Robotics, Computer Vision, PhD, Reinforcement Learning",
                application_process="Submit CV, transcripts, and a research statement through our lab website.",
                start_date=datetime.utcnow() + timedelta(days=180),
                end_date=datetime.utcnow() + timedelta(days=180) + timedelta(days=365*4),
                status="Active",
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            ),
            Opportunity(
                creator_user_id=pi.id,
                type="Internship",
                title="Summer Research Internship in AI",
                domain="Artificial Intelligence, Natural Language Processing",
                eligibility="Undergraduate/Masters students with programming experience in Python and background in machine learning.",
                deadline=datetime.utcnow() + timedelta(days=60),
                description="""
                Join our lab for a 10-week summer research internship focusing on natural language processing and AI. Interns will work closely with grad students and postdocs on cutting-edge research projects with potential for publication.
                
                Projects may include:
                - Developing new NLP models for scientific text mining
                - Creating multimodal systems for scientific discovery
                - Improving conversational AI systems
                
                This is a paid internship with flexible start dates during the summer.
                """,
                location="MIT, Cambridge, MA",
                duration="10 weeks (Summer)",
                compensation="$7,500 stipend + housing assistance",
                keywords="AI, NLP, Internship, Summer, Research",
                application_process="Apply through the MIT UROP office or directly contact Dr. Williams with your CV and a brief statement of interest.",
                start_date=datetime.utcnow() + timedelta(days=100),
                end_date=datetime.utcnow() + timedelta(days=100) + timedelta(days=70),
                status="Active",
                created_at=datetime.utcnow() - timedelta(days=10),
                last_updated=datetime.utcnow() - timedelta(days=10)
            ),
            Opportunity(
                creator_user_id=pi.id,
                type="PostDoc",
                title="Postdoctoral Position in Computer Vision",
                domain="Computer Vision, Deep Learning",
                eligibility="PhD in Computer Science, Electrical Engineering, or related field. Strong publication record in computer vision conferences (CVPR, ICCV, ECCV).",
                deadline=datetime.utcnow() + timedelta(days=45),
                description="""
                The Williams Lab is seeking a postdoctoral researcher to lead projects in 3D computer vision and scene understanding. The successful candidate will develop new methods for 3D reconstruction, object recognition, and scene analysis from multiple sensors.
                
                Responsibilities:
                - Lead research projects in 3D computer vision
                - Mentor graduate and undergraduate students
                - Write papers for top-tier conferences and journals
                - Assist with grant proposals
                
                The position is initially for 2 years with possibility of extension based on performance and funding.
                """,
                location="MIT, Cambridge, MA",
                duration="2 years (renewable)",
                compensation="$65,000-$75,000/year based on experience + benefits",
                keywords="Computer Vision, Deep Learning, 3D Reconstruction, PostDoc",
                application_process="Email your CV, research statement, and three representative publications to sarah.williams@mit.edu",
                start_date=datetime.utcnow() + timedelta(days=60),
                end_date=datetime.utcnow() + timedelta(days=60) + timedelta(days=365*2),
                status="Active",
                created_at=datetime.utcnow() - timedelta(days=15),
                last_updated=datetime.utcnow() - timedelta(days=5)
            ),
            
            # Industry opportunities
            Opportunity(
                creator_profile_id=industry_profile.id,
                type="Internship",
                title="AI Research Intern",
                domain="Artificial Intelligence, Healthcare",
                eligibility="Currently enrolled in a Master's or PhD program in Computer Science, Data Science, or related field. Experience with deep learning frameworks (PyTorch or TensorFlow).",
                deadline=datetime.utcnow() + timedelta(days=30),
                description="""
                InnovateTech Solutions is looking for AI Research Interns to join our Healthcare AI team for a 12-week internship. You'll work with our research scientists on developing novel machine learning models for medical image analysis and diagnostic assistance.
                
                What you'll do:
                - Implement and test state-of-the-art AI models for medical applications
                - Work with anonymized medical datasets
                - Present your findings to the research team
                - Potentially contribute to patent applications or research papers
                
                This is a paid internship with the possibility of full-time employment for exceptional candidates.
                """,
                location="San Francisco, CA (Remote options available)",
                duration="12 weeks",
                compensation="$8,000/month + housing stipend for relocating interns",
                keywords="AI, Healthcare, Internship, Machine Learning, Medical Imaging",
                application_process="Apply through our careers portal with your resume, transcript, and a cover letter explaining your interest in healthcare AI.",
                start_date=datetime.utcnow() + timedelta(days=45),
                end_date=datetime.utcnow() + timedelta(days=45) + timedelta(days=84),
                status="Active",
                created_at=datetime.utcnow() - timedelta(days=5),
                last_updated=datetime.utcnow() - timedelta(days=5)
            ),
            Opportunity(
                creator_profile_id=industry_profile.id,
                type="Job",
                title="Research Scientist - Sustainable Energy",
                domain="Renewable Energy, Materials Science",
                eligibility="PhD in Materials Science, Chemistry, Physics, or related field. 3+ years of research experience in energy storage or renewable energy technologies.",
                deadline=datetime.utcnow() + timedelta(days=60),
                description="""
                Join InnovateTech's Sustainable Energy division as a Research Scientist and help develop the next generation of energy storage solutions. We're looking for innovative scientists to lead research in novel battery materials and green energy technologies.
                
                Responsibilities:
                - Lead R&D projects in energy storage materials
                - Design and conduct experiments to test new materials
                - Collaborate with academic partners and other research institutions
                - Author technical reports and scientific publications
                - Contribute to patent applications
                
                This is a full-time position with competitive salary and benefits, including stock options.
                """,
                location="Boston, MA",
                duration="Permanent",
                compensation="$120,000-$150,000 DOE + benefits and stock options",
                keywords="Energy Storage, Batteries, Renewable Energy, Research, Materials Science",
                application_process="Submit your resume, research statement, and list of publications through our careers portal.",
                start_date=datetime.utcnow() + timedelta(days=90),
                end_date=None,
                status="Active",
                created_at=datetime.utcnow() - timedelta(days=20),
                last_updated=datetime.utcnow() - timedelta(days=20)
            ),
            Opportunity(
                creator_profile_id=industry_profile.id,
                type="Project",
                title="Collaborative Research Project in Quantum Computing",
                domain="Quantum Computing, Algorithm Development",
                eligibility="University research groups with expertise in quantum algorithms, quantum information theory, or related areas.",
                deadline=datetime.utcnow() + timedelta(days=120),
                description="""
                InnovateTech Solutions is seeking academic partners for a collaborative research project in quantum computing applications. We're looking to co-develop quantum algorithms for optimization problems relevant to logistics and supply chain management.
                
                Project details:
                - 18-month collaboration with potential for extension
                - Joint research team with our quantum computing division
                - Access to our quantum computing hardware and simulators
                - Co-publishing of results in top journals
                - Potential for joint IP development
                
                This project is funded through our academic partnership program and includes funding for graduate student researchers.
                """,
                location="Hybrid (Virtual collaboration with quarterly in-person meetings)",
                duration="18 months",
                compensation="Research grant of $250,000 to partner institution",
                keywords="Quantum Computing, Collaborative Research, Optimization, Algorithms",
                application_process="Submit a research proposal (max 5 pages) outlining your approach, team qualifications, and expected outcomes to research.partnerships@innovatetech.com",
                start_date=datetime.utcnow() + timedelta(days=150),
                end_date=datetime.utcnow() + timedelta(days=150) + timedelta(days=545),
                status="Active",
                created_at=datetime.utcnow() - timedelta(days=1),
                last_updated=datetime.utcnow() - timedelta(days=1)
            )
        ]
        
        # Add all opportunities to the database
        for opportunity in opportunities:
            db.session.add(opportunity)
        
        # Create an admin user for testing
        admin = User(
            email="admin@example.com",
            user_type="Admin",
            account_status='Active',
            verification_status='Verified',
            is_admin=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        admin.password_hash = generate_password_hash("admin123")
        db.session.add(admin)
        
        # Commit all changes
        db.session.commit()
        
        print("Seed data created successfully!")
        print("\nLogin Credentials:")
        print("------------------")
        print("Student: student@example.com / password123")
        print("PI: pi@example.com / password123")
        print("Industry: industry@example.com / password123")
        print("Vendor: vendor@example.com / password123")
        print("Admin: admin@example.com / admin123")

if __name__ == "__main__":
    # Reset database first
    reset_database()
    
    # Create seed data
    create_seed_data()