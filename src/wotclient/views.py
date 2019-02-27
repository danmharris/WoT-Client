from django.shortcuts import render
from django.http import HttpResponse, Http404
import requests

# Create your views here.

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    #TODO: Make request to thing directory and parse results to get name and ID

    response = requests.get('http://localhost:5002/things')
    context = {
        'things': response.json(),
    }
    return render(request, 'wotclient/thing/list.html', context)

def thing_single(request, thing_id):
    response = requests.get('http://localhost:5002/things/{}'.format(thing_id))
    if response.status_code == 404:
        raise Http404(response.text)
    else:
        properties_response = requests.get('http://localhost:5002/things/{}/properties'.format(thing_id)).json()
        if request.method == 'POST':
            filtered = {k: v for k, v in properties_response.items() if k == request.POST['property'] or request.POST['property'] == 'all'}
            for k, v in filtered.items():
                try:
                    value_response = requests.get(v['forms'][0]['href'])
                except:
                    v['value'] = '???'
                else:
                    #TODO: Parse schema to get result
                    v['value'] = value_response.text
                properties_response[k] = v
        context = {
            'thing': response.json(),
            'properties': properties_response,
        }
        return render(request, 'wotclient/thing/properties.html', context)
