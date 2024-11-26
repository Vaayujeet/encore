"""Correlation Rule Forms"""

from django import forms


class CorrelationRuleForm(forms.ModelForm):
    """Correlation Rule Form"""

    class Meta:
        widgets = {
            "event_title": forms.TextInput(attrs={"size": 200}),
            "itsm_title": forms.TextInput(attrs={"size": 200}),
        }


class EventLevelBasedSubRuleForm(forms.ModelForm):
    """Event Level based Sub Rule Form"""

    class Meta:
        widgets = {
            "event_level": forms.TextInput(attrs={"size": 50}),
        }
