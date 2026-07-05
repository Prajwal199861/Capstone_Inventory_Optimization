"""
=============================================================================
User Repository
=============================================================================
"""

from sqlalchemy.orm import joinedload

from database.session import SessionLocal
from models.user import User


class UserRepository:

    def __init__(self):

        self.session = SessionLocal()

    def get_by_username(
            self,
            username: str
    ):

        return (

            self.session.query(User)

            .options(joinedload(User.role))

            .filter(User.username == username)

            .first()

        )

    def close(self):

        self.session.close()