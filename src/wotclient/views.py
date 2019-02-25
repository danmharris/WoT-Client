from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    #TODO: Make request to thing directory and parse results to get name and ID
    things = [
        {
            'name': 'Thing 1',
            'uuid': '123',
        },
        {
            'name': 'Thing 2',
            'uuid': '456',
        }
    ]

    context = {
        'things': things,
    }
    return render(request, 'wotclient/thing/list.html', context)

def thing_single(request, thing_id):
    context = {
        'thing': {
            'name': 'Test Thing',
        }
    }
    return render(request, 'wotclient/thing/properties.html', context)
