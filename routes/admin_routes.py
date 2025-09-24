# routes/admin_routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from models import User, Opportunity, Application, PIProfile, Profile, Institute, Department, OpportunityLink, ApplicationLink, StudentProfile                                                                                               
from datetime import datetime
from extensions import db
import os

from werkzeug.security import generate_password_hash
from io import TextIOWrapper
from sqlalchemy import or_

# Add these imports to routes/admin_routes.py
from models import (
    UserType, AccountStatus, VerificationStatus, ProfileType, VisibilitySetting, Gender,
    ResearchProfile, CurrentStatus, TeamSize, AnnualTurnover, WarrantyStatus, WorkingStatus,
    ProjectStatus, TeamStatus, OpportunityEligibility, OpportunityStatus, Duration,
    CompensationType, ApplicationStatus, MessageStatus, NotificationType,
    NotificationReadStatus, CSRAvailability, InstituteAutonomous, CurrentlyPursuingOption,
    CurrentlyWorkingOption, TRLLevel, IPStatus, LicensingIntent, ProficiencyLevel,
    CurrentDesignation, Sector, EquipmentType, DealingCategory, FundingAgency,
    TeamPosition, OpportunityType, OpportunityDomain, CompensationCurrency,
    CSRFundCategory, InterestArea, InstituteOwnership, InstituteType,
    AdminSettingDepartment, Degree, Publisher, SkillType, ResearchArea, User, Opportunity, Application
)

import io
import csv
import pandas as pd
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', static_folder='static')

def check_admin_profile():
    """Check if admin user has a profile, create one if missing"""
    if current_user.user_type != 'Admin':
        return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'})
    
    if not current_user.profile:
        profile = Profile(user_id=current_user.id, profile_type="Admin")
        db.session.add(profile)
        db.session.commit()
    
    return None

def check_admin_profile_redirect():
    """Check if admin user has a profile, redirect if not"""
    if current_user.user_type != 'Admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if not current_user.profile:
        profile = Profile(user_id=current_user.id, profile_type="Admin")
        db.session.add(profile)
        db.session.commit()
    
    return None

def initialize_opportunity_types_and_statuses():
    """Initialize OpportunityType and OpportunityStatus tables with default values"""
    types = ['Internship', 'Fellowship', 'PhD', 'Job', 'PostDoc', 'Project']
    statuses = ['Active', 'Closed', 'Filled']
    
    for t in types:
        if not OpportunityType.query.filter_by(name=t).first():
            db.session.add(OpportunityType(name=t, status='Active'))
        else:
            opp_type = OpportunityType.query.filter_by(name=t).first()
            opp_type.status = 'Active'
    
    for s in statuses:
        if not OpportunityStatus.query.filter_by(name=s).first():
            db.session.add(OpportunityStatus(name=s, status='Active'))
        else:
            opp_status = OpportunityStatus.query.filter_by(name=s).first()
            opp_status.status = 'Active'
    
    db.session.commit()
    current_app.logger.info("Initialized OpportunityType and OpportunityStatus tables")

@admin_bp.route('/download-opportunity-template')
@login_required
def download_opportunity_template():
    redirect_check = check_admin_profile_redirect()
    if redirect_check:
        return redirect_check

    columns = [
        "Title", "Type", "Domain", "Description", "Deadline", "Duration",
        "Compensation", "Status", "Eligibility", "Keywords", "Advertisement Link"
    ]

    sample_data = [
        {
            "Title": "Machine Learning Research Internship",
            "Type": "Internship",
            "Domain": "Computer Science",
            "Description": "Work on cutting-edge ML projects with our team.",
            "Deadline": "2025-12-31",
            "Duration": "6 months",
            "Compensation": "$2000/month",
            "Status": "Active",
            "Eligibility": "Pursuing MSc/PhD in Computer Science or related field",
            "Keywords": "machine learning, AI, research",
            "Advertisement Link": "https://example.com/internship"
        },
        {
            "Title": "Data Science Fellowship",
            "Type": "Fellowship",
            "Domain": "Data Science",
            "Description": "Collaborate on data-driven research projects.",
            "Deadline": "2025-11-15",
            "Duration": "12 months",
            "Compensation": "$50000/year",
            "Status": "Active",
            "Eligibility": "BSc/MSc in Data Science, Statistics, or related field",
            "Keywords": "data science, analytics, research",
            "Advertisement Link": "https://example.com/fellowship"
        }
    ]

    df = pd.DataFrame(sample_data, columns=columns)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name="opportunity_template.csv",
        mimetype="text/csv"
    )

@admin_bp.route('/opportunities')
@login_required
def admin_opportunities():
    redirect_check = check_admin_profile_redirect()
    if redirect_check:
        return redirect_check

    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Initialize OpportunityType and OpportunityStatus tables
    initialize_opportunity_types_and_statuses()

    opportunities = Opportunity.query.filter_by(
        creator_profile_id=current_user.profile.id
    ).order_by(
        Opportunity.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    opportunity_types = OpportunityType.query.filter_by(status='Active').order_by(OpportunityType.name).all()
    opportunity_statuses = OpportunityStatus.query.filter_by(status='Active').order_by(OpportunityStatus.name).all()
    opportunity_links = OpportunityLink.query.order_by(OpportunityLink.created_at.desc()).all()

    return render_template(
        'admin/opportunities.html',
        opportunities=opportunities,
        opportunity_links=opportunity_links,
        opportunity_types=opportunity_types,
        opportunity_statuses=opportunity_statuses,
        title='My Opportunities'
    )

@admin_bp.route('/add-opportunity', methods=['POST'])
@login_required
def admin_add_opportunity():
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        opportunity = Opportunity(
            creator_profile_id=current_user.profile.id,
            type=request.form.get('type'),
            title=request.form.get('title'),
            domain=request.form.get('domain'),
            eligibility=request.form.get('eligibility'),
            description=request.form.get('description'),
            advertisement_link=request.form.get('advertisement_link'),
            location=request.form.get('location'),
            duration=request.form.get('duration'),
            compensation=request.form.get('compensation'),
            keywords=request.form.get('keywords'),
            status=request.form.get('status', 'Active')
        )
        
        deadline_str = request.form.get('deadline')
        if deadline_str:
            opportunity.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        
        db.session.add(opportunity)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Opportunity added successfully!',
            'opportunity_id': opportunity.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error adding opportunity: {str(e)}'
        })

@admin_bp.route('/bulk-upload-opportunities', methods=['POST'])
@login_required
def admin_bulk_upload_opportunities():
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        current_app.logger.info(f"Uploaded file: {file.filename}")
        if file and allowed_file(file.filename):
            result = process_opportunities_file(file, current_user.profile.id)
            response = {
                'success': True, 
                'message': f'Successfully uploaded {result["processed_count"]} opportunities!'
            }
            if result.get('errors'):
                response['errors'] = result['errors']
            return jsonify(response)
        else:
            return jsonify({
                'success': False, 
                'message': f'Invalid file type: {file.filename}. Please upload an .xlsx, .xls, or .csv file.'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in bulk upload: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error processing file: {str(e)}'
        })

