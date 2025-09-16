from dotenv import load_dotenv
load_dotenv()
import os
import logging
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy.orm import DeclarativeBase
from urllib.parse import urlparse
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
from io import TextIOWrapper
from flask import Flask
# At the top of app.py or wherever you're using it
from flask_mail import Mail, Message as MailMessage
# from flask_migrate import Migrate
# from models import db  # Make sure db is imported correctly
# from app import app  # if app is created elsewhere

from routes import register_blueprints
# migrate = Migrate(app, db)
    
import string  # ✅ Add this line
app = Flask(__name__)  # <-- Pehle app define karo

register_blueprints(app)

app.secret_key = os.getenv("SECRET_KEY")

# Mail Config
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
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'



# Create Flask app
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql+psycopg2://postgres:bbb07ak47@localhost:5432/shivamdb"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Recycle connections after 300 seconds
    "pool_pre_ping": True,  # Check if the connection is alive before using
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable modification tracking


# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)



# Add custom Jinja filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if value:
        return value.replace('\n', '<br>')

# Import models and forms after db is initialized to avoid circular imports
from models import User, Profile, StudentProfile, PIProfile, IndustryProfile, VendorProfile, Opportunity, Message, Application, Notification, Register
from forms import LoginForm, RegistrationForm, StudentProfileForm, PIProfileForm, IndustryProfileForm, VendorProfileForm, OpportunityForm, MessageForm, SearchForm

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))









# Routes
@app.route('/welcome')
def welcome():
    return render_template('website/welcome.html')

@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if current_user.user_type != 'PI':
        abort(403)
    return render_template('faculty/dashboard.html', title='Faculty Dashboard')

@app.route('/student/dashboard')
@login_required
def studentProfile():
    if current_user.user_type != 'Student':
        abort(403)
    return render_template('students/dashboard.html', title='Students Dashboard')

@app.route('/industry/dashboard')
@login_required
def industry_dashboard():
    if current_user.user_type != 'Industry':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    industry = IndustryProfile.query.filter_by(profile_id=profile.id).first()

    return render_template('industry/dashboard.html', profile=profile, industry=industry)


