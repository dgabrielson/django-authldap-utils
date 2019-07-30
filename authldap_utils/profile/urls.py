"""
LDAP enabled profile stuff.
"""
from __future__ import print_function, unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (password_change, password_change_done,
                                       password_reset, password_reset_complete,
                                       password_reset_confirm,
                                       password_reset_done)
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from ..forms import (LdapPasswordChangeForm, LdapPasswordResetForm,
                     LdapSetPasswordForm)

urlpatterns = [
    url(
        '^$',
        login_required(
            TemplateView.as_view(template_name='registration/profile.html')),
        name='user-profile',
    ),
    url(
        '^password-change/$',
        password_change,
        kwargs={
            'password_change_form': LdapPasswordChangeForm,
            'post_change_redirect': reverse_lazy('password_change_done')
        },
        name='password_change',
    ),
    url(
        '^password-change/done/$',
        password_change_done,
        name='password_change_done',
    ),
    url(
        '^password-reset/$',
        password_reset,
        kwargs={
            'password_reset_form': LdapPasswordResetForm,
            'post_reset_redirect': reverse_lazy('password_reset_done')
        },
        name='password_reset',
    ),
    url(
        '^password-reset/done/$',
        password_reset_done,
        name='password_reset_done',
    ),
    url(
        '^password-reset/confirm/(?P<uidb64>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        kwargs={
            'set_password_form': LdapSetPasswordForm,
            'post_reset_redirect': reverse_lazy('password_reset_complete')
        },
        name='password_reset_confirm',
    ),
    url(
        '^password-reset/complete/$',
        password_reset_complete,
        name='password_reset_complete',
    ),
]
