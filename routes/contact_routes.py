# routes\contact_routes.py

from flask import Blueprint, render_template, flash, redirect, url_for, jsonify
from flask_login import current_user
from extensions import db, mail
from models import ContactMessage
from forms import ContactForm
from flask_mail import Message as MailMessage
import logging
from flask import current_app, request

# Setup logging
logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__, template_folder='templates')

# Route to handle contact form submission
@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            contact_message = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                subject=dict(form.subject.choices).get(form.subject.data),  # Convert subject value to label
                message=form.message.data,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(contact_message)
            db.session.commit()

            # Send thank you email with HTML content
            try:
                msg = MailMessage(
                    subject='Thank You for Contacting JigyaSci',
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[form.email.data]
                )
                msg.html = (
                    f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{ font-family: 'Arial', sans-serif; background-color: #f7f7f7; color: #333; margin: 0; padding: 0; }}
                            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
                            .header {{ background-color: #66C0DC; color: #ffffff; padding: 20px; text-align: center; }}
                            .header h1 {{ margin: 0; font-size: 24px; }}
                            .content {{ padding: 20px; }}
                            .content h2 {{ color: #2c3e50; font-size: 20px; margin-top: 0; }}
                            .content p {{ line-height: 1.6; }}
                            .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                            .details p {{ margin: 5px 0; font-size: 14px; }}
                            .footer {{ text-align: center; padding: 10px; background-color: #f7f7f7; color: #666; font-size: 12px; }}
                            .btn {{ display: inline-block; padding: 10px 20px; background-color: #66C0DC; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                            .btn:hover {{ background-color: #4da8c4; }}
                            @media (max-width: 600px) {{
                                .container {{ margin: 10px; }}
                                .header h1 {{ font-size: 20px; }}
                                .content {{ padding: 15px; }}
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>JigyaSci</h1>
                            </div>
                            <div class="content">
                                <h2>Thank You, {form.name.data}!</h2>
                                <p>We are delighted to receive your message and appreciate you reaching out to JigyaSci. Our dedicated team is reviewing your request and will respond to you shortly.</p>
                                <div class="details">
                                    <p><strong>Subject:</strong> {dict(form.subject.choices).get(form.subject.data)}</p>
                                    <p><strong>Message:</strong> {form.message.data}</p>
                                </div>
                                <p>If you have any urgent queries, feel free to contact us at <a href="mailto:support@jigyasci.org" style="color: #66C0DC;">support@jigyasci.org</a> or call us at <a href="tel:+919876543210" style="color: #66C0DC;">+91 98765 43210</a>.</p>
                                <a href="https://jigyasci.org" class="btn">Visit Our Website</a>
                            </div>
                            <div class="footer">
                                <p>&copy; 2025 JigyaSci. All rights reserved.</p>
                                <p>Powered by <a href="https://himsoftsolution.com" style="color: #66C0DC;">Him Soft Solution</a></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                )
                mail.send(msg)
                # Return JSON response to trigger popup via JavaScript
                return jsonify({'success': True, 'message': 'Your message has been successfully sent. A confirmation email has been dispatched to your inbox.'})
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                return jsonify({'success': True, 'message': 'Your message was sent, but we encountered an issue sending the confirmation email.'})

        except Exception as e:
            logger.error(f"Error processing contact form: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred while sending your message. Please try again later.'})

    # Handle GET request or invalid form submission
    return render_template('contact.html', form=form)