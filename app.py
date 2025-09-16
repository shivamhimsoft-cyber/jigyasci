from dotenv import load_dotenv
load_dotenv()

import os
import logging
import string
import csv
import io
from io import TextIOWrapper
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message as MailMessage
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import or_
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager, mail  # Import extensions here


# Register Blueprints
from routes.admin_routes import admin_bp
from routes.pi_routes import pi_bp
from routes.student_routes import student_bp
from routes.vendor_routes import vendor_bp
from routes.industry_routes import industry_bp
from routes.auth_routes import auth_bp

from routes import register_blueprints

from routes.bookmark_routes import bookmark_bp  # ✅ Add this import

# migrate = Migrate(app, db)

app = Flask(__name__)  # <-- Pehle app define karo

# app.register_blueprint(admin_bp)
# app.register_blueprint(pi_bp)
# app.register_blueprint(student_bp)
# app.register_blueprint(vendor_bp)
# app.register_blueprint(industry_bp)
# app.register_blueprint(auth_bp)

register_blueprints(app)



app.secret_key = os.getenv("SECRET_KEY")

# Email config (ensure no space or typos)
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # Must match Gmail where you created app password
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # 16-char App Password (no spaces)

print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
print("MAIL_PASSWORD:", app.config['MAIL_PASSWORD'])
mail = Mail(app)


# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Setup database base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
# db = SQLAlchemy(model_class=Base)
# login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'



# Create Flask app
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


# Configure database
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql+psycopg2://postgres:bbb07ak47@localhost:5432/shivamdb"   # Local Database URL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql://shivamdb_xz88_user:MCMF0p7eSiKVTDPLqlYF5mFhiuDiqCpu@dpg-d2e2e5adbo4c73ek5ba0-a.oregon-postgres.render.com/shivamdb_xz88"   # External Database URL
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql://shivamdb_xz88_user:MCMF0p7eSiKVTDPLqlYF5mFhiuDiqCpu@dpg-d2e2e5adbo4c73ek5ba0-a:5432/shivamdb_xz88"      # Internal Database URL
 



app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Check if the connection is alive before using
    "pool_recycle": 300,  # Recycle connections after 300 seconds

}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable modification tracking

# In your app.py or wherever you initialize your app
app.config['BULK_UPLOAD_FOLDER'] = 'uploads/bulk_opportunities'

# init extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Initialize extensions with app
# db.init_app(app)
# login_manager.init_app(app)



# Add custom Jinja filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if value:
        return value.replace('\n', '<br>')

# Import models and forms after db is initialized to avoid circular imports
from models import User, Profile, StudentProfile, PIProfile, IndustryProfile, VendorProfile, Opportunity, OpportunityLink, Message, Application, Notification, Register, ResearchFacility, Publication, TeamMember, Education, Experience,Technology, Skill, Award, ApplicationLink
from forms import LoginForm, RegistrationForm, StudentProfileForm, PIProfileForm, IndustryProfileForm, VendorProfileForm, OpportunityForm, MessageForm, SearchForm

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


# Routes
@app.route('/welcome')
def welcome():
    return render_template('website/welcome.html')



#============================================================================================================ VIEW PROFILE 

@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    try:
        user = User.query.get_or_404(user_id)
        profile = Profile.query.filter_by(user_id=user_id).first_or_404()

        # Get stats for admin profile
        stats = None
        if profile.profile_type == 'Admin':
            stats = {
                'total_users': User.query.count(),
                'students': User.query.filter_by(user_type='Student').count(),
                'pis': User.query.filter_by(user_type='PI').count(),
                'industry': User.query.filter_by(user_type='Industry').count(),
                'vendors': User.query.filter_by(user_type='Vendor').count(),
            }

        publications = None  # define publications with default None to avoid reference errors

        if profile.profile_type == 'Student':
            specific_profile = StudentProfile.query.filter_by(profile_id=profile.id).first_or_404()
            publications = profile.publications.all()  # ✅ ADD THIS LINE
            template = 'profile/student.html'
        elif profile.profile_type == 'PI':
            specific_profile = PIProfile.query.filter_by(profile_id=profile.id).first_or_404()
            template = 'profile/pi.html'
        elif profile.profile_type == 'Industry':
            specific_profile = IndustryProfile.query.filter_by(profile_id=profile.id).first_or_404()
            template = 'profile/industry.html'
        elif profile.profile_type == 'Vendor':
            specific_profile = VendorProfile.query.filter_by(profile_id=profile.id).first_or_404()
            template = 'profile/vendor.html'
        elif profile.profile_type == 'Admin':
            # For admin, we'll use a simpler approach with a hardcoded profile
            specific_profile = {
                'name': 'System Administrator',
                'email': user.email,
                'role': 'Platform Administrator',
                'permissions': 'User Management, Content Moderation, System Configuration, Data Access',
                'contact_phone': '+1-555-123-4567'
            }
            template = 'profile/admin.html'
        else:
            flash('Invalid profile type', 'danger')
            return redirect(url_for('index'))

        return render_template(template, user=user, profile=profile, specific_profile=specific_profile, stats=stats, publications=publications)

    except Exception as e:
        logger.error(f"Error viewing profile: {str(e)}")
        flash('There was an error loading the profile. Please try again later.', 'danger')
        return redirect(url_for('index'))



#=============================================================================================================== OPPORTUNITIES

