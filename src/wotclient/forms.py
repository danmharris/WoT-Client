from django import forms

class ThingActionForm(forms.Form):
    custom_action_id = forms.IntegerField(required=False, min_value=0)
    action_id = forms.CharField(required=False, max_length=36)
    save = forms.BooleanField(required=False)

class ThingSaveActionForm(ThingActionForm):
    action_id = forms.CharField(max_length=36)
    name = forms.CharField(max_length=32)
    description = forms.CharField(max_length=255)

class ThingSettingsForm(forms.Form):
    auth_method = forms.IntegerField(required=False)
    auth_method_delete = forms.BooleanField(required=False)

class ThingEventForm(forms.Form):
    event_id = forms.CharField(max_length=32)
    thing_uuid = forms.CharField(max_length=32)
    custom_action_name = forms.CharField(max_length=32)
