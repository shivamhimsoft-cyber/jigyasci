import os
import sys
from datetime import datetime, timedelta
from app import app, db
from models import User, Opportunity

def create_seed_opportunities():
    """Create seed opportunities for demo purposes"""
    with app.app_context():
        # Check if opportunities already exist
        if Opportunity.query.count() > 0:
            print("Opportunities already exist in the database. Skipping seed data creation.")
            return
            
        # Check if users exist
        pi_user = User.query.filter_by(email="pi@example.com").first()
        industry_user = User.query.filter_by(email="industry@example.com").first()
        
        if not pi_user or not industry_user:
            print("Seed users not found. Please run seed_users.py first.")
            return
            
        print("Creating seed opportunities...")
        
        # Create opportunities from PI
        opportunities = [
            # PI opportunities
            Opportunity(
                creator_user_id=pi_user.id,
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
                creator_user_id=pi_user.id,
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
                creator_user_id=pi_user.id,
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
                creator_user_id=industry_user.id,
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
                creator_user_id=industry_user.id,
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
                creator_user_id=industry_user.id,
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
        
        # Commit changes
        db.session.commit()
        
        print(f"Successfully created {len(opportunities)} seed opportunities!")

if __name__ == "__main__":
    create_seed_opportunities()