@app.route('/opportunities', methods=['GET'])
def list_opportunities():
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', None)

    if type_filter:
        opportunities = Opportunity.query.filter_by(
            type=type_filter,
            status='Active'
        ).order_by(Opportunity.created_at.desc()).paginate(page=page, per_page=10)
    else:
        opportunities = Opportunity.query.filter_by(
            status='Active'
        ).order_by(Opportunity.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('opportunities/list.html',
                          title='Research Opportunities',
                          opportunities=opportunities)


@app.route('/my-opportunities')
@login_required
def my_opportunities():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get opportunities created by the current user
    opportunities = Opportunity.query.filter_by(creator_profile_id=current_user.profile.id)\
        .order_by(Opportunity.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('opportunities/my_opportunities.html', opportunities=opportunities)


@app.route('/add-opportunity', methods=['GET', 'POST'])
@login_required
def add_opportunity():
    try:
        form_data = request.form
        
        # Convert empty strings to None for optional fields
        def clean_field(value):
            return value if value else None
            
        if form_data.get('opportunity_id'):
            # Update existing opportunity
            opportunity = Opportunity.query.get(form_data['opportunity_id'])
            if not opportunity or opportunity.creator_profile_id != current_user.profile.id:
                flash('You are not authorized to edit this opportunity', 'error')
                return redirect(url_for('my_opportunities'))
        else:
            # Create new opportunity
            opportunity = Opportunity(creator_profile_id=current_user.profile.id)
        
        # Required fields
        opportunity.type = form_data['type']
        opportunity.title = form_data['title']
        
        # Optional fields
        opportunity.domain = clean_field(form_data.get('domain'))
        opportunity.eligibility = clean_field(form_data.get('eligibility'))
        opportunity.description = clean_field(form_data.get('description'))
        opportunity.advertisement_link = clean_field(form_data.get('advertisement_link'))
        opportunity.location = clean_field(form_data.get('location'))
        opportunity.duration = clean_field(form_data.get('duration'))
        opportunity.compensation = clean_field(form_data.get('compensation'))
        opportunity.keywords = clean_field(form_data.get('keywords'))
        opportunity.status = form_data.get('status', 'Active')
        
        # Handle date field
        deadline = form_data.get('deadline')
        opportunity.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None
        
        if not form_data.get('opportunity_id'):
            db.session.add(opportunity)
        
        db.session.commit()
        flash('Opportunity saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving opportunity: {str(e)}', 'error')
        app.logger.error(f"Error saving opportunity: {str(e)}")
    
    return redirect(url_for('my_opportunities'))


@app.route('/delete-opportunity/<int:id>', methods=['POST'])
@login_required
def delete_opportunity(id):
    opportunity = Opportunity.query.get_or_404(id)
    
    if opportunity.creator_profile_id != current_user.profile.id:
        flash('You are not authorized to delete this opportunity', 'error')
        return redirect(url_for('my_opportunities'))
    
    db.session.delete(opportunity)
    db.session.commit()
    flash('Opportunity deleted successfully', 'success')
    return redirect(url_for('my_opportunities'))


@app.route('/find-opportunities')
@login_required
def find_opportunities():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('query', '')
    show_mine = request.args.get('mine', 'false').lower() == 'true'
    
    # Base query
    if show_mine:
        # Show only current user's opportunities
        query = Opportunity.query.filter_by(creator_profile_id=current_user.profile.id)
    else:
        # For Admin: show all opportunities
        if current_user.user_type == 'Admin':
            query = Opportunity.query.join(Profile).join(User)
        # For other users: exclude their own opportunities by default
        else:
            query = Opportunity.query.filter(
                Opportunity.creator_profile_id != current_user.profile.id
            ).join(Profile).join(User)
    
    if search_query:
        query = query.filter(or_(
            Opportunity.title.ilike(f'%{search_query}%'),
            Opportunity.domain.ilike(f'%{search_query}%'),
            Opportunity.description.ilike(f'%{search_query}%'),
            Opportunity.keywords.ilike(f'%{search_query}%'),
            User.email.ilike(f'%{search_query}%')
        ))
    
    opportunities = query.order_by(Opportunity.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Add this line to fetch opportunity links
    # Only show active links when not in "my opportunities" view
    if show_mine:
        opportunity_links = []
    else:
        opportunity_links = OpportunityLink.query.filter_by(is_active=True).order_by(
            OpportunityLink.created_at.desc()
        ).all()

        # Check if current user has applied to each link
     # Check if current user has applied to each link and get status
    for link in opportunity_links:
        if current_user.user_type != 'Admin':  # Admin can't apply
            application = ApplicationLink.query.filter_by(
                opportunity_link_id=link.id,
                applicant_user_id=current_user.id
            ).first()
            
            link.user_has_applied = application is not None
            link.application_status = application.status if application else None
        else:
            link.user_has_applied = False
            link.application_status = None


    return render_template('opportunities/find_opportunities.html', 
                         opportunities=opportunities,
                         show_mine=show_mine,
                         opportunity_links=opportunity_links)


# applying to opportunity links
@app.route('/apply-opportunity-link/<int:link_id>', methods=['POST'])
@login_required
def apply_opportunity_link(link_id):
    # Admin cannot apply to opportunity links
    if current_user.user_type == 'Admin':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Admin cannot apply to opportunity links'})
        flash('Admin cannot apply to opportunity links', 'warning')
        return redirect(url_for('find_opportunities'))
    
    opportunity_link = OpportunityLink.query.get_or_404(link_id)
    
    # Check if user already applied
    existing_application = ApplicationLink.query.filter_by(
        opportunity_link_id=link_id,
        applicant_user_id=current_user.id
    ).first()
    
    if existing_application:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'You have already applied to this opportunity link'})
        flash('You have already applied to this opportunity link', 'warning')
        return redirect(url_for('find_opportunities'))
    
    # Create new application
    application = ApplicationLink(
        opportunity_link_id=link_id,
        applicant_user_id=current_user.id,
        applicant_profile_id=current_user.profile.id,
        cover_letter=request.form.get('cover_letter', ''),
        notes=request.form.get('notes', ''),
        status='Pending'
    )
    
    # Handle file uploads (similar to regular opportunity application)
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Process resume upload
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename and allowed_file(resume_file.filename):
                if resume_file.content_length > MAX_FILE_SIZE:
                    flash('Resume file is too large', 'error')
                else:
                    filename = f"resume_link_{current_user.id}_{link_id}_{secure_filename(resume_file.filename)}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    resume_file.save(filepath)
                    application.resume = filename
        
        # Process multiple additional documents
        additional_docs = []
        if 'additional_documents[]' in request.files:
            doc_files = request.files.getlist('additional_documents[]')
            doc_names = request.form.getlist('document_names[]')
            
            for i, doc_file in enumerate(doc_files):
                if doc_file and doc_file.filename and allowed_file(doc_file.filename):
                    if doc_file.content_length > MAX_FILE_SIZE:
                        flash(f'Document {i+1} is too large', 'error')
                        continue
                    
                    # Use provided name or generate one
                    doc_name = doc_names[i] if i < len(doc_names) and doc_names[i] else f"document_{i+1}"
                    safe_name = secure_filename(doc_name)
                    
                    filename = f"doc_link_{current_user.id}_{link_id}_{safe_name}_{secure_filename(doc_file.filename)}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    doc_file.save(filepath)
                    
                    additional_docs.append({
                        'name': doc_name,
                        'filename': filename
                    })
        
        # Store additional documents as JSON
        if additional_docs:
            application.additional_documents = json.dumps(additional_docs)
        
        db.session.add(application)
        db.session.commit()
        
        # Return JSON response for AJAX handling
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Application submitted successfully!'})
            
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error submitting application: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg})
            
        flash(error_msg, 'error')
    
    return redirect(url_for('find_opportunities'))



@app.route('/link-applicants/<int:link_id>')
@login_required
def link_applicants(link_id):
    opportunity_link = OpportunityLink.query.get_or_404(link_id)
    
    # Check if current user is the owner of the opportunity link or admin
    if opportunity_link.added_by != current_user.profile.id and current_user.user_type != 'Admin':
        flash('You are not authorized to view applicants for this opportunity link', 'error')
        return redirect(url_for('find_opportunities'))
    
    applicants = ApplicationLink.query.filter_by(opportunity_link_id=link_id).all()
    
    # Parse additional documents for each application
    for application in applicants:
        if application.additional_documents:
            try:
                application.parsed_documents = json.loads(application.additional_documents)
            except (ValueError, TypeError, json.JSONDecodeError):
                application.parsed_documents = []
        else:
            application.parsed_documents = []
    
    return render_template('opportunities/link_applicants.html', 
                         opportunity_link=opportunity_link,
                         applicants=applicants)

