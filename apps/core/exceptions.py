from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Add custom error structure
    if response is not None:
        response.data = {
            'status_code': response.status_code,
            'errors': response.data,
            'message': 'Something went wrong'
        }

    else:
        # If response is None, return a generic server error
        return Response({
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'errors': 'Internal server error',
            'message': str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
