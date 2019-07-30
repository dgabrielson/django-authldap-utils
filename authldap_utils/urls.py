"""
The url patterns for the authldap_utils application.
"""
from __future__ import print_function, unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(
        '^$',
        login_required(
            TemplateView.as_view(template_name='registration/profile.html')),
        name='user-profile',
    ),
    url(
        '^password-change/$',
        views.LdapPasswordChangeView.as_view(),
        name='password_change',
    ),
    url(
        '^password-change/done/$',
        views.LdapPasswordChangeDoneView.as_view(),
        name='password_change_done',
    ),
    url(
        '^password-reset/$',
        views.LdapPasswordResetView.as_view(),
        name='password_reset',
    ),
    url(
        '^password-reset/done/$',
        views.LdapPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    url(
        '^password-reset/confirm/(?P<uidb64>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.LdapPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    url(
        '^password-reset/complete/$',
        views.LdapPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]