@app.route('/update-link-application-status/<int:application_id>', methods=['POST'])
@login_required
def update_link_application_status(application_id):
    application = ApplicationLink.query.get_or_404(application_id)
    opportunity_link = application.opportunity_link

    # Check ownership - only link owner or admin can update
    if opportunity_link.added_by != current_user.profile.id and current_user.user_type != 'Admin':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Not authorized"), 403
        flash('You are not authorized to update this application', 'error')
        return redirect(url_for('find_opportunities'))

    new_status = request.form.get('status')
    if new_status in ['Pending', 'Accepted', 'Rejected', 'Shortlisted']:
        application.status = new_status
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, new_status=new_status)
        flash('Application status updated successfully', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Invalid status"), 400
        flash('Invalid status', 'error')

    return redirect(url_for('link_applicants', link_id=opportunity_link.id))



@app.route('/get-application-status/<int:link_id>')
@login_required
def get_application_status(link_id):
    if current_user.user_type == 'Admin':
        return jsonify({'success': False, 'message': 'Admin cannot apply'})
    
    application = ApplicationLink.query.filter_by(
        opportunity_link_id=link_id,
        applicant_user_id=current_user.id
    ).first()
    
    if application:
        return jsonify({
            'success': True, 
            'has_applied': True,
            'status': application.status
        })
    else:
        return jsonify({
            'success': True, 
            'has_applied': False,
            'status': None
        })  





    
@app.route('/get-opportunity/<int:opportunity_id>')
@login_required
def get_opportunity(opportunity_id):
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    return jsonify({
        'id': opportunity.id,
        'title': opportunity.title,
        'type': opportunity.type,
        'domain': opportunity.domain,
        'eligibility': opportunity.eligibility,
        'deadline': opportunity.deadline.strftime('%Y-%m-%d') if opportunity.deadline else None,
        'description': opportunity.description,
        'advertisement_link': opportunity.advertisement_link,
        'location': opportunity.location,
        'duration': opportunity.duration,
        'compensation': opportunity.compensation,
        'keywords': opportunity.keywords,
        'status': opportunity.status,
        'creator_profile_id': opportunity.creator_profile_id,   
        'creator_email': opportunity.creator.user.email,
        'creator_type': opportunity.creator.profile_type
    })

@app.route('/follow-profile/<int:profile_id>', methods=['POST'])
@login_required
def follow_profile(profile_id):
    # Implement your follow logic here
    # This is just a placeholder
    try:
        # Add follow relationship to database
        # Return success or failure
        return jsonify({'success': True, 'message': 'Followed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/opp_view-profile/<int:profile_id>')
@login_required
def opp_view_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)

    # All opportunities created by this profile
    opportunities = Opportunity.query.filter_by(creator_profile_id=profile.id)\
                                     .order_by(Opportunity.created_at.desc()).all()

    # If publications are needed (mostly for PI or Student profiles)
    publications = Publication.query.filter_by(profile_id=profile.id).all()

    if profile.profile_type == 'PI':
        return render_template('visit_profile/facultyinfo.html',
                               pi=profile.pi_profile,  # Changed to use pi_profile
                               profile=profile,       # Added profile object
                               opportunities=opportunities,
                               publications=publications)

    elif profile.profile_type == 'Student':
        return render_template('visit_profile/student.html',
                               student=profile.student_profile,  # Changed to use student_profile
                               profile=profile,                 # Added profile object
                               opportunities=opportunities,
                               publications=publications)

    elif profile.profile_type == 'Industry':
        return render_template('visit_profile/industry.html',
                               industry=profile.industry_profile,  # Changed to use industry_profile
                               profile=profile,                   # Added profile object
                               opportunities=opportunities)

    elif profile.profile_type == 'Vendor':
        return render_template('visit_profile/vendor.html',
                               vendor=profile.vendor_profile,  # Changed to use vendor_profile
                               profile=profile,               # Added profile object
                               opportunities=opportunities)

    else:
        abort(404)




# app.py

import os
import json  # Add this import at the top of your app.py file
from werkzeug.utils import secure_filename

# Configure upload settings
UPLOAD_FOLDER = 'uploads/applications'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS         



@app.route('/apply-opportunity/<int:opportunity_id>', methods=['POST'])
@login_required
def apply_opportunity(opportunity_id):
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if user already applied
    existing_application = Application.query.filter_by(
        opportunity_id=opportunity_id,
        applicant_user_id=current_user.id
    ).first()
    
    if existing_application:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'You have already applied to this opportunity'})
        flash('You have already applied to this opportunity', 'warning')
        return redirect(url_for('find_opportunities'))
    
    # Create new application
    application = Application(
        opportunity_id=opportunity_id,
        applicant_user_id=current_user.id,
        applicant_profile_id=current_user.profile.id,
        cover_letter=request.form.get('cover_letter', ''),
        notes=request.form.get('notes', ''),
        status='Pending'
    )
    
    # Handle file uploads
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Process resume upload
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename and allowed_file(resume_file.filename):
                if resume_file.content_length > MAX_FILE_SIZE:
                    flash('Resume file is too large', 'error')
                else:
                    filename = f"resume_{current_user.id}_{opportunity_id}_{secure_filename(resume_file.filename)}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    resume_file.save(filepath)
                    application.resume = filename
        
        # Process multiple additional documents
        additional_docs = []
        if 'additional_documents[]' in request.files:
            doc_files = request.files.getlist('additional_documents[]')
            doc_names = request.form.getlist('document_names[]')
            
            for i, doc_file in enumerate(doc_files):
                if doc_file and doc_file.filename and allowed_file(doc_file.filename):
                    if doc_file.content_length > MAX_FILE_SIZE:
                        flash(f'Document {i+1} is too large', 'error')
                        continue
                    
                    # Use provided name or generate one
                    doc_name = doc_names[i] if i < len(doc_names) and doc_names[i] else f"document_{i+1}"
                    safe_name = secure_filename(doc_name)
                    
                    filename = f"doc_{current_user.id}_{opportunity_id}_{safe_name}_{secure_filename(doc_file.filename)}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    doc_file.save(filepath)
                    
                    additional_docs.append({
                        'name': doc_name,
                        'filename': filename
                    })
        
        # Store additional documents as JSON
        if additional_docs:
            application.additional_documents = json.dumps(additional_docs)
        
        db.session.add(application)
        db.session.commit()
        
        # Return JSON response for AJAX handling
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Application submitted successfully!'})
            
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error submitting application: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg})
            
        flash(error_msg, 'error')
    
    return redirect(url_for('find_opportunities'))


@app.route('/opportunity-applicants/<int:opportunity_id>')
@login_required
def opportunity_applicants(opportunity_id):
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Check if current user is the owner of the opportunity
    if opportunity.creator_profile_id != current_user.profile.id:
        flash('You are not authorized to view applicants for this opportunity', 'error')
        return redirect(url_for('my_opportunities'))
    
    applicants = Application.query.filter_by(opportunity_id=opportunity_id).all()
    
    # Parse additional documents for each application
    for application in applicants:
        if application.additional_documents:
            try:
                application.parsed_documents = json.loads(application.additional_documents)
            except (ValueError, TypeError, json.JSONDecodeError):
                application.parsed_documents = []
        else:
            application.parsed_documents = []
    
    return render_template('opportunities/applicants.html', 
                         opportunity=opportunity,
                         applicants=applicants)


from flask import jsonify, request

