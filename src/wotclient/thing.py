from django.conf import settings
from wotclient.models import ThingAuthorization, AuthorizationMethod
import requests

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

class Thing(object):
    def __init__(self, thing_id, schema=None):
        self.thing_id = thing_id
        if schema is None:
            self.schema = get_thing_or_404(thing_id)
    def perform_action(self, action_id, data):
        action_schema = self.schema.get('actions', dict())
        if action_id not in action_id:
            raise KeyError('Action does not exist')
        action = action_schema[action_id]

        content_type = action['forms'][0].get('contentType', 'application/x-www-form-urlencoded')
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

        response = requests.post(action['forms'][0]['href'], headers=headers, data=data.encode())
        response.raise_for_status()
    def read_property(self, property_id):
        property_schema = self.schema.get('properties', dict())
        if property_id not in property_schema:
            raise KeyError('Property does not exist')
        prop = property_schema[property_id]

        value_response = requests.get(prop['forms'][0]['href'])
        try:
            json_response = json.loads(value_response.text)
        except:
            return _pretty_print_object(value_response.text)
        else:
            return _pretty_print_object(json_response)
