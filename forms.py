# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, HiddenField, TelField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, ValidationError
from models import User, UserType, University, College, CurrentDesignation  # Import UserType
import re


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')



# class RegistrationForm(FlaskForm):
#     email       = StringField('Email', validators=[DataRequired(), Email()])
#     user_type   = SelectField('User Type', coerce=str, validators=[DataRequired()])
#     full_name   = StringField('Full Name', validators=[DataRequired()])
#     organization= StringField('Institution / Company', validators=[DataRequired()])
#     designation = StringField('Designation / Role', validators=[DataRequired()])
#     bio         = TextAreaField('Short Bio (Optional)', validators=[Length(max=300)])
#     password    = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
#     password2   = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
#     agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])

#     # Hidden field for frozen user_type
#     user_type_frozen = HiddenField()

#     submit = SubmitField('Complete Registration')

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user_type.choices = [('', 'Select User Type')] + \
#             [(ut.name, ut.name) for ut in UserType.query.filter_by(status='Active').all()]

#     def validate_email(self, field):
#         if User.query.filter_by(email=field.data).first():
#             raise ValidationError('Email already registered.')

# forms.py

class RegistrationForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired("Email is required."), Email("Invalid email format.")],
        render_kw={"placeholder": "you@example.com"}
    )

    user_type = SelectField(
        'User Type',
        validators=[DataRequired("Please select a user type.")],
        coerce=str
    )

    full_name = StringField(
        'Full Name',
        validators=[DataRequired("Full name is required."), Length(2, 100)],
        render_kw={"placeholder": "Dr. John Doe"}
    )

    organization = SelectField(
        'Institution / Company',
        validators=[DataRequired("Please select an institution.")],
        coerce=str,  # ← str mein, int('') error nahi hoga
        render_kw={"class": "form-control rounded-full"}
    )

    designation = SelectField(
        'Designation / Role',
        validators=[DataRequired("Please select a designation.")],
        coerce=str,  # ← str mein
        render_kw={"class": "form-control rounded-full"}
    )

    phone = TelField(
        'Phone Number (Optional)',
        validators=[Optional()],
        render_kw={"placeholder": "+91 9876543210"}
    )

    user_type_frozen = HiddenField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # User Types
        active = UserType.query.filter_by(status='Active').order_by(UserType.name).all()
        self.user_type.choices = [('', 'Select User Type')] + [(t.name, t.name) for t in active]

        # Designations
        desigs = CurrentDesignation.query.filter_by(status='Active').order_by(CurrentDesignation.name).all()
        self.designation.choices = [('', 'Select Designation')] + [(str(d.id), d.name) for d in desigs]

        # Institutions
        unis = University.query.filter_by(status='Active').order_by(University.name).all()
        cols = College.query.filter_by(status='Active').order_by(College.name).all()
        institutions = unis + cols
        self.organization.choices = [('', 'Select Institution')] + [(str(i.id), i.name) for i in institutions]
            





class StudentProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    affiliation = StringField('University/Institution', validators=[DataRequired(), Length(max=100)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say')
    ], validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    research_interests = TextAreaField('Research Interests', validators=[DataRequired()])
    why_me = TextAreaField('Why Choose Me', validators=[Optional()])
    current_status = StringField('Current Status', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Save Profile')

class PIProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    affiliation = StringField('University/Institution', validators=[DataRequired(), Length(max=100)])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say')
    ], validators=[Optional()])
    current_designation = StringField('Current Designation', validators=[DataRequired(), Length(max=100)])
    email = StringField('Academic Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Lab Address', validators=[Optional(), Length(max=200)])
    current_message = TextAreaField('Welcome Message', validators=[Optional()])
    current_focus = TextAreaField('Current Research Focus', validators=[DataRequired()])
    expectations_from_students = TextAreaField('Expectations from Students', validators=[Optional()])
    why_join_lab = TextAreaField('Why Join My Lab', validators=[Optional()])
    submit = SubmitField('Save Profile')

class IndustryProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    gst = StringField('GST Number', validators=[Optional(), Length(max=20)])
    pan = StringField('PAN Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Company Address', validators=[Optional(), Length(max=200)])
    vision = TextAreaField('Company Vision', validators=[Optional()])
    sector = StringField('Industry Sector', validators=[DataRequired(), Length(max=100)])
    team_size = IntegerField('Team Size', validators=[Optional()])
    annual_turnover = StringField('Annual Turnover', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Profile')

class VendorProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[DataRequired(), Length(max=100)])
    dealing_categories = StringField('Dealing Categories', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    gst = StringField('GST Number', validators=[Optional(), Length(max=20)])
    pan = StringField('PAN Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Company Address', validators=[Optional(), Length(max=200)])
    product_categories = StringField('Product Categories', validators=[DataRequired(), Length(max=200)])
    why_me = TextAreaField('Why Choose Us', validators=[Optional()])
    region = StringField('Service Region', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Profile')

class OpportunityForm(FlaskForm):
    type = SelectField('Opportunity Type', choices=[
        ('Internship', 'Internship'),
        ('PhD', 'PhD Position'),
        ('Job', 'Job Opening'),
        ('PostDoc', 'Post-Doctoral Position'),
        ('Project', 'Research Project')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    domain = StringField('Research Domain', validators=[DataRequired(), Length(max=100)])
    eligibility = TextAreaField('Eligibility Criteria', validators=[DataRequired()])
    deadline = DateField('Application Deadline', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    duration = StringField('Duration', validators=[DataRequired(), Length(max=50)])
    compensation = StringField('Compensation/Stipend', validators=[Optional(), Length(max=100)])
    keywords = StringField('Keywords (comma separated)', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Post Opportunity')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('all', 'All'),
        ('profiles', 'Profiles'),
        ('opportunities', 'Opportunities')
    ], default='all')
    submit = SubmitField('Search')



class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(message="Full Name is required."), Length(max=100)])
    email = StringField('Email Address', validators=[DataRequired(message="Email Address is required."), Email(message="Invalid email address."), Length(max=120)])
    subject = SelectField('Subject', choices=[
        ('general', 'General Inquiry'),
        ('partnership', 'Partnership Opportunity'),
        ('technical', 'Technical Support'),
        ('feedback', 'Feedback/Suggestions'),
        ('other', 'Other')
    ], validators=[DataRequired(message="Please select a subject.")])
    message = TextAreaField('Your Message', validators=[DataRequired(message="Message is required."), Length(max=500)])
    submit = SubmitField('Send Message')