@app.route('/update-application-status/<int:application_id>', methods=['POST'])
@login_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    opportunity = application.opportunity

    # Check ownership
    if opportunity.creator_profile_id != current_user.profile.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Not authorized"), 403
        flash('You are not authorized to update this application', 'error')
        return redirect(url_for('my_opportunities'))

    new_status = request.form.get('status')
    if new_status in ['Pending', 'Accepted', 'Rejected', 'Shortlisted']:
        application.status = new_status
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True, new_status=new_status)
        flash('Application status updated successfully', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Invalid status"), 400
        flash('Invalid status', 'error')

    return redirect(url_for('opportunity_applicants', opportunity_id=opportunity.id))



@app.route('/download-application-file/<filename>')
@login_required
def download_application_file(filename):
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    # Verify the user has permission to access this file
    # (either the applicant, opportunity creator, or link owner)
    application = None
    
    if filename.startswith('resume_link_') or filename.startswith('doc_link_'):
        # Handle link application files
        try:
            # Parse filename format: type_userId_linkId_filename
            parts = filename.split('_')
            if len(parts) >= 4:
                user_id = int(parts[2])
                link_id = int(parts[3])
                
                # Check if current user is the applicant
                if current_user.id == user_id:
                    application = ApplicationLink.query.filter_by(
                        applicant_user_id=user_id,
                        opportunity_link_id=link_id
                    ).first()
                else:
                    # Check if current user is the link owner or admin
                    opportunity_link = OpportunityLink.query.get(link_id)
                    if opportunity_link and (opportunity_link.added_by == current_user.profile.id or current_user.user_type == 'Admin'):
                        application = ApplicationLink.query.filter_by(
                            applicant_user_id=user_id,
                            opportunity_link_id=link_id
                        ).first()
        except (ValueError, IndexError):
            pass
    else:
        # Handle regular opportunity application files (existing logic)
        try:
            parts = filename.split('_')
            if len(parts) >= 4:
                user_id = int(parts[1])
                opportunity_id = int(parts[2])
                
                # Check if current user is the applicant
                if current_user.id == user_id:
                    application = Application.query.filter_by(
                        applicant_user_id=user_id,
                        opportunity_id=opportunity_id
                    ).first()
                else:
                    # Check if current user is the opportunity creator
                    opportunity = Opportunity.query.get(opportunity_id)
                    if opportunity and opportunity.creator_profile_id == current_user.profile.id:
                        application = Application.query.filter_by(
                            applicant_user_id=user_id,
                            opportunity_id=opportunity_id
                        ).first()
        except (ValueError, IndexError):
            pass
    
    if not application:
        flash('You do not have permission to access this file', 'error')
        return redirect(url_for('find_opportunities'))
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('find_opportunities'))
    
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('find_opportunities'))







#  SEARCH LOGIC WITH TABLE VIEW ==============================================================================================SEARCH LOGIC WITH TABLE VIEW 
# from sqlalchemy import or_, func
# from math import ceil

# @app.route('/', methods=['GET'])
# def index():
#     query = request.args.get('query', '').strip()
#     page = int(request.args.get('page', 1))
#     per_page = 10

#  # Safe empty pagination object
#     profiles_paginated = Profile.query.join(PIProfile).paginate(page=page, per_page=per_page, error_out=False)
#     profiles_paginated.items = []

#     total_pages = 0
#     students = []
#     vendors = []
#     industries = []
#     facilities = []
#     publications = []
#     technologies = []
#     active_tab = None

#     if query:
#         profiles = Profile.query.join(PIProfile).filter(
#             or_(
#                 func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
#                 PIProfile.department.ilike(f'%{query}%'),
#                 PIProfile.affiliation.ilike(f'%{query}%'),
#                 PIProfile.affiliation_short.ilike(f'%{query}%'),
#                 PIProfile.location.ilike(f'%{query}%'),
#                 PIProfile.current_designation.ilike(f'%{query}%'),
#                 PIProfile.current_focus.ilike(f'%{query}%')
#             )
#         )
#         profiles_paginated = profiles.paginate(page=page, per_page=per_page, error_out=False)

#         total_pages = profiles_paginated.pages


#         students = StudentProfile.query.filter(
#             or_(
#                 StudentProfile.name.ilike(f'%{query}%'),
#                 StudentProfile.affiliation.ilike(f'%{query}%'),
#                 StudentProfile.research_interests.ilike(f'%{query}%')
#             )
#         ).all()

#         vendors = VendorProfile.query.filter(
#             or_(
#                 VendorProfile.company_name.ilike(f'%{query}%'),
#                 VendorProfile.dealing_categories.ilike(f'%{query}%'),
#                 VendorProfile.region.ilike(f'%{query}%')
#             )
#         ).all()

#         industries = IndustryProfile.query.filter(
#             or_(
#                 IndustryProfile.company_name.ilike(f'%{query}%'),
#                 IndustryProfile.vision.ilike(f'%{query}%'),
#                 IndustryProfile.sector.ilike(f'%{query}%')
#             )
#         ).all()

#         facilities = ResearchFacility.query.filter(
#             or_(
#                 ResearchFacility.equipment_name.ilike(f'%{query}%'),
#                 ResearchFacility.make.ilike(f'%{query}%'),
#                 ResearchFacility.model.ilike(f'%{query}%')
#             )
#         ).all()

#         publications = Publication.query.filter(
#             or_(
#                 Publication.title.ilike(f'%{query}%'),
#                 Publication.authors.ilike(f'%{query}%'),
#                 Publication.keywords.ilike(f'%{query}%')
#             )
#         ).all()

#         technologies = Technology.query.filter(
#             or_(
#                 Technology.title.ilike(f'%{query}%'),
#                 Technology.keywords.ilike(f'%{query}%'),
#                 Technology.target_industries.ilike(f'%{query}%')
#             )
#         ).all()

#         # Prioritized tab detection
#         tab_counts = {
#             'PI-profile': profiles_paginated.total,
#             'Student': len(students),
#             'Vendor': len(vendors),
#             'Industry': len(industries),
#             'Research-Facilities': len(facilities),
#             'Publication': len(publications),
#             'technologies': len(technologies)
#         }

#         for tab, count in tab_counts.items():
#             if count > 0:
#                 active_tab = tab
#                 break

#     return render_template('welcome.html',
#                            query=query,
#                            profiles=profiles_paginated,
#                            students=students,
#                            vendors=vendors,
#                            industries=industries,
#                            facilities=facilities,
#                            publications=publications,
#                            technologies=technologies,
#                            active_tab=active_tab,
#                            page=page,
#                            total_pages=total_pages)
from flask import request, render_template, jsonify
from sqlalchemy import or_, func

# @app.route('/', methods=['GET'])
# def index():
#     query = request.args.get('query', '').strip()
#     limit = int(request.args.get('limit', 5))  # Default to showing 5 results initially
#     active_tab = request.args.get('active_tab', None)

#     # Initialize all result lists
#     profiles = []
#     students = []
#     vendors = []
#     industries = []
#     facilities = []
#     publications = []
#     technologies = []

#     if query:
#         # PI Profiles
#         profiles = Profile.query.join(PIProfile).filter(
#             or_(
#                 func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
#                 PIProfile.department.ilike(f'%{query}%'),
#                 PIProfile.affiliation.ilike(f'%{query}%'),
#                 PIProfile.affiliation_short.ilike(f'%{query}%'),
#                 PIProfile.location.ilike(f'%{query}%'),
#                 PIProfile.current_designation.ilike(f'%{query}%'),
#                 PIProfile.current_focus.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Student Profiles
#         students = StudentProfile.query.filter(
#             or_(
#                 StudentProfile.name.ilike(f'%{query}%'),
#                 StudentProfile.affiliation.ilike(f'%{query}%'),
#                 StudentProfile.research_interests.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Vendor Profiles
#         vendors = VendorProfile.query.filter(
#             or_(
#                 VendorProfile.company_name.ilike(f'%{query}%'),
#                 VendorProfile.dealing_categories.ilike(f'%{query}%'),
#                 VendorProfile.region.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Industry Profiles
#         industries = IndustryProfile.query.filter(
#             or_(
#                 IndustryProfile.company_name.ilike(f'%{query}%'),
#                 IndustryProfile.vision.ilike(f'%{query}%'),
#                 IndustryProfile.sector.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Research Facilities
#         facilities = ResearchFacility.query.filter(
#             or_(
#                 ResearchFacility.equipment_name.ilike(f'%{query}%'),
#                 ResearchFacility.make.ilike(f'%{query}%'),
#                 ResearchFacility.model.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Publications
#         publications = Publication.query.filter(
#             or_(
#                 Publication.title.ilike(f'%{query}%'),
#                 Publication.authors.ilike(f'%{query}%'),
#                 Publication.keywords.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         # Technologies
#         technologies = Technology.query.filter(
#             or_(
#                 Technology.title.ilike(f'%{query}%'),
#                 Technology.keywords.ilike(f'%{query}%'),
#                 Technology.target_industries.ilike(f'%{query}%')
#             )
#         ).limit(limit).all()

