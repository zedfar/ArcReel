"""
Environment initialization module.

Load .env file.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def init_environment():
    """
    Initialize project environment.

    1. Locate project root directory
    2. Load .env file
    """
    # Get project root directory (parent of lib)
    lib_dir = Path(__file__).parent
    project_root = lib_dir.parent

    # Load .env file
    try:
        from dotenv import load_dotenv

        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
    except ImportError:
        pass  # Skip if python-dotenv is not installed

    return project_root


# Auto-initialize when module is imported
PROJECT_ROOT = init_environment()
