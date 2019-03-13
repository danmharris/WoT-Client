from django.conf import settings
from wotclient.models import ThingAuthorization, AuthorizationMethod
import requests
import json
from aiocoap import Context, Message
from aiocoap.numbers.codes import GET
import asyncio

def get_thing_or_404(thing_id):
    response = requests.get('{}/things/{}'.format(settings.THING_DIRECTORY_HOST, thing_id), headers={
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

class Thing(object):
    def __init__(self, thing_id, schema=None):
        self.thing_id = thing_id
        if schema is None:
            self.schema = get_thing_or_404(thing_id)
    def perform_action(self, action_id, data):
        action_schema = self.schema.get('actions', dict())
        action = action_schema[action_id]

        action['forms'] = [ f for f in action['forms'] if 'href' in f ]
        for form in action['forms']:
            content_type = form.get('contentType', 'application/x-www-form-urlencoded')
            headers = {
                'content-type': content_type
            }

            # Add Authorization header if one has been set for this thing
            try:
                auth_method = ThingAuthorization.objects.get(thing_uuid=self.thing_id).authorization_method
            except:
                pass
            else:
                headers['Authorization'] = '{} {}'.format(auth_method.auth_type, auth_method.auth_credentials)

            try:
                response = requests.post(form['href'], headers=headers, data=data.encode())
                response.raise_for_status()
            except:
                continue

        # We should only get here if every form raises an exception
        raise Exception('Action could not be performed through any forms')

    def read_property(self, property_id):
        property_schema = self.schema.get('properties', dict())
        prop = property_schema[property_id]

        prop['forms'] = [ f for f in prop['forms'] if 'href' in f ]
        for form in prop['forms']:
            # Set headers if they are required (i.e. for auth)
            try:
                auth_method = ThingAuthorization.objects.get(thing_uuid=self.thing_id).authorization_method
            except:
                headers=None
            else:
                headers={
                    'Authorization': '{} {}'.format(auth_method.auth_type, auth_method.auth_credentials),
                }

            # Attempt the request for a form. If it fails try next form
            try:
                value_response = requests.get(form['href'], headers=headers)
                value_response.raise_for_status()
            except:
                continue

            # See if the data returned is json
            try:
                json_response = json.loads(value_response.text)
            except:
                return _pretty_print_object(value_response.text)
            else:
                return _pretty_print_object(json_response)

        # We should only get here if every form raises an exception
        raise Exception('Property could not be read through any forms')

    async def observe_event(self, event_id, callback):
        event_schema = self.schema.get('events', dict())
        event = event_schema[event_id]

        event['forms'] = [ f for f in event['forms'] if 'href' in f]
        for form in event['forms']:
            c = await Context.create_client_context()
            message = Message(code=GET, uri=form['href'])
            message.opt.observe = 0
            request = c.request(message, handle_blockwise=False)
            request.observation.register_callback(callback)
            await request.response

        # We should only get here if every form raises an exception
        raise Exception('Event could not be subscribed to through any forms')
