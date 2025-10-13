# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, ValidationError
from models import User, UserType  # Import UserType
import re


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# class RegistrationForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     user_type = SelectField('User Type', choices=[
#         ('Student', 'Student'),
#         ('PI', 'Principal Investigator/Lab Director'),
#         ('Industry', 'Industry/Company'),
#         ('Vendor', 'Vendor/Service Provider')
#     ], validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
#     password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
#     submit = SubmitField('Register')

#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user is not None:
#             raise ValidationError('Email already registered. Please use a different email address.')


# form.py


# In forms.py, simplify the email validation
# class RegistrationForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     user_type = SelectField('User Type', choices=[
#         ('Student', 'Student'),
#         ('PI', 'Principal Investigator/Lab Director'),
#         ('Industry', 'Industry/Company'),
#         ('Vendor', 'Vendor/Service Provider')
#     ], validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
#     password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
#     submit = SubmitField('Register')

#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user is not None:
#             raise ValidationError('Email already registered. Please use a different email address.')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_type = SelectField('User Type', coerce=str, validators=[DataRequired()])  # coerce=str for string choices
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Dynamic choices from UserType table (assuming seeded with 'Student', 'PI', 'Industry', 'Vendor')
        self.user_type.choices = [('', 'Select User Type')] + [(ut.name, ut.name) for ut in UserType.query.filter_by(status='Active').all()]

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')


            

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



