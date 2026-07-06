"""
=============================================================================
File Utility
=============================================================================
"""

import os
import uuid


UPLOAD_FOLDER = "uploads"


def generate_filename(
        original_filename: str
):

    extension = os.path.splitext(
        original_filename
    )[1]

    return (
            str(uuid.uuid4())

            + extension
    )