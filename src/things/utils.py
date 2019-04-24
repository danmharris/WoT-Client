"""This module contains utility functions/classes to be used in thing views"""
import json
from requests import exceptions
from django.shortcuts import render

class RequestExceptionMiddleware:
    """Middleware to catch errors thrown by requests API"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Returns different status codes depending on what the API returns"""
        if isinstance(exception, exceptions.ConnectionError):
            return render(request, 'exceptions/exception.html', context={
                'message': 'Cannot connect to the thing directory. Please ensure it is started and online',
                'status': 503,
            }, status=503)
        elif isinstance(exception, exceptions.HTTPError):
            return render(request, 'exceptions/exception.html', context={
                'message': exception.response.json()['message'],
                'status': exception.response.status_code,
            }, status=exception.response.status_code)
        else:
            return None
