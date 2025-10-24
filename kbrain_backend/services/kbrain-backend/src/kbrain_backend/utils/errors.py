"""Error handling utilities."""

from typing import Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class APIError(Exception):
    """Base API error."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[list] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError(APIError):
    """Validation error."""

    def __init__(
        self, message: str = "Validation failed", details: Optional[list] = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DuplicateResourceError(APIError):
    """Duplicate resource error."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            code="DUPLICATE_RESOURCE",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class StorageError(APIError):
    """Storage backend error."""

    def __init__(self, message: str = "Storage error occurred"):
        super().__init__(
            code="STORAGE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }

    if exc.details:
        error_response["error"]["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip 'body'
        details.append(
            {
                "field": field,
                "message": error["msg"],
            }
        )

    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": details,
        }
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    # Log the error
    print(f"Unhandled exception: {exc}")

    error_response = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
        }
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle database errors."""
    print(f"Database error: {exc}")

    error_response = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "A database error occurred",
        }
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )
