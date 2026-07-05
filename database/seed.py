"""
=============================================================================
Database Seed
=============================================================================
"""

import bcrypt

from models.role import Role
from models.user import User
from database.session import SessionLocal


def seed_database():

    session = SessionLocal()

    try:

        # ---------------------------------------------------
        # Roles
        # ---------------------------------------------------

        if session.query(Role).count() == 0:

            session.add_all([
                Role(
                    role_name="Admin",
                    description="System Administrator"
                ),
                Role(
                    role_name="Manager",
                    description="Business Manager"
                ),
                Role(
                    role_name="User",
                    description="Normal User"
                )
            ])

            session.commit()

        # ---------------------------------------------------
        # Admin User
        # ---------------------------------------------------

        if session.query(User).count() == 0:

            admin_role = (
                session.query(Role)
                .filter_by(role_name="Admin")
                .first()
            )

            password = bcrypt.hashpw(
                "admin123".encode(),
                bcrypt.gensalt()
            ).decode()

            admin = User(
                full_name="System Administrator",
                username="admin",
                email="admin@retailai.com",
                password_hash=password,
                role_id=admin_role.id,
                is_active=True
            )

            session.add(admin)

            session.commit()

    finally:

        session.close()