def allowed_file(filename):
    """Check if the file extension is allowed"""
    allowed_extensions = {'csv', 'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_opportunities_file(file, creator_profile_id):
    """Process the uploaded Excel or CSV file and create opportunities."""
    try:
        extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        current_app.logger.info(f"Processing file: {file.filename}, extension: {extension}")

        if extension not in {'xlsx', 'xls', 'csv'}:
            raise ValueError(f"Unsupported file extension: {extension}")

        df = None
        if extension in {'xlsx', 'xls'}:
            try:
                df = pd.read_excel(file, sheet_name="Template")
            except ValueError as e:
                current_app.logger.error(f"Excel sheet 'Template' not found: {str(e)}")
                raise ValueError("Excel file must contain a sheet named 'Template'")
            except Exception as e:
                current_app.logger.error(f"Error reading Excel file: {str(e)}")
                raise ValueError(f"Failed to read Excel file: {str(e)}")
        else:
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except Exception as e:
                current_app.logger.error(f"Error reading CSV file: {str(e)}")
                raise ValueError(f"Failed to read CSV file: {str(e)}")

        if df is None:
            current_app.logger.error("DataFrame could not be created")
            raise ValueError("Failed to create DataFrame from file")

        current_app.logger.info(f"File columns: {list(df.columns)}")

        expected_columns = [
            "Title", "Type", "Domain", "Description", "Deadline", "Duration",
            "Compensation", "Status", "Eligibility", "Keywords", "Advertisement Link"
        ]

        if not all(col in df.columns for col in expected_columns):
            missing_cols = [col for col in expected_columns if col not in df.columns]
            current_app.logger.error(f"Missing columns: {missing_cols}")
            raise ValueError(f"File does not contain all required columns: {', '.join(expected_columns)}")

        processed_count = 0
        errors = []
        for index, row in df.iterrows():
            try:
                if pd.isna(row["Title"]) or pd.isna(row["Type"]) or pd.isna(row["Domain"]):
                    errors.append(f"Row {index + 2}: Missing required fields (Title, Type, or Domain)")
                    current_app.logger.warning(f"Row {index + 2}: Missing required fields")
                    continue

                opportunity_type = OpportunityType.query.filter_by(name=str(row["Type"]), status="Active").first()
                opportunity_status = OpportunityStatus.query.filter_by(name=str(row["Status"]), status="Active").first()
                if not opportunity_type:
                    errors.append(f"Row {index + 2}: Invalid OpportunityType '{row['Type']}'")
                    current_app.logger.warning(f"Row {index + 2}: Invalid OpportunityType '{row['Type']}'")
                    continue
                if not opportunity_status:
                    errors.append(f"Row {index + 2}: Invalid OpportunityStatus '{row['Status']}'")
                    current_app.logger.warning(f"Row {index + 2}: Invalid OpportunityStatus '{row['Status']}'")
                    continue

                opportunity = Opportunity(
                    creator_profile_id=creator_profile_id,
                    title=str(row["Title"]),
                    type=str(row["Type"]),
                    domain=str(row["Domain"]),
                    description=str(row.get("Description", "")) if pd.notna(row.get("Description")) else "",
                    duration=str(row.get("Duration", "")) if pd.notna(row.get("Duration")) else "",
                    compensation=str(row.get("Compensation", "")) if pd.notna(row.get("Compensation")) else "",
                    status=str(row.get("Status", "Active")) if pd.notna(row.get("Status")) else "Active",
                    eligibility=str(row.get("Eligibility", "")) if pd.notna(row.get("Eligibility")) else "",
                    keywords=str(row.get("Keywords", "")) if pd.notna(row.get("Keywords")) else "",
                    advertisement_link=str(row.get("Advertisement Link", "")) if pd.notna(row.get("Advertisement Link")) else ""
                )

                deadline = row.get("Deadline")
                if pd.notna(deadline):
                    try:
                        if isinstance(deadline, str):
                            opportunity.deadline = datetime.strptime(deadline.strip(), '%Y-%m-%d')
                        else:
                            opportunity.deadline = pd.to_datetime(deadline).to_pydatetime()
                    except (ValueError, TypeError) as e:
                        errors.append(f"Row {index + 2}: Invalid deadline format '{deadline}'")
                        current_app.logger.warning(f"Row {index + 2}: Invalid deadline format '{deadline}'")
                        continue

                db.session.add(opportunity)
                processed_count += 1
                db.session.flush()
                current_app.logger.info(f"Row {index + 2}: Successfully added opportunity '{row['Title']}'")
            except Exception as e:
                errors.append(f"Row {index + 2}: Error processing row - {str(e)}")
                current_app.logger.error(f"Row {index + 2}: Error processing row - {str(e)}")
                continue

        if processed_count > 0:
            db.session.commit()
            current_app.logger.info(f"Committed {processed_count} opportunities")
        else:
            current_app.logger.warning("No opportunities to commit")

        response = {'processed_count': processed_count}
        if errors:
            response['errors'] = errors
        return response

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
        return {'success': False, 'message': f"Error processing file: {str(e)}"}

@admin_bp.route('/get-opportunity/<int:id>')
@login_required
def admin_get_opportunity(id):
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        opportunity = Opportunity.query.get_or_404(id)
        
        deadline_str = opportunity.deadline.strftime('%Y-%m-%d') if opportunity.deadline else ''
        created_at_str = opportunity.created_at.strftime('%Y-%m-%d') if opportunity.created_at else ''
        
        return jsonify({
            'success': True, 
            'opportunity': {
                'id': opportunity.id,
                'type': opportunity.type or '',
                'title': opportunity.title or '',
                'domain': opportunity.domain or '',
                'location': opportunity.location or '',
                'deadline': deadline_str,
                'duration': opportunity.duration or '',
                'compensation': opportunity.compensation or '',
                'status': opportunity.status or 'Active',
                'eligibility': opportunity.eligibility or '',
                'description': opportunity.description or '',
                'keywords': opportunity.keywords or '',
                'advertisement_link': opportunity.advertisement_link or '',
                'created_at': created_at_str
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error fetching opportunity {id}: {str(e)}')
        return jsonify({
            'success': False, 
            'message': f'Error fetching opportunity: {str(e)}'
        })

@admin_bp.route('/edit-opportunity/<int:id>', methods=['POST'])
@login_required
def admin_edit_opportunity(id):
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        opportunity = Opportunity.query.get_or_404(id)
        
        opportunity.type = request.form.get('type')
        opportunity.title = request.form.get('title')
        opportunity.domain = request.form.get('domain')
        opportunity.location = request.form.get('location')
        opportunity.duration = request.form.get('duration')
        opportunity.compensation = request.form.get('compensation')
        opportunity.eligibility = request.form.get('eligibility')
        opportunity.description = request.form.get('description')
        opportunity.keywords = request.form.get('keywords')
        opportunity.advertisement_link = request.form.get('advertisement_link')
        opportunity.status = request.form.get('status', 'Active')
        
        deadline_str = request.form.get('deadline')
        if deadline_str:
            opportunity.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        else:
            opportunity.deadline = None
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Opportunity updated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error updating opportunity: {str(e)}'
        })

@admin_bp.route('/delete-opportunity/<int:id>', methods=['POST'])
@login_required
def admin_delete_opportunity(id):
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        opportunity = Opportunity.query.get_or_404(id)
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Opportunity deleted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error deleting opportunity: {str(e)}'
        })


# =========================================================================================
#                     ADD OPPORTUNITIES LINK ROUTES
# =========================================================================================

# Add opportunity link (modal form)
@admin_bp.route('/add-opportunity-link', methods=['POST'])
@login_required
def admin_add_opportunity_link():
    # Check admin profile first
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        data = request.get_json()
        if not data or 'links' not in data:
            return jsonify({'success': False, 'message': 'No data received'})
        
        added_count = 0
        for link_data in data['links']:
            # Validate required fields
            if not link_data.get('url'):
                continue
                
            # Check if link already exists for this user
            existing_link = OpportunityLink.query.filter_by(
                url=link_data.get('url'),
                added_by=current_user.profile.id
            ).first()
            
            if existing_link:
                continue  # Skip if link already exists
                
            # Create opportunity link
            opportunity_link = OpportunityLink(
                title=link_data.get('title', ''),
                url=link_data.get('url'),
                description=link_data.get('description', ''),
                added_by=current_user.profile.id
            )
            
            db.session.add(opportunity_link)
            added_count += 1
        
        if added_count == 0:
            return jsonify({
                'success': False,
                'message': 'No new links were added (possible duplicates detected)'
            })
            
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully added {added_count} opportunity link(s)!'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding opportunity links: {str(e)}')
        return jsonify({
            'success': False, 
            'message': f'Error adding links: {str(e)}'
        })


# Delete opportunity link
@admin_bp.route('/delete-opportunity-link/<int:id>', methods=['POST'])
@login_required
def admin_delete_opportunity_link(id):
    # Check admin profile first
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        link = OpportunityLink.query.get_or_404(id)
        db.session.delete(link)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Opportunity link deleted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error deleting link: {str(e)}'
        })

# Toggle opportunity link status
@admin_bp.route('/toggle-opportunity-link/<int:id>', methods=['POST'])
@login_required
def admin_toggle_opportunity_link(id):
    # Check admin profile first
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        link = OpportunityLink.query.get_or_404(id)
        data = request.get_json()
        link.is_active = data.get('is_active', not link.is_active)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Opportunity link {"activated" if link.is_active else "deactivated"} successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error updating link: {str(e)}'
        })


# Get opportunity link data for editing
@admin_bp.route('/get-opportunity-link/<int:id>', methods=['GET'])
@login_required
def admin_get_opportunity_link(id):
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        link = OpportunityLink.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': link.id,
                'title': link.title or '',
                'url': link.url or '',
                'description': link.description or '',
                'is_active': link.is_active
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching opportunity link {id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error fetching link: {str(e)}'
        }), 404

# Edit opportunity link route
@admin_bp.route('/edit-opportunity-link/<int:id>', methods=['POST'])
@login_required
def admin_edit_opportunity_link(id):
    profile_check = check_admin_profile()
    if profile_check:
        return profile_check
    
    try:
        link = OpportunityLink.query.get_or_404(id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
            
        link.title = data.get('title', '')
        link.url = data.get('url', '')
        link.description = data.get('description', '')
        link.is_active = data.get('is_active', True)
        
        if not link.url:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Opportunity link updated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating opportunity link: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error updating link: {str(e)}'
        }), 500











# ======================================================================================================================
#                                DASHBOARD
# ======================================================================================================================

@admin_bp.route('/dashboard')   
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

    return render_template('admin/admin_settings/dashboard.html',
                          title='Admin Dashboard',
                          stats=stats,
                          recent_users=recent_users,
                          recent_opportunities=recent_opportunities)




# ===========================================================================================================INSTITUDE INSTITUDE INSTITUDE INSTITUDE


REQUIRED_COLUMNS = [
    "Name", "Centers", "Lab Sector", "FocusArea", "KeyResources", 
    "Researchers", "Director", "City", "State", "Link", "Ownership"
]

