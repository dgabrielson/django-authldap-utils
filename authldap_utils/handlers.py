"""
Handlers for various signals in the Skaro LDAP application.

This module is imported by models.py, so signal handlers get registered
at runtime.
"""
################################################################
from __future__ import print_function, unicode_literals

from django.contrib.auth import get_user_model

################################################################


def user_sync_post_save(sender, instance, **kwargs):
    """
    Synchronize updates from LdapUser records to corresponding
    DjangoUser records.
    
    This signal handler should only be registered for LdapUser objects,
    so ``instance`` is an ``LdapUser`` object.
    
    This handler should do more to handle the Django Custom User Model 
    feature. For now, we are assuming the following fields exist on
    the Django User Model:
    * username  -  Should be ``get_by_natural_key(username)``
    * first_name
    * last_name
    * email
    
    This should all just work if the default User model has been extended.    
    See: https://docs.djangoproject.com/en/dev/topics/auth/customizing/
    """
    if kwargs.get('raw', False):
        return
    DjangoUserModel = get_user_model()
    user, flag = DjangoUserModel.objects.get_or_create(
        username=instance.username,
        defaults={
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
        })
    if not flag:
        user.first_name = instance.first_name
        user.last_name = instance.last_name
        user.email = instance.email
        user.save()


################################################################