#         if not active_tab:
#             tab_counts = {
#                 'PI-profile': len(profiles),
#                 'Student': len(students),
#                 'Vendor': len(vendors),
#                 'Industry': len(industries),
#                 'Research-Facilities': len(facilities),
#                 'Publication': len(publications),
#                 'technologies': len(technologies)
#             }

#             for tab, count in tab_counts.items():
#                 if count > 0:
#                     active_tab = tab
#                     break
                    
#     return render_template('welcome.html',
#                          query=query,
#                          profiles=profiles,
#                          students=students,
#                          vendors=vendors,
#                          industries=industries,
#                          facilities=facilities,
#                          publications=publications,
#                          technologies=technologies,
#                          active_tab=active_tab,
#                          current_limit=limit)

# @app.route('/search', methods=['POST'])
# def search():
#     query = request.form.get('query', '').strip()
#     limit = int(request.form.get('limit', 5))
#     active_tab = request.form.get('active_tab', 'PI-profile')

#     # Initialize all result lists
#     profiles = []
#     students = []
#     vendors = []
#     industries = []
#     facilities = []
#     publications = []
#     technologies = []

#     if query:
#         if active_tab == 'PI-profile':
#             profiles = Profile.query.join(PIProfile).filter(
#                 or_(
#                     func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
#                     PIProfile.department.ilike(f'%{query}%'),
#                     PIProfile.affiliation.ilike(f'%{query}%'),
#                     PIProfile.affiliation_short.ilike(f'%{query}%'),
#                     PIProfile.location.ilike(f'%{query}%'),
#                     PIProfile.current_designation.ilike(f'%{query}%'),
#                     PIProfile.current_focus.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'Student':
#             students = StudentProfile.query.filter(
#                 or_(
#                     StudentProfile.name.ilike(f'%{query}%'),
#                     StudentProfile.affiliation.ilike(f'%{query}%'),
#                     StudentProfile.research_interests.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'Vendor':
#             vendors = VendorProfile.query.filter(
#                 or_(
#                     VendorProfile.company_name.ilike(f'%{query}%'),
#                     VendorProfile.dealing_categories.ilike(f'%{query}%'),
#                     VendorProfile.region.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'Industry':
#             industries = IndustryProfile.query.filter(
#                 or_(
#                     IndustryProfile.company_name.ilike(f'%{query}%'),
#                     IndustryProfile.vision.ilike(f'%{query}%'),
#                     IndustryProfile.sector.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'Research-Facilities':
#             facilities = ResearchFacility.query.filter(
#                 or_(
#                     ResearchFacility.equipment_name.ilike(f'%{query}%'),
#                     ResearchFacility.make.ilike(f'%{query}%'),
#                     ResearchFacility.model.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'Publication':
#             publications = Publication.query.filter(
#                 or_(
#                     Publication.title.ilike(f'%{query}%'),
#                     Publication.authors.ilike(f'%{query}%'),
#                     Publication.keywords.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#         elif active_tab == 'technologies':
#             technologies = Technology.query.filter(
#                 or_(
#                     Technology.title.ilike(f'%{query}%'),
#                     Technology.keywords.ilike(f'%{query}%'),
#                     Technology.target_industries.ilike(f'%{query}%')
#                 )
#             ).limit(limit).all()

#     return render_template('partials/search_results.html',
#                          query=query,
#                          profiles=profiles,
#                          students=students,
#                          vendors=vendors,
#                          industries=industries,
#                          facilities=facilities,
#                          publications=publications,
#                          technologies=technologies,
#                          active_tab=active_tab,
#                          current_limit=limit)



@app.route('/', methods=['GET'])
def index():
    query_str = request.args.get('query', '').strip()

    # Initialize all data containers
    profiles = []
    students = []
    vendors = []
    industries = []
    facilities = []
    publications = []
    technologies = []
    active_tab = None

   # Set PI-profile as default active tab
    active_tab = 'PI-profile'  # This is the key change

    # Set the default limit for display
    current_limit = 5  # or whatever you want as the initial load limit

    if query_str:
        # Filter PI profiles (join Profile + PIProfile)
        profiles = (
            Profile.query.join(PIProfile)
            .filter(
                or_(
                    func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query_str.replace(' ', '').lower()}%"),
                    PIProfile.department.ilike(f'%{query_str}%'),
                    PIProfile.affiliation.ilike(f'%{query_str}%'),
                    PIProfile.affiliation_short.ilike(f'%{query_str}%'),
                    PIProfile.location.ilike(f'%{query_str}%'),
                    PIProfile.current_designation.ilike(f'%{query_str}%'),
                    PIProfile.current_focus.ilike(f'%{query_str}%'),
                )
            )
            .all()
        )

        # Student matches
        students = StudentProfile.query.filter(
            or_(
                StudentProfile.name.ilike(f'%{query_str}%'),
                StudentProfile.affiliation.ilike(f'%{query_str}%'),
                StudentProfile.research_interests.ilike(f'%{query_str}%')
            )
        ).all()

        # Vendor matches
        vendors = VendorProfile.query.filter(
            or_(
                VendorProfile.company_name.ilike(f'%{query_str}%'),
                VendorProfile.dealing_categories.ilike(f'%{query_str}%'),
                VendorProfile.region.ilike(f'%{query_str}%'),
            )
        ).all()

        # Industry matches
        industries = IndustryProfile.query.filter(
            or_(
                IndustryProfile.company_name.ilike(f'%{query_str}%'),
                IndustryProfile.vision.ilike(f'%{query_str}%'),
                IndustryProfile.sector.ilike(f'%{query_str}%'),
            )
        ).all()

        # Research Facilities
        facilities = ResearchFacility.query.filter(
            or_(
                ResearchFacility.equipment_name.ilike(f'%{query_str}%'),
                ResearchFacility.make.ilike(f'%{query_str}%'),
                ResearchFacility.model.ilike(f'%{query_str}%'),
            )
        ).all()

        # Publications
        publications = Publication.query.filter(
            or_(
                Publication.title.ilike(f'%{query_str}%'),
                Publication.authors.ilike(f'%{query_str}%'),
                Publication.keywords.ilike(f'%{query_str}%'),
            )
        ).all()

        # Technologies
        technologies = Technology.query.filter(
            or_(
                Technology.title.ilike(f'%{query_str}%'),
                Technology.keywords.ilike(f'%{query_str}%'),
                Technology.target_industries.ilike(f'%{query_str}%'),
            )
        ).all()

        # Determine active tab (first non-empty)
        tab_counts = {
            'PI-profile': len(profiles),
            'Student': len(students),
            'Vendor': len(vendors),
            'Industry': len(industries),
            'Research-Facilities': len(facilities),
            'Publication': len(publications),
            'technologies': len(technologies),
        }

        # If PI-profile has results, keep it as active
        if tab_counts['PI-profile'] > 0:
            active_tab = 'PI-profile'
        else:
            # Otherwise find the first tab with results
            for tab, count in tab_counts.items():
                if count > 0:
                    active_tab = tab
                    break


    return render_template(
        'welcome.html',
        query=query_str,
        profiles=profiles,
        students=students,
        vendors=vendors,
        industries=industries,
        facilities=facilities,
        publications=publications,
        technologies=technologies,
        active_tab=active_tab,
        current_limit=current_limit
    )