@admin_bp.route('/add-institute', methods=['GET', 'POST'])
@login_required
def add_institute():
    if current_user.user_type != 'Admin':
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = request.args.get('query', '')
    
    # Fetch dropdown options for manual addition
    ownerships = InstituteOwnership.query.filter_by(status='Active').all()
    sectors = Sector.query.filter_by(status='Active').all()
    
    # Get all institutes for admin view
    institutes_query = Institute.query
    
    if query:
        institutes_query = institutes_query.filter(
            or_(
                Institute.name.ilike(f'%{query}%'),
                Institute.centers.ilike(f'%{query}%'),
                Institute.lab_sector.ilike(f'%{query}%'),
                Institute.director.ilike(f'%{query}%')
            )
        )
    
    institutes = institutes_query.order_by(Institute.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    if request.method == 'POST':
        # Check if it's CSV upload or manual add
        if 'file' in request.files and request.files['file'].filename:
            return handle_institute_csv_upload()
        else:
            return handle_manual_institute_addition()
    
    return render_template('admin/institute/add_institute.html', 
                         institutes=institutes,
                         ownerships=ownerships,
                         sectors=sectors,
                         query=query)

def handle_manual_institute_addition():
    """Handle manual institute addition"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        
        # Validate required fields
        required_fields = ['name', 'centers', 'lab_sector', 'focus_area', 'key_resources', 
                           'researchers', 'director', 'city', 'state', 'link', 'ownership']
        for field in required_fields:
            if not request.form.get(field, '').strip():
                flash(f"{field.capitalize().replace('_', ' ')} is required for manual addition", "error")
                return redirect(url_for('admin.add_institute'))
        
        # Create institute
        institute = Institute(
            name=name,
            centers=request.form.get('centers', '').strip(),
            lab_sector=request.form.get('lab_sector', '').strip(),
            focus_area=request.form.get('focus_area', '').strip(),
            key_resources=request.form.get('key_resources', '').strip(),
            researchers=request.form.get('researchers', '').strip(),
            director=request.form.get('director', '').strip(),
            city=request.form.get('city', '').strip(),
            state=request.form.get('state', '').strip(),
            link=request.form.get('link', '').strip(),
            ownership=request.form.get('ownership', '').strip()
        )
        
        db.session.add(institute)
        db.session.commit()
        
        flash(f"Institute {institute.name} added successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding institute manually: {str(e)}")
        flash(f"Error adding institute: {str(e)}", "error")
    
    return redirect(url_for('admin.add_institute'))

def handle_institute_csv_upload():
    """Handle CSV file upload for bulk institute addition"""
    try:
        csv_file = request.files['file']
        
        # Validate file
        if not csv_file or csv_file.filename == '':
            flash("No file selected. Please choose a valid CSV file.", "error")
            return redirect(url_for('admin.add_institute'))
        
        if not csv_file.filename.lower().endswith('.csv'):
            flash("Invalid file format. Please upload a valid CSV file.", "error")
            return redirect(url_for('admin.add_institute'))
        
        # Read and process CSV
        stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream, delimiter=',')
        
        # Validate CSV headers
        missing_headers = [h for h in REQUIRED_COLUMNS if h not in csv_reader.fieldnames]
        if missing_headers:
            flash(f"CSV missing required columns: {', '.join(missing_headers)}", "error")
            return redirect(url_for('admin.add_institute'))
        
        added_count = 0
        errors = []
        row_num = 2
        
        for row in csv_reader:
            try:
                # Clean and validate data
                name = row.get('Name', '').strip()
                
                if not name:
                    errors.append(f"Row {row_num}: Name is required")
                    row_num += 1
                    continue
                
                # No duplicate check for name as per requirement
                
                lab_sector = ', '.join([x.strip() for x in row.get("Lab Sector", "").split(',') if x.strip()])
                focus_area = ', '.join([x.strip() for x in row.get("FocusArea", "").split(',') if x.strip()])
                key_resources = ', '.join([x.strip() for x in row.get("KeyResources", "").split(',') if x.strip()])
                
                institute = Institute(
                    name=name,
                    centers=row.get('Centers', '').strip(),
                    lab_sector=lab_sector,
                    focus_area=focus_area,
                    key_resources=key_resources,
                    researchers=row.get('Researchers', '').strip(),
                    director=row.get('Director', '').strip(),
                    city=row.get('City', '').strip(),
                    state=row.get('State', '').strip(),
                    link=row.get('Link', '').strip(),
                    ownership=row.get('Ownership', '').strip()
                )
                
                db.session.add(institute)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
            
            row_num += 1
        
        if added_count > 0:
            db.session.commit()
            flash(f"Successfully imported {added_count} institute{'s' if added_count != 1 else ''} from the CSV file.", "success")
        else:
            db.session.rollback()
            flash("No institutes were imported from the CSV file. Please check the file format and data.", "warning")
        
        if errors:
            error_msg = "; ".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"; and {len(errors) - 5} more error{'s' if len(errors) - 5 != 1 else ''}."
            flash(f"Some issues were encountered during import: {error_msg}", "warning")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing CSV file: {str(e)}")
        flash(f"Failed to import institute data due to an error: {str(e)}. Please ensure the CSV file is correctly formatted.", "error")
    
    return redirect(url_for('admin.add_institute'))

@admin_bp.route('/delete_institute/<int:institute_id>', methods=['POST'])
@login_required
def delete_institute(institute_id):
    if current_user.user_type != 'Admin':
        abort(403)
    
    try:
        institute = Institute.query.get_or_404(institute_id)
        db.session.delete(institute)
        db.session.commit()
        flash("Institute deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting institute: {str(e)}")
        flash(f"Error deleting institute: {str(e)}", "error")
    
    return redirect(url_for('admin.add_institute'))

@admin_bp.route('/download-institute-template')
@login_required
def download_institute_template():
    if current_user.user_type != 'Admin':
        abort(403)
    
    # Create CSV template
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = REQUIRED_COLUMNS
    writer.writerow(headers)
    
    # Write sample data
    sample_data = [
        'Example Institute', 'Research Center 1, Center 2', 'Computer Science', 'AI, Machine Learning', 'High-performance computers, Datasets',
        'John Doe, Jane Smith', 'Dr. Director', 'New York', 'NY', 'https://example.com', 'Public'
    ]
    writer.writerow(sample_data)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='institute_template.csv'
    )


# DEPARTMENT =============================================================================================== DEPARTMENT DEPARTMENT DEPARTMENT DEPARTMENT 



@admin_bp.route('/departments')
def departments():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Department.query.paginate(page=page, per_page=per_page)

    total_departments = pagination.total
    total_pages = pagination.pages

    return render_template(
        'admin/department/departments.html',
        departments=pagination.items,
        page=page,
        total_pages=total_pages,
        total_departments=total_departments
    )


@admin_bp.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form.get('name')
        institute_ids = request.form.getlist('institute_ids')

        if not name:
            flash('Department name is required!', 'error')
            return redirect(url_for('admin.add_department'))

        existing_dept = Department.query.filter_by(name=name).first()
        if existing_dept:
            flash('Department already exists!', 'error')
            return redirect(url_for('admin.add_department'))

        institutes = Institute.query.filter(Institute.id.in_(institute_ids)).all()
        new_dept = Department(name=name, institutes=institutes)
        db.session.add(new_dept)
        db.session.commit()

        flash('Department added successfully!', 'success')
        return redirect(url_for('admin.departments'))

    institutes = Institute.query.all()
    return render_template('admin/department/add_department.html', institutes=institutes)


def allowed_file(filename):
    """Check if the file has a valid CSV extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

    
@admin_bp.route('/upload_departments', methods=['POST'])
def upload_departments():
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin.departments'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.departments'))
    
    if file and allowed_file(file.filename):
        try:
            stream = TextIOWrapper(file.stream, encoding='utf-8')
            csv_reader = csv.DictReader(stream)
            
            departments_added = 0
            for row in csv_reader:
                if not row.get('name'):
                    flash('CSV file must contain a "name" column', 'error')
                    return redirect(url_for('admin.departments'))
                
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
    
    return redirect(url_for('admin.departments'))



