# routes/bookmark_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Bookmark, Profile, Publication, Project, ResearchFacility, Technology, Award, Skill, Education, Experience, TeamMember, PIProfile, StudentProfile, VendorProfile, IndustryProfile
from sqlalchemy.orm.exc import ObjectDeletedError
from datetime import datetime

bookmark_bp = Blueprint('bookmark', __name__)

# routes/bookmark_routes.py - Update the get_bookmark_item function

def get_bookmark_item(bookmark):
    """Get the actual item from bookmark with proper error handling"""
    model_map = {
        'profile': Profile,
        'student': StudentProfile,
        'vendor': VendorProfile,
        'industry': IndustryProfile,
        'education': Education,
        'experience': Experience,
        'facility': ResearchFacility,
        'technology': Technology,
        'skill': Skill,
        'award': Award,
        'project': Project,
        'team': TeamMember,
        'publication': Publication
    }
    
    if bookmark.bookmark_type not in model_map:
        return None
    
    try:
        item = db.session.get(model_map[bookmark.bookmark_type], bookmark.bookmark_item_id)
        
        if item is None:
            return None
        
        # Handle different profile types
        if bookmark.bookmark_type in ['profile', 'student', 'vendor', 'industry']:
            # For profile types, we need to get the parent profile
            if bookmark.bookmark_type == 'profile':
                profile = item
                profile_data = {
                    'id': profile.id,
                    'name': get_profile_name(profile),
                    'current_designation': get_profile_designation(profile),
                    'profile_picture': get_profile_picture(profile),
                    'profile': profile
                }
            elif bookmark.bookmark_type == 'student':
                student = item
                profile_data = {
                    'id': student.id,
                    'name': student.name,
                    'current_designation': 'Student',
                    'profile_picture': student.profile_picture,
                    'profile': student.profile if student.profile else None
                }
            elif bookmark.bookmark_type == 'vendor':
                vendor = item
                profile_data = {
                    'id': vendor.id,
                    'name': vendor.company_name,
                    'current_designation': vendor.contact_person_designation if hasattr(vendor, 'contact_person_designation') else 'Vendor',
                    'profile_picture': vendor.logo if hasattr(vendor, 'logo') else None,
                    'profile': vendor.profile if vendor.profile else None
                }
            elif bookmark.bookmark_type == 'industry':
                industry = item
                profile_data = {
                    'id': industry.id,
                    'name': industry.company_name,
                    'current_designation': industry.contact_person_designation if hasattr(industry, 'contact_person_designation') else 'Industry',
                    'profile_picture': industry.logo if hasattr(industry, 'logo') else None,
                    'profile': industry.profile if industry.profile else None
                }
            
            # Add specific profile type for template use
            if hasattr(profile_data.get('profile', None), 'pi_profile'):
                profile_data['pi_profile'] = profile_data['profile'].pi_profile
            if hasattr(profile_data.get('profile', None), 'student_profile'):
                profile_data['student_profile'] = profile_data['profile'].student_profile
            if hasattr(profile_data.get('profile', None), 'industry_profile'):
                profile_data['industry_profile'] = profile_data['profile'].industry_profile
            if hasattr(profile_data.get('profile', None), 'vendor_profile'):
                profile_data['vendor_profile'] = profile_data['profile'].vendor_profile
                
            return profile_data
        
        return item
        
    except ObjectDeletedError:
        db.session.rollback()
        return None
    except Exception as e:
        print(f"Error getting bookmark item: {e}")
        return None

def get_profile_name(profile):
    """Get the name from any profile type"""
    if profile.pi_profile:
        return profile.pi_profile.name
    elif profile.student_profile:
        return profile.student_profile.name
    elif profile.industry_profile:
        return profile.industry_profile.company_name
    elif profile.vendor_profile:
        return profile.vendor_profile.company_name
    return "Unknown"

def get_profile_designation(profile):
    """Get the designation from any profile type"""
    if profile.pi_profile:
        return profile.pi_profile.current_designation
    elif profile.student_profile:
        return "Student"
    elif profile.industry_profile:
        return profile.industry_profile.contact_person_designation
    elif profile.vendor_profile:
        return profile.vendor_profile.contact_person_designation
    return "N/A"

def get_profile_picture(profile):
    """Get the profile picture from any profile type"""
    if profile.pi_profile:
        return profile.pi_profile.profile_picture
    elif profile.student_profile:
        return profile.student_profile.profile_picture
    # Industry and vendor profiles might not have profile pictures
    return None

# routes/bookmark_routes.py - Update the item_exists function

def item_exists(bookmark_type, item_id):
    """Check if the item exists in the database"""
    model_map = {
        'profile': Profile,
        'student': StudentProfile,  # Changed from 'profile' to 'student'
        'vendor': VendorProfile,    # Changed from 'profile' to 'vendor'
        'industry': IndustryProfile, # Changed from 'profile' to 'industry'
        'education': Education,
        'experience': Experience,
        'facility': ResearchFacility,
        'technology': Technology,
        'skill': Skill,
        'award': Award,
        'project': Project,
        'team': TeamMember,
        'publication': Publication
    }
    
    if bookmark_type in model_map:
        try:
            item = db.session.get(model_map[bookmark_type], item_id)
            return item is not None
        except Exception:
            return False
    return False

def cleanup_orphaned_bookmarks():
    """Remove bookmarks that reference deleted items"""
    try:
        bookmarks = Bookmark.query.all()
        deleted_count = 0
        
        for bookmark in bookmarks:
            if not item_exists(bookmark.bookmark_type, bookmark.bookmark_item_id):
                db.session.delete(bookmark)
                deleted_count += 1
        
        if deleted_count > 0:
            db.session.commit()
            print(f"Cleaned up {deleted_count} orphaned bookmarks")
            
        return deleted_count
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up orphaned bookmarks: {e}")
        return 0

