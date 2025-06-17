"""
Contract Validation Utility for WordBattle API

This module provides functionality to validate API requests and responses
against the frontend-backend contract schemas.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
from fastapi import Request, Response
import functools

from app.config import CONTRACTS_DIR, ENABLE_CONTRACT_VALIDATION, CONTRACT_VALIDATION_STRICT

logger = logging.getLogger(__name__)

class ContractValidator:
    """Validates API requests and responses against frontend contracts."""
    
    def __init__(self):
        self.schemas = {}
        self.loaded = False
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all contract schemas from the contracts directory."""
        if not ENABLE_CONTRACT_VALIDATION:
            logger.info("📋 Contract validation disabled")
            return
        
        if not os.path.exists(CONTRACTS_DIR):
            logger.warning(f"📋 Contracts directory not found: {CONTRACTS_DIR}")
            return
        
        try:
            # Load all schema files
            schema_files = [
                "all_schemas.json",
                "auth_schemas.json", 
                "game_schemas.json",
                "error_schemas.json",
                "config_schemas.json"
            ]
            
            for filename in schema_files:
                filepath = os.path.join(CONTRACTS_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        schema_name = filename.replace('_schemas.json', '').replace('.json', '')
                        self.schemas[schema_name] = data
                        logger.info(f"📋 Loaded schema: {filename}")
            
            self.loaded = True
            logger.info(f"📋 Contract validation enabled with {len(self.schemas)} schema files")
            
        except Exception as e:
            logger.error(f"📋 Failed to load contract schemas: {e}")
            if CONTRACT_VALIDATION_STRICT:
                raise
    
    def validate_response(self, endpoint: str, response_data: Dict[str, Any], status_code: int = 200) -> bool:
        """
        Validate a response against the contract schema.
        
        Args:
            endpoint: API endpoint path (e.g., '/auth/register')
            response_data: Response data to validate
            status_code: HTTP status code
            
        Returns:
            True if validation passes, False otherwise
        """
        if not self.loaded or not ENABLE_CONTRACT_VALIDATION:
            return True
        
        try:
            schema = self._get_response_schema(endpoint, status_code)
            if not schema:
                logger.debug(f"📋 No schema found for {endpoint} ({status_code})")
                return not CONTRACT_VALIDATION_STRICT
            
            validate(response_data, schema)
            logger.debug(f"📋 ✅ Response validation passed: {endpoint}")
            return True
            
        except ValidationError as e:
            logger.error(f"📋 ❌ Response validation failed for {endpoint}: {e.message}")
            if CONTRACT_VALIDATION_STRICT:
                raise
            return False
        except Exception as e:
            logger.error(f"📋 ❌ Validation error for {endpoint}: {e}")
            if CONTRACT_VALIDATION_STRICT:
                raise
            return False
    
    def validate_request(self, endpoint: str, request_data: Dict[str, Any]) -> bool:
        """
        Validate a request against the contract schema.
        
        Args:
            endpoint: API endpoint path
            request_data: Request data to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        if not self.loaded or not ENABLE_CONTRACT_VALIDATION:
            return True
        
        try:
            schema = self._get_request_schema(endpoint)
            if not schema:
                logger.debug(f"📋 No request schema found for {endpoint}")
                return not CONTRACT_VALIDATION_STRICT
            
            validate(request_data, schema)
            logger.debug(f"📋 ✅ Request validation passed: {endpoint}")
            return True
            
        except ValidationError as e:
            logger.error(f"📋 ❌ Request validation failed for {endpoint}: {e.message}")
            if CONTRACT_VALIDATION_STRICT:
                raise
            return False
        except Exception as e:
            logger.error(f"📋 ❌ Request validation error for {endpoint}: {e}")
            if CONTRACT_VALIDATION_STRICT:
                raise
            return False
    
    def _get_response_schema(self, endpoint: str, status_code: int) -> Optional[Dict[str, Any]]:
        """Get the response schema for an endpoint and status code."""
        # Map endpoints to schema locations
        endpoint_mapping = {
            '/auth/register': ('auth', 'authResponse'),
            '/auth/verify': ('auth', 'authResponse'),
            '/auth/verify-code': ('auth', 'authResponse'),
            '/auth/login': ('auth', 'authResponse'),
            '/auth/email-login': ('auth', 'authResponse'),
            '/auth/refresh': ('auth', 'authResponse'),
            '/auth/logout': ('auth', 'authResponse'),
            '/games/my': ('games', 'listResponse'),
            '/games/available': ('games', 'listResponse'),
            '/games/create': ('games', 'stateResponse'),
            '/health': ('config', 'healthResponse'),
            '/config': ('config', 'configResponse')
        }
        
        # Handle dynamic endpoints
        if '/games/' in endpoint and endpoint.endswith('/join'):
            schema_path = ('games', 'stateResponse')
        elif '/games/' in endpoint and endpoint.endswith('/move'):
            schema_path = ('games', 'moveResponse')
        elif '/games/' in endpoint and endpoint.endswith('/pass'):
            schema_path = ('games', 'moveResponse')
        elif '/games/' in endpoint and endpoint.endswith('/exchange'):
            schema_path = ('games', 'moveResponse')
        elif endpoint.startswith('/games/') and not any(x in endpoint for x in ['/join', '/move', '/pass', '/exchange']):
            schema_path = ('games', 'stateResponse')
        else:
            schema_path = endpoint_mapping.get(endpoint)
        
        if not schema_path:
            return None
        
        schema_file, schema_key = schema_path
        
        # Handle error responses
        if status_code >= 400:
            return self._get_error_schema(status_code)
        
        # Get schema from loaded schemas
        if schema_file in self.schemas:
            schemas = self.schemas[schema_file].get('schemas', {})
            if schema_file == 'all':
                # For all_schemas.json, look in nested structure
                return schemas.get(schema_key.split('.')[0], {}).get(schema_key.split('.')[1] if '.' in schema_key else 'response')
            else:
                return schemas.get(schema_key)
        
        return None
    
    def _get_request_schema(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get the request schema for an endpoint."""
        endpoint_mapping = {
            '/auth/register': ('auth', 'authRequest'),
            '/auth/verify': ('auth', 'authRequest'),
            '/auth/verify-code': ('auth', 'authRequest'),
            '/auth/login': ('auth', 'authRequest'),
            '/auth/email-login': ('auth', 'authRequest'),
            '/games/create': ('games', 'createRequest'),
            '/games/join': ('games', 'joinRequest'),
            '/games/move': ('games', 'moveRequest'),
            '/games/exchange': ('games', 'exchangeRequest')
        }
        
        # Handle dynamic endpoints
        if '/games/' in endpoint and endpoint.endswith('/join'):
            schema_path = ('games', 'joinRequest')
        elif '/games/' in endpoint and endpoint.endswith('/move'):
            schema_path = ('games', 'moveRequest')
        elif '/games/' in endpoint and endpoint.endswith('/exchange'):
            schema_path = ('games', 'exchangeRequest')
        else:
            schema_path = endpoint_mapping.get(endpoint)
        
        if not schema_path:
            return None
        
        schema_file, schema_key = schema_path
        
        if schema_file in self.schemas:
            schemas = self.schemas[schema_file].get('schemas', {})
            return schemas.get(schema_key)
        
        return None
    
    def _get_error_schema(self, status_code: int) -> Optional[Dict[str, Any]]:
        """Get the error response schema for a status code."""
        if 'error' in self.schemas:
            error_schemas = self.schemas['error'].get('schemas', {})
            
            if status_code == 400:
                return error_schemas.get('validationError')
            elif status_code == 401:
                return error_schemas.get('authError')
            elif status_code == 403:
                return error_schemas.get('forbiddenError')
            elif status_code == 404:
                return error_schemas.get('notFoundError')
            elif status_code >= 500:
                return error_schemas.get('serverError')
            else:
                return error_schemas.get('standardError')
        
        return None
    
    def get_contract_info(self) -> Dict[str, Any]:
        """Get information about loaded contracts."""
        return {
            "enabled": ENABLE_CONTRACT_VALIDATION,
            "strict_mode": CONTRACT_VALIDATION_STRICT,
            "contracts_dir": CONTRACTS_DIR,
            "loaded": self.loaded,
            "schema_files": list(self.schemas.keys()) if self.loaded else [],
            "total_schemas": sum(len(v.get('schemas', {})) for v in self.schemas.values()) if self.loaded else 0
        }


# Global validator instance
validator = ContractValidator()


def validate_contract_response(endpoint: str):
    """
    Decorator to validate response against contract schema.
    
    Usage:
        @validate_contract_response('/auth/register')
        def register_user(...):
            return response_data
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if ENABLE_CONTRACT_VALIDATION:
                # Extract response data - handle different return types
                response_data = result
                if hasattr(result, 'body'):
                    response_data = json.loads(result.body)
                elif hasattr(result, 'model_dump'):
                    response_data = result.model_dump()
                elif isinstance(result, dict):
                    response_data = result
                
                validator.validate_response(endpoint, response_data)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if ENABLE_CONTRACT_VALIDATION:
                response_data = result
                if hasattr(result, 'body'):
                    response_data = json.loads(result.body)
                elif hasattr(result, 'model_dump'):
                    response_data = result.model_dump()
                elif isinstance(result, dict):
                    response_data = result
                
                validator.validate_response(endpoint, response_data)
            
            return result
        
        # Return appropriate wrapper based on whether function is async
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def check_contracts_compliance() -> Dict[str, Any]:
    """
    Check if the current API implementation complies with the contracts.
    
    Returns:
        Dictionary with compliance information
    """
    if not validator.loaded:
        return {
            "compliant": False,
            "reason": "Contract schemas not loaded",
            "missing_schemas": True
        }
    
    compliance_report = {
        "compliant": True,
        "contract_info": validator.get_contract_info(),
        "issues": [],
        "recommendations": []
    }
    
    # Check for required response fields
    required_fields = {
        "auth_response": ["success"],
        "game_response": ["id", "status", "players"],
        "error_response": ["success", "error"]
    }
    
    # Add more detailed compliance checks here as needed
    
    return compliance_report


# Export main validator instance
__all__ = ['validator', 'validate_contract_response', 'check_contracts_compliance', 'ContractValidator'] 