@app.route('/load_more_profiles')
def load_more_profiles():
    offset = int(request.args.get('offset', 0))
    limit = 5
    query_str = request.args.get('query', '').strip()

    # Filter query (same as before)
    base_query = (
        Profile.query.join(PIProfile)
        .filter(
            or_(
                func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query_str.replace(' ', '').lower()}%"),
                PIProfile.department.ilike(f'%{query_str}%'),
                PIProfile.affiliation.ilike(f'%{query_str}%'),
                PIProfile.affiliation_short.ilike(f'%{query_str}%'),
                PIProfile.location.ilike(f'%{query_str}%'),
                PIProfile.current_designation.ilike(f'%{query_str}%'),
                PIProfile.current_focus.ilike(f'%{query_str}%'),
            )
        )
    )

    total = base_query.count()  # total matching profiles

    profiles = base_query.offset(offset).limit(limit).all()

    result = []
    for profile in profiles:
        pi = profile.pi_profile
        if not pi:
            continue
        result.append({
            'id': profile.id,
            'name': pi.name or 'N/A',
            'designation': pi.current_designation or 'N/A',
            'affiliation': pi.affiliation_short or pi.affiliation or 'N/A',
            'focus': pi.current_focus or 'N/A',
            'department': pi.department or 'N/A',
            'location': pi.location or 'N/A',
            'profile_image_url': pi.profile_picture or '',
        })

    return jsonify({
        'profiles': result,
        'total': total
    })

# @app.route('/load_more_students')
# def load_more_students():
#     offset = int(request.args.get('offset', 0))
#     query = request.args.get('query', '')

#     all_students = search_students(query)
#     students = all_students[offset:offset+5]
    
#     return jsonify({
#         "students": [{
#             "id": s.id,
#             "name": s.name,
#             "profile_image_url": s.profile_image_url,
#             "degree_program": s.degree_program,
#             "affiliation": s.affiliation,
#             "research_interests": s.research_interests,
#             "skills": s.skills
#         } for s in students],
#         "total": len(all_students)
#     })


@app.route('/load_more_students')
def load_more_students():
    offset = int(request.args.get('offset', 0))
    query_str = request.args.get('query', '').strip()
    limit = 5

    students = StudentProfile.query.filter(
        or_(
            StudentProfile.name.ilike(f'%{query_str}%'),
            StudentProfile.affiliation.ilike(f'%{query_str}%'),
            StudentProfile.research_interests.ilike(f'%{query_str}%')
        )
    ).offset(offset).limit(limit).all()

    return jsonify([
        {
            'id': student.id,
            'name': student.name or 'N/A',
            'degree_program': student.degree_program or '',
            'affiliation': student.affiliation or '',
            'research_interests': student.research_interests or '',
            'skills': student.skills or ''
        }
        for student in students
    ])



@app.route('/load_more_vendors')
def load_more_vendors():
    offset = int(request.args.get('offset', 0))
    limit = 5
    query_str = request.args.get('query', '').strip()

    # Base query with search functionality
    base_query = Vendor.query.filter(
        or_(
            func.lower(func.replace(Vendor.company_name, ' ', '')).ilike(f"%{query_str.replace(' ', '').lower()}%"),
            Vendor.dealing_categories.ilike(f'%{query_str}%'),
            Vendor.region.ilike(f'%{query_str}%'),
            Vendor.location.ilike(f'%{query_str}%'),
            Vendor.products_services.ilike(f'%{query_str}%'),
            Vendor.description.ilike(f'%{query_str}%')
        )
    )

    total = base_query.count()  # Get total matching vendors

    vendors = base_query.offset(offset).limit(limit).all()

    result = []
    for vendor in vendors:
        result.append({
            'id': vendor.id,
            'company_name': vendor.company_name or 'N/A',
            'dealing_categories': vendor.dealing_categories or 'N/A',
            'region': vendor.region or 'N/A',
            'location': vendor.location or 'N/A',
            'products_services': vendor.products_services or 'N/A',
            'logo_url': vendor.logo_url or ''
        })

    return jsonify({
        'vendors': result,
        'total': total
    })



@app.route('/load_more_industries')
def load_more_industries():
    offset = int(request.args.get('offset', 0))
    limit = 5
    query_str = request.args.get('query', '').strip()

    # Base query with search functionality
    base_query = Industry.query.filter(
        or_(
            func.lower(func.replace(Industry.company_name, ' ', '')).ilike(f"%{query_str.replace(' ', '').lower()}%"),
            Industry.sector.ilike(f'%{query_str}%'),
            Industry.region.ilike(f'%{query_str}%'),
            Industry.location.ilike(f'%{query_str}%'),
            Industry.research_interest.ilike(f'%{query_str}%'),
            Industry.vision.ilike(f'%{query_str}%')
        )
    )

    total = base_query.count()  # Get total matching industries

    industries = base_query.offset(offset).limit(limit).all()

    result = []
    for industry in industries:
        result.append({
            'id': industry.id,
            'company_name': industry.company_name or 'N/A',
            'sector': industry.sector or 'N/A',
            'region': industry.region or 'N/A',
            'location': industry.location or 'N/A',
            'research_interest': industry.research_interest or 'N/A',
            'vision': industry.vision or 'N/A',
            'logo_url': industry.logo_url or ''
        })

    return jsonify({
        'industries': result,
        'total': total
    })





