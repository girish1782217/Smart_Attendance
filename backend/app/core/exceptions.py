class AppError(Exception):
    """Base class for domain errors that map to a stable HTTP error envelope.

    Never let a raw exception reach the client — raise (a subclass of) this
    instead, so `main.py`'s exception handler can produce
    `{"success": false, "error": {"code": ..., "message": ...}}` without
    leaking internals.
    """

    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationAppError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
