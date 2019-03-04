from django.shortcuts import render
from django.http import HttpResponse, Http404
import requests
import json

#TODO: Add handler for if thing directory is offline

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    response = requests.get('http://localhost:5002/things')
    response.raise_for_status()
    context = {
        'things': response.json(),
    }
    return render(request, 'wotclient/thing/list.html', context)

def get_thing_or_404(thing_id):
    response = requests.get('http://localhost:5002/things/{}'.format(thing_id))
    response.raise_for_status()
    return response.json()

# Based off answer from https://stackoverflow.com/questions/32044/how-can-i-render-a-tree-structure-recursive-using-a-django-template
def _pretty_print_object(value, key=None):
    output = list()
    if type(value) is dict:
        output.append('&in')
        for k, v in value.items():
            output = output + _pretty_print_object(v, k)
        output.append('&out')
    elif key is not None:
        output.append('{}: {}'.format(key, value))
    else:
        output.append(value)
    return output

def thing_single_properties(request, thing_id):
    thing = get_thing_or_404(thing_id)
    properties = thing.get('properties', dict())

    err = None
    if request.method == 'POST':
        filtered = {k: v for k, v in properties.items() if k == request.POST['property'] or request.POST['property'] == 'all'}
        for k, v in filtered.items():
            try:
                value_response = requests.get(v['forms'][0]['href'])
            except:
                v['value'] = '???'
                err = 'One or more properties could not be read'
            else:
                #TODO: Parse schema to get result
                try:
                    json_response = json.loads(value_response.text)
                    v['value'] = _pretty_print_object(json_response)
                except:
                    v['value'] = _pretty_print_object(value_response.text)
            properties[k] = v
    context = {
        'tab': 'properties',
        'uuid': thing_id,
        'thing': thing,
        'properties': properties,
        'err': err,
    }
    return render(request, 'wotclient/thing/properties.html', context)

def _schema_to_list(schema, prefix=''):
    output = list()
    if schema['type'] == 'string':
        output.append({
            'name': prefix + '.value',
            'type': 'text',
            'label': prefix[1:],
        })
    elif schema['type'] == 'number':
        output.append({
            'name': prefix + '.value',
            'type': 'number',
            'label': prefix[1:],
        })
    elif schema['type'] == 'object':
        # If this is an object, generate the names for each property and append
        for k, v in schema['properties'].items():
            output = output + _schema_to_list(v, prefix+'.'+k)
    return output

def _list_to_data(data):
    # If not a form (i.e. no input) just return
    if 'value' in data:
        return ''

    # Remove unneeded fields from POST request
    data = {k: v for k, v in data.items() if k != 'action_id' and k != 'csrfmiddlewaretoken'}
    output = dict()
    for k, v in data.items():
        keys = k.split('.')[1:-1] # Work out the path in the JSON tree to this leaf
        final_key = keys.pop() # Find the value of the leaf key

        # Go through each of the nodes and check they exist in the output structure
        current = output
        for key in keys:
            current.setdefault(key, dict()) # If a node is not in the tree, add it
            current = current['key']
        current[final_key] = v # Insert the value at the final leaf node
    return json.dumps(output)

def thing_single_actions(request, thing_id):
    thing = get_thing_or_404(thing_id)
    actions = thing.get('actions', dict())

    err = None
    success = None
    if request.method == 'POST':
        filtered = {k: v for k, v in actions.items() if k == request.POST['action_id']}
        for k, v in filtered.items():
            try:
                content_type = v['forms'][0].get('contentType', 'application/x-www-form-urlencoded')
                headers = {
                    'content-type': content_type
                }
                response = requests.post(v['forms'][0]['href'], headers=headers, data=_list_to_data(request.POST).encode())
                response.raise_for_status()
            except Exception as e:
                err = 'An error occured performing action: ' + str(e)
            else:
                success = 'Action performed successfully'

    for k, v in actions.items():
        if 'input' in v:
            v['input_form'] = _schema_to_list(v['input'])

    context = {
        'tab': 'actions',
        'uuid': thing_id,
        'thing': thing,
        'actions': actions,
        'err': err,
        'success': success,
    }
    return render(request, 'wotclient/thing/actions.html', context)

def thing_single_events(request, thing_id):
    thing = get_thing_or_404(thing_id)
    events = thing.get('events', dict())
    context = {
        'tab': 'events',
        'uuid': thing_id,
        'thing': thing,
        'events': events,
    }
    return render(request, 'wotclient/thing/events.html', context)

def thing_single_schema(request, thing_id):
    thing = get_thing_or_404(thing_id)

    context = {
        'tab': 'schema',
        'uuid': thing_id,
        'thing': thing,
        'thing_pretty': json.dumps(thing, indent=4),
    }
    return render(request, 'wotclient/thing/schema.html', context)
