from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings
from wotclient.models import CustomAction, AuthorizationMethod, ThingAuthorization
import requests
import json

#TODO: Add handler for if thing directory is offline

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    response = requests.get('http://localhost:5002/things', headers={
            'Authorization': settings.THING_DIRECTORY_KEY,
    })
    response.raise_for_status()
    context = {
        'things': response.json(),
    }
    return render(request, 'wotclient/thing/list.html', context)

def get_thing_or_404(thing_id):
    response = requests.get('http://localhost:5002/things/{}'.format(thing_id), headers={
            'Authorization': settings.THING_DIRECTORY_KEY,
    })
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
    data = {k: v for k, v in data.items() if k[0] == '.'}
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
        # Checks if performing custom action, and retrieves payload and action name
        if 'custom_action_id' in request.POST:
            custom_action = CustomAction.objects.get(id=request.POST['custom_action_id'])
            payload = custom_action.data
            action_id = custom_action.action_id
        else:
            # If not a custom action, retrieve ID and payload from POST data
            action_id = request.POST['action_id']
            payload = _list_to_data(request.POST)

        # Make the request with the data (custom or not)
        filtered = {k: v for k, v in actions.items() if k == action_id}
        for k, v in filtered.items():
            try:
                content_type = v['forms'][0].get('contentType', 'application/x-www-form-urlencoded')
                headers = {
                    'content-type': content_type
                }

                # Add Authorization header if one has been set for this thing
                try:
                    auth_method = ThingAuthorization.objects.get(thing_uuid=thing_id).authorization_method
                except:
                    pass
                else:
                    headers['Authorization'] = '{} {}'.format(auth_method.auth_type, auth_method.auth_credentials)

                response = requests.post(v['forms'][0]['href'], headers=headers, data=payload.encode())
                response.raise_for_status()
            except Exception as e:
                err = 'An error occured performing action: ' + str(e)
            else:
                success = 'Action performed successfully'

                # If save box checked (only shows on non-custom actions), save the data into the model
                if request.POST.get('save', '0') == '1':
                    custom_action = CustomAction(name=request.POST['name'], description=request.POST['description'],
                        action_id=request.POST['action_id'], thing_uuid=thing_id, data=payload)
                    custom_action.save()


    for k, v in actions.items():
        if 'input' in v:
            v['input_form'] = _schema_to_list(v['input'])

    custom_actions = CustomAction.objects.filter(thing_uuid=thing_id)

    context = {
        'tab': 'actions',
        'uuid': thing_id,
        'thing': thing,
        'actions': actions,
        'custom_actions': custom_actions,
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

def thing_single_settings(request, thing_id):
    thing = get_thing_or_404(thing_id)

    success = None
    methods = AuthorizationMethod.objects.all()
    try:
        thing_method = ThingAuthorization.objects.get(thing_uuid=thing_id)
    except (ThingAuthorization.DoesNotExist, ThingAuthorization.MultipleObjectsReturned):
        thing_method = None

    if request.method == 'POST':
        if 'delete' in request.POST and thing_method is not None:
            thing_method.delete()
            thing_method = None
        else:
            if thing_method is None:
                thing_method = ThingAuthorization(thing_uuid=thing_id)
            thing_method.authorization_method = AuthorizationMethod.objects.get(id=request.POST['auth_method'])
            thing_method.save()
            success = 'Updated'

    context = {
        'tab': 'settings',
        'uuid': thing_id,
        'thing': thing,
        'methods': methods,
        'thing_method': thing_method,
        'success': success,
    }
    return render(request, 'wotclient/thing/settings.html', context)

def thing_single_schema(request, thing_id):
    thing = get_thing_or_404(thing_id)

    context = {
        'tab': 'schema',
        'uuid': thing_id,
        'thing': thing,
        'thing_pretty': json.dumps(thing, indent=4),
    }
    return render(request, 'wotclient/thing/schema.html', context)
