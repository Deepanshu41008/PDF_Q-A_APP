from __future__ import annotations

"""
Central application configuration

Environment variables can be placed in a `.env` file at repository root or
exported normally. This module guarantees:

1. Directories `data/documents` and `data/indices` always exist.
2. OpenAI client is initialized when API key is available.
3. Configuration for models, CORS, file uploads, and database is provided.
"""

import logging
import os
from pathlib import Path
from typing import Final, Optional, Set, cast

try:
    from dotenv import load_dotenv, find_dotenv
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "python-dotenv is required but not installed, run "
        "'pip install python-dotenv'"
    ) from exc

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
# Ensure the root logger has at least a basic configuration.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Environment variables
# --------------------------------------------------------------------------- #
# load_dotenv() no-ops when file is missing, so warn explicitly
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)
    logger.debug("Loaded environment from %s", _dotenv_path)
else:
    logger.debug(".env file not found – relying solely on process env vars")


def _env(
    key: str,
    default: Optional[str] = None,
    *,
    mandatory: bool = False,
) -> Optional[str]:
    """
    Retrieve environment variable `key`.

    If *mandatory* is True and the variable is missing **or empty**,
    an ``EnvironmentError`` is raised.
    """
    val = os.getenv(key, default)
    if mandatory and (val is None or val == ""):
        raise EnvironmentError(f"Environment variable '{key}' is required but not set")
    return val


# API keys / endpoints ------------------------------------------------------- #
OPENROUTER_API_KEY: Final[Optional[str]] = _env("OPENROUTER_API_KEY", mandatory=True)
LLM_API_BASE: Final[Optional[str]] = _env("LLM_API_BASE", "https://openrouter.ai/api/v1")

# Model Configuration -------------------------------------------------------- #
CHAT_MODEL_NAME: Final[str] = cast(str, _env("CHAT_MODEL_NAME", "sarvamai/sarvam-m:free"))
EMBEDDING_MODEL: Final[str] = cast(str, _env("EMBEDDING_MODEL", "text-embedding-ada-002")) # Assuming this model name is compatible with OpenRouter or used with specific settings

# CORS Configuration --------------------------------------------------------- #
CORS_ORIGINS: Final[str] = cast(str, _env("CORS_ORIGINS", "http://localhost:12001,http://localhost:3000"))

# File upload settings ------------------------------------------------------- #
MAX_UPLOAD_SIZE: Final[int] = int(_env("MAX_UPLOAD_SIZE", str(20 * 1024 * 1024)) or str(20 * 1024 * 1024))  # 20MB default
ALLOWED_EXTENSIONS: Final[Set[str]] = {".pdf"}

# Database ------------------------------------------------------------------- #
# DATABASE_URL will be defined after DATA_DIR is set below

# --------------------------------------------------------------------------- #
# Filesystem paths
# --------------------------------------------------------------------------- #
# Resolve repository root robustly even if folder depth is < 2.
_repo_root = Path(__file__).resolve()
for _ in range(3):  # walk up until we find the git repo, or exhaust 3 levels
    if (_repo_root / ".git").exists() or (_repo_root / "pyproject.toml").exists():
        break
    _repo_root = _repo_root.parent

REPO_ROOT: Final[Path] = _repo_root
DATA_DIR: Final[Path] = REPO_ROOT / "data"
UPLOAD_DIR: Final[Path] = DATA_DIR / "documents"
INDEX_DIR: Final[Path] = DATA_DIR / "indices"

for _dir in (UPLOAD_DIR, INDEX_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

logger.debug("DATA_DIR set to %s", DATA_DIR)

# now that DATA_DIR is defined, set DATABASE_URL
DATABASE_URL: Final[str] = cast(
    str,
    _env("DATABASE_URL", f"sqlite:///{DATA_DIR}/pdf_qa.db")
)

# --------------------------------------------------------------------------- #
# Optional third-party client configuration
# --------------------------------------------------------------------------- #
llm_client = None
if OPENROUTER_API_KEY:
    try:
        from openai import OpenAI # Keep using openai library for OpenAI-compatible APIs
        
        llm_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=LLM_API_BASE)
        logger.info("LLM client initialized successfully for OpenRouter.")
    except ModuleNotFoundError:
        logger.warning("openai package not installed – skipping LLM client configuration")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
else:
    logger.warning("OPENROUTER_API_KEY not set - LLM functionality will not work")

# --------------------------------------------------------------------------- #
# Public exports
# --------------------------------------------------------------------------- #
__all__ = [
    "OPENROUTER_API_KEY",
    "LLM_API_BASE",
    "CHAT_MODEL_NAME",
    "EMBEDDING_MODEL",
    "CORS_ORIGINS",
    "MAX_UPLOAD_SIZE",
    "ALLOWED_EXTENSIONS",
    "DATABASE_URL",
    "REPO_ROOT",
    "DATA_DIR",
    "UPLOAD_DIR",
    "INDEX_DIR",
    "llm_client", # Renamed from openai_client
    "_env",
]
