from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings
from wotclient.models import CustomAction, AuthorizationMethod, ThingAuthorization
from wotclient.thing import Thing
from wotclient.forms import ThingActionForm, ThingSaveActionForm, ThingSettingsForm, ThingEventForm, ThingPropertyForm, ThingObservePropertyForm
import requests
import json
import asyncio, threading

def _subscribe(func, id, callback):
    # Run subscription in new thread to prevent locking up HTTP request
    def subscription():
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.create_task(func(id, callback))
        asyncio.get_event_loop().run_forever()
    threading.Thread(target=subscription).start()

def index(request):
    return render(request, 'wotclient/index.html')

def thing_list(request):
    response = requests.get('{}/things'.format(settings.THING_DIRECTORY_HOST), headers={
            'Authorization': settings.THING_DIRECTORY_KEY,
    })
    response.raise_for_status()
    context = {
        'things': response.json(),
    }
    return render(request, 'wotclient/thing/list.html', context)

def thing_single_properties(request, thing_id):
    thing = Thing(thing_id)
    properties = thing.schema.get('properties', dict())

    err = None
    success = None
    if request.method == 'POST':
        if 'observe' in request.POST:
            form = ThingObservePropertyForm(request.POST)
        else:
            form = ThingPropertyForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['observe'] == True:
                custom_action = CustomAction.objects.get(name=form.cleaned_data['custom_action_name'], thing_uuid=form.cleaned_data['thing_uuid'])
                callback_thing = Thing(form.cleaned_data['thing_uuid'])

                def callback(response):
                    if form.cleaned_data['condition'] == response.payload.decode():
                        try:
                            callback_thing.perform_action(custom_action.action_id, custom_action.data)
                        except:
                            pass
                _subscribe(thing.observe_property, form.cleaned_data['property_id'], callback)
                success = 'Property subscribed to'
            else:
                filtered = {k: v for k, v in properties.items() if k == form.cleaned_data['property_id'] or form.cleaned_data['property_id'] == 'all'}
                for k, v in filtered.items():
                    try:
                        v['value'] = thing.read_property(k)
                    except:
                        v['value'] = ['???']
                        err = 'One or more properties could not be read'
                    properties[k] = v
        else:
            err = 'Invalid data supplied'

    context = {
        'tab': 'properties',
        'uuid': thing_id,
        'thing': thing.schema,
        'properties': properties,
        'err': err,
        'success': success,
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
    thing = Thing(thing_id)
    actions = thing.schema.get('actions', dict())

    err = None
    success = None
    if request.method == 'POST':
        if 'save' in request.POST:
            form = ThingSaveActionForm(request.POST)
        else:
            form = ThingActionForm(request.POST)
        if form.is_valid():
            # Checks if performing custom action, and retrieves payload and action name
            if form.cleaned_data['custom_action_id'] is not None:
                custom_action = CustomAction.objects.get(id=form.cleaned_data['custom_action_id'])
                payload = custom_action.data
                action_id = custom_action.action_id
            else:
                # If not a custom action, retrieve ID and payload from POST data
                action_id = form.cleaned_data['action_id']
                payload = _list_to_data(request.POST)

            # Make the request with the data (custom or not)
            try:
                thing.perform_action(action_id, payload)
                pass
            except Exception as e:
                err = 'An error occured performing action: ' + str(e)
            else:
                success = 'Action performed successfully'
                # If save box checked (only shows on non-custom actions), save the data into the model
                if form.cleaned_data['save'] == True:
                    custom_action = CustomAction(name=form.cleaned_data['name'], description=form.cleaned_data['description'],
                        action_id=form.cleaned_data['action_id'], thing_uuid=thing_id, data=payload)
                    custom_action.save()
        else:
            err = 'Invalid data supplied'

    for k, v in actions.items():
        if 'input' in v:
            v['input_form'] = _schema_to_list(v['input'])

    custom_actions = CustomAction.objects.filter(thing_uuid=thing_id)

    context = {
        'tab': 'actions',
        'uuid': thing_id,
        'thing': thing.schema,
        'actions': actions,
        'custom_actions': custom_actions,
        'err': err,
        'success': success,
    }
    return render(request, 'wotclient/thing/actions.html', context)

def thing_single_events(request, thing_id):
    thing = Thing(thing_id)
    events = thing.schema.get('events', dict())

    err = None
    success = None
    if request.method == 'POST':
        form = ThingEventForm(request.POST)
        if form.is_valid():
            custom_action = CustomAction.objects.get(name=form.cleaned_data['custom_action_name'], thing_uuid=form.cleaned_data['thing_uuid'])
            callback_thing = Thing(form.cleaned_data['thing_uuid'])
            def callback(response):
                try:
                    callback_thing.perform_action(custom_action.action_id, custom_action.data)
                except:
                    pass

            _subscribe(thing.observe_event, form.cleaned_data['event_id'], callback)
            success = 'Event subscribed to'
        else:
            err = 'Invalid data supplied'

    context = {
        'tab': 'events',
        'uuid': thing_id,
        'thing': thing.schema,
        'events': events,
        'err': err,
        'success': success,
    }
    return render(request, 'wotclient/thing/events.html', context)

def thing_single_settings(request, thing_id):
    thing = Thing(thing_id)

    err = None
    success = None
    methods = AuthorizationMethod.objects.all()
    try:
        thing_method = ThingAuthorization.objects.get(thing_uuid=thing_id)
    except (ThingAuthorization.DoesNotExist, ThingAuthorization.MultipleObjectsReturned):
        thing_method = None

    if request.method == 'POST':
        form = ThingSettingsForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['auth_method_delete'] == True:
                if thing_method is not None:
                    thing_method.delete()
                    thing_method = None
                success = 'Cleared'
            else:
                if thing_method is None:
                    thing_method = ThingAuthorization(thing_uuid=thing_id)
                try:
                    thing_method.authorization_method = AuthorizationMethod.objects.get(id=form.cleaned_data['auth_method'])
                except AuthorizationMethod.DoesNotExist:
                    err = 'Unknown authorisation method'
                else:
                    thing_method.save()
                    success = 'Updated'
        else:
            err = 'Invalid data supplied'

    context = {
        'tab': 'settings',
        'uuid': thing_id,
        'thing': thing.schema,
        'methods': methods,
        'thing_method': thing_method,
        'success': success,
        'err': err,
    }
    return render(request, 'wotclient/thing/settings.html', context)

def thing_single_schema(request, thing_id):
    thing = Thing(thing_id)

    context = {
        'tab': 'schema',
        'uuid': thing_id,
        'thing': thing.schema,
        'thing_pretty': json.dumps(thing.schema, indent=4),
    }
    return render(request, 'wotclient/thing/schema.html', context)
