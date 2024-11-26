"""Event Form"""

from django import forms


class EventForm(forms.ModelForm):
    """Event Form"""

    class Meta:
        widgets = {
            "doc_id": forms.TextInput(attrs={"size": 200}),
            "doc_index": forms.TextInput(attrs={"size": 50}),
            "level": forms.TextInput(attrs={"size": 200}),
            "title": forms.TextInput(attrs={"size": 200}),
            "asset_unique_id": forms.TextInput(attrs={"size": 200}),
            "asset_type": forms.TextInput(attrs={"size": 200}),
        }
