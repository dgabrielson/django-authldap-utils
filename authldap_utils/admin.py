# -*- coding: utf-8 -*-
#
# django-ldapdb
# Copyright (c) 2009-2011, Bolloré telecom
# All rights reserved.
#
# See AUTHORS file for a full list of contributors.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Bolloré telecom nor the names of its contributors
#        may be used to endorse or promote products derived from this software
#        without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################
#
# Further modifications and customizations by Dave Gabrielson.
#
################################################################
from __future__ import print_function, unicode_literals

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from . import conf
from .forms import LdapGroupForm, LdapUserForm
from .models import LdapGroup, LdapSambaDomain, LdapUser
from .views import EmailUsersAdminAction

################################################################


class LdapGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'gid']
    search_fields = ['name']
    ordering = [
        'gid',
    ]
    form = LdapGroupForm


admin.site.register(LdapGroup, LdapGroupAdmin)

################################################################


class LdapUserAdmin(admin.ModelAdmin):
    """
    Admin interface for LdapUser objects.

    Note the custom user form.
    """
    actions = [
        'email_users_action',
    ]
    fieldsets = (
        ('Posix Account', {
            'fields': [
                'uid',
                'username',
                'password',
                'group',
                'gecos',
                'home_directory',
                'login_shell',
            ]
        }),
        ('Inet Org Person', {
            'fields': [
                'email',
                'first_name',
                'last_name',
                'full_name',
                'phone',
                'mobile_phone',
            ]
        }),
    )
    form = LdapUserForm
    list_display = ['username', 'first_name', 'last_name', 'email', 'uid']
    ordering = [
        'uid',
    ]
    save_on_top = True
    search_fields = ['first_name', 'last_name', 'full_name', 'username']

    def get_fieldsets(self, *args, **kwargs):
        fieldsets = super(LdapUserAdmin, self).get_fieldsets(*args, **kwargs)
        if conf.get('enable_samba'):
            fieldsets += (
                ('Samba', {
                    'fields': [
                        'domain',
                    ]
                }),
                (
                    'Samba SAM Account',
                    {
                        'classes': [
                            'collapse',
                        ],
                        'fields': [
                            'lm_password',
                            'nt_password',
                            'sid',
                            'pwd_last_set',
                            'pwd_can_change',
                            'pwd_must_change',
                            'logon_time',
                            'logoff_time',
                            'kickoff_time',
                            'bad_password_count',
                            'bad_password_time',
                            #'logon_hours',
                        ]
                    }),
            )
        return fieldsets

    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super(LdapUserAdmin, self).get_readonly_fields(
            *args, **kwargs)
        if conf.get('enable_samba'):
            readonly_fields += ('lm_password', 'nt_password', 'sid',
                                'pwd_last_set', 'logon_time', 'logoff_time',
                                'bad_password_count', 'bad_password_time')
        return readonly_fields

    def get_urls(self):
        """
        Extend the admin urls for this model.
        Provide a link by subclassing the admin change_form,
        and adding to the object-tools block.
        """
        urls = super(LdapUserAdmin, self).get_urls()
        urls = [
            url(
                r'^email-users/$',
                self.admin_site.admin_view(EmailUsersAdminAction.as_view()),
                name='ldap-email-users',
            ),
        ] + urls
        return urls

    def email_users_action(self, request, queryset):
        """
        Redirect to the actual view.
        """
        url = reverse_lazy('admin:ldap-email-users')
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        query = '&'.join(['to={0}'.format(s) for s in selected])
        return HttpResponseRedirect(url + '?' + query)

    email_users_action.short_description = "Email selected user(s)"


admin.site.register(LdapUser, LdapUserAdmin)

################################################################


class LdapSambaDomainAdmin(admin.ModelAdmin):
    list_display = ['domain_name', 'sid']
    search_fields = ['domain_name']
    ordering = [
        'domain_name',
    ]
    exclude = [
        'dn',
    ]


if conf.get('enable_samba'):
    admin.site.register(LdapSambaDomain, LdapSambaDomainAdmin)

################################################################
