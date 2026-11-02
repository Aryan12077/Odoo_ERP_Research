"""
Configuration module for Odoo JSON-RPC Client and Target PostgreSQL DWH.

Responsibilities:
- Load environment variables from .env
- Validate required settings
- Expose immutable configuration objects
"""

from dataclasses import dataclass
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


@dataclass(frozen=True)
class OdooConfig:
    """
    Immutable configuration for connecting to Odoo.
    """
    url: str
    database: str
    username: str
    secret: str
    timeout: int
    verify_ssl: bool


@dataclass(frozen=True)
class TargetDBConfig:
    """
    Configuration for connecting to the target PostgreSQL Data Warehouse.
    """
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: str = "EVA_BI"


def _get_env(name: str, default: str = None, required: bool = True) -> str:
    """
    Return an environment variable.

    Raises:
        ValueError: if the variable is required but missing or empty.
    """
    value = os.getenv(name, default)

    if required and (value is None or value.strip() == ""):
        raise ValueError(f"Environment variable '{name}' is missing or empty.")

    return value


# Odoo Source Configuration
config = OdooConfig(
    url=_get_env("ODOO_URL").rstrip("/"),
    database=_get_env("ODOO_DB"),
    username=_get_env("ODOO_USERNAME"),
    secret=_get_env("ODOO_SECRET"),
    timeout=int(os.getenv("ODOO_TIMEOUT", 30)),
    verify_ssl=os.getenv("ODOO_VERIFY_SSL", "True").lower() == "true",
)


def get_target_db_config() -> TargetDBConfig:
    """
    Returns the target PostgreSQL database configuration.
    Validates required settings lazily when destination DB is accessed.
    """
    return TargetDBConfig(
        host=_get_env("TARGET_DB_HOST"),
        port=int(_get_env("TARGET_DB_PORT", "5432")),
        database=_get_env("TARGET_DB_NAME"),
        username=_get_env("TARGET_DB_USER"),
        password=_get_env("TARGET_DB_PASSWORD"),
        schema=_get_env("TARGET_DB_SCHEMA", "EVA_BI", required=False) or "EVA_BI",
    )
