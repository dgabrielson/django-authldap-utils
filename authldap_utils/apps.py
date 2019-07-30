#########################################################################
from __future__ import print_function, unicode_literals

from django.apps import AppConfig
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from . import handlers

#########################################################################


class BaseConfig(AppConfig):
    name = "authldap_utils"
    verbose_name = _("LDAP")


#########################################################################


class MirrorToUserConfig(BaseConfig):
    def ready(self):
        """
        Any app specific startup code, e.g., registering signals,
        should go here.
        """
        super(MirrorToUserConfig, self).ready()

        # Mirror LdapUser changes to User model:
        from .models import LdapUser
        signals.post_save.connect(
            handlers.user_sync_post_save, sender=LdapUser)


#########################################################################
