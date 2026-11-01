"""Optional community module: python-garminconnect (unofficial Garmin Connect API).

Used only when ENABLE_GARMINCONNECT=true, for what the official Personal API does not offer:
structured workouts (write access), per-lap grade-adjusted pace and shoes.
Login tokens are persisted in DATA_DIR/tokens.
"""
from __future__ import annotations

import getpass
import logging

from . import config

log = logging.getLogger(__name__)

RELOGIN_HINT = "Log in again with: docker compose run --rm garmin-coach login"


EXTENSION_MSG = (
    "Writing workouts to Garmin is not available in the Claude Desktop extension: the official Garmin "
    "Personal API used by the extension is read-only. Write access is available in the Docker version "
    "with the optional community module (see the project README, 'Write access (optional)')."
)

DISABLED_MSG = (
    "This needs write access to Garmin Connect, which the official Personal API does not provide "
    "(it is read-only). Enable the optional community module: set ENABLE_GARMINCONNECT=true in .env, "
    "run `docker compose up -d`, then `docker compose run --rm garmin-coach login` and "
    "`docker compose restart`. See the README section 'Write access (optional)'."
)


class AuthRequired(RuntimeError):
    pass


class Disabled(RuntimeError):
    pass


def too_many_requests_error() -> type[Exception]:
    """python-garminconnect's 429 exception, or a placeholder when the package is not installed."""
    try:
        from garminconnect.exceptions import GarminConnectTooManyRequestsError
        return GarminConnectTooManyRequestsError
    except ImportError:  # desktop extension: community module not installed
        class _NeverRaised(Exception):
            pass
        return _NeverRaised


def _tokenstore() -> str:
    config.TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    return str(config.TOKEN_DIR)


def client():
    """Authenticated client from saved tokens (refreshed automatically).
    Raises AuthRequired when tokens are no longer valid and no usable credentials exist,
    Disabled when the module is not enabled."""
    if config.RUNTIME == "extension":
        raise Disabled(EXTENSION_MSG)
    if not config.ENABLE_GARMINCONNECT:
        raise Disabled(DISABLED_MSG)
    from garminconnect import Garmin
    g = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD,
               prompt_mfa=_no_mfa, retry_attempts=3)
    try:
        g.login(_tokenstore())
    except Exception as e:  # noqa: BLE001
        raise AuthRequired(f"Garmin login failed ({type(e).__name__}: {e}). {RELOGIN_HINT}") from e
    return g


def persist(g) -> None:
    """Save tokens (they may have been refreshed during the calls)."""
    try:
        g.client.dump(_tokenstore())
    except Exception as e:  # noqa: BLE001
        log.warning("Could not save tokens: %s", e)


def _no_mfa() -> str:
    raise AuthRequired("Garmin is asking for an MFA code: an interactive login is required.")


def interactive_login() -> None:
    email = config.GARMIN_EMAIL or input("Garmin email: ").strip()
    password = config.GARMIN_PASSWORD or getpass.getpass("Garmin password: ")
    from garminconnect import Garmin
    g = Garmin(email, password, prompt_mfa=lambda: input("MFA code: ").strip())
    g.login(_tokenstore())
    persist(g)
    name = None
    try:
        name = g.get_full_name()
    except Exception:  # noqa: BLE001
        pass
    print(f"Login OK{f' ({name})' if name else ''}. Tokens saved in {config.TOKEN_DIR}")