@admin_bp.route('/edit_department/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    department = Department.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        institute_ids = request.form.getlist('institute_ids')

        if not name:
            flash('Department name is required!', 'error')
            return redirect(url_for('admin.edit_department', id=id))

        # Check if another department already has this name
        existing_dept = Department.query.filter(Department.name == name, Department.id != id).first()
        if existing_dept:
            flash('Another department with this name already exists!', 'error')
            return redirect(url_for('admin.edit_department', id=id))

        department.name = name
        department.institutes = Institute.query.filter(Institute.id.in_(institute_ids)).all()
        db.session.commit()

        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin.departments'))

    institutes = Institute.query.all()
    selected_ids = [inst.id for inst in department.institutes]
    return render_template('admin/department/edit_department.html', department=department, institutes=institutes, selected_ids=selected_ids)



@admin_bp.route('/delete_department/<int:id>', methods=['POST'])
def delete_department(id):
    department = Department.query.get_or_404(id)
    
    try:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {str(e)}', 'error')
    
    return redirect(url_for('admin.departments'))


# ========================================================================================STUDENTS

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
def adminstudents():
    if current_user.user_type != 'Admin':
        abort(403)
    
    if request.method == 'POST':
        # Check if it's CSV upload or manual add
        if 'student_csv' in request.files and request.files['student_csv'].filename:
            return handle_student_csv_upload()
        else:
            return handle_manual_student_addition()
    
    # GET request - display students
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = request.args.get('query', '')
    
    # Get all students for admin view
    students_query = StudentProfile.query
    
    if query:
        students_query = students_query.filter(
            or_(
                StudentProfile.name.ilike(f'%{query}%'),
                StudentProfile.affiliation.ilike(f'%{query}%'),
                StudentProfile.research_interests.ilike(f'%{query}%'),
                StudentProfile.contact_email.ilike(f'%{query}%')
            )
        )
    
    students = students_query.order_by(StudentProfile.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/adminstudents.html', 
                         students=students,
                         query=query)

@admin_bp.route('/add-student', methods=['POST'])
@login_required
def add_student():
    """Separate route for manual student addition"""
    if current_user.user_type != 'Admin':
        abort(403)
    
    return handle_manual_student_addition()

def handle_manual_student_addition():
    """Handle manual student addition"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        affiliation = request.form.get('affiliation', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        
        # Validate required fields
        if not name:
            flash("Name is required for manual addition", "error")
            return redirect(url_for('admin.adminstudents'))
        
        if not affiliation:
            flash("Affiliation is required for manual addition", "error")
            return redirect(url_for('admin.adminstudents'))
        
        # Create email if not provided (you might want to change this logic)
        if not contact_email:
            # Generate a temporary email or require it
            flash("Contact email is required", "error")
            return redirect(url_for('admin.adminstudents'))
        
        # Check if user with this email already exists
        if User.query.filter_by(email=contact_email).first():
            flash(f"User with email {contact_email} already exists.", "error")
            return redirect(url_for('admin.adminstudents'))
        
        # Create new user
        user = User(
            email=contact_email,
            user_type='Student',
            password_hash=generate_password_hash('temppassword123'),  # Use proper password hashing
            account_status='Active',
            verification_status='Verified',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create profile
        profile = Profile(
            user_id=user.id,
            profile_type='Student',
            profile_completeness=50,
            visibility_settings='Public',
            last_updated=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.flush()  # Get profile ID
        
        # Create student profile
        student_profile = StudentProfile(
            profile_id=profile.id,
            name=name,
            affiliation=affiliation,
            contact_email=contact_email,
            contact_phone=request.form.get('contact_phone', '').strip(),
            address=request.form.get('address', '').strip(),
            research_interests=request.form.get('research_interests', '').strip(),
            why_me=request.form.get('why_me', '').strip(),
            current_status=request.form.get('current_status', '').strip(),
        )
        
        # Handle date field
        dob_str = request.form.get('dob', '').strip()
        if dob_str:
            try:
                student_profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid date format for Date of Birth", "warning")
        
        # Handle gender field
        gender = request.form.get('gender', '').strip()
        if gender and gender != '':
            student_profile.gender = gender
        
        db.session.add(student_profile)
        db.session.commit()
        
        flash(f"Student {student_profile.name} added successfully! Login email: {contact_email}, Temporary password: temppassword123", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding student manually: {str(e)}")
        flash(f"Error adding student: {str(e)}", "error")
    
    return redirect(url_for('admin.adminstudents'))

def handle_student_csv_upload():
    """Handle CSV file upload for bulk student addition"""
    try:
        csv_file = request.files['student_csv']
        
        # Validate file
        if not csv_file or csv_file.filename == '':
            flash("No file selected", "error")
            return redirect(url_for('admin.adminstudents'))
        
        if not csv_file.filename.lower().endswith('.csv'):
            flash("Please upload a valid CSV file", "error")
            return redirect(url_for('admin.adminstudents'))
        
        # Read and process CSV
        stream = TextIOWrapper(csv_file.stream, encoding='utf-8')
        csv_reader = csv.DictReader(stream)
        
        # Validate CSV headers
        required_headers = ['name', 'affiliation', 'contact_email']
        missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
        if missing_headers:
            flash(f"CSV missing required columns: {', '.join(missing_headers)}", "error")
            return redirect(url_for('admin.adminstudents'))
        
        added_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Clean and validate data
                name = row.get('name', '').strip()
                affiliation = row.get('affiliation', '').strip()
                contact_email = row.get('contact_email', '').strip().lower()
                
                if not name:
                    errors.append(f"Row {row_num}: Name is required")
                    continue
                
                if not affiliation:
                    errors.append(f"Row {row_num}: Affiliation is required")
                    continue
                
                if not contact_email:
                    errors.append(f"Row {row_num}: Contact email is required")
                    continue
                
                # Check if user already exists
                if User.query.filter_by(email=contact_email).first():
                    errors.append(f"Row {row_num}: User with email {contact_email} already exists")
                    continue
                
                # Create user
                user = User(
                    email=contact_email,
                    user_type='Student',
                    password_hash=generate_password_hash('temppassword123'),
                    account_status='Active',
                    verification_status='Verified',
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
                db.session.add(user)
                db.session.flush()
                
                # Create profile
                profile = Profile(
                    user_id=user.id,
                    profile_type='Student',
                    profile_completeness=50,
                    visibility_settings='Public',
                    last_updated=datetime.utcnow()
                )
                db.session.add(profile)
                db.session.flush()
                
                # Create student profile
                student_profile = StudentProfile(
                    profile_id=profile.id,
                    name=name,
                    affiliation=affiliation,
                    contact_email=contact_email,
                    contact_phone=row.get('contact_phone', '').strip(),
                    address=row.get('address', '').strip(),
                    research_interests=row.get('research_interests', '').strip(),
                    why_me=row.get('why_me', '').strip(),
                    current_status=row.get('current_status', '').strip(),
                )
                
                # Handle date field
                dob_str = row.get('dob', '').strip()
                if dob_str:
                    try:
                        student_profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format for DOB (use YYYY-MM-DD)")
                        continue
                
                # Handle gender field
                gender = row.get('gender', '').strip()
                if gender and gender.lower() not in ['', 'none', 'n/a']:
                    student_profile.gender = gender
                
                db.session.add(student_profile)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        if added_count > 0:
            db.session.commit()
            flash(f"Successfully added {added_count} students from CSV", "success")
        else:
            db.session.rollback()
            flash("No students were added from the CSV", "warning")
        
        if errors:
            error_msg = "; ".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f" ... and {len(errors) - 5} more errors"
            flash(f"Some errors occurred: {error_msg}", "warning")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing CSV file: {str(e)}")
        flash(f"Error processing CSV file: {str(e)}", "error")
    
    return redirect(url_for('admin.adminstudents'))

@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.user_type != 'Admin':
        abort(403)
    
    try:
        student = StudentProfile.query.get_or_404(student_id)
        profile = student.profile
        user = profile.user
        
        # Delete in reverse order of creation
        db.session.delete(student)
        db.session.delete(profile)
        db.session.delete(user)
        db.session.commit()
        
        flash("Student deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting student: {str(e)}")
        flash(f"Error deleting student: {str(e)}", "error")
    
    return redirect(url_for('admin.adminstudents'))

# Helper route to download CSV template
@admin_bp.route('/download-student-template')
@login_required
def download_student_template():
    if current_user.user_type != 'Admin':
        abort(403)
    
    # Create CSV template
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'name', 'affiliation', 'contact_email', 'contact_phone', 
        'dob', 'gender', 'address', 'research_interests', 
        'why_me', 'current_status'
    ]
    writer.writerow(headers)
    
    # Write sample data
    sample_data = [
        'John Doe', 'University of Example', 'john.doe@example.com', '1234567890',
        '1995-01-15', 'Male', '123 Example St, City', 'Machine Learning, AI',
        'Passionate about research', 'PhD Student'
    ]
    writer.writerow(sample_data)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='student_template.csv'
    )
# ==============================================================================================================FACULTY FACULTY FACULTY FACULTY

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


# Update the adminfaculty route to handle both CSV and manual addition
@admin_bp.route('/faculty', methods=['GET', 'POST'])
def adminfaculty():
    upload_folder = os.path.join(current_app.root_path, 'Uploads')

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Fetch dropdown options for manual addition
    designations = CurrentDesignation.query.filter_by(status='Active').all()
    departments = AdminSettingDepartment.query.filter_by(status='Active').all()
    research_areas = ResearchArea.query.filter_by(status='Active').all()

    if request.method == 'POST':
        if 'faculty_csv' in request.files:
            file = request.files['faculty_csv']
            if file.filename == '':
                flash('No file selected. Please choose a valid CSV file.', 'error')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                try:
                    process_faculty_csv(filepath)
                except Exception as e:
                    db.session.rollback()
                    flash(f'Failed to import faculty data due to an error: {str(e)}. Please ensure the CSV file is correctly formatted.', 'error')
                finally:
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                flash('Invalid file format. Please upload a valid CSV file.', 'error')
        else:
            # Manual addition logic
            email = request.form.get('email', '').lower()
            
            if not email:
                flash('Email is required for manual addition.', 'error')
                return redirect(url_for('admin.adminfaculty'))
            
            if User.query.filter_by(email=email).first():
                flash(f'A user with the email {email} already exists.', 'error')
                return redirect(url_for('admin.adminfaculty'))
            
            # Create user
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

            # Create profile
            profile = Profile(
                user_id=user.id,
                profile_type='PI',
                profile_completeness=0,
                visibility_settings='Public',
                last_updated=datetime.utcnow()
            )
            db.session.add(profile)
            db.session.flush()

            # Parse dates
            def parse_date(val):
                try:
                    return datetime.strptime(val, '%Y-%m-%d').date() if val else None
                except:
                    return None

            # Create PI profile
            pi_profile = PIProfile(
                profile_id=profile.id,
                name=request.form.get('name'),
                department=request.form.get('department'),
                affiliation=request.form.get('affiliation'),
                affiliation_short=request.form.get('affiliation_short'),
                location=request.form.get('location'),
                education_summary=request.form.get('education'),
                research_interest=request.form.get('research_interest'),
                papers_published=int(request.form.get('papers_published', 0) or 0),
                total_citations=int(request.form.get('total_citations', 0) or 0),
                research_experience_years=int(request.form.get('research_experience_years', 0) or 0),
                h_index=int(request.form.get('h_index', 0) or 0),
                gender=request.form.get('gender'),
                dob=parse_date(request.form.get('dob')),
                current_designation=request.form.get('current_designation'),
                start_date=parse_date(request.form.get('start_date')),
                email=email,
                contact_phone=request.form.get('contact_phone'),
                address=request.form.get('address'),
                current_message=request.form.get('current_message'),
                current_focus=request.form.get('current_focus'),
                expectations_from_students=request.form.get('expectations_from_students'),
                why_join_lab=request.form.get('why_join_lab'),
                profile_url=request.form.get('profile_url'),
                last_updated=datetime.utcnow()
            )
            db.session.add(pi_profile)
            db.session.commit()
            flash(f'Faculty profile for {pi_profile.name} added successfully.', 'success')
        
        return redirect(url_for('admin.adminfaculty'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    faculty_query = PIProfile.query.join(Profile).join(User).filter(
        User.user_type == 'PI',
        User.account_status == 'Active'
    ).order_by(PIProfile.name)

    faculty = faculty_query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/adminfaculty.html', 
                         faculty=faculty,
                         designations=designations,
                         departments=departments,
                         research_areas=research_areas)





def process_faculty_csv(filepath):
    df = pd.read_csv(filepath, sep=None, engine='python', on_bad_lines='skip')

    # Normalize columns: lower case, underscores, no spaces, etc.
    df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_') for col in df.columns]

    added_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        email = clean_str(row.get('email')).lower()
        if not email:
            errors.append(f"Row {idx + 2}: Missing email")
            continue

        if User.query.filter_by(email=email).first():
            errors.append(f"Row {idx + 2}: Email {email} already exists")
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
            affiliation=clean_str(row.get('affiliation_(full_form)')),
            affiliation_short=clean_str(row.get('affiliation_(short_form)')),
            location=clean_str(row.get('location_(city)')),
            education_summary=clean_str(row.get('education')),
            research_interest=clean_str(row.get('research_intrest')),
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
        added_count += 1

    if added_count > 0:
        db.session.commit()
        flash(f"Successfully imported {added_count} faculty profile{'s' if added_count != 1 else ''} from the CSV file.", "success")
    else:
        db.session.rollback()
        flash("No faculty profiles were imported from the CSV file. Please check the file format and data.", "warning")

    if errors:
        error_msg = "; ".join(errors[:5])  # Show up to 5 errors
        if len(errors) > 5:
            error_msg += f"; and {len(errors) - 5} more error{'s' if len(errors) - 5 != 1 else ''}."
        flash(f"Some issues were encountered during import: {error_msg}", "warning")


@admin_bp.route('/faculty/delete/<int:id>', methods=['POST'])
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

    return redirect(url_for('admin.adminfaculty'))

@admin_bp.route('/download-faculty-template')
@login_required
def download_faculty_template():
    if current_user.user_type != 'Admin':
        abort(403)
    
    # Create CSV template
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header (adjust headers to match faculty CSV processing in process_faculty_csv)
    headers = [
        'name', 'email', 'department', 'affiliation_(full_form)', 'affiliation_(short_form)',
        'location_(city)', 'education', 'research_intrest', 'papers', 'citations',
        'research_experience_(number_of_years)', 'h_index', 'gender', 'dob',
        'current_designation', 'start_date', 'contact_phone', 'address',
        'profile_picture', 'current_message', 'current_focus_(research_area)',
        'expectations_from_student', 'why_join_my_lab', 'profile_url'
    ]
    writer.writerow(headers)
    
    # Write sample data
    sample_data = [
        'Jane Doe', 'jane.doe@example.com', 'Computer Science', 'University of Example', 'UoE',
        'New York', 'PhD in Computer Science', 'Artificial Intelligence, Data Science', '50', '1000',
        '10', '20', 'Female', '1985-05-20', 'Professor', '2015-01-01', '1234567890',
        '123 Example St, City', '', 'Looking for motivated students', 'AI Research',
        'Strong analytical skills', 'Innovative lab environment', 'http://example.com/janedoe'
    ]
    writer.writerow(sample_data)
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='faculty_template.csv'
    )




@admin_bp.route('/pi_profile')
@login_required
def view_pi_profile():
    if current_user.user_type != 'PI':
        abort(403)
    
    profile = current_user.profile.pi_profile
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('admin.basic_info'))
    
    return render_template('faculty/profile.html', profile=profile)


@admin_bp.route('/faculty/sponsor-request', methods=['GET', 'POST'])
@login_required
def sponsor_request():
    if current_user.user_type != 'PI':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    pi_profile = PIProfile.query.filter_by(profile_id=profile.id).first()

    if not pi_profile:
        flash("No PI Profile found.", "danger")
        return redirect(url_for('pi.faculty_dashboard'))

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
        return redirect(url_for('admin.sponsor_request'))

    return render_template('faculty/sponsor_request.html', pi_profile=pi_profile)









# Add this to your existing imports
from functools import wraps
from flask import abort

# ===========================================================================================================
# OPPORTUNITY MANAGEMENT ROUTES
# ===========================================================================================================

# Add this helper function at the top of your admin_routes.py
def get_or_create_admin_profile():
    """Get or create a profile for admin users"""
    if not current_user.profile:
        # Create a profile for admin if it doesn't exist
        profile = Profile(
            user_id=current_user.id,
            profile_type='Admin',
            profile_completeness=100,
            visibility_settings='Public',
            last_updated=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.commit()
        return profile
    return current_user.profile

# Update the admin_opportunities route
# @admin_bp.route('/opportunities')
# @login_required
# @admin_required
# def admin_opportunities():
#     # Get or create admin profile
#     profile = get_or_create_admin_profile()
    
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 10, type=int)
    
#     # Get opportunities created by the admin
#     opportunities = Opportunity.query.filter_by(creator_profile_id=profile.id)\
#         .order_by(Opportunity.created_at.desc())\
#         .paginate(page=page, per_page=per_page, error_out=False)
    
#     return render_template('admin/opportunities.html', opportunities=opportunities)

# # Update the admin_add_opportunity route
# @admin_bp.route('/add-opportunity', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def admin_add_opportunity():
#     # Get or create admin profile
#     profile = get_or_create_admin_profile()
    
#     if request.method == 'POST':
#         try:
#             form_data = request.form
            
#             # Convert empty strings to None for optional fields
#             def clean_field(value):
#                 return value if value else None
                
#             # Create new opportunity
#             opportunity = Opportunity(creator_profile_id=profile.id)
            
#             # Required fields
#             opportunity.type = form_data['type']
#             opportunity.title = form_data['title']
            
#             # Optional fields
#             opportunity.domain = clean_field(form_data.get('domain'))
#             opportunity.eligibility = clean_field(form_data.get('eligibility'))
#             opportunity.description = clean_field(form_data.get('description'))
#             opportunity.advertisement_link = clean_field(form_data.get('advertisement_link'))
#             opportunity.location = clean_field(form_data.get('location'))
#             opportunity.duration = clean_field(form_data.get('duration'))
#             opportunity.compensation = clean_field(form_data.get('compensation'))
#             opportunity.keywords = clean_field(form_data.get('keywords'))
#             opportunity.status = form_data.get('status', 'Active')
            
#             # Handle date field
#             deadline = form_data.get('deadline')
#             opportunity.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None
            
#             db.session.add(opportunity)
#             db.session.commit()
            
#             flash('Opportunity created successfully', 'success')
#             return redirect(url_for('admin.admin_opportunities'))
            
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error creating opportunity: {str(e)}', 'error')
    
#     return render_template('admin/add_opportunity.html')

# # Update the admin_bulk_upload_opportunities route
# @admin_bp.route('/bulk-upload-opportunities', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def admin_bulk_upload_opportunities():
#     # Get or create admin profile
#     profile = get_or_create_admin_profile()
    
#     form = BulkUploadForm()
    
#     if form.validate_on_submit():
#         file = form.file.data
        
#         if file and allowed_bulk_file(file.filename):
#             filename = secure_filename(file.filename)
#             filepath = os.path.join(current_app.config['BULK_UPLOAD_FOLDER'], filename)
            
#             # Ensure directory exists
#             os.makedirs(current_app.config['BULK_UPLOAD_FOLDER'], exist_ok=True)
#             file.save(filepath)
            
#             try:
#                 # Process the file based on extension
#                 if filename.endswith('.csv'):
#                     df = pd.read_csv(filepath)
#                 else:  # Excel files
#                     df = pd.read_excel(filepath)
                
#                 # Process each row
#                 success_count = 0
#                 error_count = 0
#                 errors = []
                
#                 for index, row in df.iterrows():
#                     try:
#                         # Create new opportunity
#                         opportunity = Opportunity(creator_profile_id=profile.id)
                        
#                         # Map CSV columns to opportunity fields
#                         opportunity.type = row.get('type', 'Other')
#                         opportunity.title = row.get('title', 'Untitled Opportunity')
#                         opportunity.domain = row.get('domain')
#                         opportunity.eligibility = row.get('eligibility')
#                         opportunity.description = row.get('description')
#                         opportunity.advertisement_link = row.get('advertisement_link')
#                         opportunity.location = row.get('location')
#                         opportunity.duration = row.get('duration')
#                         opportunity.compensation = row.get('compensation')
#                         opportunity.keywords = row.get('keywords')
#                         opportunity.status = row.get('status', 'Active')
                        
#                         # Handle deadline
#                         deadline_str = row.get('deadline')
#                         if deadline_str:
#                             try:
#                                 opportunity.deadline = datetime.strptime(str(deadline_str), '%Y-%m-%d')
#                             except ValueError:
#                                 # Try different formats if needed
#                                 opportunity.deadline = None
                        
#                         db.session.add(opportunity)
#                         success_count += 1
                        
#                     except Exception as e:
#                         error_count += 1
#                         errors.append(f"Row {index+1}: {str(e)}")
                
#                 db.session.commit()
                
#                 flash(f'Bulk upload completed. Success: {success_count}, Errors: {error_count}', 
#                       'success' if error_count == 0 else 'warning')
                
#                 if errors:
#                     flash('Errors: ' + '; '.join(errors[:5]) + ('...' if len(errors) > 5 else ''), 'warning')
                
#                 return redirect(url_for('admin.admin_opportunities'))
                
#             except Exception as e:
#                 flash(f'Error processing file: {str(e)}', 'error')
#         else:
#             flash('Invalid file format. Please upload CSV or Excel files.', 'error')
    
#     return render_template('admin/bulk_upload_opportunities.html', form=form)






# =======================================================================

# ADMIN settings

# ======================================================================

# Helper function to check if user is admin
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'Admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_view



def manage_model(model, redirect_endpoint, display_name, slug, button_text_class='text-black', form_data=None):
    status_filter = request.args.get('status', 'all')
    query = model.query
    
    if status_filter == 'active':
        query = query.filter_by(status='Active')
    elif status_filter == 'inactive':
        query = query.filter_by(status='Inactive')
    
    items = query.order_by(model.id).all()
    
    # Derive variables for template
    lower_name = display_name.lower().rstrip('s')  # e.g., 'user type' from 'User Types'
    title = f"Manage {display_name}"
    description = f"Add or disable {display_name.lower()}"
    add_placeholder = f"Add new {lower_name}"
    
    # Use the actual endpoint names instead of trying to construct them
    # This maps the slug to the correct endpoint name
    endpoint_map = {
        'current_designations': 'admin.add_current_designation',
        'sectors': 'admin.add_sector',
        'equipment_types': 'admin.add_equipment_type',
        'funding_agencies': 'admin.add_funding_agency',
        'team_positions': 'admin.add_team_position',
        'opportunity_types': 'admin.add_opportunity_type',
        'opportunity_domains': 'admin.add_opportunity_domain',
        'compensation_currencies': 'admin.add_compensation_currency',
        'csr_fund_categories': 'admin.add_csr_fund_category',
        'interest_areas': 'admin.add_interest_area',
        'institute_ownerships': 'admin.add_institute_ownership',
        'institute_types': 'admin.add_institute_type',
        'departments': 'admin.add_new_department',
        'degrees': 'admin.add_degree',
        'publishers': 'admin.add_publisher',
        'skill_types': 'admin.add_skill_type',
        'research_areas': 'admin.add_research_area',
        'user_types': 'admin.add_user_type',
        'account_statuses': 'admin.add_account_status',
        'verification_statuses': 'admin.add_verification_status',
        'profile_types': 'admin.add_profile_type',
        'visibility_settings': 'admin.add_visibility_setting',
        'genders': 'admin.add_gender',
        'research_profiles': 'admin.add_research_profile',
        'current_statuses': 'admin.add_current_status',
        'team_sizes': 'admin.add_team_size',
        'annual_turnovers': 'admin.add_annual_turnover',
        'warranty_statuses': 'admin.add_warranty_status',
        'working_statuses': 'admin.add_working_status',
        'project_statuses': 'admin.add_project_status',
        'team_statuses': 'admin.add_team_status',
        'opportunity_eligibilities': 'admin.add_opportunity_eligibility',
        'opportunity_statuses': 'admin.add_opportunity_status',
        'durations': 'admin.add_duration',
        'compensation_types': 'admin.add_compensation_type',
        'application_statuses': 'admin.add_application_status',
        'message_statuses': 'admin.add_message_status',
        'notification_types': 'admin.add_notification_type',
        'notification_read_statuses': 'admin.add_notification_read_status',
        'csr_availabilities': 'admin.add_csr_availability',
        'institute_autonomous': 'admin.add_institute_autonomous',
        'currently_pursuing_options': 'admin.add_currently_pursuing_option',
        'currently_working_options': 'admin.add_currently_working_option',
        'trl_levels': 'admin.add_trl_level',
        'ip_statuses': 'admin.add_ip_status',
        'licensing_intents': 'admin.add_licensing_intent',
        'proficiency_levels': 'admin.add_proficiency_level'
    }
    
    # Get the correct endpoint from the map, or fall back to a default pattern
    add_action = url_for(endpoint_map.get(slug, 'admin.index'))
    
    no_found = f"No {display_name.lower()} found"
    
    return render_template(
        'admin/admin_settings/generic_management.html',
        items=items,
        title=title,
        description=description,
        add_placeholder=add_placeholder,
        add_action=add_action,
        no_found=no_found,
        model_slug=slug,
        button_text_class=button_text_class
    )


    
def add_model_item(model, name_field, success_message, redirect_endpoint, additional_fields=None):
    name = request.form.get(name_field)
    if name:
        # Check if item already exists (case insensitive)
        existing_item = model.query.filter(db.func.lower(model.name) == db.func.lower(name)).first()
        if existing_item:
            if existing_item.status == 'Inactive':
                # Reactivate inactive item
                existing_item.status = 'Active'
                if additional_fields:
                    for field, value in additional_fields.items():
                        setattr(existing_item, field, value)
                db.session.commit()
                flash(f'{success_message} reactivated successfully.', 'success')
            else:
                flash(f'{success_message} already exists.', 'warning')
        else:
            # Create new item
            if additional_fields:
                new_item = model(name=name, **additional_fields)
            else:
                new_item = model(name=name)
            db.session.add(new_item)
            db.session.commit()
            flash(f'{success_message} added successfully.', 'success')
    else:
        flash('Name cannot be empty.', 'danger')
    
    return redirect(url_for(redirect_endpoint))

def toggle_model_item_status(model, item_id, success_message, redirect_endpoint):
    item = model.query.get_or_404(item_id)
    item.status = 'Inactive' if item.status == 'Active' else 'Active'
    db.session.commit()
    flash(f'{success_message} status updated successfully.', 'success')
    return redirect(url_for(redirect_endpoint))

def generic_toggle_status(model, item_id, success_message, redirect_endpoint):
    result = toggle_model_item_status(model, item_id, success_message, redirect_endpoint)
    
    if hasattr(result, 'status_code') and result.status_code == 302:
        item = model.query.get(item_id)
        if item:
            return jsonify({
                'success': True,
                'new_status': item.status,
                'message': 'Status updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Item not found after update'
            }), 404
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to update status'
        }), 400

# @admin_bp.route('/dashboard')   
# @login_required
# def admin_dashboard():
#     if current_user.user_type != 'Admin':
#         abort(403)
#     stats = {
#         'total_users': User.query.count(),
#         'students': User.query.filter_by(user_type='Student').count(),
#         'pis': User.query.filter_by(user_type='PI').count(),
#         'industry': User.query.filter_by(user_type='Industry').count(),
#         'vendors': User.query.filter_by(user_type='Vendor').count(),
#         'opportunities': Opportunity.query.count(),
#         'active_opportunities': Opportunity.query.filter_by(status='Active').count(),
#         'applications': Application.query.count()
#     }
#     recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
#     recent_opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).limit(10).all()
#     return render_template('admin/admin_settings/dashboard.html',
#                           title='Admin Dashboard',
#                           stats=stats,
#                           recent_users=recent_users,
#                           recent_opportunities=recent_opportunities)

# Current Designations
@admin_bp.route('/current_designations')
@login_required
@admin_required
def current_designations():
    return manage_model(CurrentDesignation, 'admin.current_designations', 'Current Designations', 'current_designations', button_text_class='text-black')

@admin_bp.route('/current_designations/add', methods=['POST'])
@login_required
@admin_required
def add_current_designation():
    return add_model_item(CurrentDesignation, 'name', 'Current designation', 'admin.current_designations')

@admin_bp.route('/current_designations/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_current_designation_status(item_id):
    return generic_toggle_status(CurrentDesignation, item_id, 'Current designation', 'admin.current_designations')

# Sectors
@admin_bp.route('/sectors')
@login_required
@admin_required
def sectors():
    return manage_model(Sector, 'admin.sectors', 'Sectors', 'sectors', button_text_class='text-black')

@admin_bp.route('/sectors/add', methods=['POST'])
@login_required
@admin_required
def add_sector():
    return add_model_item(Sector, 'name', 'Sector', 'admin.sectors')

@admin_bp.route('/sectors/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_sector_status(item_id):
    return generic_toggle_status(Sector, item_id, 'Sector', 'admin.sectors')

# Equipment Types
@admin_bp.route('/equipment_types')
@login_required
@admin_required
def equipment_types():
    return manage_model(EquipmentType, 'admin.equipment_types', 'Equipment Types', 'equipment_types', button_text_class='text-black')

@admin_bp.route('/equipment_types/add', methods=['POST'])
@login_required
@admin_required
def add_equipment_type():
    return add_model_item(EquipmentType, 'name', 'Equipment type', 'admin.equipment_types')

@admin_bp.route('/equipment_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_equipment_type_status(item_id):
    return generic_toggle_status(EquipmentType, item_id, 'Equipment type', 'admin.equipment_types')

# Dealing Categories (special case)
@admin_bp.route('/dealing_categories')
@login_required
@admin_required
def dealing_categories():
    categories = DealingCategory.query.filter_by(status='Active').all()
    equipment_types = EquipmentType.query.filter_by(status='Active').all()
    return render_template('admin/admin_settings/dealing_categories.html', 
                         items=categories, 
                         equipment_types=equipment_types)

@admin_bp.route('/dealing_categories/add', methods=['POST'])
@login_required
@admin_required
def add_dealing_category():
    name = request.form.get('name')
    equipment_type_id = request.form.get('equipment_type_id')
    if name and equipment_type_id:
        additional_fields = {'equipment_type_id': equipment_type_id}
        return add_model_item(DealingCategory, 'name', 'Dealing category', 'admin.dealing_categories', additional_fields)
    else:
        flash('Name and equipment type are required.', 'danger')
        return redirect(url_for('admin.dealing_categories'))

@admin_bp.route('/dealing_categories/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_dealing_category_status(item_id):
    return generic_toggle_status(DealingCategory, item_id, 'Dealing category', 'admin.dealing_categories')

# Funding Agencies
@admin_bp.route('/funding_agencies')
@login_required
@admin_required
def funding_agencies():
    return manage_model(FundingAgency, 'admin.funding_agencies', 'Funding Agencies', 'funding_agencies', button_text_class='text-black')

@admin_bp.route('/funding_agencies/add', methods=['POST'])
@login_required
@admin_required
def add_funding_agency():
    return add_model_item(FundingAgency, 'name', 'Funding agency', 'admin.funding_agencies')

@admin_bp.route('/funding_agencies/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_funding_agency_status(item_id):
    return generic_toggle_status(FundingAgency, item_id, 'Funding agency', 'admin.funding_agencies')

# Team Positions
@admin_bp.route('/team_positions')
@login_required
@admin_required
def team_positions():
    return manage_model(TeamPosition, 'admin.team_positions', 'Team Positions', 'team_positions', button_text_class='text-black')

@admin_bp.route('/team_positions/add', methods=['POST'])
@login_required
@admin_required
def add_team_position():
    return add_model_item(TeamPosition, 'name', 'Team position', 'admin.team_positions')

@admin_bp.route('/team_positions/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_team_position_status(item_id):
    return generic_toggle_status(TeamPosition, item_id, 'Team position', 'admin.team_positions')

# Opportunity Types
@admin_bp.route('/opportunity_types')
@login_required
@admin_required
def opportunity_types():
    return manage_model(OpportunityType, 'admin.opportunity_types', 'Opportunity Types', 'opportunity_types', button_text_class='text-black')

@admin_bp.route('/opportunity_types/add', methods=['POST'])
@login_required
@admin_required
def add_opportunity_type():
    return add_model_item(OpportunityType, 'name', 'Opportunity type', 'admin.opportunity_types')

@admin_bp.route('/opportunity_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_opportunity_type_status(item_id):
    return generic_toggle_status(OpportunityType, item_id, 'Opportunity type', 'admin.opportunity_types')

# Opportunity Domains
@admin_bp.route('/opportunity_domains')
@login_required
@admin_required
def opportunity_domains():
    return manage_model(OpportunityDomain, 'admin.opportunity_domains', 'Opportunity Domains', 'opportunity_domains', button_text_class='text-black')

@admin_bp.route('/opportunity_domains/add', methods=['POST'])
@login_required
@admin_required
def add_opportunity_domain():
    return add_model_item(OpportunityDomain, 'name', 'Opportunity domain', 'admin.opportunity_domains')

@admin_bp.route('/opportunity_domains/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_opportunity_domain_status(item_id):
    return generic_toggle_status(OpportunityDomain, item_id, 'Opportunity domain', 'admin.opportunity_domains')

# Compensation Currencies
@admin_bp.route('/compensation_currencies')
@login_required
@admin_required
def compensation_currencies():
    return manage_model(CompensationCurrency, 'admin.compensation_currencies', 'Compensation Currencies', 'compensation_currencies', button_text_class='text-black')

@admin_bp.route('/compensation_currencies/add', methods=['POST'])
@login_required
@admin_required
def add_compensation_currency():
    return add_model_item(CompensationCurrency, 'name', 'Compensation currency', 'admin.compensation_currencies')

@admin_bp.route('/compensation_currencies/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_compensation_currency_status(item_id):
    return generic_toggle_status(CompensationCurrency, item_id, 'Compensation currency', 'admin.compensation_currencies')

# CSR Fund Categories
@admin_bp.route('/csr_fund_categories')
@login_required
@admin_required
def csr_fund_categories():
    return manage_model(CSRFundCategory, 'admin.csr_fund_categories', 'CSR Fund Categories', 'csr_fund_categories', button_text_class='text-black')

@admin_bp.route('/csr_fund_categories/add', methods=['POST'])
@login_required
@admin_required
def add_csr_fund_category():
    return add_model_item(CSRFundCategory, 'name', 'CSR fund category', 'admin.csr_fund_categories')

@admin_bp.route('/csr_fund_categories/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_csr_fund_category_status(item_id):
    return generic_toggle_status(CSRFundCategory, item_id, 'CSR fund category', 'admin.csr_fund_categories')

# Interest Areas
@admin_bp.route('/interest_areas')
@login_required
@admin_required
def interest_areas():
    return manage_model(InterestArea, 'admin.interest_areas', 'Interest Areas', 'interest_areas', button_text_class='text-black')

@admin_bp.route('/interest_areas/add', methods=['POST'])
@login_required
@admin_required
def add_interest_area():
    return add_model_item(InterestArea, 'name', 'Interest area', 'admin.interest_areas')

@admin_bp.route('/interest_areas/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_interest_area_status(item_id):
    return generic_toggle_status(InterestArea, item_id, 'Interest area', 'admin.interest_areas')

# Institute Ownerships
@admin_bp.route('/institute_ownerships')
@login_required
@admin_required
def institute_ownerships():
    return manage_model(InstituteOwnership, 'admin.institute_ownerships', 'Institute Ownerships', 'institute_ownerships', button_text_class='text-black')

@admin_bp.route('/institute_ownerships/add', methods=['POST'])
@login_required
@admin_required
def add_institute_ownership():
    return add_model_item(InstituteOwnership, 'name', 'Institute ownership', 'admin.institute_ownerships')

@admin_bp.route('/institute_ownerships/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_institute_ownership_status(item_id):
    return generic_toggle_status(InstituteOwnership, item_id, 'Institute ownership', 'admin.institute_ownerships')

# Institute Types
@admin_bp.route('/institute_types')
@login_required
@admin_required
def institute_types():
    return manage_model(InstituteType, 'admin.institute_types', 'Institute Types', 'institute_types', button_text_class='text-black')

@admin_bp.route('/institute_types/add', methods=['POST'])
@login_required
@admin_required
def add_institute_type():
    return add_model_item(InstituteType, 'name', 'Institute type', 'admin.institute_types')

@admin_bp.route('/institute_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_institute_type_status(item_id):
    return generic_toggle_status(InstituteType, item_id, 'Institute type', 'admin.institute_types')

# Departments
@admin_bp.route('/settings/departments', endpoint='admin_settings_departments')
@login_required
@admin_required
def admin_setting_departments():
    return manage_model(AdminSettingDepartment, 'admin.admin_settings_departments', 'Departments', 'departments', button_text_class='text-black')

@admin_bp.route('/settings/departments/add', methods=['POST'])
@login_required
@admin_required
def add_new_department():
    return add_model_item(AdminSettingDepartment, 'name', 'Department', 'admin.admin_settings_departments')

@admin_bp.route('/settings/departments/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_department_status(item_id):
    return generic_toggle_status(AdminSettingDepartment, item_id, 'Department', 'admin.admin_settings_departments')

# Degrees
@admin_bp.route('/degrees')
@login_required
@admin_required
def degrees():
    return manage_model(Degree, 'admin.degrees', 'Degrees', 'degrees', button_text_class='text-black')

@admin_bp.route('/degrees/add', methods=['POST'])
@login_required
@admin_required
def add_degree():
    return add_model_item(Degree, 'name', 'Degree', 'admin.degrees')

@admin_bp.route('/degrees/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_degree_status(item_id):
    return generic_toggle_status(Degree, item_id, 'Degree', 'admin.degrees')

# Publishers
@admin_bp.route('/publishers')
@login_required
@admin_required
def publishers():
    return manage_model(Publisher, 'admin.publishers', 'Publishers', 'publishers', button_text_class='text-black')

@admin_bp.route('/publishers/add', methods=['POST'])
@login_required
@admin_required
def add_publisher():
    return add_model_item(Publisher, 'name', 'Publisher', 'admin.publishers')

@admin_bp.route('/publishers/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_publisher_status(item_id):
    return generic_toggle_status(Publisher, item_id, 'Publisher', 'admin.publishers')

# Skill Types
@admin_bp.route('/skill_types')
@login_required
@admin_required
def skill_types():
    return manage_model(SkillType, 'admin.skill_types', 'Skill Types', 'skill_types', button_text_class='text-black')

@admin_bp.route('/skill_types/add', methods=['POST'])
@login_required
@admin_required
def add_skill_type():
    return add_model_item(SkillType, 'name', 'Skill type', 'admin.skill_types')

@admin_bp.route('/skill_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_skill_type_status(item_id):
    return generic_toggle_status(SkillType, item_id, 'Skill type', 'admin.skill_types')

# Research Areas
@admin_bp.route('/research_areas')
@login_required
@admin_required
def research_areas():
    return manage_model(ResearchArea, 'admin.research_areas', 'Research Areas', 'research_areas', button_text_class='text-black')

@admin_bp.route('/research_areas/add', methods=['POST'])
@login_required
@admin_required
def add_research_area():
    return add_model_item(ResearchArea, 'name', 'Research area', 'admin.research_areas')

@admin_bp.route('/research_areas/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_research_area_status(item_id):
    return generic_toggle_status(ResearchArea, item_id, 'Research area', 'admin.research_areas')

# User Types
@admin_bp.route('/user_types')
@login_required
@admin_required
def user_types():
    return manage_model(UserType, 'admin.user_types', 'User Types', 'user_types', button_text_class='text-black')

@admin_bp.route('/user_types/add', methods=['POST'])
@login_required
@admin_required
def add_user_type():
    return add_model_item(UserType, 'name', 'User type', 'admin.user_types')

@admin_bp.route('/user_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_user_type_status(item_id):
    return generic_toggle_status(UserType, item_id, 'User type', 'admin.user_types')

# Account Statuses
@admin_bp.route('/account_statuses')
@login_required
@admin_required
def account_statuses():
    return manage_model(AccountStatus, 'admin.account_statuses', 'Account Statuses', 'account_statuses', button_text_class='text-black')

@admin_bp.route('/account_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_account_status():
    return add_model_item(AccountStatus, 'name', 'Account status', 'admin.account_statuses')

@admin_bp.route('/account_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_account_status_status(item_id):
    return generic_toggle_status(AccountStatus, item_id, 'Account status', 'admin.account_statuses')

# Verification Statuses
@admin_bp.route('/verification_statuses')
@login_required
@admin_required
def verification_statuses():
    return manage_model(VerificationStatus, 'admin.verification_statuses', 'Verification Statuses', 'verification_statuses', button_text_class='text-black')

@admin_bp.route('/verification_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_verification_status():
    return add_model_item(VerificationStatus, 'name', 'Verification status', 'admin.verification_statuses')

@admin_bp.route('/verification_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_verification_status_status(item_id):
    return generic_toggle_status(VerificationStatus, item_id, 'Verification status', 'admin.verification_statuses')

# Profile Types
@admin_bp.route('/profile_types')
@login_required
@admin_required
def profile_types():
    return manage_model(ProfileType, 'admin.profile_types', 'Profile Types', 'profile_types', button_text_class='text-black')

@admin_bp.route('/profile_types/add', methods=['POST'])
@login_required
@admin_required
def add_profile_type():
    return add_model_item(ProfileType, 'name', 'Profile type', 'admin.profile_types')

@admin_bp.route('/profile_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_profile_type_status(item_id):
    return generic_toggle_status(ProfileType, item_id, 'Profile type', 'admin.profile_types')

# Visibility Settings
@admin_bp.route('/visibility_settings')
@login_required
@admin_required
def visibility_settings():
    return manage_model(VisibilitySetting, 'admin.visibility_settings', 'Visibility Settings', 'visibility_settings', button_text_class='text-black')

@admin_bp.route('/visibility_settings/add', methods=['POST'])
@login_required
@admin_required
def add_visibility_setting():
    return add_model_item(VisibilitySetting, 'name', 'Visibility setting', 'admin.visibility_settings')

@admin_bp.route('/visibility_settings/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_visibility_setting_status(item_id):
    return generic_toggle_status(VisibilitySetting, item_id, 'Visibility setting', 'admin.visibility_settings')

# Genders
@admin_bp.route('/genders')
@login_required
@admin_required
def genders():
    return manage_model(Gender, 'admin.genders', 'Genders', 'genders', button_text_class='text-black')

@admin_bp.route('/genders/add', methods=['POST'])
@login_required
@admin_required
def add_gender():
    return add_model_item(Gender, 'name', 'Gender', 'admin.genders')

@admin_bp.route('/genders/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_gender_status(item_id):
    return generic_toggle_status(Gender, item_id, 'Gender', 'admin.genders')

# Research Profiles
@admin_bp.route('/research_profiles')
@login_required
@admin_required
def research_profiles():
    return manage_model(ResearchProfile, 'admin.research_profiles', 'Research Profiles', 'research_profiles', button_text_class='text-black')

@admin_bp.route('/research_profiles/add', methods=['POST'])
@login_required
@admin_required
def add_research_profile():
    return add_model_item(ResearchProfile, 'name', 'Research profile', 'admin.research_profiles')

@admin_bp.route('/research_profiles/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_research_profile_status(item_id):
    return generic_toggle_status(ResearchProfile, item_id, 'Research profile', 'admin.research_profiles')

# Current Statuses
@admin_bp.route('/current_statuses')
@login_required
@admin_required
def current_statuses():
    return manage_model(CurrentStatus, 'admin.current_statuses', 'Current Statuses', 'current_statuses', button_text_class='text-black')

@admin_bp.route('/current_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_current_status():
    return add_model_item(CurrentStatus, 'name', 'Current status', 'admin.current_statuses')

@admin_bp.route('/current_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_current_status_status(item_id):
    return generic_toggle_status(CurrentStatus, item_id, 'Current status', 'admin.current_statuses')

# Team Sizes
@admin_bp.route('/team_sizes')
@login_required
@admin_required
def team_sizes():
    return manage_model(TeamSize, 'admin.team_sizes', 'Team Sizes', 'team_sizes', button_text_class='text-black')

@admin_bp.route('/team_sizes/add', methods=['POST'])
@login_required
@admin_required
def add_team_size():
    return add_model_item(TeamSize, 'name', 'Team size', 'admin.team_sizes')

@admin_bp.route('/team_sizes/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_team_size_status(item_id):
    return generic_toggle_status(TeamSize, item_id, 'Team size', 'admin.team_sizes')

# Annual Turnovers
@admin_bp.route('/annual_turnovers')
@login_required
@admin_required
def annual_turnovers():
    return manage_model(AnnualTurnover, 'admin.annual_turnovers', 'Annual Turnovers', 'annual_turnovers', button_text_class='text-black')

@admin_bp.route('/annual_turnovers/add', methods=['POST'])
@login_required
@admin_required
def add_annual_turnover():
    return add_model_item(AnnualTurnover, 'name', 'Annual turnover', 'admin.annual_turnovers')

@admin_bp.route('/annual_turnovers/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_annual_turnover_status(item_id):
    return generic_toggle_status(AnnualTurnover, item_id, 'Annual turnover', 'admin.annual_turnovers')

# Warranty Statuses
@admin_bp.route('/warranty_statuses')
@login_required
@admin_required
def warranty_statuses():
    return manage_model(WarrantyStatus, 'admin.warranty_statuses', 'Warranty Statuses', 'warranty_statuses', button_text_class='text-black')

@admin_bp.route('/warranty_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_warranty_status():
    return add_model_item(WarrantyStatus, 'name', 'Warranty status', 'admin.warranty_statuses')

@admin_bp.route('/warranty_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_warranty_status_status(item_id):
    return generic_toggle_status(WarrantyStatus, item_id, 'Warranty status', 'admin.warranty_statuses')

# Working Statuses
@admin_bp.route('/working_statuses')
@login_required
@admin_required
def working_statuses():
    return manage_model(WorkingStatus, 'admin.working_statuses', 'Working Statuses', 'working_statuses', button_text_class='text-black')

@admin_bp.route('/working_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_working_status():
    return add_model_item(WorkingStatus, 'name', 'Working status', 'admin.working_statuses')

@admin_bp.route('/working_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_working_status_status(item_id):
    return generic_toggle_status(WorkingStatus, item_id, 'Working status', 'admin.working_statuses')

# Project Statuses
@admin_bp.route('/project_statuses')
@login_required
@admin_required
def project_statuses():
    return manage_model(ProjectStatus, 'admin.project_statuses', 'Project Statuses', 'project_statuses', button_text_class='text-black')

@admin_bp.route('/project_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_project_status():
    return add_model_item(ProjectStatus, 'name', 'Project status', 'admin.project_statuses')

@admin_bp.route('/project_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_project_status_status(item_id):
    return generic_toggle_status(ProjectStatus, item_id, 'Project status', 'admin.project_statuses')

# Team Statuses
@admin_bp.route('/team_statuses')
@login_required
@admin_required
def team_statuses():
    return manage_model(TeamStatus, 'admin.team_statuses', 'Team Statuses', 'team_statuses', button_text_class='text-black')

@admin_bp.route('/team_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_team_status():
    return add_model_item(TeamStatus, 'name', 'Team status', 'admin.team_statuses')

@admin_bp.route('/team_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_team_status_status(item_id):
    return generic_toggle_status(TeamStatus, item_id, 'Team status', 'admin.team_statuses')

# Opportunity Eligibilities
@admin_bp.route('/opportunity_eligibilities')
@login_required
@admin_required
def opportunity_eligibilities():
    return manage_model(OpportunityEligibility, 'admin.opportunity_eligibilities', 'Opportunity Eligibilities', 'opportunity_eligibilities', button_text_class='text-black')

@admin_bp.route('/opportunity_eligibilities/add', methods=['POST'])
@login_required
@admin_required
def add_opportunity_eligibility():
    return add_model_item(OpportunityEligibility, 'name', 'Opportunity eligibility', 'admin.opportunity_eligibilities')

@admin_bp.route('/opportunity_eligibilities/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_opportunity_eligibility_status(item_id):
    return generic_toggle_status(OpportunityEligibility, item_id, 'Opportunity eligibility', 'admin.opportunity_eligibilities')

# Opportunity Statuses
@admin_bp.route('/opportunity_statuses')
@login_required
@admin_required
def opportunity_statuses():
    return manage_model(OpportunityStatus, 'admin.opportunity_statuses', 'Opportunity Statuses', 'opportunity_statuses', button_text_class='text-black')

@admin_bp.route('/opportunity_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_opportunity_status():
    return add_model_item(OpportunityStatus, 'name', 'Opportunity status', 'admin.opportunity_statuses')

@admin_bp.route('/opportunity_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_opportunity_status_status(item_id):
    return generic_toggle_status(OpportunityStatus, item_id, 'Opportunity status', 'admin.opportunity_statuses')

# Durations
@admin_bp.route('/durations')
@login_required
@admin_required
def durations():
    return manage_model(Duration, 'admin.durations', 'Durations', 'durations', button_text_class='text-black')

@admin_bp.route('/durations/add', methods=['POST'])
@login_required
@admin_required
def add_duration():
    return add_model_item(Duration, 'name', 'Duration', 'admin.durations')

@admin_bp.route('/durations/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_duration_status(item_id):
    return generic_toggle_status(Duration, item_id, 'Duration', 'admin.durations')

# Compensation Types
@admin_bp.route('/compensation_types')
@login_required
@admin_required
def compensation_types():
    return manage_model(CompensationType, 'admin.compensation_types', 'Compensation Types', 'compensation_types', button_text_class='text-black')

@admin_bp.route('/compensation_types/add', methods=['POST'])
@login_required
@admin_required
def add_compensation_type():
    return add_model_item(CompensationType, 'name', 'Compensation type', 'admin.compensation_types')

@admin_bp.route('/compensation_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_compensation_type_status(item_id):
    return generic_toggle_status(CompensationType, item_id, 'Compensation type', 'admin.compensation_types')

# Application Statuses
@admin_bp.route('/application_statuses')
@login_required
@admin_required
def application_statuses():
    return manage_model(ApplicationStatus, 'admin.application_statuses', 'Application Statuses', 'application_statuses', button_text_class='text-black')

@admin_bp.route('/application_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_application_status():
    return add_model_item(ApplicationStatus, 'name', 'Application status', 'admin.application_statuses')

@admin_bp.route('/application_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_application_status_status(item_id):
    return generic_toggle_status(ApplicationStatus, item_id, 'Application status', 'admin.application_statuses')

# Message Statuses
@admin_bp.route('/message_statuses')
@login_required
@admin_required
def message_statuses():
    return manage_model(MessageStatus, 'admin.message_statuses', 'Message Statuses', 'message_statuses', button_text_class='text-black')

@admin_bp.route('/message_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_message_status():
    return add_model_item(MessageStatus, 'name', 'Message status', 'admin.message_statuses')

@admin_bp.route('/message_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_message_status_status(item_id):
    return generic_toggle_status(MessageStatus, item_id, 'Message status', 'admin.message_statuses')

# Notification Types
@admin_bp.route('/notification_types')
@login_required
@admin_required
def notification_types():
    return manage_model(NotificationType, 'admin.notification_types', 'Notification Types', 'notification_types', button_text_class='text-black')

@admin_bp.route('/notification_types/add', methods=['POST'])
@login_required
@admin_required
def add_notification_type():
    return add_model_item(NotificationType, 'name', 'Notification type', 'admin.notification_types')

@admin_bp.route('/notification_types/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_notification_type_status(item_id):
    return generic_toggle_status(NotificationType, item_id, 'Notification type', 'admin.notification_types')

# Notification Read Statuses
@admin_bp.route('/notification_read_statuses')
@login_required
@admin_required
def notification_read_statuses():
    return manage_model(NotificationReadStatus, 'admin.notification_read_statuses', 'Notification Read Statuses', 'notification_read_statuses', button_text_class='text-black')

@admin_bp.route('/notification_read_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_notification_read_status():
    return add_model_item(NotificationReadStatus, 'name', 'Notification read status', 'admin.notification_read_statuses')

@admin_bp.route('/notification_read_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_notification_read_status_status(item_id):
    return generic_toggle_status(NotificationReadStatus, item_id, 'Notification read status', 'admin.notification_read_statuses')

# CSR Availabilities
@admin_bp.route('/csr_availabilities')
@login_required
@admin_required
def csr_availabilities():
    return manage_model(CSRAvailability, 'admin.csr_availabilities', 'CSR Availabilities', 'csr_availabilities', button_text_class='text-black')

@admin_bp.route('/csr_availabilities/add', methods=['POST'])
@login_required
@admin_required
def add_csr_availability():
    return add_model_item(CSRAvailability, 'name', 'CSR availability', 'admin.csr_availabilities')

@admin_bp.route('/csr_availabilities/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_csr_availability_status(item_id):
    return generic_toggle_status(CSRAvailability, item_id, 'CSR availability', 'admin.csr_availabilities')

# Institute Autonomous
@admin_bp.route('/institute_autonomous')
@login_required
@admin_required
def institute_autonomous():
    return manage_model(InstituteAutonomous, 'admin.institute_autonomous', 'Institute Autonomous', 'institute_autonomous', button_text_class='text-black')

@admin_bp.route('/institute_autonomous/add', methods=['POST'])
@login_required
@admin_required
def add_institute_autonomous():
    return add_model_item(InstituteAutonomous, 'name', 'Institute autonomous', 'admin.institute_autonomous')

@admin_bp.route('/institute_autonomous/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_institute_autonomous_status(item_id):
    return generic_toggle_status(InstituteAutonomous, item_id, 'Institute autonomous', 'admin.institute_autonomous')

# Currently Pursuing Options
@admin_bp.route('/currently_pursuing_options')
@login_required
@admin_required
def currently_pursuing_options():
    return manage_model(CurrentlyPursuingOption, 'admin.currently_pursuing_options', 'Currently Pursuing Options', 'currently_pursuing_options', button_text_class='text-black')

@admin_bp.route('/currently_pursuing_options/add', methods=['POST'])
@login_required
@admin_required
def add_currently_pursuing_option():
    return add_model_item(CurrentlyPursuingOption, 'name', 'Currently pursuing option', 'admin.currently_pursuing_options')

@admin_bp.route('/currently_pursuing_options/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_currently_pursuing_option_status(item_id):
    return generic_toggle_status(CurrentlyPursuingOption, item_id, 'Currently pursuing option', 'admin.currently_pursuing_options')

# Currently Working Options
@admin_bp.route('/currently_working_options')
@login_required
@admin_required
def currently_working_options():
    return manage_model(CurrentlyWorkingOption, 'admin.currently_working_options', 'Currently Working Options', 'currently_working_options', button_text_class='text-black')

@admin_bp.route('/currently_working_options/add', methods=['POST'])
@login_required
@admin_required
def add_currently_working_option():
    return add_model_item(CurrentlyWorkingOption, 'name', 'Currently working option', 'admin.currently_working_options')

@admin_bp.route('/currently_working_options/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_currently_working_option_status(item_id):
    return generic_toggle_status(CurrentlyWorkingOption, item_id, 'Currently working option', 'admin.currently_working_options')

# TRL Levels
@admin_bp.route('/trl_levels')
@login_required
@admin_required
def trl_levels():
    return manage_model(TRLLevel, 'admin.trl_levels', 'TRL Levels', 'trl_levels', button_text_class='text-black')

@admin_bp.route('/trl_levels/add', methods=['POST'])
@login_required
@admin_required
def add_trl_level():
    return add_model_item(TRLLevel, 'name', 'TRL level', 'admin.trl_levels')

@admin_bp.route('/trl_levels/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_trl_level_status(item_id):
    return generic_toggle_status(TRLLevel, item_id, 'TRL level', 'admin.trl_levels')

# IP Statuses
@admin_bp.route('/ip_statuses')
@login_required
@admin_required
def ip_statuses():
    return manage_model(IPStatus, 'admin.ip_statuses', 'IP Statuses', 'ip_statuses', button_text_class='text-black')

@admin_bp.route('/ip_statuses/add', methods=['POST'])
@login_required
@admin_required
def add_ip_status():
    return add_model_item(IPStatus, 'name', 'IP status', 'admin.ip_statuses')

@admin_bp.route('/ip_statuses/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_ip_status_status(item_id):
    return generic_toggle_status(IPStatus, item_id, 'IP status', 'admin.ip_statuses')

# Licensing Intents
@admin_bp.route('/licensing_intents')
@login_required
@admin_required
def licensing_intents():
    return manage_model(LicensingIntent, 'admin.licensing_intents', 'Licensing Intents', 'licensing_intents', button_text_class='text-black')

@admin_bp.route('/licensing_intents/add', methods=['POST'])
@login_required
@admin_required
def add_licensing_intent():
    return add_model_item(LicensingIntent, 'name', 'Licensing intent', 'admin.licensing_intents')

@admin_bp.route('/licensing_intents/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_licensing_intent_status(item_id):
    return generic_toggle_status(LicensingIntent, item_id, 'Licensing intent', 'admin.licensing_intents')

# Proficiency Levels
@admin_bp.route('/proficiency_levels')
@login_required
@admin_required
def proficiency_levels():
    return manage_model(ProficiencyLevel, 'admin.proficiency_levels', 'Proficiency Levels', 'proficiency_levels', button_text_class='text-black')

@admin_bp.route('/proficiency_levels/add', methods=['POST'])
@login_required
@admin_required
def add_proficiency_level():
    return add_model_item(ProficiencyLevel, 'name', 'Proficiency level', 'admin.proficiency_levels')

@admin_bp.route('/proficiency_levels/toggle_status/<int:item_id>')
@login_required
@admin_required
def toggle_proficiency_level_status(item_id):
    return generic_toggle_status(ProficiencyLevel, item_id, 'Proficiency level', 'admin.proficiency_levels')


