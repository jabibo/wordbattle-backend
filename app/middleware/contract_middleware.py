"""
Contract Validation Middleware for WordBattle API

This middleware optionally validates API responses against the frontend contracts
to ensure API compliance in real-time.
"""

import json
import logging
from typing import Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime, timezone

from app.config import ENABLE_CONTRACT_VALIDATION, CONTRACT_VALIDATION_STRICT

logger = logging.getLogger(__name__)

class ContractValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API responses against contracts."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.validator = None
        self._load_validator()
    
    def _load_validator(self):
        """Load the contract validator."""
        if not ENABLE_CONTRACT_VALIDATION:
            return
        
        try:
            from app.utils.contract_validator import validator
            self.validator = validator
            if validator.loaded:
                logger.info("📋 Contract validation middleware enabled")
            else:
                logger.warning("📋 Contract validation middleware disabled - no schemas loaded")
        except ImportError as e:
            logger.warning(f"📋 Contract validation middleware disabled - import error: {e}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate response if needed."""
        
        # Call the actual endpoint
        response = await call_next(request)
        
        # Only validate JSON responses for specific endpoints
        if (self.validator and 
            self.validator.loaded and 
            response.headers.get("content-type", "").startswith("application/json") and
            self._should_validate_endpoint(request.url.path)):
            
            try:
                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Parse JSON
                response_data = json.loads(response_body.decode())
                
                # Validate against contract
                endpoint_path = self._normalize_endpoint_path(request.url.path)
                is_valid = self.validator.validate_response(
                    endpoint_path, 
                    response_data, 
                    response.status_code
                )
                
                if not is_valid and CONTRACT_VALIDATION_STRICT:
                    logger.error(f"📋 STRICT MODE: Contract validation failed for {endpoint_path}")
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": "API contract validation failed",
                            "error_code": "CONTRACT_VALIDATION_FAILED",
                            "endpoint": endpoint_path,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "request_id": request.headers.get("X-Request-ID", "")
                        }
                    )
                
                # Add contract validation header for debugging
                response.headers["X-Contract-Validated"] = "true" if is_valid else "false"
                
                # Recreate response with same body
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
                
            except Exception as e:
                logger.warning(f"📋 Contract validation error for {request.url.path}: {e}")
                if CONTRACT_VALIDATION_STRICT:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": "Contract validation system error",
                            "error_code": "CONTRACT_VALIDATION_ERROR",
                            "details": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "request_id": request.headers.get("X-Request-ID", "")
                        }
                    )
        
        return response
    
    def _should_validate_endpoint(self, path: str) -> bool:
        """Determine if an endpoint should be validated."""
        # Skip validation for certain endpoints
        skip_paths = [
            "/docs",
            "/openapi.json",
            "/admin/debug",
            "/health",  # Keep health simple
            "/metrics"
        ]
        
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return False
        
        # Validate API endpoints
        validate_paths = [
            "/auth/",
            "/games/",
            "/users/",
            "/admin/contracts/"  # Validate our contract endpoints
        ]
        
        for validate_path in validate_paths:
            if path.startswith(validate_path):
                return True
        
        return False
    
    def _normalize_endpoint_path(self, path: str) -> str:
        """Normalize endpoint path for schema lookup."""
        # Remove query parameters
        path = path.split('?')[0]
        
        # Remove trailing slash
        if path.endswith('/'):
            path = path[:-1]
            
        return path 