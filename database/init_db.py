"""
=============================================================================
Database Initialization
=============================================================================
"""

from database.base import Base
from database.engine import engine
from models.dataset import Dataset
from models.dataset_file import DatasetFile
from models.column_mapping import ColumnMapping

# Import Models
from models.role import Role
from models.user import User
from models.audit_log import AuditLog

from database.seed import seed_database


def initialize_database():

    Base.metadata.create_all(bind=engine)

    seed_database()