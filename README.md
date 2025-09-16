# Research Collaboration Platform

A comprehensive web platform connecting students, principal investigators, industry partners, and vendors in the research ecosystem.

## Overview

The Research Collaboration Platform is designed to streamline connections between different stakeholders in the research community. It provides a centralized system for:

- Students seeking research opportunities
- Principal Investigators looking for talented researchers
- Industry partners seeking academic collaborations
- Vendors providing specialized services and equipment

## Key Features

- **User Profiles**: Customized profiles for each user type with relevant information
- **Opportunity Discovery**: Browse and search for research opportunities across various domains
- **Messaging System**: Direct communication between users
- **Application Management**: Streamlined process for applying to opportunities
- **Admin Dashboard**: Comprehensive admin controls for platform management

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: Bootstrap, Vanilla JavaScript
- **Authentication**: Flask-Login
- **Form Handling**: Flask-WTF
- **ORM**: SQLAlchemy

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vin33t/research-collaboration-platform.git
   cd research-collaboration-platform
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   SESSION_SECRET=your_secure_secret_key
   ```

5. **Initialize the database**
   ```bash
   python initialize_database.py
   ```

6. **Create demo users (optional)**
   ```bash
   python create_demo_users.py
   ```

7. **Run the development server**
   ```bash
   flask run
   ```
   The application will be available at http://127.0.0.1:5000/

## Production Deployment

### Option 1: Deploy using Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Start the server**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```

### Option 2: Deploy to a cloud platform

The application can be deployed to various cloud platforms:

- **Heroku**: Use the provided Procfile
- **AWS**: Deploy using Elastic Beanstalk or EC2
- **Google Cloud**: Use App Engine or Cloud Run

### Important Production Considerations

- Use environment variables for all sensitive information
- Set DEBUG=False in production
- Use HTTPS with a valid SSL certificate
- Set up database backups
- Implement proper logging

## Demo Accounts

The following demo accounts are available for testing the platform functionality:

| User Type | Email | Password | Description |
|----------|-------|----------|-------------|
| Student | student@example.com | password123 | Demo student account with complete profile |
| PI | pi@example.com | password123 | Demo PI account with lab information |
| Industry | industry@example.com | password123 | Demo industry partner account |
| Vendor | vendor@example.com | password123 | Demo vendor account |
| Admin | admin@example.com | admin123 | Administrator account with full access |

## Database Structure

The platform uses a relational database model with the following key tables:

- `users`: User authentication information
- `profiles`: Basic profile information for all users
- `student_profiles`, `pi_profiles`, `industry_profiles`, `vendor_profiles`: Type-specific profile data
- `opportunities`: Research positions and collaborations
- `applications`: User applications to opportunities
- `messages`: Direct messages between users
- `notifications`: System notifications

## Contributing

We welcome contributions to the Research Collaboration Platform. Please feel free to submit pull requests or open issues for bugs and feature requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The research community for providing valuable feedback
- Contributors and testers who helped improve the platform
- Open source libraries and frameworks that made this project possible
