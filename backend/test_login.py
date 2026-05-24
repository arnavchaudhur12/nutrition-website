#!/usr/bin/env python3.12
"""
Quick test script to debug login without running the full server
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import get_settings
    from app.core.security import get_password_hash, verify_password, create_access_token
    from app.db.session import SessionLocal, engine
    from app.db.base import Base
    from app.models.user import User
    from sqlalchemy import select
    
    print("✓ All imports successful")
    
    # Initialize database
    print("\n--- Initializing Database ---")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Get settings
    settings = get_settings()
    print(f"\n--- Settings ---")
    print(f"✓ Database URL: {settings.database_url}")
    print(f"✓ Secret key length: {len(settings.secret_key)} chars")
    print(f"✓ Algorithm: {settings.algorithm}")
    print(f"✓ Access token expire minutes: {settings.access_token_expire_minutes}")
    
    # Test with database
    db = SessionLocal()
    
    # Check if admin exists
    admin_email = settings.admin_email
    admin_password = settings.admin_password
    
    print(f"\n--- Checking Admin User ---")
    admin = db.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
    
    if admin:
        print(f"✓ Admin user exists: {admin.email}")
        print(f"  - ID: {admin.id}")
        print(f"  - Full name: {admin.full_name}")
        print(f"  - Is admin: {admin.is_admin}")
        print(f"  - Password hash length: {len(admin.hashed_password)}")
        
        # Test password verification
        print(f"\n--- Testing Password Verification ---")
        is_valid = verify_password(admin_password, admin.hashed_password)
        print(f"  - Password valid: {is_valid}")
        
        if is_valid:
            # Test token creation
            print(f"\n--- Testing Token Creation ---")
            token = create_access_token(admin.email)
            print(f"  - Token created: {token[:50]}...")
            print("✓ All operations successful!")
        else:
            print("✗ Password verification failed!")
    else:
        print(f"✗ Admin user not found: {admin_email}")
        print("  Creating admin user...")
        
        admin = User(
            email=admin_email,
            full_name="Lagads Nutrition Admin",
            hashed_password=get_password_hash(admin_password),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        print(f"✓ Admin user created")
        
        # Test password verification
        print(f"\n--- Testing Password Verification ---")
        is_valid = verify_password(admin_password, admin.hashed_password)
        print(f"  - Password valid: {is_valid}")
        
        if is_valid:
            # Test token creation
            print(f"\n--- Testing Token Creation ---")
            token = create_access_token(admin.email)
            print(f"  - Token created: {token[:50]}...")
            print("✓ All operations successful!")
        else:
            print("✗ Password verification failed!")
    
    db.close()
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