@bookmark_bp.route('/bookmark/<bookmark_type>/<int:item_id>', methods=['POST'])
@login_required
def toggle_bookmark(bookmark_type, item_id):
    """Toggle bookmark status for an item"""
    # Check if item exists
    if not item_exists(bookmark_type, item_id):
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    
    # Check if already bookmarked
    existing_bookmark = Bookmark.query.filter_by(
        user_id=current_user.id,
        bookmark_type=bookmark_type,
        bookmark_item_id=item_id
    ).first()
    
    if existing_bookmark:
        # Remove bookmark
        db.session.delete(existing_bookmark)
        db.session.commit()
        return jsonify({'success': True, 'bookmarked': False})
    else:
        # Add bookmark
        new_bookmark = Bookmark(
            user_id=current_user.id,
            bookmark_type=bookmark_type,
            bookmark_item_id=item_id
        )
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({'success': True, 'bookmarked': True})

@bookmark_bp.route('/bookmark/status/<bookmark_type>/<int:item_id>')
@login_required
def check_bookmark_status(bookmark_type, item_id):
    """Check if an item is bookmarked by the current user"""
    # First check if item still exists
    if not item_exists(bookmark_type, item_id):
        return jsonify({'bookmarked': False})
    
    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id,
        bookmark_type=bookmark_type,
        bookmark_item_id=item_id
    ).first()
    
    return jsonify({'bookmarked': bookmark is not None})

@bookmark_bp.route('/my-bookmarks')
@login_required
def my_bookmarks():
    """Display all bookmarks for the current user"""
    cleanup_orphaned_bookmarks()
    
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    
    bookmark_items = []
    for bookmark in bookmarks:
        item = get_bookmark_item(bookmark)
        if item:
            # For profiles, we need to handle the dictionary return
            if bookmark.bookmark_type == 'profile':
                bookmark_items.append({
                    'bookmark': bookmark,
                    'item': item,  # This is now a dictionary
                    'type': bookmark.bookmark_type,
                    'title': item['name'],
                    'description': item['current_designation']
                })
            else:
                bookmark_items.append({
                    'bookmark': bookmark,
                    'item': item,
                    'type': bookmark.bookmark_type,
                    'title': getattr(item, 'title', None) or getattr(item, 'name', None) or getattr(item, 'degree_name', None),
                    'description': getattr(item, 'description', None) or getattr(item, 'project_title', None)
                })
        else:
            db.session.delete(bookmark)
    
    if bookmarks and not bookmark_items:
        db.session.commit()
    
    organized_bookmarks = {}
    for bookmark_item in bookmark_items:
        bookmark_type = bookmark_item['type']
        if bookmark_type not in organized_bookmarks:
            organized_bookmarks[bookmark_type] = []
        organized_bookmarks[bookmark_type].append(bookmark_item)
    
    return render_template('bookmarks/my_bookmarks.html', 
                         bookmarks=organized_bookmarks)

@bookmark_bp.route('/bookmarks/count')
@login_required
def bookmarks_count():
    """Get the count of bookmarks for the current user (for badge)"""
    # Only count bookmarks that reference existing items
    count = 0
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    
    for bookmark in bookmarks:
        if item_exists(bookmark.bookmark_type, bookmark.bookmark_item_id):
            count += 1
        else:
            # Remove orphaned bookmark
            db.session.delete(bookmark)
    
    if count != len(bookmarks):
        db.session.commit()
    
    return jsonify({'count': count})

@bookmark_bp.route('/bookmarks/cleanup', methods=['POST'])
@login_required
def cleanup_bookmarks():
    """Clean up orphaned bookmarks (admin/maintenance function)"""
    try:
        deleted_count = cleanup_orphaned_bookmarks()
        return jsonify({
            'success': True, 
            'message': f'Cleaned up {deleted_count} orphaned bookmarks'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bookmark_bp.route('/bookmarks/clear', methods=['POST'])
@login_required
def clear_all_bookmarks():
    """Clear all bookmarks for the current user"""
    try:
        count = Bookmark.query.filter_by(user_id=current_user.id).count()
        Bookmark.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'All bookmarks cleared',
            'count': count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bookmark_bp.route('/bookmarks/export')
@login_required
def export_bookmarks():
    """Export bookmarks as JSON"""
    # Clean up orphaned bookmarks first
    cleanup_orphaned_bookmarks()
    
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    
    # Simple JSON export
    bookmarks_data = []
    for bookmark in bookmarks:
        item = get_bookmark_item(bookmark)
        if item:
            bookmarks_data.append({
                'type': bookmark.bookmark_type,
                'item_id': bookmark.bookmark_item_id,
                'created_at': bookmark.created_at.isoformat(),
                'item_data': {
                    'title': getattr(item, 'title', None) or getattr(item, 'name', None) or getattr(item, 'degree_name', None),
                    'description': getattr(item, 'description', None) or getattr(item, 'project_title', None)
                }
            })
    
    return jsonify({'bookmarks': bookmarks_data})

@bookmark_bp.route('/debug/profile/<int:profile_id>')
def debug_profile(profile_id):
    """Debug route to check profile data"""
    profile = Profile.query.get(profile_id)
    if profile:
        return jsonify({
            'profile_id': profile.id,
            'user_id': profile.user_id,
            'profile_type': profile.profile_type,
            'pi_profile': bool(profile.pi_profile),
            'student_profile': bool(profile.student_profile),
            'industry_profile': bool(profile.industry_profile),
            'vendor_profile': bool(profile.vendor_profile)
        })
    return jsonify({'error': 'Profile not found'})







