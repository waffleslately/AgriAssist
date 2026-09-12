"""
Firebase Admin SDK service.

Lazy-initializes the Firebase Admin app exactly once using the service-account
JSON file path set in FIREBASE_SERVICE_ACCOUNT_JSON_PATH.

If that env var is empty (local dev without Firebase), the module runs in
SIMULATION mode: verify_firebase_id_token() raises ValueError so callers
know Firebase is not configured, rather than silently succeeding.
"""
import logging
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings

log = logging.getLogger("agri_backend")

_firebase_app: Optional[firebase_admin.App] = None
_simulation_mode: bool = False


def _init_firebase() -> None:
    global _firebase_app, _simulation_mode

    if _firebase_app is not None:
        return  # already initialised

    sa_path = settings.FIREBASE_SERVICE_ACCOUNT_JSON_PATH.strip()
    project_id = settings.FIREBASE_PROJECT_ID.strip()

    if not sa_path:
        log.warning(
            "FIREBASE_SERVICE_ACCOUNT_JSON_PATH is not set -- "
            "Firebase Admin running in SIMULATION mode. "
            "verify_firebase_id_token() will always raise ValueError."
        )
        _simulation_mode = True
        return

    sa_file = Path(sa_path)
    if not sa_file.exists():
        log.error("Firebase service-account file not found at: %s", sa_path)
        _simulation_mode = True
        return

    cred = credentials.Certificate(str(sa_file))
    options = {"projectId": project_id} if project_id else {}
    _firebase_app = firebase_admin.initialize_app(cred, options)
    log.info("Firebase Admin SDK initialised (project: %s)", project_id or "from-service-account")


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token server-side.

    Returns the decoded token payload dict with keys:
        uid, phone_number, iss, aud, iat, exp, ...

    Raises:
        ValueError  -- Firebase not configured (simulation mode).
        firebase_admin.auth.InvalidIdTokenError -- token is invalid/expired.
    """
    _init_firebase()

    if _simulation_mode:
        raise ValueError(
            "Firebase is not configured on this server. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON_PATH in your .env file."
        )

    # check_revoked=True ensures revoked tokens are rejected
    decoded = firebase_auth.verify_id_token(id_token, check_revoked=True)
    return decoded
