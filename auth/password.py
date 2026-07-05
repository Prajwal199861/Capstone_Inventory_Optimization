"""
=============================================================================
Password Utility
=============================================================================
"""

import bcrypt


class PasswordManager:

    @staticmethod
    def hash_password(password: str) -> str:

        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    @staticmethod
    def verify_password(
            password: str,
            password_hash: str
    ) -> bool:

        return bcrypt.checkpw(
            password.encode(),
            password_hash.encode()
        )