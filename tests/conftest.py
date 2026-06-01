"""Shared test environment defaults."""

import os


os.environ.setdefault("DATABASE_URL", "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-auth")
