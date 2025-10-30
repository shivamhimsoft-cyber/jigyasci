# __init__.py
from routes.admin_routes import admin_bp
from routes.pi_routes import pi_bp
from routes.student_routes import student_bp
from routes.vendor_routes import vendor_bp
from routes.industry_routes import industry_bp
from routes.auth_routes import auth_bp

from routes.research_facilities_routes import facility_bp
from routes.publication_routes import pub_bp
from routes.technology_routes import tech_bp
from routes.bookmark_routes import bookmark_bp  # ✅ Add this import

from routes.profile_routes import profile_bp  # ✅ Add this import
from routes.contact_routes import contact_bp  # Add this import

def register_blueprints(app):
    app.register_blueprint(admin_bp)
    app.register_blueprint(pi_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(industry_bp)
    app.register_blueprint(auth_bp)  # <--- yeh hona chahiye

    app.register_blueprint(facility_bp)
    app.register_blueprint(pub_bp)
    app.register_blueprint(tech_bp)
    app.register_blueprint(bookmark_bp)  # ✅ Register the bookmark blueprint

    app.register_blueprint(profile_bp)  # ✅ Register the new profile blueprint
    app.register_blueprint(contact_bp)  # Register contact blueprint without prefix


