from __future__ import annotations

"""
Central application configuration

Environment variables can be placed in a `.env` file at repository root or
exported normally. This module guarantees:

1. Directories `data/documents` and `data/indices` always exist.
2. `OPENAI_API_KEY` is mandatory (clear exception if missing or empty).
3. `openai` Python client is initialised automatically when present.
"""

import logging
import os
from pathlib import Path
from typing import Final, Optional, cast

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
OPENAI_API_KEY: Final[str] = cast(str, _env("OPENAI_API_KEY", mandatory=True))
OPENAI_API_BASE: Final[Optional[str]] = _env("OPENAI_API_BASE")

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

# --------------------------------------------------------------------------- #
# Optional third-party client configuration
# --------------------------------------------------------------------------- #
try:
    import openai  # type: ignore

    openai.api_key = OPENAI_API_KEY
    if OPENAI_API_BASE:
        logger.info("Configured OpenAI client with custom base URL %s", OPENAI_API_BASE)
except ModuleNotFoundError:
    logger.info("openai package not installed – skipping client configuration")

# --------------------------------------------------------------------------- #
# Public exports
# --------------------------------------------------------------------------- #
__all__ = [
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "REPO_ROOT",
    "DATA_DIR",
    "UPLOAD_DIR",
    "INDEX_DIR",
    "_env",
]
