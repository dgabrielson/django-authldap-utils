django-authldap-utils
======================

A django application that makes working with LDAP Authenticated users much easier.

Uses the fantastic ``django-ldapdb`` library to expose LDAP users,
groups, and samba domains in the Django Admin.

Provides standard forms for e.g., django password changes to
the LDAP users.
See ``authldap_utils.profile.urls`` for an example on how
these can be used.

Since the password related forms subclass the existing
``django.contrib.auth.forms`` classes, password validation from
Django 1.9+ comes for free.

Opportunistically uses ``django-passwords`` if installed (not required).


Setup
------

Add ``'authldap_utils.apps.MirrorToUserConfig'`` or
``'authldap_utils.apps.BaseConfig'``to your list of
``INSTALLED_APPS``.
The ``MirrorToUserConfig`` pushes changes from the LdapUser model
to the regular Django user model (**caution** this has not been
thoroughly tested with custom user models).


Add your LDAP server to the ``DATABASES`` setting::

    "DATABASES": {
        "default": {
            ...
        },
         "ldap": {
            "ENGINE": "ldapdb.backends.ldap",
            "NAME": "ldap[s]://ip-or-hostname",
            "PASSWORD": "sekrit",
            "USER": "cn=admin,dc=example,dc=com"
        }


Finally, add the ``ldapdb `` database router to ``settings.py``::


    from django import db
    from ldapdb.router import Router

    # Add the LDAP router
    db.router.routers.append(Router())
