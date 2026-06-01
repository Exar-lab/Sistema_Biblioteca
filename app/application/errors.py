"""Domain / application error types.

Plain Python exceptions — no FastAPI, no HTTP status codes, no infrastructure imports.
Exception handlers in the API layer translate these into HTTP responses.
"""


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message)


class OutOfStockError(Exception):
    """Raised when a book has no available stock for a new loan."""

    def __init__(self, message: str = "Book has no available stock for loan.") -> None:
        super().__init__(message)


class ConflictError(Exception):
    """Raised when an operation would create a duplicate or conflicting record."""

    def __init__(self, message: str = "A conflicting record already exists.") -> None:
        super().__init__(message)


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid username or password.") -> None:
        super().__init__(message)


class InactiveUserError(Exception):
    """Raised when an inactive user attempts an action."""

    def __init__(self, message: str = "User account is inactive.") -> None:
        super().__init__(message)
