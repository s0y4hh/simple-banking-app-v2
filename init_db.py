import os
import pymysql
from dotenv import load_dotenv
import subprocess
from werkzeug.security import generate_password_hash
import datetime
import psgc_api
import traceback  # For detailed error tracing
from extensions import db

# Load environment variables
load_dotenv()

def init_mysql_database():
    """Initialize the MySQL database directly in Python instead of using schema.sql."""
    # Use correct environment variable names
    mysql_user = os.environ.get('MYSQL_USER', 'bankapp')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 's0y4hh')
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'simple_banking')
    
    # Convert port to string to avoid type issues
    mysql_port = str(mysql_port)
    
    # Try to connect to MySQL server without database (to create it if needed)
    try:
        print("Attempting to connect to MySQL server...")
        print(f"Connection details: {mysql_host}:{mysql_port} as {mysql_user}")
        connection = pymysql.connect(
            host=mysql_host,
            port=int(mysql_port),
            user=mysql_user,
            password=mysql_password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10  # Add timeout to prevent hanging
        )
        
        print("Connected to MySQL server successfully!")
        
        try:
            with connection.cursor() as cursor:
                # Drop database if exists
                print("Dropping database if it exists...")
                cursor.execute(f"DROP DATABASE IF EXISTS {mysql_database}")
                
                # Create database
                print("Creating database...")
                cursor.execute(f"CREATE DATABASE {mysql_database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                
                # Use the database
                print("Switching to database...")
                cursor.execute(f"USE {mysql_database}")
                
                # Create users table
                print("Creating users table...")
                cursor.execute("""
                CREATE TABLE user (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  username VARCHAR(64) NOT NULL UNIQUE,
                  email VARCHAR(120) NOT NULL UNIQUE,
                  firstname VARCHAR(64),
                  lastname VARCHAR(64),
                  address_line VARCHAR(256),
                  region_code VARCHAR(20),
                  region_name VARCHAR(100),
                  province_code VARCHAR(20),
                  province_name VARCHAR(100),
                  city_code VARCHAR(20),
                  city_name VARCHAR(100),
                  barangay_code VARCHAR(20),
                  barangay_name VARCHAR(100),
                  postal_code VARCHAR(10),
                  phone VARCHAR(20),
                  password_hash VARCHAR(128) NOT NULL,
                  account_number VARCHAR(10) NOT NULL UNIQUE,
                  balance FLOAT DEFAULT 1000.0,
                  status VARCHAR(20) DEFAULT 'pending',
                  is_admin BOOLEAN DEFAULT FALSE,
                  is_manager BOOLEAN DEFAULT FALSE,
                  pin VARCHAR(4),  -- New field: PIN
                  security_question VARCHAR(100),  -- New field: Security question
                  security_answer_hash VARCHAR(128),  -- New field: Security answer (hashed)
                  date_registered DATETIME DEFAULT CURRENT_TIMESTAMP,
                  INDEX idx_username (username),
                  INDEX idx_email (email),
                  INDEX idx_account_number (account_number)
                ) ENGINE=InnoDB
                """)
                
                # Create transactions table
                print("Creating transactions table...")
                cursor.execute("""
                CREATE TABLE transaction (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  sender_id INT,
                  receiver_id INT,
                  amount FLOAT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  transaction_type VARCHAR(20) DEFAULT 'transfer',
                  details TEXT,
                  FOREIGN KEY (sender_id) REFERENCES user (id),
                  FOREIGN KEY (receiver_id) REFERENCES user (id),
                  INDEX idx_sender (sender_id),
                  INDEX idx_receiver (receiver_id),
                  INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB
                """)
                
                print("Database schema initialized successfully!")
            
            connection.commit()
        except Exception as sql_error:
            print(f"Error during SQL execution: {sql_error}")
            print(traceback.format_exc())
            return False
    
    except Exception as e:
        print(f"Error initializing database: {e}")
        print(traceback.format_exc())
        return False
    
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("MySQL connection closed.")
    
    return True  # Return True on success

def init_flask_app_db():
    """Initialize the Flask application's database tables using SQLAlchemy."""
    try:
        from app import app
        from extensions import db, bcrypt
        from models import User, Transaction
        
        with app.app_context():
            print("Initializing Flask application database...")
            
            # Drop all tables and recreate them
            try:
                print("Dropping existing tables...")
                db.drop_all()
                print("Creating new tables...")
                db.create_all()
                print("Tables created with the updated schema")
            except Exception as schema_error:
                print(f"Error creating schema: {schema_error}")
                print(traceback.format_exc())
                return False
            
            # Create sample data
            try:
                # Check if there are manager users, if not create one
                print("Creating manager user...")
                manager = User.query.filter_by(is_manager=True).first()
                if not manager:
                    manager_user = User(
                        username="manager",
                        email="manager@bankapp.com",
                        account_number="0000000000",
                        status="active",
                        is_admin=True,
                        is_manager=True,
                        balance=1000.0,
                        firstname="System",
                        lastname="Manager",
                        # NCR - Manila - Malate address
                        address_line="123 Taft Avenue",
                        region_code="130000000",
                        region_name="National Capital Region",
                        province_code="137400000",
                        province_name="NCR Fourth District",
                        city_code="137404000",
                        city_name="Manila",
                        barangay_code="137404022",
                        barangay_name="Malate",
                        postal_code="1004",
                        phone="+63917123456"
                    )
                    manager_user.set_password("manager123")
                    db.session.add(manager_user)
                    db.session.commit()
                    print("Created manager user with username 'manager' and password 'manager123'")
                
                # Check if there are admin users, if not create one
                print("Creating admin user...")
                admin = User.query.filter_by(is_admin=True, is_manager=False).first()
                if not admin:
                    admin_user = User(
                        username="admin",
                        email="admin@bankapp.com",
                        account_number="0000000001",
                        status="active",
                        is_admin=True,
                        is_manager=False,
                        balance=1000.0,
                        firstname="Admin",
                        lastname="User",
                        # Cebu - Cebu City address
                        address_line="456 Osmeña Boulevard",
                        region_code="070000000",
                        region_name="Central Visayas",
                        province_code="072200000",
                        province_name="Cebu",
                        city_code="072217000",
                        city_name="Cebu City",
                        barangay_code="072217009",
                        barangay_name="Guadalupe",
                        postal_code="6000",
                        phone="+63918765432"
                    )
                    admin_user.set_password("admin123")
                    db.session.add(admin_user)
                    db.session.commit()
                    print("Created admin user with username 'admin' and password 'admin123'")
                
                # Create a sample active user for testing
                sample_user = User.query.filter_by(username="testuser").first()
                if not sample_user:
                    sample_user = User(
                        username="testuser",
                        email="test@example.com",
                        account_number="1234567890",
                        status="active",  # Active for testing
                        balance=1000.0,
                        firstname="Test",
                        lastname="User",
                        # Davao - Davao City address
                        address_line="789 Quimpo Boulevard",
                        region_code="110000000",
                        region_name="Davao Region",
                        province_code="112400000",
                        province_name="Davao del Sur",
                        city_code="112402000",
                        city_name="Davao City",
                        barangay_code="112402036",
                        barangay_name="Matina Crossing",
                        postal_code="8000",
                        phone="+63929876543"
                    )
                    sample_user.set_password("testpassword")
                    db.session.add(sample_user)
                    db.session.commit()
                    print("Created sample user: testuser (active)")
                
                # Create a sample inactive user for testing
                inactive_user = User.query.filter_by(username="pendinguser").first()
                if not inactive_user:
                    inactive_user = User(
                        username="pendinguser",
                        email="pending@example.com",
                        account_number="0987654321",
                        status="pending",  # Pending for testing
                        balance=1000.0,
                        firstname="Pending",
                        lastname="User",
                        address_line="321 Pending Road",  # Fix: use address_line instead of address
                        city_name="Pending Valley",
                        phone="+5566778899"
                    )
                    inactive_user.set_password("pendingpassword")
                    db.session.add(inactive_user)
                    db.session.commit()
                    print("Created sample user: pendinguser (pending approval)")
                
                # Create a sample deactivated user for testing
                deactivated_user = User.query.filter_by(username="deactivateduser").first()
                if not deactivated_user:
                    deactivated_user = User(
                        username="deactivateduser",
                        email="deactivated@example.com",
                        account_number="5678901234",
                        status="deactivated",  # Deactivated for testing
                        balance=1000.0,
                        firstname="Deactivated",
                        lastname="User",
                        address_line="654 Inactive Street",  # Fix: use address_line instead of address
                        city_name="Inactive City",
                        phone="+9988776655"
                    )
                    deactivated_user.set_password("deactivatedpassword")
                    db.session.add(deactivated_user)
                    db.session.commit()
                    print("Created sample user: deactivateduser (deactivated)")
                
                # Create some sample transactions for testing
                if sample_user and admin:
                    # Check if we already have transactions
                    transaction_count = Transaction.query.count()
                    if transaction_count == 0:
                        # Create a sample deposit from admin to test user
                        deposit_transaction = Transaction(
                            sender_id=admin.id,
                            receiver_id=sample_user.id,
                            amount=250.0,
                            transaction_type='deposit',
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.session.add(deposit_transaction)
                        
                        # Create a sample transfer between users
                        transfer_transaction = Transaction(
                            sender_id=sample_user.id,
                            receiver_id=inactive_user.id,
                            amount=100.0,
                            transaction_type='transfer',
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.session.add(transfer_transaction)
                        
                        # Admin receiving a transfer (for audit testing)
                        admin_receive_transaction = Transaction(
                            sender_id=sample_user.id,
                            receiver_id=admin.id,
                            amount=50.0,
                            transaction_type='transfer',
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.session.add(admin_receive_transaction)
                        
                        # Admin making a transfer (for audit testing)
                        admin_send_transaction = Transaction(
                            sender_id=admin.id,
                            receiver_id=inactive_user.id,
                            amount=75.0,
                            transaction_type='transfer',
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.session.add(admin_send_transaction)
                        
                        # Add a sample deposit between admins (if multiple admins exist)
                        if manager:
                            admin_deposit_transaction = Transaction(
                                sender_id=manager.id,
                                receiver_id=admin.id,
                                amount=500.0,
                                transaction_type='deposit',
                                timestamp=datetime.datetime.utcnow()
                            )
                            db.session.add(admin_deposit_transaction)
                        
                        # Add a sample user edit transaction for audit demonstration
                        sample_edit_details = [
                            "First Name: None → Test",
                            "Last Name: None → User",
                            "Address Line: None → 789 Quimpo Boulevard",
                            "Region: None → Davao Region",
                            "City/Municipality: None → Davao City",
                            "Status: pending → active"
                        ]
                        
                        user_edit_transaction = Transaction(
                            sender_id=admin.id,      # Admin who made the edit
                            receiver_id=sample_user.id,   # User who was edited
                            amount=None,                  # No amount for user edits
                            transaction_type='user_edit',
                            details="\n".join(sample_edit_details),
                            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1)  # Slightly older to show in history
                        )
                        db.session.add(user_edit_transaction)
                        
                        db.session.commit()
                        print("Created sample transactions including admin transactions for audit")
                    else:
                        print(f"Found {transaction_count} existing transactions in the database")
            
            except Exception as data_error:
                print(f"Error creating sample data: {data_error}")
                print(traceback.format_exc())
                return False
            
            print("Flask application database initialized successfully!")
            return True
    except Exception as e:
        print(f"Error initializing Flask app database: {e}")
        print(traceback.format_exc())
        return False

def init_db():
    """Initialize the database by dropping and recreating all tables, and adding a default admin user."""
    from models import User, Transaction
    db.drop_all()
    db.create_all()
    credentials = []
    # Create default admin user
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@bankapp.com",
            status="active",
            is_admin=True
        )
        admin.set_password("Admin!234")
        admin.set_pin("4321")
        admin.security_question = "first_teacher"
        admin.set_security_answer("Smith")
        db.session.add(admin)
        db.session.commit()
        credentials.append("Admin: username=admin, password=Admin!234, PIN=4321, security question='What is the last name of your first teacher?', answer=Smith")
    # Create default manager user
    if not User.query.filter_by(username="manager").first():
        manager = User(
            username="manager",
            email="manager@bankapp.com",
            status="active",
            is_admin=True,
            is_manager=True
        )
        manager.set_password("Manager!234")
        manager.set_pin("9876")
        manager.security_question = "dream_job"
        manager.set_security_answer("Astronaut")
        db.session.add(manager)
        db.session.commit()
        credentials.append("Manager: username=manager, password=Manager!234, PIN=9876, security question='What was your dream job as a child?', answer=Astronaut")
    # Create a sample active user
    if not User.query.filter_by(username="testuser").first():
        user = User(
            username="testuser",
            email="testuser@example.com",
            status="active"
        )
        user.set_password("Test!234")
        user.set_pin("2468")
        user.security_question = "memorable_place"
        user.set_security_answer("Boracay")
        db.session.add(user)
        db.session.commit()
        credentials.append("Test User: username=testuser, password=Test!234, PIN=2468, security question='What is the name of a memorable place from your childhood?', answer=Boracay")
    # Create a sample pending user
    if not User.query.filter_by(username="pendinguser").first():
        user = User(
            username="pendinguser",
            email="pendinguser@example.com",
            status="pending"
        )
        user.set_password("Pending!234")
        user.set_pin("1357")
        user.security_question = "favorite_childhood_friend"
        user.set_security_answer("Miguel")
        db.session.add(user)
        db.session.commit()
        credentials.append("Pending User: username=pendinguser, password=Pending!234, PIN=1357, security question='What is the first name of your favorite childhood friend?', answer=Miguel")
    # Create a sample deactivated user
    if not User.query.filter_by(username="deactivateduser").first():
        user = User(
            username="deactivateduser",
            email="deactivateduser@example.com",
            status="deactivated"
        )
        user.set_password("Deactivated!234")
        user.set_pin("8642")
        user.security_question = "first_pet"
        user.set_security_answer("Shadow")
        db.session.add(user)
        db.session.commit()
        credentials.append("Deactivated User: username=deactivateduser, password=Deactivated!234, PIN=8642, security question='What was the name of your first pet?', answer=Shadow")
    print("\n=== Database recreated and all default users added with PIN and security question/answer. ===\n")
    print("Credentials for all default users:")
    for cred in credentials:
        print(cred)

if __name__ == "__main__":
    print("== Simple Banking App Database Initialization (SQLAlchemy based) ==")

    from app import app

    with app.app_context():
        init_db() 
    
    print("\n=== SQLAlchemy database schema created and default users seeded. ===")
    print("If this is for production, ensure drop_all() is handled carefully or removed after first setup.")