@app.route('/industry/profile', methods=['GET', 'POST'])
@login_required
def industryProfile():
    if current_user.user_type != 'Industry':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    industry = IndustryProfile.query.filter_by(profile_id=profile.id).first()

    if request.method == 'POST':                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        if not industry:
            industry = IndustryProfile(profile_id=profile.id)

        industry.company_name = request.form['company_name']
        industry.contact_person = request.form['contact_person']
        industry.email = request.form['email']
        industry.contact_phone = request.form['contact_phone']
        industry.gst = request.form['gst']
        industry.pan = request.form['pan']
        industry.address = request.form['address']
        industry.sector = request.form['sector']
        industry.team_size = request.form.get('team_size', type=int)
        industry.annual_turnover = request.form['annual_turnover']
        industry.vision = request.form['vision']

        # Logo upload
        logo_file = request.files.get('logo')                                                                                                                                                                                                                                              
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            upload_path = os.path.join('static/uploads/industry_logos', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            logo_file.save(upload_path)
            industry.logo = upload_path

        db.session.add(industry)
        db.session.commit()
        flash("Industry profile saved successfully.", "success")
        return redirect(url_for('industryProfile'))

    return render_template('industry/profile.html', industry=industry)


@app.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    if current_user.user_type != 'Vendor':
        abort(403)

    # ✅ Define these before passing to template
    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    vendor = VendorProfile.query.filter_by(profile_id=profile.id).first()

    return render_template('vendor/dashboard.html', profile=profile, vendor=vendor)

@app.route('/vendor/profile', methods=['GET', 'POST'])
@login_required
def vendorProfile():
    if current_user.user_type != 'Vendor':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    vendor = VendorProfile.query.filter_by(profile_id=profile.id).first()

    if request.method == 'POST':
        if not vendor:
            vendor = VendorProfile(profile_id=profile.id)

        vendor.company_name = request.form['company_name']
        vendor.contact_person = request.form['contact_person']
        vendor.email = request.form['email']
        vendor.contact_phone = request.form['contact_phone']
        vendor.gst = request.form['gst']
        vendor.pan = request.form['pan']
        vendor.address = request.form['address']
        vendor.region = request.form['region']
        vendor.dealing_categories = request.form['dealing_categories']
        vendor.product_categories = request.form['product_categories']
        vendor.why_me = request.form['why_me']

        # Handle logo file upload
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join('static/uploads/vendor_logos', filename)
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            logo_file.save(logo_path)
            vendor.logo = logo_path

        db.session.add(vendor)
        db.session.commit()
        flash('Vendor profile saved successfully.', 'success')
        return redirect(url_for('vendorProfile'))

    return render_template('vendor/profile.html', vendor=vendor)














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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # 👇 Redirect to correct dashboard based on user_type if already logged in
        if current_user.user_type == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.user_type == 'PI':
            return redirect(url_for('faculty_dashboard'))
        elif current_user.user_type == 'Student':
            return redirect(url_for('studentProfile'))
        elif current_user.user_type == 'Industry':
            return redirect(url_for('industry_dashboard'))
        elif current_user.user_type == 'Vendor':
            return redirect(url_for('vendor_dashboard'))
        else:
            return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        flash('Login successful!', 'success')

        # Redirect to respective dashboard based on user type
        if user.user_type == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user.user_type == 'PI':
            return redirect(url_for('faculty_dashboard'))
        elif user.user_type == 'Student':
            return redirect(url_for('studentProfile'))
        elif user.user_type == 'Industry':
            return redirect(url_for('industry_dashboard'))
        elif user.user_type == 'Vendor':
            return redirect(url_for('vendor_dashboard'))
        else:
            return redirect(url_for('index'))

    return render_template('auth/login.html', title='Sign In', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # 🧠 Ye redirect karo index pe nahi, ek static welcome page pe






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




@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    try:
        profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()

        if profile.profile_type == 'Student':
            form = StudentProfileForm()
            specific_profile = StudentProfile.query.filter_by(profile_id=profile.id).first_or_404()
        elif profile.profile_type == 'PI':
            form = PIProfileForm()
            specific_profile = PIProfile.query.filter_by(profile_id=profile.id).first_or_404()
        elif profile.profile_type == 'Industry':
            form = IndustryProfileForm()
            specific_profile = IndustryProfile.query.filter_by(profile_id=profile.id).first_or_404()
        elif profile.profile_type == 'Vendor':
            form = VendorProfileForm()
            specific_profile = VendorProfile.query.filter_by(profile_id=profile.id).first_or_404()
        else:
            flash('Invalid profile type', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error loading profile for editing: {str(e)}")
        flash('There was an error loading your profile. Please try again later.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':
        # Populate form with existing data
        if profile.profile_type == 'Student' and specific_profile.name:
            form.name.data = specific_profile.name
            form.affiliation.data = specific_profile.affiliation
            form.contact_email.data = specific_profile.contact_email
            form.contact_phone.data = specific_profile.contact_phone
            form.gender.data = specific_profile.gender
            form.address.data = specific_profile.address
            form.research_interests.data = specific_profile.research_interests
            form.why_me.data = specific_profile.why_me
            form.current_status.data = specific_profile.current_status
        elif profile.profile_type == 'PI' and specific_profile.name:
            form.name.data = specific_profile.name
            form.department.data = specific_profile.department
            form.affiliation.data = specific_profile.affiliation
            form.gender.data = specific_profile.gender
            form.current_designation.data = specific_profile.current_designation
            form.email.data = specific_profile.email
            form.contact_phone.data = specific_profile.contact_phone
            form.address.data = specific_profile.address
            form.current_message.data = specific_profile.current_message
            form.current_focus.data = specific_profile.current_focus
            form.expectations_from_students.data = specific_profile.expectations_from_students
            form.why_join_lab.data = specific_profile.why_join_lab
        elif profile.profile_type == 'Industry' and specific_profile.company_name:
            form.company_name.data = specific_profile.company_name
            form.contact_person.data = specific_profile.contact_person
            form.email.data = specific_profile.email
            form.contact_phone.data = specific_profile.contact_phone
            form.gst.data = specific_profile.gst
            form.pan.data = specific_profile.pan
            form.address.data = specific_profile.address
            form.vision.data = specific_profile.vision
            form.sector.data = specific_profile.sector
            form.team_size.data = specific_profile.team_size
            form.annual_turnover.data = specific_profile.annual_turnover
        elif profile.profile_type == 'Vendor' and specific_profile.company_name:
            form.company_name.data = specific_profile.company_name
            form.contact_person.data = specific_profile.contact_person
            form.dealing_categories.data = specific_profile.dealing_categories
            form.email.data = specific_profile.email
            form.contact_phone.data = specific_profile.contact_phone
            form.gst.data = specific_profile.gst
            form.pan.data = specific_profile.pan
            form.address.data = specific_profile.address
            form.product_categories.data = specific_profile.product_categories
            form.why_me.data = specific_profile.why_me
            form.region.data = specific_profile.region

    if form.validate_on_submit():
        # Update specific profile based on user type
        completeness = 0

        if profile.profile_type == 'Student':
            specific_profile.name = form.name.data
            specific_profile.affiliation = form.affiliation.data
            specific_profile.contact_email = form.contact_email.data
            specific_profile.contact_phone = form.contact_phone.data
            specific_profile.gender = form.gender.data
            specific_profile.address = form.address.data
            specific_profile.research_interests = form.research_interests.data
            specific_profile.why_me = form.why_me.data
            specific_profile.current_status = form.current_status.data

            # Calculate profile completeness
            fields = [form.name.data, form.affiliation.data, form.contact_email.data,
                      form.gender.data, form.research_interests.data, form.current_status.data]
            completeness = sum(1 for field in fields if field) / len(fields) * 100

        elif profile.profile_type == 'PI':
            specific_profile.name = form.name.data
            specific_profile.department = form.department.data
            specific_profile.affiliation = form.affiliation.data
            specific_profile.gender = form.gender.data
            specific_profile.current_designation = form.current_designation.data
            specific_profile.email = form.email.data
            specific_profile.contact_phone = form.contact_phone.data
            specific_profile.address = form.address.data
            specific_profile.current_message = form.current_message.data
            specific_profile.current_focus = form.current_focus.data
            specific_profile.expectations_from_students = form.expectations_from_students.data
            specific_profile.why_join_lab = form.why_join_lab.data

            # Calculate profile completeness
            fields = [form.name.data, form.department.data, form.affiliation.data,
                      form.current_designation.data, form.email.data, form.current_focus.data]
            completeness = sum(1 for field in fields if field) / len(fields) * 100

        elif profile.profile_type == 'Industry':
            specific_profile.company_name = form.company_name.data
            specific_profile.contact_person = form.contact_person.data
            specific_profile.email = form.email.data
            specific_profile.contact_phone = form.contact_phone.data
            specific_profile.gst = form.gst.data
            specific_profile.pan = form.pan.data
            specific_profile.address = form.address.data
            specific_profile.vision = form.vision.data
            specific_profile.sector = form.sector.data
            specific_profile.team_size = form.team_size.data
            specific_profile.annual_turnover = form.annual_turnover.data

            # Calculate profile completeness
            fields = [form.company_name.data, form.contact_person.data, form.email.data,
                      form.sector.data, form.vision.data]
            completeness = sum(1 for field in fields if field) / len(fields) * 100

        elif profile.profile_type == 'Vendor':
            specific_profile.company_name = form.company_name.data
            specific_profile.contact_person = form.contact_person.data
            specific_profile.dealing_categories = form.dealing_categories.data
            specific_profile.email = form.email.data
            specific_profile.contact_phone = form.contact_phone.data
            specific_profile.gst = form.gst.data
            specific_profile.pan = form.pan.data
            specific_profile.address = form.address.data
            specific_profile.product_categories = form.product_categories.data
            specific_profile.why_me = form.why_me.data
            specific_profile.region = form.region.data

            # Calculate profile completeness
            fields = [form.company_name.data, form.contact_person.data, form.email.data,
                      form.dealing_categories.data, form.product_categories.data]
            completeness = sum(1 for field in fields if field) / len(fields) * 100

        # Update profile completeness and last updated
        profile.profile_completeness = int(completeness)
        profile.last_updated = datetime.utcnow()

        db.session.commit()

        flash('Your profile has been updated!', 'success')
        return redirect(url_for('view_profile', user_id=current_user.id))

    return render_template('profile/edit.html', title='Edit Profile', form=form, profile_type=profile.profile_type)

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






# @app.route('/opportunities/create', methods=['GET', 'POST'])
# @login_required
# def create_opportunity():
#     # Check if user is a PI or Industry
#     user_profile = Profile.query.filter_by(user_id=current_user.id).first()
#     if user_profile.profile_type not in ['PI', 'Industry']:
#         flash('Only PIs and Industry partners can post opportunities', 'danger')
#         return redirect(url_for('index'))

#     form = OpportunityForm()

#     if form.validate_on_submit():
#         opportunity = Opportunity(
#             creator_profile_id=user_profile.id,
#             type=form.type.data,
#             title=form.title.data,
#             domain=form.domain.data,
#             eligibility=form.eligibility.data,
#             deadline=form.deadline.data,
#             description=form.description.data,
#             location=form.location.data,
#             duration=form.duration.data,
#             compensation=form.compensation.data,
#             keywords=form.keywords.data,
#             status='Active',
#             created_at=datetime.utcnow()
#         )

#         db.session.add(opportunity)
#         db.session.commit()

#         flash('Your opportunity has been posted!', 'success')
#         return redirect(url_for('view_opportunity', opportunity_id=opportunity.id))

#     return render_template('opportunities/create.html',
#                           title='Post Opportunity',
#                           form=form)

# @app.route('/opportunities/<int:opportunity_id>')
# def view_opportunity(opportunity_id):
#     opportunity = Opportunity.query.get_or_404(opportunity_id)
#     creator_profile = Profile.query.get_or_404(opportunity.creator_profile_id)
#     creator_user = User.query.get_or_404(creator_profile.user_id)

#     has_applied = False
#     if current_user.is_authenticated:
#         user_profile = Profile.query.filter_by(user_id=current_user.id).first()
#         if user_profile:
#             application = Application.query.filter_by(
#                 opportunity_id=opportunity.id,
#                 applicant_user_id=current_user.id
#             ).first()
#             has_applied = application is not None

#     return render_template('opportunities/view.html',
#                           title=opportunity.title,
#                           opportunity=opportunity,
#                           creator_profile=creator_profile,
#                           creator_user=creator_user,
#                           has_applied=has_applied)

# @app.route('/opportunities/<int:opportunity_id>/apply', methods=['POST'])
# @login_required
# def apply_opportunity(opportunity_id):
#     opportunity = Opportunity.query.get_or_404(opportunity_id)

#     # Check if user already applied
#     existing_application = Application.query.filter_by(
#         opportunity_id=opportunity.id,
#         applicant_user_id=current_user.id
#     ).first()

#     if existing_application:
#         flash('You have already applied for this opportunity', 'warning')
#         return redirect(url_for('view_opportunity', opportunity_id=opportunity.id))

#     # Create new application
#     application = Application(
#         opportunity_id=opportunity.id,
#         applicant_user_id=current_user.id,
#         application_date=datetime.utcnow(),
#         status='Pending'
#     )

#     db.session.add(application)
#     db.session.commit()

#     # Create notification for opportunity creator
#     creator_profile = Profile.query.get_or_404(opportunity.creator_profile_id)
#     notification = Notification(
#         user_id=creator_profile.user_id,
#         type='application',
#         reference_id=application.id,
#         message=f'New application received for {opportunity.title}',
#         created_at=datetime.utcnow(),
#         read_status=False
#     )

#     db.session.add(notification)
#     db.session.commit()

#     flash('Your application has been submitted!', 'success')
#     return redirect(url_for('view_opportunity', opportunity_id=opportunity.id))

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

# @app.route('/find-opportunities')
# @login_required
# def find_opportunities():
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
#     search_query = request.args.get('query', '')
    
#     # For Admin: show all opportunities
#     if current_user.user_type == 'Admin':
#         query = Opportunity.query.join(Profile).join(User)
#     # For other users: exclude their own opportunities
#     else:
#         query = Opportunity.query.filter(
#             Opportunity.creator_profile_id != current_user.profile.id
#         ).join(Profile).join(User)
    
#     if search_query:
#         query = query.filter(or_(
#             Opportunity.title.ilike(f'%{search_query}%'),
#             Opportunity.domain.ilike(f'%{search_query}%'),
#             Opportunity.description.ilike(f'%{search_query}%'),
#             Opportunity.keywords.ilike(f'%{search_query}%'),
#             User.email.ilike(f'%{search_query}%')
#         ))
    
#     opportunities = query.order_by(Opportunity.created_at.desc())\
#         .paginate(page=page, per_page=per_page, error_out=False)
    
#     return render_template('opportunities/find_opportunities.html', opportunities=opportunities)
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
    
    return render_template('opportunities/find_opportunities.html', 
                         opportunities=opportunities,
                         show_mine=show_mine)
                         
    
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

@app.route('/messages')
@login_required
def messages():
    conversations = db.session.query(
        Message.sender_user_id,
        Message.receiver_user_id,
        db.func.max(Message.sent_time).label('last_message_time')
    ).filter(
        (Message.sender_user_id == current_user.id) |
        (Message.receiver_user_id == current_user.id)
    ).group_by(
        Message.sender_user_id,
        Message.receiver_user_id
    ).order_by(
        db.desc('last_message_time')
    ).all()

    # Process conversations to get details
    conversation_details = []
    for sender_id, receiver_id, last_time in conversations:
        # Determine the other user
        other_user_id = sender_id if receiver_id == current_user.id else receiver_id
        other_user = User.query.get(other_user_id)

        # Get unread count
        unread_count = Message.query.filter_by(
            sender_user_id=other_user_id,
            receiver_user_id=current_user.id,
            read_status=False
        ).count()

        # Get last message
        last_message = Message.query.filter(
            ((Message.sender_user_id == current_user.id) &
             (Message.receiver_user_id == other_user_id)) |
            ((Message.sender_user_id == other_user_id) &
             (Message.receiver_user_id == current_user.id))
        ).order_by(Message.sent_time.desc()).first()

        conversation_details.append({
            'user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })

    return render_template('messages/inbox.html',
                          title='Messages',
                          conversations=conversation_details)

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)

    # Get messages between current user and other user
    messages = Message.query.filter(
        ((Message.sender_user_id == current_user.id) &
         (Message.receiver_user_id == user_id)) |
        ((Message.sender_user_id == user_id) &
         (Message.receiver_user_id == current_user.id))
    ).order_by(Message.sent_time).all()

    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        sender_user_id=user_id,
        receiver_user_id=current_user.id,
        read_status=False
    ).all()

    for msg in unread_messages:
        msg.read_status = True

    db.session.commit()

    # Handle new message submission
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(
            sender_user_id=current_user.id,
            receiver_user_id=user_id,
            content=form.content.data,
            sent_time=datetime.utcnow(),
            read_status=False
        )

        db.session.add(message)
        db.session.commit()

        # Create notification for message receiver
        notification = Notification(
            user_id=user_id,
            type='message',
            reference_id=message.id,
            message=f'New message from {current_user.email}',
            created_at=datetime.utcnow(),
            read_status=False
        )

        db.session.add(notification)
        db.session.commit()

        return redirect(url_for('conversation', user_id=user_id))

    return render_template('messages/conversation.html',
                          title=f'Conversation with {other_user.email}',
                          other_user=other_user,
                          messages=messages,
                          form=form)

@app.route('/documentation')
def documentation():
    """Display the platform documentation and user guide"""
    return render_template('documentation.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Check if user is admin
    if current_user.user_type != 'Admin':
        abort(403)

    # Get basic statistics
    stats = {
        'total_users': User.query.count(),
        'students': User.query.filter_by(user_type='Student').count(),
        'pis': User.query.filter_by(user_type='PI').count(),
        'industry': User.query.filter_by(user_type='Industry').count(),
        'vendors': User.query.filter_by(user_type='Vendor').count(),
        'opportunities': Opportunity.query.count(),
        'active_opportunities': Opportunity.query.filter_by(status='Active').count(),
        'applications': Application.query.count()
    }

    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    # Recent opportunities
    recent_opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          stats=stats,
                          recent_users=recent_users,
                          recent_opportunities=recent_opportunities)

# Initialize database
with app.app_context():
    db.create_all()

    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            email='admin@example.com',
            user_type='Admin',
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        admin.password_hash = generate_password_hash('adminpassword')
        db.session.add(admin)
        db.session.commit()














#  INSTITUDE ========================================================================================================================================INSTITUDE INSTITUDE INSTITUDE INSTITUDE


@app.route('/institute')
def institute():
    return render_template('institute/institute.html')  # Make sure institute.html exists in your templates folder


from models import Institute, Department 

@app.route('/add-institute')
def add_institute():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # You can adjust this number
    
    # Update the query to use pagination
    institutes = Institute.query.paginate(page=page, per_page=per_page)
    
    return render_template('institute/add_institute.html', institutes=institutes)


# @app.route('/upload_csv', methods=['POST'])
# def upload_csv():
#     if 'file' not in request.files:
#         flash("No file part")
#         return redirect(request.url)
    
#     file = request.files['file']
#     if file.filename == '':
#         flash("No selected file")
#         return redirect(url_for('add_institute'))

#     stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
#     csv_input = csv.DictReader(stream, delimiter=',')

#     for row in csv_input:
#         # Skip rows with only "None" or empty fields
#         if all(value.strip().lower() == 'none' or value.strip() == '' for value in row.values()):
#             continue

#         # Clean data
#         def clean(val):
#             return val.strip() if val and val.strip().lower() != 'none' else None

#         lab_sector = ', '.join([x.strip() for x in row.get("Lab Sector", "").split(',') if x.strip()])
#         focus_area = ', '.join([x.strip() for x in row.get("FocusArea", "").split(',') if x.strip()])
#         key_resources = ', '.join([x.strip() for x in row.get("KeyResources", "").split(',') if x.strip()])


#         institute = Institute(
#             name=clean(row.get("Name")),
#             centers=clean(row.get("Centers")),
#             lab_sector=lab_sector,
#             focus_area=focus_area,
#             key_resources=key_resources,
#             researchers=clean(row.get("Researchers")),
#             director=clean(row.get("Director")),
#             city=clean(row.get("City")),
#             state=clean(row.get("State")),
#             link=clean(row.get("Link")),
#             ownership=clean(row.get("Ownership"))
#         )
#         db.session.add(institute)

#     db.session.commit()
#     flash("CSV uploaded successfully.")
#     return redirect(url_for('add_institute'))

REQUIRED_COLUMNS = [
    "Name", "Centers", "Lab Sector", "FocusArea", "KeyResources", 
    "Researchers", "Director", "City", "State", "Link", "Ownership"
]

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('add_institute'))

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream, delimiter=',')

    # Check for required columns
    if not set(REQUIRED_COLUMNS).issubset(csv_input.fieldnames):
        flash("Invalid CSV format. Please download and use the sample template.")
        return redirect(url_for('add_institute'))

    for row in csv_input:
        if all(value.strip().lower() == 'none' or value.strip() == '' for value in row.values()):
            continue

        def clean(val):
            return val.strip() if val and val.strip().lower() != 'none' else None

        lab_sector = ', '.join([x.strip() for x in row.get("Lab Sector", "").split(',') if x.strip()])
        focus_area = ', '.join([x.strip() for x in row.get("FocusArea", "").split(',') if x.strip()])
        key_resources = ', '.join([x.strip() for x in row.get("KeyResources", "").split(',') if x.strip()])

        institute = Institute(
            name=clean(row.get("Name")),
            centers=clean(row.get("Centers")),
            lab_sector=lab_sector,
            focus_area=focus_area,
            key_resources=key_resources,
            researchers=clean(row.get("Researchers")),
            director=clean(row.get("Director")),
            city=clean(row.get("City")),
            state=clean(row.get("State")),
            link=clean(row.get("Link")),
            ownership=clean(row.get("Ownership"))
        )
        db.session.add(institute)

    db.session.commit()
    flash("CSV uploaded successfully.")
    return redirect(url_for('add_institute'))

@app.route('/delete_institute/<int:institute_id>', methods=['POST'])
def delete_institute(institute_id):
    institute = Institute.query.get_or_404(institute_id)
    db.session.delete(institute)
    db.session.commit()
    flash('Institute deleted successfully.')
    return redirect(url_for('add_institute'))  # or the route that shows the institute list



















# DEPARTMENT =============================================================================================== DEPARTMENT DEPARTMENT DEPARTMENT DEPARTMENT 



@app.route('/departments')
def departments():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Department.query.paginate(page=page, per_page=per_page)

    total_departments = pagination.total
    total_pages = pagination.pages

    return render_template(
        'department/departments.html',
        departments=pagination.items,
        page=page,
        total_pages=total_pages,
        total_departments=total_departments
    )


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form.get('name')
        institute_ids = request.form.getlist('institute_ids')

        if not name:
            flash('Department name is required!', 'error')
            return redirect(url_for('add_department'))

        existing_dept = Department.query.filter_by(name=name).first()
        if existing_dept:
            flash('Department already exists!', 'error')
            return redirect(url_for('add_department'))

        institutes = Institute.query.filter(Institute.id.in_(institute_ids)).all()
        new_dept = Department(name=name, institutes=institutes)
        db.session.add(new_dept)
        db.session.commit()

        flash('Department added successfully!', 'success')
        return redirect(url_for('departments'))

    institutes = Institute.query.all()
    return render_template('department/add_department.html', institutes=institutes)


def allowed_file(filename):
    """Check if the file has a valid CSV extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

    
@app.route('/upload_departments', methods=['POST'])
def upload_departments():
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('departments'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('departments'))
    
    if file and allowed_file(file.filename):
        try:
            stream = TextIOWrapper(file.stream, encoding='utf-8')
            csv_reader = csv.DictReader(stream)
            
            departments_added = 0
            for row in csv_reader:
                if not row.get('name'):
                    flash('CSV file must contain a "name" column', 'error')
                    return redirect(url_for('departments'))
                
                existing_dept = Department.query.filter_by(name=row['name']).first()
                if not existing_dept:
                    # Handle empty institute_id in CSV
                    institute_id = int(row['institute_id']) if row.get('institute_id') and row['institute_id'].strip() else None
                    
                    department = Department(
                        name=row['name'],
                        institute_id=institute_id
                    )
                    db.session.add(department)
                    departments_added += 1
            
            db.session.commit()
            flash(f'Successfully added {departments_added} departments!', 'success')
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid institute ID in CSV: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading departments: {str(e)}', 'error')
    else:
        flash('Invalid file format. Please upload a CSV file.', 'error')
    
    return redirect(url_for('departments'))



@app.route('/edit_department/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    department = Department.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        institute_ids = request.form.getlist('institute_ids')

        if not name:
            flash('Department name is required!', 'error')
            return redirect(url_for('edit_department', id=id))

        # Check if another department already has this name
        existing_dept = Department.query.filter(Department.name == name, Department.id != id).first()
        if existing_dept:
            flash('Another department with this name already exists!', 'error')
            return redirect(url_for('edit_department', id=id))

        department.name = name
        department.institutes = Institute.query.filter(Institute.id.in_(institute_ids)).all()
        db.session.commit()

        flash('Department updated successfully!', 'success')
        return redirect(url_for('departments'))

    institutes = Institute.query.all()
    selected_ids = [inst.id for inst in department.institutes]
    return render_template('department/edit_department.html', department=department, institutes=institutes, selected_ids=selected_ids)



@app.route('/delete_department/<int:id>', methods=['POST'])
def delete_department(id):
    department = Department.query.get_or_404(id)
    
    try:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {str(e)}', 'error')
    
    return redirect(url_for('departments'))















# PI ================================================================================================================================= PI PI PI  PI PI PI  PI PI PI  



@app.route('/basic_info', methods=['GET', 'POST'])
@login_required
def basic_info():
    if current_user.user_type != 'PI':
        abort(403)

    profile = current_user.profile.pi_profile

    if request.method == 'POST':
        if not profile:
            profile = PIProfile(profile_id=current_user.profile.id)
            db.session.add(profile)

        # Safely extract form data
        profile.name = request.form.get('name')
        profile.department = request.form.get('department')
        profile.affiliation = request.form.get('affiliation')
        profile.gender = request.form.get('gender')
        profile.email = request.form.get('email')
        profile.contact_phone = request.form.get('contact_phone')
        profile.address = request.form.get('address')
        profile.current_message = request.form.get('current_message')
        profile.current_focus = request.form.get('current_focus')
        profile.expectations_from_students = request.form.get('expectations')
        profile.why_join_lab = request.form.get('why_join_lab')

        # Safely handle date fields
        dob_str = request.form.get('dob')
        start_date_str = request.form.get('start_date')
        profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        profile.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('view_pi_profile'))

    return render_template('faculty/basic_info.html', profile=profile)


from sqlalchemy import or_



# @app.route('/')
# def index():
#     featured_opportunities = Opportunity.query.filter_by(status='Active').order_by(Opportunity.created_at.desc()).limit(3).all()
#     featured_profiles = Profile.query.order_by(db.func.random()).limit(4).all()
#     return render_template('welcome.html',
#                           opportunities=featured_opportunities,
#                           profiles=featured_profiles)


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     query = request.args.get('query', '').strip()

#     # Default: all featured
#     featured_opportunities = Opportunity.query.filter_by(status='Active').order_by(Opportunity.created_at.desc()).limit(3)

#     if query:
#         # Search across name, affiliation, department, etc.
#         filtered_profiles = Profile.query.join(PIProfile).filter(
#             or_(
#                 PIProfile.name.ilike(f'%{query}%'),
#                 PIProfile.affiliation.ilike(f'%{query}%'),
#                 PIProfile.department.ilike(f'%{query}%'),
#                 PIProfile.current_focus.ilike(f'%{query}%')
#             )
#         ).all()
#     else:
#         filtered_profiles = Profile.query.order_by(db.func.random()).limit(4).all()

#     return render_template('welcome.html',
#                            opportunities=featured_opportunities,
#                            profiles=filtered_profiles,
#                            query=query)

# @app.route('/', methods=['GET', 'POST'])
# def index():
    # Agar user login hai to unke user_type ke hisaab se dashboard ya profile page redirect karo
    # if current_user.is_authenticated:
    #     if current_user.user_type == 'Admin':
    #         return redirect(url_for('admin_dashboard'))
    #     elif current_user.user_type == 'PI':
    #         return redirect(url_for('faculty_dashboard'))
    #     elif current_user.user_type == 'Student':
    #         return redirect(url_for('studentProfile'))
    #     elif current_user.user_type == 'Industry':
    #         return redirect(url_for('industryProfile'))
    #     elif current_user.user_type == 'Vendor':
    #         return redirect(url_for('vendorProfile'))

    # Agar user login nahi hai to welcome page dikhana with search
#     query = request.args.get('query', '').strip()

#     # Default: all featured
#     featured_opportunities = Opportunity.query.filter_by(status='Active').order_by(Opportunity.created_at.desc()).limit(3)

#     if query:
#         # Search across name, affiliation, department, etc.
#         filtered_profiles = Profile.query.join(PIProfile).filter(
#             or_(
#                 PIProfile.name.ilike(f'%{query}%'),
#                 PIProfile.affiliation.ilike(f'%{query}%'),
#                 PIProfile.department.ilike(f'%{query}%'),
#                 PIProfile.current_focus.ilike(f'%{query}%')
#             )
#         ).all()
#     else:
#         filtered_profiles = Profile.query.order_by(db.func.random()).limit(4).all()

#     return render_template('welcome.html',
#                            opportunities=featured_opportunities,
#                            profiles=filtered_profiles,
#                            query=query)   


# @app.route('/', methods=['GET', 'POST'])
# def index():

#     query = request.args.get('query', '').strip()

#     # Default: all featured
#     featured_opportunities = Opportunity.query.filter_by(status='Active').order_by(Opportunity.created_at.desc()).limit(3)

#     if query:
#         # Search across name, affiliation, department, etc.
#         filtered_profiles = Profile.query.join(PIProfile).filter(
#             or_(
#                 PIProfile.name.ilike(f'%{query}%'),
#                 PIProfile.affiliation.ilike(f'%{query}%'),
#                 PIProfile.department.ilike(f'%{query}%'),
#                 PIProfile.current_focus.ilike(f'%{query}%')
#             )
#         ).all()
#     else:
#         filtered_profiles = Profile.query.order_by(db.func.random()).limit(4).all()

#     return render_template('welcome.html',
#                            opportunities=featured_opportunities,
#                            profiles=filtered_profiles,
#                            query=query)   











#  SEARCH LOGIC WITH TABLE VIEW ==============================================================================================SEARCH LOGIC WITH TABLE VIEW 
from sqlalchemy import or_, func
from math import ceil

@app.route('/', methods=['GET'])
def index():
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10

 # Safe empty pagination object
    profiles_paginated = Profile.query.join(PIProfile).paginate(page=page, per_page=per_page, error_out=False)
    profiles_paginated.items = []

    total_pages = 0
    students = []
    vendors = []
    industries = []
    facilities = []
    publications = []
    technologies = []
    active_tab = None

    if query:
        profiles = Profile.query.join(PIProfile).filter(
            or_(
                func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
                PIProfile.department.ilike(f'%{query}%'),
                PIProfile.affiliation.ilike(f'%{query}%'),
                PIProfile.affiliation_short.ilike(f'%{query}%'),
                PIProfile.location.ilike(f'%{query}%'),
                PIProfile.current_designation.ilike(f'%{query}%'),
                PIProfile.current_focus.ilike(f'%{query}%')
            )
        )
        profiles_paginated = profiles.paginate(page=page, per_page=per_page, error_out=False)

        total_pages = profiles_paginated.pages


        students = StudentProfile.query.filter(
            or_(
                StudentProfile.name.ilike(f'%{query}%'),
                StudentProfile.affiliation.ilike(f'%{query}%'),
                StudentProfile.research_interests.ilike(f'%{query}%')
            )
        ).all()

        vendors = VendorProfile.query.filter(
            or_(
                VendorProfile.company_name.ilike(f'%{query}%'),
                VendorProfile.dealing_categories.ilike(f'%{query}%'),
                VendorProfile.region.ilike(f'%{query}%')
            )
        ).all()

        industries = IndustryProfile.query.filter(
            or_(
                IndustryProfile.company_name.ilike(f'%{query}%'),
                IndustryProfile.vision.ilike(f'%{query}%'),
                IndustryProfile.sector.ilike(f'%{query}%')
            )
        ).all()

        facilities = ResearchFacility.query.filter(
            or_(
                ResearchFacility.equipment_name.ilike(f'%{query}%'),
                ResearchFacility.make.ilike(f'%{query}%'),
                ResearchFacility.model.ilike(f'%{query}%')
            )
        ).all()

        publications = Publication.query.filter(
            or_(
                Publication.title.ilike(f'%{query}%'),
                Publication.authors.ilike(f'%{query}%'),
                Publication.keywords.ilike(f'%{query}%')
            )
        ).all()

        technologies = Technology.query.filter(
            or_(
                Technology.title.ilike(f'%{query}%'),
                Technology.keywords.ilike(f'%{query}%'),
                Technology.target_industries.ilike(f'%{query}%')
            )
        ).all()

        # Prioritized tab detection
        tab_counts = {
            'PI-profile': profiles_paginated.total,
            'Student': len(students),
            'Vendor': len(vendors),
            'Industry': len(industries),
            'Research-Facilities': len(facilities),
            'Publication': len(publications),
            'technologies': len(technologies)
        }

        for tab, count in tab_counts.items():
            if count > 0:
                active_tab = tab
                break

    return render_template('welcome.html',
                           query=query,
                           profiles=profiles_paginated,
                           students=students,
                           vendors=vendors,
                           industries=industries,
                           facilities=facilities,
                           publications=publications,
                           technologies=technologies,
                           active_tab=active_tab,
                           page=page,
                           total_pages=total_pages)


@app.route('/faculty/<int:profile_id>')
def faculty_info(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    pi = profile.pi_profile
    if not pi:
        abort(404)

    return render_template('pi.facultyinfo.html', profile=profile, pi=pi)



from flask import request, render_template
from sqlalchemy import func, or_

@app.route('/faculty/full-table')
def faculty_full_table():
    # Get filters from request args
    query = request.args.get('query', '').strip()
    department_filter = request.args.get('department', '').strip()
    location_filter = request.args.get('location', '').strip()
    min_papers = request.args.get('min_papers', '').strip()
    min_experience = request.args.get('min_experience', '').strip()  # New filter
    max_experience = request.args.get('max_experience', '').strip()

    min_hindex = request.args.get('min_hindex', '').strip()          # New filter

    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'name')
    direction = request.args.get('direction', 'asc')
    per_page = 20

    sort_field_map = {
        'name': PIProfile.name,
        'research_focus': PIProfile.current_focus,
        'designation': PIProfile.current_designation,
        'affiliation': PIProfile.affiliation_short,
        'department': PIProfile.department,
        'location': PIProfile.location,
        'papers': PIProfile.papers_published,
        'citations': PIProfile.total_citations,
        'experience': PIProfile.research_experience_years,
        'h_index': PIProfile.h_index,
    }

    profiles_query = Profile.query.join(PIProfile)

    # Search across multiple fields if query present
    if query:
        q = f"%{query}%"
        profiles_query = profiles_query.filter(
            or_(
                func.lower(func.replace(PIProfile.name, ' ', '')).ilike(f"%{query.replace(' ', '').lower()}%"),
                PIProfile.department.ilike(q),
                PIProfile.affiliation.ilike(q),
                PIProfile.affiliation_short.ilike(q),
                PIProfile.location.ilike(q),
                PIProfile.current_designation.ilike(q),
                PIProfile.current_focus.ilike(q)
            )
        )

    # Apply exact filters if provided
    if department_filter:
        profiles_query = profiles_query.filter(PIProfile.department == department_filter)

    if location_filter:
        profiles_query = profiles_query.filter(PIProfile.location == location_filter)

    # if min_papers.isdigit():
    #     profiles_query = profiles_query.filter(PIProfile.papers_published <= int(min_papers))

    # if min_experience.isdigit():
    #     profiles_query = profiles_query.filter(PIProfile.research_experience_years <= int(min_experience))

    # if min_hindex.isdigit():
    #     profiles_query = profiles_query.filter(PIProfile.h_index <= int(min_hindex))
    # Papers filter
    if min_papers.startswith('>'):
        try:
            value = int(min_papers[1:])
            profiles_query = profiles_query.filter(PIProfile.papers_published > value)
        except ValueError:
            pass
    elif min_papers.isdigit():
        profiles_query = profiles_query.filter(PIProfile.papers_published <= int(min_papers))

    # Experience filter
    if min_experience.startswith('>'):
        try:
            value = int(min_experience[1:])
            profiles_query = profiles_query.filter(PIProfile.research_experience_years > value)
        except ValueError:
            pass
    elif min_experience.isdigit():
        profiles_query = profiles_query.filter(PIProfile.research_experience_years <= int(min_experience))

    # h-index filter
    if min_hindex.startswith('>'):
        try:
            value = int(min_hindex[1:])
            profiles_query = profiles_query.filter(PIProfile.h_index > value)
        except ValueError:
            pass
    elif min_hindex.isdigit():
        profiles_query = profiles_query.filter(PIProfile.h_index <= int(min_hindex))


    # Sorting
    sort_field = sort_field_map.get(sort, PIProfile.name)
    if direction == 'asc':
        profiles_query = profiles_query.order_by(sort_field.asc().nulls_last())
    else:
        profiles_query = profiles_query.order_by(sort_field.desc().nulls_last())

    # Pagination
    profiles_paginated = profiles_query.paginate(page=page, per_page=per_page, error_out=False)

    # Get distinct values for filters dropdowns
    departments = [d[0] for d in db.session.query(PIProfile.department).distinct().order_by(PIProfile.department).all() if d[0]]
    locations = [l[0] for l in db.session.query(PIProfile.location).distinct().order_by(PIProfile.location).all() if l[0]]

    # Render template with all variables
    return render_template(
        'faculty/full_table.html',
        query=query,
        profiles=profiles_paginated,
        page=page,
        total_pages=profiles_paginated.pages,
        sort=sort,
        direction=direction,
        departments=departments,
        locations=locations,
        selected_department=department_filter,
        selected_location=location_filter,
        min_papers=min_papers,
        min_experience=min_experience,  # Pass to template for dropdown selected state
        min_hindex=min_hindex           # Pass to template for dropdown selected state
    )



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

































from models import Institute, Department, Education, Experience, Publication, ResearchFacility, Project, Technology, Skill, Award, TeamMember, SponsorRequest



















# @app.route('/education', methods=['GET', 'POST'])
# @login_required
# def education():
#     if request.method == 'POST':
#         education_id = request.form.get('education_id')  # For edit case
#         degree_name = request.form.get('degree_name')
#         college = request.form.get('college')
#         university = request.form.get('university')
#         university_address = request.form.get('university_address')
#         start_year = request.form.get('start_year')
#         end_year = request.form.get('end_year')
#         currently_pursuing = request.form.get('currently_pursuing') == 'on'

#         # ✅ Server-side validation: Start Year must be <= End Year
#         if end_year:
#             try:
#                 if int(end_year) < int(start_year):
#                     flash("❌ End Year must be greater than or equal to Start Year.", "error")
#                     return redirect(url_for('education'))
#             except ValueError:
#                 flash("❌ Invalid year format provided.", "error")
#                 return redirect(url_for('education'))

#         if education_id:  # UPDATE existing
#             edu = Education.query.get_or_404(int(education_id))
#             if edu.profile_id != current_user.profile.id:
#                 abort(403)
#             edu.degree_name = degree_name
#             edu.college = college
#             edu.university = university
#             edu.university_address = university_address
#             edu.start_year = start_year
#             edu.end_year = end_year
#             edu.currently_pursuing = currently_pursuing
#             flash("✅ Education updated successfully!", "success")
#         else:  # CREATE new
#             new_edu = Education(
#                 degree_name=degree_name,
#                 college=college,
#                 university=university,
#                 university_address=university_address,
#                 start_year=start_year,
#                 end_year=end_year,
#                 currently_pursuing=currently_pursuing,
#                 profile_id=current_user.profile.id
#             )
#             db.session.add(new_edu)
#             flash("✅ Education added successfully!", "success")

#         db.session.commit()
#         return redirect(url_for('education'))

#     educations = Education.query.filter_by(profile_id=current_user.profile.id).all()
#     return render_template('faculty/education.html', educations=educations)

#     if request.method == 'POST':
#         education_id = request.form.get('education_id')  # For edit case
#         degree_name = request.form.get('degree_name')
#         college = request.form.get('college')
#         university = request.form.get('university')
#         university_address = request.form.get('university_address')
#         start_year = request.form.get('start_year')
#         end_year = request.form.get('end_year')
#         currently_pursuing = True if request.form.get('currently_pursuing') == 'on' else False

#         if education_id:  # UPDATE existing
#             edu = Education.query.get_or_404(int(education_id))
#             if edu.profile_id != current_user.profile.id:
#                 abort(403)
#             edu.degree_name = degree_name
#             edu.college = college
#             edu.university = university
#             edu.university_address = university_address
#             edu.start_year = start_year
#             edu.end_year = end_year
#             edu.currently_pursuing = currently_pursuing
#             flash("Education updated successfully!", "success")
#         else:  # CREATE new
#             new_edu = Education(
#                 degree_name=degree_name,
#                 college=college,
#                 university=university,
#                 university_address=university_address,
#                 start_year=start_year,
#                 end_year=end_year,
#                 currently_pursuing=currently_pursuing,
#                 profile_id=current_user.profile.id
#             )
#             db.session.add(new_edu)
#             flash("Education added successfully!", "success")

#         db.session.commit()
#         return redirect(url_for('education'))

#     educations = Education.query.filter_by(profile_id=current_user.profile.id).all()
#     return render_template('faculty/education.html', educations=educations)


# @app.route('/education/<int:id>/delete', methods=['POST'])
# @login_required
# def delete_education(id):
#     education = Education.query.get_or_404(id)
#     if education.profile_id != current_user.profile.id:
#         abort(403)
#     db.session.delete(education)
#     db.session.commit()
#     flash('Education deleted successfully.', 'success')
#     return redirect(url_for('education'))



# EDUCATION  =========================================================================================================== EDUCATION , EXPERIENCE , 

@app.route('/education', methods=['GET', 'POST'])
@login_required
def education():
    if request.method == 'POST':
        education_id = request.form.get('education_id')
        degree_name = request.form.get('degree_name')
        college = request.form.get('college')
        university = request.form.get('university')
        university_address = request.form.get('university_address')
        start_year = request.form.get('start_year')
        end_year = request.form.get('end_year')
        currently_pursuing = request.form.get('currently_pursuing') == 'on'

        # Server-side validation
        if end_year and not currently_pursuing:
            try:
                if int(end_year) < int(start_year):
                    flash("❌ End Year must be greater than or equal to Start Year.", "error")
                    return redirect(url_for('education'))
            except ValueError:
                flash("❌ Invalid year format provided.", "error")
                return redirect(url_for('education'))

        if education_id:
            edu = Education.query.get_or_404(int(education_id))
            if edu.profile_id != current_user.profile.id:
                abort(403)
            edu.degree_name = degree_name
            edu.college = college
            edu.university = university
            edu.university_address = university_address
            edu.start_year = start_year
            edu.end_year = end_year
            edu.currently_pursuing = currently_pursuing
            flash("✅ Education updated successfully!", "success")
        else:
            new_edu = Education(
                degree_name=degree_name,
                college=college,
                university=university,
                university_address=university_address,
                start_year=start_year,
                end_year=end_year,
                currently_pursuing=currently_pursuing,
                profile_id=current_user.profile.id
            )
            db.session.add(new_edu)
            flash("✅ Education added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving education data.", "error")
        return redirect(url_for('education'))

    # Get pagination parameters from request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get both paginated and all records (for any existing functionality)
    educations_paginated = Education.query.filter_by(profile_id=current_user.profile.id)\
                               .order_by(Education.start_year.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
    
    educations_all = Education.query.filter_by(profile_id=current_user.profile.id).all()
    
    return render_template('faculty/education.html', 
                         educations=educations_paginated,
                         all_educations=educations_all)

@app.route('/education/<int:id>/delete', methods=['POST'])
@login_required
def delete_education(id):
    education = Education.query.get_or_404(id)
    if education.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(education)
    db.session.commit()
    flash('Education deleted successfully.', 'success')
    return redirect(url_for('education'))

    
from datetime import datetime

@app.route('/experience', methods=['GET', 'POST'])
@login_required
def experience():
    if request.method == 'POST':
        experience_id = request.form.get('experience_id')
        project_title = request.form.get('project_title')
        position = request.form.get('position')
        pi = request.form.get('pi')
        pi_affiliation = request.form.get('pi_affiliation')
        college = request.form.get('college')
        university_or_industry = request.form.get('university_or_industry')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        currently_working = True if request.form.get('currently_working') == 'on' else False

        # ✅ Server-side validation: End Date >= Start Date
        if start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                if ed < sd:
                    flash("End Date must be greater than or equal to Start Date.", "error")
                    return redirect(url_for('experience'))
            except ValueError:
                flash("Invalid date format.", "error")
                return redirect(url_for('experience'))

        if experience_id:
            exp = Experience.query.get_or_404(int(experience_id))
            if exp.profile_id != current_user.profile.id:
                abort(403)
            exp.project_title = project_title
            exp.position = position
            exp.pi = pi
            exp.pi_affiliation = pi_affiliation
            exp.college = college
            exp.university_or_industry = university_or_industry
            exp.start_date = start_date
            exp.end_date = end_date
            exp.currently_working = currently_working
            flash("Experience updated successfully!", "success")
        else:
            new_exp = Experience(
                project_title=project_title,
                position=position,
                pi=pi,
                pi_affiliation=pi_affiliation,
                college=college,
                university_or_industry=university_or_industry,
                start_date=start_date,
                end_date=end_date,
                currently_working=currently_working,
                profile_id=current_user.profile.id
            )
            db.session.add(new_exp)
            flash("Experience added successfully!", "success")

        db.session.commit()
        return redirect(url_for('experience'))

     # Get page number from request (default to 1)
    page = request.args.get('page', 1, type=int)
    # Get items per page from request (default to 10)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Create pagination object while keeping original query
    experiences_paginated = Experience.query.filter_by(profile_id=current_user.profile.id)\
                                 .paginate(page=page, per_page=per_page, error_out=False)
    
    # Keep original non-paginated query for any existing template usage
    experiences_all = Experience.query.filter_by(profile_id=current_user.profile.id).all()
    
    return render_template('faculty/experience.html', 
                         experiences=experiences_paginated.items,
                         all_experiences=experiences_all,
                         pagination=experiences_paginated)

    # experiences = Experience.query.filter_by(profile_id=current_user.profile.id).all()
    # return render_template('faculty/experience.html', experiences=experiences)



@app.route('/experience/delete/<int:id>', methods=['POST'])
@login_required
def delete_experience(id):
    exp = Experience.query.get_or_404(id)
    if exp.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(exp)
    db.session.commit()
    flash("Experience deleted successfully!", "success")
    return redirect(url_for('experience'))

@app.route('/publications', methods=['GET', 'POST'])
@login_required
def publications():
    current_year = datetime.now().year
    
    if request.method == 'POST':
        publication_id = request.form.get('publication_id')
        title = request.form.get('title')
        authors = request.form.get('authors')
        journal_or_conference = request.form.get('journal_or_conference')
        year = request.form.get('year')
        doi = request.form.get('doi')
        citation = request.form.get('citation')
        abstract = request.form.get('abstract')
        keywords = request.form.get('keywords')

        # Validate year
        try:
            year = int(year)
            if year < 1900 or year > current_year + 2:
                flash(f"Year must be between 1900 and {current_year + 2}", "error")
                return redirect(url_for('publications'))
        except ValueError:
            flash("Invalid year format", "error")
            return redirect(url_for('publications'))

        if publication_id:
            pub = Publication.query.get_or_404(int(publication_id))
            if pub.profile_id != current_user.profile.id:
                abort(403)
            pub.title = title
            pub.authors = authors
            pub.journal_or_conference = journal_or_conference
            pub.year = year
            pub.doi = doi
            pub.citation = citation
            pub.abstract = abstract
            pub.keywords = keywords
            flash("Publication updated successfully!", "success")
        else:
            new_pub = Publication(
                title=title,
                authors=authors,
                journal_or_conference=journal_or_conference,
                year=year,
                doi=doi,
                citation=citation,
                abstract=abstract,
                keywords=keywords,
                profile_id=current_user.profile.id
            )
            db.session.add(new_pub)
            flash("Publication added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the publication.", "error")
        return redirect(url_for('publications'))

    # Handle GET request with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    publications = Publication.query.filter_by(profile_id=current_user.profile.id)\
                        .order_by(Publication.year.desc())\
                        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/publications.html', 
                         publications=publications,
                         current_year=current_year)

@app.route('/publications/delete/<int:id>', methods=['POST'])
@login_required
def delete_publication(id):
    pub = Publication.query.get_or_404(id)
    if pub.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(pub)
    db.session.commit()
    flash("Publication deleted successfully!", "success")
    return redirect(url_for('publications'))


@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)
        
    if request.method == 'POST':
        project_id = request.form.get('project_id')
        title = request.form.get('title')
        funding_agency = request.form.get('funding_agency')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status')
        description = request.form.get('description')
        keywords = request.form.get('keywords')

        # Validation
        if start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                if ed < sd:
                    flash("End Date must be after Start Date", "error")
                    return redirect(url_for('projects'))
            except ValueError:
                flash("Invalid date format", "error")
                return redirect(url_for('projects'))

        if project_id:
            project = Project.query.get_or_404(int(project_id))
            if project.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            project.title = title
            project.funding_agency = funding_agency
            project.start_date = start_date
            project.end_date = end_date
            project.status = status
            project.description = description
            project.keywords = keywords
            flash("Project updated successfully!", "success")
        else:
            new_project = Project(
                title=title,
                funding_agency=funding_agency,
                start_date=start_date,
                end_date=end_date,
                status=status,
                description=description,
                keywords=keywords,
                pi_profile_id=current_user.profile.pi_profile.id
            )
            db.session.add(new_project)
            flash("Project added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the project", "error")
        
        return redirect(url_for('projects'))

    # Get paginated projects
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    projects = Project.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
                  .order_by(Project.start_date.desc())\
                  .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/projects.html', projects=projects)

@app.route('/projects/delete/<int:id>', methods=['POST'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or project.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "success")
    return redirect(url_for('projects'))


@app.route('/technologies', methods=['GET', 'POST'])
@login_required
def technologies():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        technology_id = request.form.get('technology_id')
        title = request.form.get('title')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        trl = request.form.get('trl')
        usp = request.form.get('usp')
        target_industries = request.form.get('target_industries')
        ip_status = request.form.get('ip_status')
        licensing_intent = request.form.get('licensing_intent')

        # Basic validation
        if not title:
            flash("Title is required", "error")
            return redirect(url_for('technologies'))

        if technology_id:
            tech = Technology.query.get_or_404(int(technology_id))
            if tech.creator_profile_id != current_user.profile.id:
                abort(403)
            tech.title = title
            tech.description = description
            tech.keywords = keywords
            tech.trl = trl
            tech.usp = usp
            tech.target_industries = target_industries
            tech.ip_status = ip_status
            tech.licensing_intent = licensing_intent
            flash("Technology updated successfully!", "success")
        else:
            new_tech = Technology(
                title=title,
                description=description,
                keywords=keywords,
                trl=trl,
                usp=usp,
                target_industries=target_industries,
                ip_status=ip_status,
                licensing_intent=licensing_intent,
                creator_profile_id=current_user.profile.id
            )
            db.session.add(new_tech)
            flash("Technology added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the technology", "error")
        
        return redirect(url_for('technologies'))

    # Get paginated technologies
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    technologies = Technology.query.filter_by(creator_profile_id=current_user.profile.id)\
                         .order_by(Technology.updated_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/technologies.html', technologies=technologies)

@app.route('/technologies/delete/<int:id>', methods=['POST'])
@login_required
def delete_technology(id):
    tech = Technology.query.get_or_404(id)
    if not current_user.profile or tech.creator_profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(tech)
    db.session.commit()
    flash("Technology deleted successfully!", "success")
    return redirect(url_for('technologies'))























from werkzeug.utils import secure_filename
import os

# Configure upload folder (add at the top of app.py)
UPLOAD_SUBDIR = os.path.join('uploads', 'sops')  # for storing in DB
UPLOAD_FOLDER = os.path.join('static', UPLOAD_SUBDIR)  # full path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


#UPLOAD_FOLDER = 'static/uploads/sops'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/research-facilities', methods=['GET', 'POST'])
@login_required
def research_facilities():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)

    if request.method == 'POST':
        facility_id = request.form.get('facility_id')
        equipment_name = request.form.get('equipment_name')
        make = request.form.get('make')
        model = request.form.get('model')
        working_status = request.form.get('working_status')
        equipment_type = request.form.get('equipment_type')

        # SOP file upload
        sop_file = None

        if 'sop_file' in request.files:
            file = request.files['sop_file']
            print("UPLOAD FILE:", file.filename)

            if file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    try:
                        file.save(filepath)
                        print("FILE SAVED TO:", filepath)
                        # Store relative path in DB
                        sop_file = os.path.join('uploads', 'sops', filename)
                        print("SOP FILE PATH TO SAVE IN DB:", sop_file)
                    except Exception as e:
                        print("FILE SAVE ERROR:", str(e))
                else:
                    print("FILE TYPE NOT ALLOWED:", file.filename)
            else:
                print("NO FILE SELECTED")
        else:
            print("NO sop_file FIELD IN REQUEST.FILES")

        # Validate
        if not equipment_name:
            flash("Equipment name is required", "error")
            return redirect(url_for('research_facilities'))

        if facility_id:
            facility = ResearchFacility.query.get_or_404(int(facility_id))
            if facility.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            facility.equipment_name = equipment_name
            facility.make = make
            facility.model = model
            facility.working_status = working_status
            facility.equipment_type = equipment_type
            if sop_file:
                # Delete old file if exists
                if facility.sop_file:
                    old_path = os.path.join('static', facility.sop_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                facility.sop_file = sop_file
            flash("Research facility updated successfully!", "success")
        else:
            new_facility = ResearchFacility(
                equipment_name=equipment_name,
                make=make,
                model=model,
                working_status=working_status,
                equipment_type=equipment_type,
                sop_file=sop_file,
                pi_profile_id=current_user.profile.pi_profile.id
            )
            db.session.add(new_facility)
            flash("Research facility added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("An error occurred while saving the facility", "error")

        return redirect(url_for('research_facilities'))

    # Get paginated facilities
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    facilities = ResearchFacility.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
        .order_by(ResearchFacility.equipment_name.asc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('faculty/research_facilities.html', facilities=facilities)


@app.route('/research-facilities/delete/<int:id>', methods=['POST'])
@login_required
def delete_research_facility(id):
    facility = ResearchFacility.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or facility.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)

    # Delete associated file
    if facility.sop_file:
        full_path = os.path.join('static', facility.sop_file)
        if os.path.exists(full_path):
            os.remove(full_path)

    db.session.delete(facility)
    db.session.commit()
    flash("Research facility deleted successfully!", "success")
    return redirect(url_for('research_facilities'))


@app.route('/download-sop/<int:facility_id>')
@login_required
def download_sop(facility_id):
    facility = ResearchFacility.query.get_or_404(facility_id)
    if not facility.sop_file:
        abort(404)
    
    file_path = os.path.join('static', facility.sop_file)
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True)



@app.route('/skills', methods=['GET', 'POST'])
@login_required
def skills():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        skill_type = request.form.get('skill_type')
        skill_name = request.form.get('skill_name')
        proficiency_level = request.form.get('proficiency_level')

        # Validation
        if not all([skill_type, skill_name]):
            flash("Skill type and name are required", "error")
            return redirect(url_for('skills'))

        if skill_id:
            skill = Skill.query.get_or_404(int(skill_id))
            if skill.profile_id != current_user.profile.id:
                abort(403)
            skill.skill_type = skill_type
            skill.skill_name = skill_name
            skill.proficiency_level = proficiency_level
            flash("Skill updated successfully!", "success")
        else:
            new_skill = Skill(
                skill_type=skill_type,
                skill_name=skill_name,
                proficiency_level=proficiency_level,
                profile_id=current_user.profile.id
            )
            db.session.add(new_skill)
            flash("Skill added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the skill", "error")
        
        return redirect(url_for('skills'))

    # Get paginated skills
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    skills = Skill.query.filter_by(profile_id=current_user.profile.id)\
              .order_by(Skill.skill_type.asc(), Skill.skill_name.asc())\
              .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/skills.html', skills=skills)

@app.route('/skills/delete/<int:id>', methods=['POST'])
@login_required
def delete_skill(id):
    skill = Skill.query.get_or_404(id)
    if not current_user.profile or skill.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(skill)
    db.session.commit()
    flash("Skill deleted successfully!", "success")
    return redirect(url_for('skills'))


from datetime import datetime

@app.route('/awards', methods=['GET', 'POST'])
@login_required
def awards():
    if not current_user.profile:
        abort(403)
        
    if request.method == 'POST':
        award_id = request.form.get('award_id')
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        issuing_organization = request.form.get('issuing_organization')

        # Validation
        if not all([title, date]):
            flash("Title and date are required", "error")
            return redirect(url_for('awards'))

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            if date_obj > datetime.now().date():
                flash("Award date cannot be in the future", "error")
                return redirect(url_for('awards'))
        except ValueError:
            flash("Invalid date format", "error")
            return redirect(url_for('awards'))

        if award_id:
            award = Award.query.get_or_404(int(award_id))
            if award.profile_id != current_user.profile.id:
                abort(403)
            award.title = title
            award.date = date_obj
            award.description = description
            award.issuing_organization = issuing_organization
            flash("Award updated successfully!", "success")
        else:
            new_award = Award(
                title=title,
                date=date_obj,
                description=description,
                issuing_organization=issuing_organization,
                profile_id=current_user.profile.id
            )
            db.session.add(new_award)
            flash("Award added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving the award", "error")
        
        return redirect(url_for('awards'))

    # Get paginated awards
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    awards = Award.query.filter_by(profile_id=current_user.profile.id)\
              .order_by(Award.date.desc())\
              .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('faculty/awards.html', awards=awards)


@app.route('/awards/delete/<int:id>', methods=['POST'])
@login_required
def delete_award(id):
    award = Award.query.get_or_404(id)
    if not current_user.profile or award.profile_id != current_user.profile.id:
        abort(403)
    db.session.delete(award)
    db.session.commit()
    flash("Award deleted successfully!", "success")
    return redirect(url_for('awards'))




@app.route('/team-members', methods=['GET', 'POST'])
@login_required
def team_members():
    if not current_user.profile or not current_user.profile.pi_profile:
        abort(403)
        
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        student_profile_id = request.form.get('student_profile_id')
        name = request.form.get('name')
        position = request.form.get('position')
        status = request.form.get('status')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Validation
        if not student_profile_id and not name:
            flash("Either select a student or provide a name for external members", "error")
            return redirect(url_for('team_members'))

        if status == 'Former' and not end_date:
            flash("End date is required for former members", "error")
            return redirect(url_for('team_members'))

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            
            if end_date_obj and start_date_obj and end_date_obj < start_date_obj:
                flash("End date must be after start date", "error")
                return redirect(url_for('team_members'))
        except ValueError:
            flash("Invalid date format", "error")
            return redirect(url_for('team_members'))

        if member_id:
            member = TeamMember.query.get_or_404(int(member_id))
            if member.pi_profile_id != current_user.profile.pi_profile.id:
                abort(403)
            member.student_profile_id = student_profile_id if student_profile_id else None
            member.name = name if not student_profile_id else None
            member.position = position
            member.status = status
            member.start_date = start_date_obj
            member.end_date = end_date_obj
            flash("Team member updated successfully!", "success")
        else:
            new_member = TeamMember(
                pi_profile_id=current_user.profile.pi_profile.id,
                student_profile_id=student_profile_id if student_profile_id else None,
                name=name if not student_profile_id else None,
                position=position,
                status=status,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            db.session.add(new_member)
            flash("Team member added successfully!", "success")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving team member", "error")
        
        return redirect(url_for('team_members'))

    # Get paginated team members
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    team_members = TeamMember.query.filter_by(pi_profile_id=current_user.profile.pi_profile.id)\
                          .order_by(TeamMember.status.asc(), TeamMember.start_date.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get list of students for dropdown
    students = StudentProfile.query.all()
    
    return render_template('faculty/team_members.html', 
                         team_members=team_members,
                         students=students)

@app.route('/team-members/delete/<int:id>', methods=['POST'])
@login_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    if not current_user.profile or not current_user.profile.pi_profile or member.pi_profile_id != current_user.profile.pi_profile.id:
        abort(403)
    db.session.delete(member)
    db.session.commit()
    flash("Team member deleted successfully!", "success")
    return redirect(url_for('team_members'))




# STUDENTS APP ROUTES: ==================>


from models import StudentProfile

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    student_profile = StudentProfile.query.filter_by(profile_id=profile.id).first()

    if request.method == 'POST':
        if not student_profile:
            student_profile = StudentProfile(profile_id=profile.id)

        student_profile.name = request.form['name']
        student_profile.affiliation = request.form['affiliation']
        student_profile.contact_email = request.form['email']
        student_profile.contact_phone = request.form['contact_phone']
        student_profile.dob = datetime.strptime(request.form['dob'], '%Y-%m-%d') if request.form['dob'] else None
        student_profile.gender = request.form['gender']
        student_profile.address = request.form['address']
        student_profile.research_interests = request.form['current_focus']
        student_profile.why_me = request.form['why_join_lab']
        student_profile.current_status = request.form['current_message']
        # profile_picture logic optional here

        db.session.add(student_profile)
        db.session.commit()
        flash("Student profile updated successfully.", "success")
        return redirect(url_for('student_profile'))

    return render_template('students/student_profile.html', profile=student_profile)



# @app.route('/student/<int:student_id>')
# def student_details(student_id):
#     # Get the student profile with all related data
#     student = StudentProfile.query.get_or_404(student_id)
    
#     # Get related data
#     profile = student.profile
#     educations = profile.educations.order_by(Education.start_year.desc()).all()
#     experiences = profile.experiences.order_by(Experience.start_date.desc()).all()
#     publications = profile.publications.order_by(Publication.year.desc()).all()
#     skills = profile.skills.order_by(Skill.proficiency_level.desc()).all()
#     awards = profile.awards.order_by(Award.date.desc()).all()
    
#     # Get team memberships
#     team_memberships = TeamMember.query.filter_by(student_profile_id=student_id).all()
    
#     return render_template(
#         'student.html',
#         student=student,
#         profile=profile,
#         educations=educations,
#         experiences=experiences,
#         publications=publications,
#         skills=skills,
#         awards=awards,
#         team_memberships=team_memberships
#     )

@app.route('/student/<int:student_id>')
def student_details(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    profile = student.profile

    educations = Education.query.filter_by(profile_id=profile.id).order_by(Education.start_year.desc()).all()
    experiences = Experience.query.filter_by(profile_id=profile.id).order_by(Experience.start_date.desc()).all()
    publications = Publication.query.filter_by(profile_id=profile.id).order_by(Publication.year.desc()).all()
    skills = Skill.query.filter_by(profile_id=profile.id).order_by(Skill.proficiency_level.desc()).all()
    awards = Award.query.filter_by(profile_id=profile.id).order_by(Award.date.desc()).all()

    team_memberships = TeamMember.query.filter_by(student_profile_id=student_id).all()

    return render_template(
        'visit_profile/student.html',
        student=student,
        profile=profile,
        educations=educations,
        experiences=experiences,
        publications=publications,
        skills=skills,
        awards=awards,
        team_memberships=team_memberships
    )



@app.route('/vendor/<int:vendor_id>')
def vendor_profile(vendor_id):
    vendor = VendorProfile.query.get_or_404(vendor_id)
    return render_template('visit_profile/vendor.html', vendor=vendor)


@app.route('/industry/<int:industry_id>')
def industry_profile(industry_id):
    industry = IndustryProfile.query.get_or_404(industry_id)
    return render_template('visit_profile/industry.html', industry=industry)

# @app.route("/faculty/<int:pi_id>")
# def view_faculty_profile(pi_id):
#     pi = PIProfile.query.get_or_404(pi_id)
#     return render_template("facultyinfo.html", pi=pi)



import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Clean string helper to avoid 'nan' and NaN errors
def clean_str(val):
    if pd.isna(val):
        return ''
    s = str(val).strip()
    if s.lower() == 'nan':
        return ''
    return s

@app.route('/admin/faculty', methods=['GET', 'POST'])
def adminfaculty():
    upload_folder = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    if request.method == 'POST':
        if 'faculty_csv' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['faculty_csv']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            try:
                process_faculty_csv(filepath)
                flash('Faculty data imported successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing faculty data: {str(e)}', 'error')
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

            return redirect(url_for('adminfaculty'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    faculty_query = PIProfile.query.join(Profile).join(User).filter(
        User.user_type == 'PI',
        User.account_status == 'Active'
    ).order_by(PIProfile.name)

    faculty = faculty_query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/adminfaculty.html', faculty=faculty)

def process_faculty_csv(filepath):
    df = pd.read_csv(filepath, sep=None, engine='python', on_bad_lines='skip')

    # Normalize columns: lower case, underscores, no spaces, etc.
    df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_') for col in df.columns]

    for idx, row in df.iterrows():
        email = clean_str(row.get('email')).lower()
        if not email:
            print(f"Skipping row {idx}: missing email")
            continue

        if User.query.filter_by(email=email).first():
            print(f"Skipping row {idx}: email {email} already exists")
            continue

        user = User(
            email=email,
            password_hash='scrypt:32768:8:1$I8E3dYyIRDp5xaaU$dc6449d73add70030add0bf15dfee034487d095642dd6d7f2980722c04cb204b2d23bc72c073e8fcc4e76d6b889a244e0f67156e60870bef2385c8efd068108f',
            user_type='PI',
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()

        profile = Profile(
            user_id=user.id,
            profile_type='PI',
            profile_completeness=0,
            visibility_settings='Public',
            last_updated=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.flush()

        # Convert dates safely
        def parse_date(val):
            try:
                return datetime.strptime(str(val).strip(), '%Y-%m-%d').date()
            except:
                return None

        dob = parse_date(row.get('dob'))
        start_date = parse_date(row.get('start_date'))
        last_updated_dt = None
        if 'last_updated_date' in df.columns and pd.notna(row.get('last_updated_date')):
            try:
                last_updated_dt = datetime.strptime(str(row.get('last_updated_date')).strip(), '%Y-%m-%d')
            except:
                last_updated_dt = None

        # Integer fields safely parse
        def parse_int(val):
            try:
                return int(float(val))
            except:
                return None

        pi_profile = PIProfile(
            profile_id=profile.id,
            name=clean_str(row.get('name')),
            department=clean_str(row.get('department')),
            affiliation=clean_str(row.get('affiliation_(full_form)')),  # column name adjusted to CSV header
            affiliation_short=clean_str(row.get('affiliation_(short_form)')),
            location=clean_str(row.get('location_(city)')),
            education_summary=clean_str(row.get('education')),
            research_interest=clean_str(row.get('research_intrest')),  # note spelling as per CSV
            papers_published=parse_int(row.get('papers')),
            total_citations=parse_int(row.get('citations')),
            research_experience_years=parse_int(row.get('research_experience_(number_of_years)')),
            h_index=parse_int(row.get('h_index')),
            gender=clean_str(row.get('gender')),
            dob=dob,
            current_designation=clean_str(row.get('current_designation')),
            start_date=start_date,
            email=email,
            contact_phone=clean_str(row.get('contact_phone')),
            address=clean_str(row.get('address')),
            profile_picture=clean_str(row.get('profile_picture')),
            current_message=clean_str(row.get('current_message')),
            current_focus=clean_str(row.get('current_focus_(research_area)')),
            expectations_from_students=clean_str(row.get('expectations_from_student')),
            why_join_lab=clean_str(row.get('why_join_my_lab')),
            profile_url=clean_str(row.get('profile_url')),
            last_updated=last_updated_dt
        )
        db.session.add(pi_profile)

    db.session.commit()





@app.route('/admin/faculty/delete/<int:id>', methods=['POST'])
def delete_faculty(id):
    pi = PIProfile.query.get_or_404(id)
    profile = Profile.query.get(pi.profile_id)
    user = User.query.get(profile.user_id)

    # Delete in order: pi_profile -> profile -> user
    try:
        db.session.delete(pi)
        db.session.delete(profile)
        db.session.delete(user)
        db.session.commit()
        flash('Faculty deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting faculty: {str(e)}', 'error')

    return redirect(url_for('adminfaculty'))



@app.route('/pi_profile')
@login_required
def view_pi_profile():
    if current_user.user_type != 'PI':
        abort(403)
    
    profile = current_user.profile.pi_profile
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('basic_info'))
    
    return render_template('faculty/profile.html', profile=profile)





@app.route('/faculty/sponsor-request', methods=['GET', 'POST'])
@login_required
def sponsor_request():
    if current_user.user_type != 'PI':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    pi_profile = PIProfile.query.filter_by(profile_id=profile.id).first()

    if not pi_profile:
        flash("No PI Profile found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    if request.method == 'POST':
        event_spec = request.form.get('event_specifications')
        target_amount = request.form.get('target_amount')

        new_request = SponsorRequest(
            profile_id=pi_profile.id,
            event_specifications=event_spec,
            target_amount=target_amount
        )
        db.session.add(new_request)
        db.session.commit()
        flash("Sponsor request submitted!", "success")
        return redirect(url_for('sponsor_request'))

    return render_template('faculty/sponsor_request.html', pi_profile=pi_profile)



from flask import render_template, redirect, url_for, flash, request, session
import random
from datetime import datetime, timedelta

verification_codes = {}

# app.py
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST':
        email = request.form.get('email')
        user_type = request.form.get('user_type')

        # Step 1: Send OTP
        if 'verify_email' in request.form:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('⚠️ Email already registered. Please log in.', 'danger')
                return redirect(url_for('register'))

            # Create or update Register entry
            register_entry = Register.query.filter_by(email=email).first()
            if not register_entry:
                register_entry = Register(
                    email=email,
                    user_type=user_type,
                    created_at=datetime.utcnow(),
                    verified=False
                )
                db.session.add(register_entry)
            else:
                register_entry.user_type = user_type
                register_entry.created_at = datetime.utcnow()
                register_entry.verified = False

            db.session.commit()

            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            verification_codes[email] = {
                'code': otp_code,
                'expires': datetime.now() + timedelta(minutes=10),
                'user_type': user_type
            }

            print(f"[DEBUG] OTP for {email}: {otp_code}")  # Replace with email sending later

            # Save to session
            session['register_email'] = email
            session['register_user_type'] = user_type

            flash('📧 OTP sent to your email. Please enter it below.', 'success')
            return render_template('auth/register.html', form=form, show_verification=True)

        # Step 2: Final form submit
        elif form.validate_on_submit():
            email = form.email.data
            verification_code = request.form.get('verification_code', '').strip()
            password = form.password.data

            otp_data = verification_codes.get(email)
            if not otp_data:
                flash('❌ OTP expired or invalid. Please resend.', 'danger')
                return redirect(url_for('register'))

            if datetime.now() > otp_data['expires']:
                flash('⏰ OTP expired. Please resend.', 'danger')
                return render_template('auth/register.html', form=form, show_verification=True)

            if otp_data['code'] != verification_code:
                flash('❌ Invalid OTP. Please try again.', 'danger')
                return render_template('auth/register.html', form=form, show_verification=True)

            if otp_data['user_type'] != form.user_type.data:
                flash('⚠️ User type changed after OTP. Please re-verify.', 'warning')
                session.pop('register_email', None)
                session.pop('register_user_type', None)
                verification_codes.pop(email, None)
                return redirect(url_for('register'))

            try:
                # Create User
                hashed_password = generate_password_hash(password)
                user = User(
                    email=email,
                    user_type=form.user_type.data,
                    password_hash=hashed_password,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow(),
                    verification_status='Verified',
                    account_status='Active'
                )
                db.session.add(user)
                db.session.flush()  # Get user.id

                # Create Profile
                profile = Profile(
                    user_id=user.id,
                    profile_type=user.user_type,
                    profile_completeness=0,
                    visibility_settings='Public',
                    last_updated=datetime.utcnow()
                )
                db.session.add(profile)

                # Update Register table
                register_entry = Register.query.filter_by(email=email).first()
                if register_entry:
                    register_entry.verified = True
                    register_entry.password_hash = hashed_password
                    register_entry.created_at = datetime.utcnow()

                db.session.commit()

                # Cleanup
                verification_codes.pop(email, None)
                session.pop('register_email', None)
                session.pop('register_user_type', None)

                flash('✅ Registration successful! You may log in now.', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                db.session.rollback()
                print("Error during registration:", e)
                flash('❌ Something went wrong. Please try again.', 'danger')
                return redirect(url_for('register'))

    # Prefill from session
    if 'register_email' in session:
        form.email.data = session['register_email']
    if 'register_user_type' in session:
        form.user_type.data = session['register_user_type']

    return render_template('auth/register.html', form=form)

from flask import session
import random, string, time

@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    otp = ''.join(random.choices(string.digits, k=6))

    # Optional: store timestamp if you want backend expiry too
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_time'] = int(time.time())  # Store generation time

    html_template = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e2e2; border-radius: 8px;">
        <h2 style="color: #2b2b2b;">🔐 Your One-Time Password (OTP)</h2>
        <p>Hi there,</p>
        <p>We received a request to create a new account or verify your email on <strong>jigyasci Research Collaboration Platform</strong>.</p>
        <p style="font-size: 18px; color: #333;">Please use the following OTP to verify your email:</p>
        <div style="font-size: 30px; font-weight: bold; color: #2f54eb; letter-spacing: 4px; text-align: center; margin: 20px 0;">{otp}</div>
        <p>This OTP is valid for <strong>5 minutes</strong>. Please do not share it with anyone.</p>
        <hr style="border: none; border-top: 1px solid #eaeaea; margin: 30px 0;">
        <p style="font-size: 12px; color: #888;">If you didn’t request this, you can safely ignore this email.</p>
        <p style="font-size: 14px; color: #555;">— The jigyasci Team</p>
    </div>
    """

    msg = MailMessage(
        subject='[jigyasci] Your OTP Code',
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"Your OTP is: {otp}"  # fallback plain text
    msg.html = html_template

    mail.send(msg)
    return jsonify({'message': 'OTP sent successfully'})




@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        entered_otp = data.get('otp')
        entered_email = data.get('email')

        if session.get('otp') == entered_otp and session.get('otp_email') == entered_email:
            session.pop('otp', None)
            session.pop('otp_email', None)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid OTP'})
    except Exception as e:
        print("Error in verify_otp:", e)
        return jsonify({'success': False, 'message': 'Something went wrong'}), 500





# @app.route('/login')
# def reglogin():
#     return render_template('auth/login.html')




# Register Blueprints
from routes.admin_routes import admin_bp
from routes.pi_routes import pi_bp
from routes.student_routes import student_bp
from routes.vendor_routes import vendor_bp
from routes.industry_routes import industry_bp
from routes.auth_routes import auth_bp

app.register_blueprint(admin_bp)
app.register_blueprint(pi_bp)
app.register_blueprint(student_bp)
app.register_blueprint(vendor_bp)
app.register_blueprint(industry_bp)
app.register_blueprint(auth_bp)
