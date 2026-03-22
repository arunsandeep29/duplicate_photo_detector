"""Flask application factory."""

import logging
import logging.config
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS

# Ensure werkzeug has __version__ attribute for compatibility with testing
import werkzeug
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "0"

from app.config import get_config, Config
from app.exceptions import DuplicatePhotosError
from app.api.routes import api_bp


def create_app(config: Optional[Config] = None) -> Flask:
    """Create and configure Flask application.

    Args:
        config: Optional configuration object. If not provided,
                uses environment-based configuration.

    Returns:
        Flask: Configured Flask application instance.
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)

    # Configure logging
    _configure_logging(app)
    logger = logging.getLogger(__name__)
    logger.info(f"Creating Flask app with {config.__class__.__name__}")

    # Set up CORS
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    logger.debug(f"CORS configured for origins: {config.CORS_ORIGINS}")

    # Register blueprints
    app.register_blueprint(api_bp)
    logger.debug("API blueprint registered")

    # Register error handlers
    _register_error_handlers(app)

    # Register request logging middleware
    _register_request_middleware(app)

    return app


def _configure_logging(app: Flask) -> None:
    """Configure application logging.

    Args:
        app: Flask application instance.
    """
    log_level = app.config.get("LOG_LEVEL", "INFO")

    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level))

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level))

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Add handler
    logger.addHandler(handler)


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application.

    Args:
        app: Flask application instance.
    """
    logger = logging.getLogger(__name__)

    @app.errorhandler(DuplicatePhotosError)
    def handle_custom_error(error: DuplicatePhotosError):
        """Handle custom application errors.

        Args:
            error: The custom error that occurred.

        Returns:
            tuple: JSON error response and HTTP status code.
        """
        logger.warning(f"Custom error: {error.code} - {error.message}")
        return jsonify(error.to_dict()), 400

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors.

        Args:
            error: The error that occurred.

        Returns:
            tuple: JSON error response and HTTP status code.
        """
        logger.warning(f"Bad request: {str(error)}")
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "code": "BAD_REQUEST",
                    "details": str(error),
                }
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors.

        Args:
            error: The error that occurred.

        Returns:
            tuple: JSON error response and HTTP status code.
        """
        logger.warning(f"Resource not found: {str(error)}")
        return (
            jsonify(
                {
                    "error": "Resource not found",
                    "code": "NOT_FOUND",
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors.

        Args:
            error: The error that occurred.

        Returns:
            tuple: JSON error response and HTTP status code.
        """
        logger.error(f"Internal server error: {str(error)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                }
            ),
            500,
        )


def _register_request_middleware(app: Flask) -> None:
    """Register request logging middleware.

    Args:
        app: Flask application instance.
    """
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request():
        """Log incoming request information."""
        from flask import request

        logger.debug(f"{request.method} {request.path} - IP: {request.remote_addr}")

    @app.after_request
    def log_response(response):
        """Log response information.

        Args:
            response: The Flask response object.

        Returns:
            The response object.
        """
        from flask import request

        logger.debug(f"{request.method} {request.path} - Status: {response.status_code}")
        return response
