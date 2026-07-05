"""
Utility functions for accounts app.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Custom exception handler that wraps errors in a consistent format."""
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'success': False,
            'status_code': response.status_code,
            'errors': response.data,
        }
        response.data = custom_response

    return response
