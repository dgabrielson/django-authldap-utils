"""
Views for the Auth LDAP utils application.
"""
################################################################
from __future__ import print_function, unicode_literals

from django.contrib import messages
from django.contrib.auth.views import (PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import (AdminEmailForm, LdapPasswordChangeForm,
                    LdapPasswordResetForm, LdapSetPasswordForm)
from .models import LdapUser

################################################################


class EmailUsersAdminAction(FormView):
    """
    A view for the admin to email Users as an action.
    """
    template_name = 'admin/ldap/ldapusers/email_form.html'
    form_class = AdminEmailForm
    success_url = reverse_lazy('admin:ldap_ldapuser_changelist')

    def get_initial(self):
        """
        Get initial data for the form.
        """
        initial = super(EmailUsersAdminAction, self).get_initial()

        selected = self.request.GET.getlist('to') \
                        if 'to' in self.request.GET else []
        #to_list = LdapUser.objects.filter(pk__in=selected)
        initial['to_list'] = selected
        initial['from_user'] = self.request.user
        return initial

    def form_valid(self, form):
        """
        Process successful form submission.
        """
        n = form.send_email()
        suffix = 's' if n != 1 else ''
        msg = 'Email has been sent to {0} recipient{1}.'.format(n, suffix)
        messages.success(self.request, msg, fail_silently=True)
        return super(EmailUsersAdminAction, self).form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Extend the context so the admin template works properly.
        """
        context = super(EmailUsersAdminAction, self).get_context_data(**kwargs)
        context.update({
            'app_label': 'ldap',
            'opts': {
                'verbose_name_plural': 'Email',
                'module_name': 'ldap-email-users',
            },
            'has_change_permission': True,
            'original': 'Email',
            'add': False,
        })
        return context


################################################################


class LdapPasswordChangeView(PasswordChangeView):
    form_class = LdapPasswordChangeForm
    success_url = reverse_lazy('password_change_done')


class LdapPasswordChangeDoneView(PasswordChangeDoneView):
    pass


class LdapPasswordResetView(PasswordResetView):
    form_class = LdapPasswordResetForm


class LdapPasswordResetDoneView(PasswordResetDoneView):
    pass


class LdapPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = LdapSetPasswordForm


class LdapPasswordResetCompleteView(PasswordResetCompleteView):
    pass


class LdapPasswordChangeView(PasswordChangeView):
    form_class = LdapPasswordChangeForm


class LdapPasswordChangeDoneView(PasswordChangeDoneView):
    pass


###############################################################
