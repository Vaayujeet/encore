"""Monitor Tool Forms"""

from django import forms


class MonitorToolForm(forms.ModelForm):
    """Monitor Tool Form"""

    class Meta:
        widgets = {
            "name": forms.TextInput(),
        }


class MonitorToolIPForm(forms.ModelForm):
    """Monitor Tool IP Form"""

    class Meta:
        widgets = {
            "ip": forms.TextInput(attrs={"size": 50}),
            "region": forms.TextInput(attrs={"size": 50}),
        }


class MonitorToolPipelineRuleForm(forms.ModelForm):
    """Monitor Tool Pipeline Rule Form"""

    class Meta:
        widgets = {
            "rule_type": forms.Select(attrs={"onchange": "onRuleTypeChange(event)"}),
            "event_type_field": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "event_type_up_values": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "event_type_down_values": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "event_type_neutral_values": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "set_field": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "set_value": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "grok_field": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "grok_patterns": forms.Textarea(attrs={"rows": 3, "cols": 80}),
            "grok_pattern_definitions": forms.Textarea(attrs={"rows": 3, "cols": 80}),
            "remove_field": forms.Textarea(attrs={"rows": 1, "cols": 80}),
            "if_condition": forms.Textarea(attrs={"rows": 3, "cols": 80}),
        }

    class Media:
        js = ("launchpad/js/monitor_tool_pipeline_rule.js",)
        css = {"all": ("launchpad/css/monitor_tool.css",)}
