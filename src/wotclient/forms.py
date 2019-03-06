from django import forms

class ThingActionForm(forms.Form):
    custom_action_id = forms.IntegerField(required=False, min_value=0)
    action_id = forms.CharField(required=False, max_length=36)
    save = forms.BooleanField(required=False)

class ThingSaveActionForm(ThingActionForm):
    action_id = forms.CharField(max_length=36)
    name = forms.CharField(max_length=32)
    description = forms.CharField(max_length=255)
