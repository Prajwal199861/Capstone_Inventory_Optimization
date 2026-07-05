"""
=============================================================================
Authentication Service
=============================================================================
"""

from auth.password import PasswordManager
from repositories.user_repository import UserRepository


class AuthenticationService:

    @staticmethod
    def login(
            username: str,
            password: str
    ):

        repository = UserRepository()

        user = repository.get_by_username(username)

        repository.close()

        if user is None:

            return None

        if PasswordManager.verify_password(

                password,

                user.password_hash

        ):

            return user

        return None