@app.route('/faculty/<int:profile_id>')
def faculty_info(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    pi = profile.pi_profile
    if not pi:
        abort(404)

    return render_template('visit_profile/facultyinfo.html', profile=profile, pi=pi)




# ABOUT AND CONTACT PAGES 

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


from datetime import datetime


















# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX USE LESS USE LESS XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


# @app.route('/profile/edit', methods=['GET', 'POST'])
# @login_required
# def edit_profile():
#     try:
#         profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()

#         if profile.profile_type == 'Student':
#             form = StudentProfileForm()
#             specific_profile = StudentProfile.query.filter_by(profile_id=profile.id).first_or_404()
#         elif profile.profile_type == 'PI':
#             form = PIProfileForm()
#             specific_profile = PIProfile.query.filter_by(profile_id=profile.id).first_or_404()
#         elif profile.profile_type == 'Industry':
#             form = IndustryProfileForm()
#             specific_profile = IndustryProfile.query.filter_by(profile_id=profile.id).first_or_404()
#         elif profile.profile_type == 'Vendor':
#             form = VendorProfileForm()
#             specific_profile = VendorProfile.query.filter_by(profile_id=profile.id).first_or_404()
#         else:
#             flash('Invalid profile type', 'danger')
#             return redirect(url_for('index'))
#     except Exception as e:
#         logger.error(f"Error loading profile for editing: {str(e)}")
#         flash('There was an error loading your profile. Please try again later.', 'danger')
#         return redirect(url_for('index'))

#     if request.method == 'GET':
#         # Populate form with existing data
#         if profile.profile_type == 'Student' and specific_profile.name:
#             form.name.data = specific_profile.name
#             form.affiliation.data = specific_profile.affiliation
#             form.contact_email.data = specific_profile.contact_email
#             form.contact_phone.data = specific_profile.contact_phone
#             form.gender.data = specific_profile.gender
#             form.address.data = specific_profile.address
#             form.research_interests.data = specific_profile.research_interests
#             form.why_me.data = specific_profile.why_me
#             form.current_status.data = specific_profile.current_status
#         elif profile.profile_type == 'PI' and specific_profile.name:
#             form.name.data = specific_profile.name
#             form.department.data = specific_profile.department
#             form.affiliation.data = specific_profile.affiliation
#             form.gender.data = specific_profile.gender
#             form.current_designation.data = specific_profile.current_designation
#             form.email.data = specific_profile.email
#             form.contact_phone.data = specific_profile.contact_phone
#             form.address.data = specific_profile.address
#             form.current_message.data = specific_profile.current_message
#             form.current_focus.data = specific_profile.current_focus
#             form.expectations_from_students.data = specific_profile.expectations_from_students
#             form.why_join_lab.data = specific_profile.why_join_lab
#         elif profile.profile_type == 'Industry' and specific_profile.company_name:
#             form.company_name.data = specific_profile.company_name
#             form.contact_person.data = specific_profile.contact_person
#             form.email.data = specific_profile.email
#             form.contact_phone.data = specific_profile.contact_phone
#             form.gst.data = specific_profile.gst
#             form.pan.data = specific_profile.pan
#             form.address.data = specific_profile.address
#             form.vision.data = specific_profile.vision
#             form.sector.data = specific_profile.sector
#             form.team_size.data = specific_profile.team_size
#             form.annual_turnover.data = specific_profile.annual_turnover
#         elif profile.profile_type == 'Vendor' and specific_profile.company_name:
#             form.company_name.data = specific_profile.company_name
#             form.contact_person.data = specific_profile.contact_person
#             form.dealing_categories.data = specific_profile.dealing_categories
#             form.email.data = specific_profile.email
#             form.contact_phone.data = specific_profile.contact_phone
#             form.gst.data = specific_profile.gst
#             form.pan.data = specific_profile.pan
#             form.address.data = specific_profile.address
#             form.product_categories.data = specific_profile.product_categories
#             form.why_me.data = specific_profile.why_me
#             form.region.data = specific_profile.region

#     if form.validate_on_submit():
#         # Update specific profile based on user type
#         completeness = 0

#         if profile.profile_type == 'Student':
#             specific_profile.name = form.name.data
#             specific_profile.affiliation = form.affiliation.data
#             specific_profile.contact_email = form.contact_email.data
#             specific_profile.contact_phone = form.contact_phone.data
#             specific_profile.gender = form.gender.data
#             specific_profile.address = form.address.data
#             specific_profile.research_interests = form.research_interests.data
#             specific_profile.why_me = form.why_me.data
#             specific_profile.current_status = form.current_status.data

#             # Calculate profile completeness
#             fields = [form.name.data, form.affiliation.data, form.contact_email.data,
#                       form.gender.data, form.research_interests.data, form.current_status.data]
#             completeness = sum(1 for field in fields if field) / len(fields) * 100

#         elif profile.profile_type == 'PI':
#             specific_profile.name = form.name.data
#             specific_profile.department = form.department.data
#             specific_profile.affiliation = form.affiliation.data
#             specific_profile.gender = form.gender.data
#             specific_profile.current_designation = form.current_designation.data
#             specific_profile.email = form.email.data
#             specific_profile.contact_phone = form.contact_phone.data
#             specific_profile.address = form.address.data
#             specific_profile.current_message = form.current_message.data
#             specific_profile.current_focus = form.current_focus.data
#             specific_profile.expectations_from_students = form.expectations_from_students.data
#             specific_profile.why_join_lab = form.why_join_lab.data

#             # Calculate profile completeness
#             fields = [form.name.data, form.department.data, form.affiliation.data,
#                       form.current_designation.data, form.email.data, form.current_focus.data]
#             completeness = sum(1 for field in fields if field) / len(fields) * 100

#         elif profile.profile_type == 'Industry':
#             specific_profile.company_name = form.company_name.data
#             specific_profile.contact_person = form.contact_person.data
#             specific_profile.email = form.email.data
#             specific_profile.contact_phone = form.contact_phone.data
#             specific_profile.gst = form.gst.data
#             specific_profile.pan = form.pan.data
#             specific_profile.address = form.address.data
#             specific_profile.vision = form.vision.data
#             specific_profile.sector = form.sector.data
#             specific_profile.team_size = form.team_size.data
#             specific_profile.annual_turnover = form.annual_turnover.data

#             # Calculate profile completeness
#             fields = [form.company_name.data, form.contact_person.data, form.email.data,
#                       form.sector.data, form.vision.data]
#             completeness = sum(1 for field in fields if field) / len(fields) * 100

#         elif profile.profile_type == 'Vendor':
#             specific_profile.company_name = form.company_name.data
#             specific_profile.contact_person = form.contact_person.data
#             specific_profile.dealing_categories = form.dealing_categories.data
#             specific_profile.email = form.email.data
#             specific_profile.contact_phone = form.contact_phone.data
#             specific_profile.gst = form.gst.data
#             specific_profile.pan = form.pan.data
#             specific_profile.address = form.address.data
#             specific_profile.product_categories = form.product_categories.data
#             specific_profile.why_me = form.why_me.data
#             specific_profile.region = form.region.data

#             # Calculate profile completeness
#             fields = [form.company_name.data, form.contact_person.data, form.email.data,
#                       form.dealing_categories.data, form.product_categories.data]
#             completeness = sum(1 for field in fields if field) / len(fields) * 100

#         # Update profile completeness and last updated
#         profile.profile_completeness = int(completeness)
#         profile.last_updated = datetime.utcnow()

#         db.session.commit()

#         flash('Your profile has been updated!', 'success')
#         return redirect(url_for('view_profile', user_id=current_user.id))

#     return render_template('profile/edit.html', title='Edit Profile', form=form, profile_type=profile.profile_type)




# @app.route('/messages')
# @login_required
# def messages():
#     conversations = db.session.query(
#         Message.sender_user_id,
#         Message.receiver_user_id,
#         db.func.max(Message.sent_time).label('last_message_time')
#     ).filter(
#         (Message.sender_user_id == current_user.id) |
#         (Message.receiver_user_id == current_user.id)
#     ).group_by(
#         Message.sender_user_id,
#         Message.receiver_user_id
#     ).order_by(
#         db.desc('last_message_time')
#     ).all()

#     # Process conversations to get details
#     conversation_details = []
#     for sender_id, receiver_id, last_time in conversations:
#         # Determine the other user
#         other_user_id = sender_id if receiver_id == current_user.id else receiver_id
#         other_user = User.query.get(other_user_id)

#         # Get unread count
#         unread_count = Message.query.filter_by(
#             sender_user_id=other_user_id,
#             receiver_user_id=current_user.id,
#             read_status=False
#         ).count()

#         # Get last message
#         last_message = Message.query.filter(
#             ((Message.sender_user_id == current_user.id) &
#              (Message.receiver_user_id == other_user_id)) |
#             ((Message.sender_user_id == other_user_id) &
#              (Message.receiver_user_id == current_user.id))
#         ).order_by(Message.sent_time.desc()).first()

#         conversation_details.append({
#             'user': other_user,
#             'last_message': last_message,
#             'unread_count': unread_count
#         })

#     return render_template('messages/inbox.html',
#                           title='Messages',
#                           conversations=conversation_details)

# @app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
# @login_required
# def conversation(user_id):
#     other_user = User.query.get_or_404(user_id)

#     # Get messages between current user and other user
#     messages = Message.query.filter(
#         ((Message.sender_user_id == current_user.id) &
#          (Message.receiver_user_id == user_id)) |
#         ((Message.sender_user_id == user_id) &
#          (Message.receiver_user_id == current_user.id))
#     ).order_by(Message.sent_time).all()

#     # Mark unread messages as read
#     unread_messages = Message.query.filter_by(
#         sender_user_id=user_id,
#         receiver_user_id=current_user.id,
#         read_status=False
#     ).all()

#     for msg in unread_messages:
#         msg.read_status = True

#     db.session.commit()

#     # Handle new message submission
#     form = MessageForm()
#     if form.validate_on_submit():
#         message = Message(
#             sender_user_id=current_user.id,
#             receiver_user_id=user_id,
#             content=form.content.data,
#             sent_time=datetime.utcnow(),
#             read_status=False
#         )

#         db.session.add(message)
#         db.session.commit()

#         # Create notification for message receiver
#         notification = Notification(
#             user_id=user_id,
#             type='message',
#             reference_id=message.id,
#             message=f'New message from {current_user.email}',
#             created_at=datetime.utcnow(),
#             read_status=False
#         )

#         db.session.add(notification)
#         db.session.commit()

#         return redirect(url_for('conversation', user_id=user_id))

#     return render_template('messages/conversation.html',
#                           title=f'Conversation with {other_user.email}',
#                           other_user=other_user,
#                           messages=messages,
#                           form=form)

# @app.route('/documentation')
# def documentation():
#     """Display the platform documentation and user guide"""
#     return render_template('documentation.html')






# USE NHI HO RAHA NHAI MAINE NEW BANAYA HAI , SEARCH FUNCTION


# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     form = SearchForm()

#     if form.validate_on_submit() or request.args.get('query'):
#         query = form.query.data if form.validate_on_submit() else request.args.get('query')
#         category = form.category.data if form.validate_on_submit() else request.args.get('category', 'all')

#         if category == 'opportunities' or category == 'all':
#             opportunities = Opportunity.query.filter(
#                 Opportunity.status == 'Active',
#                 (Opportunity.title.ilike(f'%{query}%') |
#                  Opportunity.description.ilike(f'%{query}%') |
#                  Opportunity.domain.ilike(f'%{query}%') |
#                  Opportunity.keywords.ilike(f'%{query}%'))
#             ).all()
#         else:
#             opportunities = []

#         if category == 'profiles' or category == 'all':
#             # Get student profiles
#             student_profiles = db.session.query(Profile, StudentProfile, User).join(
#                 StudentProfile, Profile.id == StudentProfile.profile_id
#             ).join(
#                 User, Profile.user_id == User.id
#             ).filter(
#                 (StudentProfile.name.ilike(f'%{query}%') |
#                  StudentProfile.research_interests.ilike(f'%{query}%'))
#             ).all()

#             # Get PI profiles
#             pi_profiles = db.session.query(Profile, PIProfile, User).join(
#                 PIProfile, Profile.id == PIProfile.profile_id
#             ).join(
#                 User, Profile.user_id == User.id
#             ).filter(
#                 (PIProfile.name.ilike(f'%{query}%') |
#                  PIProfile.current_focus.ilike(f'%{query}%') |
#                  PIProfile.department.ilike(f'%{query}%'))
#             ).all()

#             # Get industry profiles
#             industry_profiles = db.session.query(Profile, IndustryProfile, User).join(
#                 IndustryProfile, Profile.id == IndustryProfile.profile_id
#             ).join(
#                 User, Profile.user_id == User.id
#             ).filter(
#                 (IndustryProfile.company_name.ilike(f'%{query}%') |
#                  IndustryProfile.sector.ilike(f'%{query}%') |
#                  IndustryProfile.vision.ilike(f'%{query}%'))
#             ).all()

#             # Get vendor profiles
#             vendor_profiles = db.session.query(Profile, VendorProfile, User).join(
#                 VendorProfile, Profile.id == VendorProfile.profile_id
#             ).join(
#                 User, Profile.user_id == User.id
#             ).filter(
#                 (VendorProfile.company_name.ilike(f'%{query}%') |
#                  VendorProfile.dealing_categories.ilike(f'%{query}%') |
#                  VendorProfile.product_categories.ilike(f'%{query}%'))
#             ).all()

#             # Combine all profiles
#             profiles = {
#                 'student': student_profiles,
#                 'pi': pi_profiles,
#                 'industry': industry_profiles,
#                 'vendor': vendor_profiles
#             }
#         else:
#             profiles = {'student': [], 'pi': [], 'industry': [], 'vendor': []}

#         return render_template('search/results.html',
#                               title='Search Results',
#                               query=query,
#                               category=category,
#                               opportunities=opportunities,
#                               profiles=profiles)

#     return render_template('search/results.html',
#                           title='Search',
#                           form=form,
#                           opportunities=[],
#                           profiles={'student': [], 'pi': [], 'industry': [], 'vendor': []})








# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))

#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user is None or not check_password_hash(user.password_hash, form.password.data):
#             flash('Invalid email or password', 'danger')
#             return redirect(url_for('login'))

#         login_user(user, remember=form.remember_me.data)
#         next_page = request.args.get('next')
#         if not next_page or urlparse(next_page).netloc != '':
#             next_page = url_for('index')

#         flash('Login successful!', 'success')
#         return redirect(next_page)

#     return render_template('auth/login.html', title='Sign In', form=form)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))

#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user is None or not check_password_hash(user.password_hash, form.password.data):
#             flash('Invalid email or password', 'danger')
#             return redirect(url_for('login'))

#         login_user(user, remember=form.remember_me.data)
#         flash('Login successful!', 'success')

#         # ✅ Redirect based on user_type
#         if user.user_type == 'Admin':
#             return redirect(url_for('admin_dashboard'))
#         elif user.user_type == 'PI':
#             return redirect(url_for('faculty_dashboard'))  # 👈 Updated line
#         elif user.user_type == 'Student':
#             return redirect(url_for('studentProfile'))
#         elif user.user_type == 'Industry':
#             return redirect(url_for('industryProfile'))
#         elif user.user_type == 'Vendor':
#             return redirect(url_for('vendorProfile'))
#         else:
#             return redirect(url_for('index'))

#     return render_template('auth/login.html', title='Sign In', form=form)



# LOGIN / LOGOUT ============================================================================================================ LOGIN / LOGOUT LOGIN / LOGOUT LOGIN / LOGOUT LOGIN / LOGOUT



# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))

#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(
#             email=form.email.data,
#             user_type=form.user_type.data,
#             account_status='Active',
#             verification_status='Pending',
#             created_at=datetime.utcnow(),
#             last_login=datetime.utcnow()
#         )
#         user.password_hash = generate_password_hash(form.password.data)

#         db.session.add(user)
#         db.session.commit()

#         # Create profile based on user type
#         profile = Profile(
#             user_id=user.id,
#             profile_type=form.user_type.data,
#             profile_completeness=0,
#             visibility_settings="Public",
#             last_updated=datetime.utcnow()
#         )
#         db.session.add(profile)
#         db.session.commit()

#         # Create specific profile type
#         if form.user_type.data == 'Student':
#             student_profile = StudentProfile(profile_id=profile.id)
#             db.session.add(student_profile)
#         elif form.user_type.data == 'PI':
#             pi_profile = PIProfile(profile_id=profile.id)
#             db.session.add(pi_profile)
#         elif form.user_type.data == 'Industry':
#             industry_profile = IndustryProfile(profile_id=profile.id)
#             db.session.add(industry_profile)
#         elif form.user_type.data == 'Vendor':
#             vendor_profile = VendorProfile(profile_id=profile.id)
#             db.session.add(vendor_profile)

#         db.session.commit()

#         flash('Congratulations, you are now registered! Please complete your profile.', 'success')
#         login_user(user)
#         return redirect(url_for('edit_profile'))

#     return render_template('auth/register.html', title='Register', form=form)




@app.route('/search')
def search():
    category = request.args.get('category', 'profiles')
    query = request.args.get('query', '')
    # Your search logic here
    return render_template('search.html', category=category, query=query)







