from django.shortcuts import render
from django.http import HttpResponse, Http404
import requests
import json

#TODO: Add handler for if thing directory is offline

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    response = requests.get('http://localhost:5002/things')
    context = {
        'things': response.json(),
    }
    return render(request, 'wotclient/thing/list.html', context)

def get_thing_or_404(thing_id):
    response = requests.get('http://localhost:5002/things/{}'.format(thing_id))
    if response.status_code == 404:
        raise Http404(response.text)
    else:
        return response.json()

def thing_single_properties(request, thing_id):
    thing = get_thing_or_404(thing_id)
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
        'tab': 'properties',
        'uuid': thing_id,
        'thing': thing,
        'properties': properties_response,
    }
    return render(request, 'wotclient/thing/properties.html', context)

def thing_single_actions(request, thing_id):
    thing = get_thing_or_404(thing_id)
    actions_response = requests.get('http://localhost:5002/things/{}/actions'.format(thing_id)).json()
    context = {
        'tab': 'actions',
        'uuid': thing_id,
        'thing': thing,
        'actions': actions_response,
    }
    return render(request, 'wotclient/thing/actions.html', context)

def thing_single_events(request, thing_id):
    thing = get_thing_or_404(thing_id)
    events_response = requests.get('http://localhost:5002/things/{}/events'.format(thing_id)).json()
    context = {
        'tab': 'events',
        'uuid': thing_id,
        'thing': thing,
        'events': events_response,
    }
    return render(request, 'wotclient/thing/events.html', context)

def thing_single_schema(request, thing_id):
    thing = get_thing_or_404(thing_id)

    # TODO: Add /all interactions to thing directory to reduce request count
    properties = requests.get('http://localhost:5002/things/{}/properties'.format(thing_id)).json()
    actions = requests.get('http://localhost:5002/things/{}/actions'.format(thing_id)).json()
    events = requests.get('http://localhost:5002/things/{}/events'.format(thing_id)).json()

    context = {
        'tab': 'schema',
        'uuid': thing_id,
        'thing': thing,
        'thing_pretty': json.dumps(thing, indent=4),
        'properties_pretty': json.dumps(properties, indent=4),
        'actions_pretty': json.dumps(actions, indent=4),
        'events_pretty': json.dumps(events, indent=4),
    }
    return render(request, 'wotclient/thing/schema.html', context)
