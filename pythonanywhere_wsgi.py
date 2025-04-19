"""
This file contains the WSGI configuration for PythonAnywhere.
You should copy this content to your PythonAnywhere WSGI file and 
replace the environment variable values with your actual credentials.
"""

import sys
import os

# Set environment variables for database connection
# Replace these values with your actual PythonAnywhere MySQL credentials
os.environ['SECRET_KEY'] = 'your_secure_secret_key_here'
os.environ['MYSQL_USER'] = 'ripir28264'  # Usually your PythonAnywhere username
os.environ['MYSQL_PASSWORD'] = 'your_mysql_password'
os.environ['MYSQL_HOST'] = 'ripir28264.mysql.pythonanywhere-services.com'  # Use the full hostname
os.environ['MYSQL_PORT'] = '3306'  # MySQL port is typically 3306
os.environ['MYSQL_DATABASE'] = 'ripir28264$simple_banking'  # database name with username prefix

# Add your project directory to the sys.path
project_home = '/home/ripir28264/simple-banking-app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import flask app but need to call it "application" for WSGI to work
from app import app as application  # noqa 