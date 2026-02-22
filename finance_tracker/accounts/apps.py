"""
Accounts App Configuration
============================
We use Django signals here to automatically create a UserProfile
whenever a new User is created. This way you never have to manually
create a profile — it happens behind the scenes.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        This method runs when Django starts up.
        We import signals here so they get registered.
        """
        import accounts.signals  # noqa
