"""Domain exceptions and their FastAPI handlers."""
import logging

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class ConflictError(AppError):
    status_code = 409
    code = "conflict"

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message)


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"

    def __init__(self, message: str = "Invalid input") -> None:
        super().__init__(message)


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message)


class ExternalServiceError(AppError):
    status_code = 502
    code = "external_service_error"

    def __init__(self, message: str = "Upstream service failed") -> None:
        super().__init__(message)


class ServiceUnavailableError(ExternalServiceError):
    status_code = 503
    code = "service_unavailable"

    def __init__(self, message: str = "Service temporarily unavailable") -> None:
        super().__init__(message)


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers=headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal server error"}},
    )


_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
}


def _envelope(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, **extra}}


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        f"{'.'.join(str(p) for p in err.get('loc', ()))}: {err.get('msg', 'invalid')}"
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_envelope("validation_error", "Invalid request", details=details),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    headers = dict(exc.headers) if exc.headers else None
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(code, str(exc.detail)),
        headers=headers,
    )


async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RateLimitExceeded)
    response = JSONResponse(
        status_code=429,
        content=_envelope("rate_limited", "Too many requests. Please slow down and try again."),
        headers={"Retry-After": "60"},
    )
    limiter = getattr(request.app.state, "limiter", None)
    limit = getattr(request.state, "view_rate_limit", None)
    if limiter is not None and limit is not None:
        try:  # adds Retry-After / X-RateLimit-* headers
            response = limiter._inject_headers(response, limit)  # may overwrite Retry-After
        except Exception:  # pragma: no cover - header injection is best effort
            logger.debug("Could not inject rate limit headers", exc_info=True)
    return response


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
