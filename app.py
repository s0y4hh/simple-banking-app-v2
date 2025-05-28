import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
import secrets
import pymysql
from flask_wtf.csrf import CSRFProtect
from flask_limiter.errors import RateLimitExceeded
from werkzeug.urls import url_parse

# Import extensions
from extensions import db, login_manager, bcrypt, limiter

# Load environment variables
load_dotenv()

# Initialize CSRF protection
csrf = CSRFProtect()

# MySQL connection
pymysql.install_as_MySQLdb()

# Create Flask application
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)

    # CSRF Protection
    csrf.init_app(app)

    # Database configuration

    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Heroku's DATABASE_URL for Postgres starts with postgres://, SQLAlchemy prefers postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"Using DATABASE_URL from environment: {database_url[:30]}...") # Log a snippet for security
    else:
        # Fallback to local MySQL setup using individual environment variables
        print("DATABASE_URL not found, falling back to MYSQL_... variables for local development.")
        mysql_user = os.environ.get('MYSQL_USER', 'bankapp')
        mysql_password = os.environ.get('MYSQL_PASSWORD', 's0y4hh')
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_database = os.environ.get('MYSQL_DATABASE', 'simple_banking')
        
        if not all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_database]):
            print("WARNING: One or more MYSQL_ environment variables are not set for local development.")
            # Handle this case appropriately, maybe raise an error or use a default SQLite for local if preferred
            # For now, we'll assume they are set or the defaults are acceptable for local testing
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        print(f"Using local MySQL URI: mysql+pymysql://{mysql_user}:****@{mysql_host}:{mysql_port}/{mysql_database}")


    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    # Register custom error handler for rate limiting
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        # Check if it's an API request (expecting JSON)
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Rate limit exceeded", "message": str(e)}), 429
        # Otherwise, return the HTML template
        return render_template('rate_limit_error.html', message=str(e)), 429

    return app

# Create Flask app
app = create_app()

# Import models - must be after db initialization
from models import User, Transaction

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes after app creation
from routes import *

# --- Add: Make balance visibility available in all templates ---
@app.context_processor
def inject_balance_visibility():
    return {'show_balance': session.get('show_balance', True)}

# Database initialization function
def init_db():
    """Initialize the database with required tables and default admin user."""
    with app.app_context():
        db.create_all()
        # Check if there are admin users, if not create one
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@bankapp.com",
                account_number="0000000001",
                status="active",
                is_admin=True,
                balance=0.0
            )
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
            print("Created admin user with username 'admin' and password 'admin123'")

if __name__ == '__main__':
    # Print environment variables for debugging
    print(f"Environment variables:")
    print(f"MYSQL_HOST: {os.environ.get('MYSQL_HOST')}")
    print(f"MYSQL_USER: {os.environ.get('MYSQL_USER')}")
    print(f"MYSQL_DATABASE: {os.environ.get('MYSQL_DATABASE')}")
    
    with app.app_context():
        db.create_all()
    app.run(debug=True)
