"""Correlator Admin Config"""

from django.contrib.admin.apps import AdminConfig


class CorrelatorAdminConfig(AdminConfig):
    """Correlator Admin Config"""

    default_site = "correlator.admin.CorrelatorAdminSite"
