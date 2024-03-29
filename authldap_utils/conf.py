"""
The DEFAULT configuration is loaded when the named _CONFIG dictionary
is not present in your settings.
"""
from __future__ import print_function, unicode_literals

from django.conf import settings

CONFIG_NAME = 'AUTHLDAP_UTILS_CONFIG'  # must be uppercase!

DEFAULT = {

    # put application configuration items here.

    # Default home template when creating users.
    'home_template': '/home/{username}',
    'enable_samba': False,
}

#########################################################################


def get(setting):
    """
    get(setting) -> value

    setting should be a string representing the application settings to
    retrieve.
    """
    assert setting in DEFAULT, 'the setting %r has no default value' % setting
    app_settings = getattr(settings, CONFIG_NAME, DEFAULT)
    return app_settings.get(setting, DEFAULT[setting])


def get_all():
    """
    Return all current settings as a dictionary.
    """
    app_settings = getattr(settings, CONFIG_NAME, DEFAULT)
    return dict([(setting, app_settings.get(setting, DEFAULT[setting])) \
                 for setting in DEFAULT])


#########################################################################
