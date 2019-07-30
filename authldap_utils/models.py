# -*- coding: utf-8 -*-
#
# Based on examples from django-ldapdb
# Copyright (c) 2009-2011, Bolloré telecom
# All rights reserved.
#

# Modifications (e.g., set_password) Copyright (c) 2013, Dave Gabrielson.

################################################################
from __future__ import print_function, unicode_literals

import time

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

import ldapdb.models
from ldapdb.models.fields import CharField, ImageField, IntegerField, ListField

from . import conf
from .utils import (generate_random_password, is_ssha_password_usable,
                    make_lm_password, make_nt_password, make_ssha_password)

LDAP_DC_DN = getattr(settings, 'LDAP_DC_DN', 'dc=example,dc=com')

################################################################


@python_2_unicode_compatible
class LdapUser(ldapdb.models.Model):
    """
    Class for representing an LDAP user entry.

    LDIF::
        dn: ou=People,dc=stats,dc=umanitoba,dc=ca
        objectClass: organizationalUnit
        ou: People

    """
    # LDAP meta-data
    base_dn = "ou=People," + LDAP_DC_DN
    if conf.get('enable_samba'):
        object_classes = [
            'posixAccount',
            'shadowAccount',
            'inetOrgPerson',
            'sambaSamAccount',
        ]
    else:
        object_classes = [
            'posixAccount',
            'shadowAccount',
            'inetOrgPerson',
        ]

    # inetOrgPerson
    first_name = CharField(db_column='givenName')
    last_name = CharField(db_column='sn')
    full_name = CharField(
        db_column='cn',
        blank=True,
        help_text='Leave blank to auto populate this field')
    email = CharField(db_column='mail')
    phone = CharField(db_column='telephoneNumber', blank=True)
    mobile_phone = CharField(db_column='mobile', blank=True)
    photo = ImageField(db_column='jpegPhoto')

    # posixAccount
    uid = IntegerField(
        db_column='uidNumber',
        unique=True,
        verbose_name='User ID',
        blank=True,
        help_text='Leave blank to auto populate this field')
    group = IntegerField(db_column='gidNumber')  # Can this be a ListField?
    gecos = CharField(
        db_column='gecos',
        blank=True,
        help_text='Leave blank to auto populate this field')
    home_directory = CharField(
        db_column='homeDirectory',
        blank=True,
        help_text='Leave blank to auto populate this field')
    login_shell = CharField(db_column='loginShell', default='/bin/bash')
    username = CharField(db_column='uid', primary_key=True)
    password = CharField(
        db_column='userPassword', default=generate_random_password)

    # shadowAccount
    #shadowLastChange
    #shadowMax default -1

    # sambaSamAccount
    if conf.get('enable_samba'):
        domain = CharField(
            db_column='sambaDomainName',
            verbose_name='samba domain',
            blank=True)
        acct_flags = CharField(
            db_column='sambaAcctFlags',
            default='[U          ]',
            verbose_name='account flags')
        lm_password = CharField(
            db_column='sambaLMPassword',
            verbose_name='LM password',
            blank=True)
        nt_password = CharField(
            db_column='sambaNTPassword',
            verbose_name='NT password',
            blank=True)
        sid = CharField(
            db_column='sambaSID', unique=True, verbose_name='SID', blank=True)
        pwd_last_set = IntegerField(
            db_column='sambaPwdLastSet',
            default=0,
            help_text='Timestamp of the last password update')
        pwd_can_change = IntegerField(
            db_column='sambaPwdCanChange',
            default=0,
            help_text=
            'Timestamp of when the user is allowed to update the password')
        pwd_must_change = IntegerField(
            db_column='sambaPwdMustChange',
            default=0,
            help_text='Timestamp of when the password will expire')
        logon_time = IntegerField(
            db_column='sambaLogonTime',
            default=0,
            help_text='Timestamp of last logon')
        logoff_time = IntegerField(
            db_column='sambaLogoffTime',
            default=0,
            help_text='Timestamp of last logoff')
        kickoff_time = IntegerField(
            db_column='sambaKickoffTime',
            default=0,
            help_text=
            'Timestamp of when the user will be logged off automatically')
        bad_password_count = IntegerField(
            db_column='sambaBadPasswordCount',
            default=0,
            help_text='Bad password attempt count')
        bad_password_time = IntegerField(
            db_column='sambaBadPasswordTime',
            default=0,
            help_text='Time of the last bad password attempt')
        logon_hours = CharField(
            db_column='sambaLogonHours',
            default='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    class Meta:
        verbose_name = 'User'

    def __str__(self):
        return self.full_name

    def set_password(self, password):
        """
        This function changes the given plaintext password to {SSHA}
        Note that this function **does not** save the password.
        """
        self.password = make_ssha_password(password)
        self.lm_password = make_lm_password(password)
        self.nt_password = make_nt_password(password)
        self.pwd_last_set = int(time.time())

    def check_password(self, password):
        """
        Checks the given password against the user's password
        Normally this is done via the LDAP backend, but sometimes forms
        need this also.
        """
        return make_ssha_password(password) == self.password

    def has_usable_password(self):
        """
        Standard check for usable passwords.
        """
        return is_ssha_password_usable(self.password)

    def save(self, *args, **kwargs):
        """
        Override sid
        """
        if conf.get('enable_samba'):
            samba_domain = LdapSambaDomain.objects.get(domain_name=self.domain)
            self.sid = samba_domain.sid + '-' + str(2 * int(self.uid) + 1000)
        # may need to modify fields, if present...
        return super(LdapUser, self).save(*args, **kwargs)


################################################################


@python_2_unicode_compatible
class LdapGroup(ldapdb.models.Model):
    """
    Class for representing an LDAP group entry.

    LDIF::
        dn: ou=Groups,dc=stats,dc=umanitoba,dc=ca
        objectClass: organizationalUnit
        ou: Groups
    """
    # LDAP meta-data
    base_dn = "ou=Groups," + LDAP_DC_DN
    object_classes = ['posixGroup']

    # posixGroup attributes
    gid = IntegerField(
        db_column='gidNumber',
        unique=True,
        blank=True,
        verbose_name='Group ID',
        help_text='Leave blank to auto populate this field')
    name = CharField(db_column='cn', max_length=200, primary_key=True)
    usernames = ListField(db_column='memberUid')

    class Meta:
        verbose_name = 'group'

    def __str__(self):
        return self.name


################################################################


@python_2_unicode_compatible
class LdapSambaDomain(ldapdb.models.Model):
    """
    Class for representing a Samba domain.

    LDIF::
        dn: dc=stats,dc=umanitoba,dc=ca
        objectClass: organizationalUnit
        ou: Samba

    """
    # LDAP meta-data
    base_dn = LDAP_DC_DN
    object_classes = [
        'sambaDomain',
    ]

    domain_name = CharField(db_column='sambaDomainName', primary_key=True)
    sid = CharField(db_column='sambaSID', unique=True, verbose_name='SID')

    class Meta:
        verbose_name = 'samba domain'

    def __str__(self):
        return self.domain_name


################################################################
