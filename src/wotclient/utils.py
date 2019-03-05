from requests import exceptions
from django.shortcuts import render
import json

class RequestExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, exceptions.ConnectionError):
            return render(request, 'wotclient/exceptions/exception.html', context={
                'message': 'Cannot connect to the thing directory. Please ensure it is started and online',
                'status': 503,
            }, status=503)
        elif isinstance(exception, exceptions.HTTPError):
            return render(request, 'wotclient/exceptions/exception.html', context={
                'message': exception.response.json()['message'],
                'status': exception.response.status_code,
            }, status=exception.response.status_code)
        else:
            return None
