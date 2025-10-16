# routes\vendor_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Profile, VendorProfile, DealingCategory
from extensions import db  # yeh alag se import karo
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
import os

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

@vendor_bp.route('/dashboard')
@login_required
def vendor_dashboard():
    if current_user.user_type != 'Vendor':
        abort(403)
    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    vendor = VendorProfile.query.filter_by(profile_id=profile.id).first()
    return render_template('vendor/dashboard.html', profile=profile, vendor=vendor)


@vendor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def vendorProfile():
    if current_user.user_type != 'Vendor':
        abort(403)

    profile = Profile.query.filter_by(user_id=current_user.id).first_or_404()
    vendor = VendorProfile.query.filter_by(profile_id=profile.id).first()
    dealing_categories = DealingCategory.query.filter_by(status='Active').all()

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
        vendor.dealing_categories = ', '.join(request.form.getlist('dealing_categories'))
        vendor.product_categories = request.form['product_categories']
        vendor.why_me = request.form['why_me']
        vendor.regional_contacts = request.form['regional_contacts']
        vendor.proud_customers = request.form['proud_customers']

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            relative_path = os.path.join('uploads/vendor_logos', filename).replace('\\', '/')
            upload_path = os.path.join('static', relative_path)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            try:
                logo_file.save(upload_path)
                vendor.logo = relative_path
            except Exception as e:
                flash(f"Error uploading logo: {str(e)}", "error")
                return redirect(url_for('vendor.vendorProfile'))

        document_file = request.files.get('document_upload')
        if document_file and document_file.filename:
            filename = secure_filename(document_file.filename)
            relative_path = os.path.join('uploads/vendor_documents', filename).replace('\\', '/')
            upload_path = os.path.join('static', relative_path)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            try:
                document_file.save(upload_path)
                vendor.document_upload = relative_path
            except Exception as e:
                flash(f"Error uploading document: {str(e)}", "error")
                return redirect(url_for('vendor.vendorProfile'))

        try:
            db.session.add(vendor)
            db.session.commit()
            flash('Vendor profile saved successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error saving profile: {str(e)}', 'error')

        return redirect(url_for('vendor.vendorProfile'))

    return render_template('vendor/profile.html', vendor=vendor, dealing_categories=dealing_categories)


@vendor_bp.route('/vendor/<int:vendor_id>')
def vendor_profile(vendor_id):
    vendor = VendorProfile.query.get_or_404(vendor_id)

    # Dummy orders
    orders = [
        {'id': '24567', 'date': '2023-06-15', 'total': '$12,450', 'status': 'Processing'},
        {'id': '7890',  'date': '2023-06-10', 'total': '$25,000', 'status': 'Shipped'},
        {'id': '4567',  'date': '2023-06-05', 'total': '$8,750',  'status': 'Completed'},
    ]

    order_stats = {
        'processing_count': sum(1 for o in orders if o['status'] == 'Processing'),
        'shipped_count':    sum(1 for o in orders if o['status'] == 'Shipped'),
        'completed_count':  sum(1 for o in orders if o['status'] == 'Completed'),
    }

    # Inject dummy rating (out of 5)
    rating = 4  # or any int 0–5

    return render_template(
        'visit_profile/vendor.html',
        vendor=vendor,
        rating=rating,
        orders=orders,
        order_stats=order_stats,
        orders_description="Manage and track your vendor orders"
    )






def search_vendors(query):
    """Search vendors by company name, dealing categories or region"""
    if not query:
        return VendorProfile.query.all()
    
    return VendorProfile.query.filter(
        or_(
            VendorProfile.company_name.ilike(f'%{query}%'),
            VendorProfile.dealing_categories.ilike(f'%{query}%'),
            VendorProfile.region.ilike(f'%{query}%'),
        )
    ).all()

@vendor_bp.route('/full-table')
def full_table():
    query = request.args.get('query', '')
    vendors = search_vendors(query)
    return render_template('vendor/full_table.html', 
                         vendors=vendors,
                         query=query)