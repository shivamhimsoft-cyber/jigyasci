# routes\vendor_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Profile, VendorProfile
from extensions import db  # yeh alag se import karo
from sqlalchemy import or_
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
        return redirect(url_for('vendor.vendor_profile', vendor_id=vendor.id))

    return render_template('vendor/profile.html', vendor=vendor)


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
