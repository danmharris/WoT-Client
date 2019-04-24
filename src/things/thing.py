"""This module contains code pertaining to an abstract (virtual) thing

Allows wrapping HTTP/CoAP requests in method calls
"""
import json
import asyncio
import requests
from django.conf import settings
from aiocoap import Context, Message
from aiocoap.numbers.codes import GET
from .models import ThingAuthorization, CustomAction

def new_things(url):
    """Attempts to register new things on the directory

    Takes 1 argument:
    url - URL containing thing descriptions to register
    """
    response = requests.post('{}/things/register_url'.format(settings.THING_DIRECTORY_HOST), headers={
            'Authorization': settings.THING_DIRECTORY_KEY,
    }, json={'url':url})
    response.raise_for_status()
    return response.json()['uuids']

def get_thing_or_404(thing_id):
    """Attempts to retrieve thing with given ID. Raises 404 error if non-existent

    Takes 1 argument:
    thing_id - ID of thing to look up
    """
    response = requests.get('{}/things/{}'.format(settings.THING_DIRECTORY_HOST, thing_id), headers={
            'Authorization': settings.THING_DIRECTORY_KEY,
    })
    response.raise_for_status()
    return response.json()

# Based off answer from https://stackoverflow.com/questions/32044/how-can-i-render-a-tree-structure-recursive-using-a-django-template
def _pretty_print_object(value, key=None):
    """Transforms JSON object into flat list that can be displayed as in an HTML UL tag

    Takes 2 arguments:
    value - JSON object to parse
    key - Key of the object currently being parsed
    """
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

class Thing:
    """Abstract representation of a thing. Allows its interactions to be performed"""
    def __init__(self, thing_id, schema=None):
        """Creates new instance of this class

        Takes 2 arguments:
        thing_id - The ID of this thing
        schema - The thing description. If not provided the ID will be looked up in the directory
        """
        self.thing_id = thing_id
        if schema is None:
            self.schema = get_thing_or_404(thing_id)

    def has_action(self, action_id):
        """Returns True if the thing has the reqeuested action"""
        return action_id in self.schema.get('actions', dict()).keys()

    def perform_action(self, action_id, data):
        """Performs an action on the thing

        Takes 2 arguments:
        action_id - ID of the action to be performed on the device
        data - Data to pass to the request when its made
        """
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
                return
            except:
                continue

        # We should only get here if every form raises an exception
        raise Exception('Action could not be performed through any forms')

    async def _coap_read_property(self, href):
        """Async wrapper method to read a CoAP property

        Takes 1 argument:
        href - URL to request
        """
        c = await Context.create_client_context()
        message = Message(code=GET, uri=href)
        request = c.request(message, handle_blockwise=False)
        response = await request.response
        return response.payload.decode()

    def read_property(self, property_id):
        """Reads a property from a thing

        Takes 1 argument:
        property_id - ID of the property to read on the device
        """
        property_schema = self.schema.get('properties', dict())
        prop = property_schema[property_id]

        prop['forms'] = [ f for f in prop['forms'] if 'href' in f ]
        for form in prop['forms']:
            if 'coap://' in form['href']:
                # Run CoAP request in event loop if URL is not HTTP
                try:
                    data = asyncio.new_event_loop().run_until_complete(self._coap_read_property(form['href']))
                except:
                    continue
            else:
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
                    data = value_response.text
                except:
                    continue

            # See if the data returned is json
            try:
                json_response = json.loads(data)
            except:
                return _pretty_print_object(data)
            else:
                return _pretty_print_object(json_response)

        # We should only get here if every form raises an exception
        raise Exception('Property could not be read through any forms')

    async def _observe(self, href, callback):
        """Perform CoAP observe request at a URL

        Takes 2 arguments:
        href - URL where observation is to be made
        callback - Function to run when the event is emitted
        """
        c = await Context.create_client_context()
        message = Message(code=GET, uri=href)
        message.opt.observe = 0
        request = c.request(message, handle_blockwise=False)
        request.observation.register_callback(callback)
        await request.response

    async def observe_property(self, property_id, callback):
        """Observes a property on a thing

        Takes 2 arguments:
        property_id - Name of property to observe
        callback - Function to run when property value changes
        """
        property_schema = self.schema.get('properties', dict())
        prop = property_schema[property_id]

        prop['forms'] = [ f for f in prop['forms'] if 'href' in f ]
        for form in prop['forms']:
            try:
                await self._observe(form['href'], callback)
            except:
                continue
            else:
                return

        # We should only get here if every form raises an exception
        raise Exception('Property could not be observed through any forms')

    async def observe_event(self, event_id, callback):
        """Subscribes to an event on a thing

        Takes 2 arguments:
        event_id - ID of the event to subscribe to
        callback - Function to run when the event is emitted
        """
        event_schema = self.schema.get('events', dict())
        event = event_schema[event_id]

        event['forms'] = [ f for f in event['forms'] if 'href' in f]
        for form in event['forms']:
            try:
                await self._observe(form['href'], callback)
            except:
                continue
            else:
                return

        # We should only get here if every form raises an exception
        raise Exception('Event could not be subscribed to through any forms')

    def delete(self):
        """Delete this thing from all places

        Removes from thing directory and local database
        """
        ThingAuthorization.objects.filter(thing_uuid=self.thing_id).delete()
        CustomAction.objects.filter(thing_uuid=self.thing_id).delete()

        response = requests.delete('{}/things/{}'.format(settings.THING_DIRECTORY_HOST, self.thing_id), headers={
                'Authorization': settings.THING_DIRECTORY_KEY,
        })
        response.raise_for_status()
        return response.json()
