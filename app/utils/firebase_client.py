from typing import Optional
import os

from flask import current_app

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:  # pragma: no cover
    firebase_admin = None
    credentials = None
    firestore = None

_fs_client = None


def init_firebase(app) -> None:
    """Initialize Firebase Admin SDK if enabled by config.
    Safe to call multiple times; it will only initialize once.
    """
    global _fs_client

    enabled = app.config.get('FIREBASE_ENABLED', False)
    if not enabled:
        return

    if firebase_admin is None:
        print('[Firebase] firebase_admin package not installed. Skipping init.')
        return

    if _fs_client is not None:
        return

    try:
        # If already initialized elsewhere
        try:
            firebase_admin.get_app()
        except ValueError:
            cred_path = app.config.get('FIREBASE_CREDENTIALS_PATH')
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Try application default credentials (e.g., ADC or emulator)
                firebase_admin.initialize_app()
        _fs_client = firestore.client()
        print('[Firebase] Firestore initialized successfully.')
    except Exception as e:  # pragma: no cover
        _fs_client = None
        # Disable to avoid runtime errors elsewhere
        app.config['FIREBASE_ENABLED'] = False
        print(f'[Firebase] Initialization failed: {e}. Disabled FIREBASE_ENABLED.')


def get_db():
    """Return Firestore client if initialized, else None."""
    return _fs_client
