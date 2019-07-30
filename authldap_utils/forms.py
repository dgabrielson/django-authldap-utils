"""
Forms for ldap administration.
"""
################################################################
from __future__ import print_function, unicode_literals

import unicodedata
from collections import OrderedDict

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, send_mail
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from . import conf
from .models import LdapGroup, LdapSambaDomain, LdapUser
from .utils import generate_random_password, make_ssha_password

DjangoUser = get_user_model()

################################################################

################################################################


class PasswordField(forms.CharField):
    widget = forms.PasswordInput


################################################################


class CheckAlreadyAssignedMixin(object):
    """
    Use this mixin when something like an ID field or a username
    needs to be checked for uniqueness.
    """

    def auto_numeric_check(self, name, default, qs, verbose_name=None):
        value = self.data[name]
        #values_list = [int(getattr(o, name, default)) for o in qs.all()]
        values_list = [int(v) for v in qs.values_list(name, flat=True)]
        if not value:
            if values_list:
                M = max(values_list)
                value = M + 1
            else:
                value = default
        else:
            value = int(value)
        return self.check_already_assigned(name, qs, value, values_list,
                                           verbose_name)

    def check_already_assigned(self,
                               name,
                               qs,
                               value=None,
                               field_list=None,
                               verbose_name=None):
        if value is None:
            value = self.data[name]
        if field_list is None:
            field_list = qs.values_list(name, flat=True)
        if not isinstance(field_list, list):
            field_list = list(field_list)
        if verbose_name is None:
            verbose_name = name.title()
        if self.instance is not None:
            instance_value = getattr(self.instance, name)
            if instance_value in field_list:
                field_list.remove(instance_value)
        if value in field_list:
            raise ValidationError(
                '{0} already assigned.  Choose something else.'.format(
                    verbose_name))
        return value


################################################################


class LdapUserMixin(object):
    """
    Provide a function to get an LDAP user from a username.
    """

    def get_ldap_user(self, username):
        """
        Get the LDAP user, if there is one.  If not, return None.
        """
        try:
            ldap_user = LdapUser.objects.get(username=username)
        except LdapUser.DoesNotExist:
            return None
        else:
            return ldap_user


class LdapUserPasswordMixin(object):
    """
    Override form save to do the right thing with the
    user passwords (using the LdapUser set_password() method).
    """

    def save(self, commit=True):
        if self.initial.get('password', '') != self.data['password']:
            # Only update passwords when they've changed.
            ldap_user = super(LdapUserPasswordMixin, self).save(commit=False)
            ldap_user.set_password(self.data['password'])
        return super(LdapUserPasswordMixin, self).save(commit=commit)


################################################################


class LdapUserForm(CheckAlreadyAssignedMixin, LdapUserPasswordMixin,
                   forms.ModelForm):
    """
    """

    group = forms.ModelChoiceField(
        queryset=LdapGroup.objects.all(), to_field_name='gid')
    if conf.get('enable_samba'):
        domain = forms.ModelChoiceField(
            queryset=LdapSambaDomain.objects.all(),
            to_field_name='domain_name')

    class Meta:
        model = LdapUser
        exclude = ['dn', 'photo']

    def clean_password(self):
        """
        Generate a random password if the password is blank.
        """
        password = self.data['password']
        if not password:
            plaintext = generate_random_password()
        return password

    def clean_group(self):
        """
        In order for the LdapGroup ModelChoiceField to work, this seems
        to be required, even though it does nothing...
        """
        group = self.data['group']
        return group

    def clean_uid(self):
        """
        Check that the UID is an integer, in a decent range, and not already
        assigned.
        """
        uid = self.auto_numeric_check(
            'uid', 10000, LdapUser.objects, verbose_name='User ID')
        if uid < 2000 or (60000 <= uid < 70000):
            raise ValidationError(
                'User ID is in a restricted range.  Choose something else.')
        return uid

    def clean_username(self):
        """
        Check that the username is not already assigned.
        """
        return self.check_already_assigned('username', LdapUser.objects)

    def clean_full_name(self):
        if not self.data['full_name']:
            first_name = self.data['first_name']
            last_name = self.data['last_name']
            return '{first_name} {last_name}'.format(
                first_name=first_name, last_name=last_name)
        return self.data['full_name']

    def clean_gecos(self):
        if not self.data['gecos']:
            first_name = self.data['first_name']
            last_name = self.data['last_name']
            value = '{first_name} {last_name}'.format(
                first_name=first_name, last_name=last_name)
        else:
            value = self.data['gecos']
        value = unicodedata.normalize('NFKD', value).encode(
            'ascii', 'ignore').decode('ascii')
        return value

    def clean_home_directory(self, home_template=None):
        if home_template is None:
            home_template = conf.get('home_template')
        if not self.data['home_directory']:
            username = self.data['username']
            return home_template.format(username=username)
        return self.data['home_directory']


# Force ordering for user info:
field_list = [
    'uid',
    'username',
    'password',
    'group',
    'gecos',
    'home_directory',
    'login_shell',
    'email',
    'first_name',
    'last_name',
    'full_name',
    'phone',
    'mobile_phone',
]
if conf.get('enable_samba'):
    field_list += [
        'domain',
        'acct_flags',
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
        'logon_hours',
    ]

LdapUserForm.base_fields = OrderedDict(
    [(k, LdapUserForm.base_fields[k]) for k in field_list])

# Note: In the LdapUserAdmin this done via formsets.

################################################################

################################################################


class LdapGroupForm(CheckAlreadyAssignedMixin, forms.ModelForm):
    """
    Form for LdapGroup objects.
    """

    class Meta:
        exclude = ['dn', 'usernames']

    def clean_gid(self):
        """
        Check that the UID is an integer, in a decent range, and not already
        assigned.
        """
        return self.auto_numeric_check(
            'gid', 5000, LdapGroup.objects, verbose_name='Group ID')

    def clean_name(self):
        """
        Check that the username is not already assigned.
        """
        return self.check_already_assigned('name', LdapGroup.objects)


################################################################


class LdapPasswordResetForm(LdapUserMixin, PasswordResetForm):
    """
    This is required because LDAP users have an unusable password in
    their Django User model instance.

    Using ``clean_email()`` in this form leaks information about valid
    email addresses on the system.

    NOTE: The parent ``PasswordResetForm`` changed substantially in
    Django 1.6 (i.e., the old implementation broke).
    """

    def _user_has_usuable_password(self, django_user):
        """
        Check the django user and the ldap user for usable passwords.
        """
        ldap_user = self.get_ldap_user(django_user.username)
        if ldap_user is None:
            flag = django_user.has_usable_password()
            return flag

        flag = ldap_user.has_usable_password()
        return flag

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        return (u for u in active_users if self._user_has_usuable_password(u))


################################################################


class LdapSetPasswordForm(LdapUserMixin, SetPasswordForm):
    """
    This form is used when doing user-password resets.
    See django.contrib.auth.forms for parent implementation.

    Use the django-passwords PasswordField.
    """
    new_password1 = PasswordField(
        label=_("New password"), widget=forms.PasswordInput)
    new_password2 = PasswordField(
        label=_("New password confirmation"), widget=forms.PasswordInput)

    def save(self, commit=True):
        """
        Save LDAP user if there is one, if not do the default.
        """
        ldap_user = self.get_ldap_user(self.user.username)
        if ldap_user is not None:
            ldap_user.set_password(self.cleaned_data['new_password1'])
            if commit:
                ldap_user.save()
            return self.user
        else:
            # default behaviour:
            return super(LdapSetPasswordForm, self).save(commit=commit)


################################################################


class LdapPasswordChangeForm(PasswordChangeForm, LdapSetPasswordForm):
    """
    This form is used when doing user-password changes.
    See django.contrib.auth.forms for parent implementation.

    **NOTE** LdapFormMixin comes by way of LdapSetPasswordForm.
    """

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        Problem:  LDAP passwords are *not* checked by
        ``user.check_password(...)``.
        """
        ldap_user = self.get_ldap_user(self.user.username)
        if ldap_user is not None:
            old_password = self.cleaned_data["old_password"]
            if ldap_user.check_password(old_password):
                raise forms.ValidationError(
                    self.error_messages['password_incorrect'])
            return old_password
        else:
            # default behaviour:
            return super(LdapPasswordChangeForm, self).clean_old_password()


################################################################


class AdminEmailForm(forms.Form):
    """
    A form for composing an email.
    Assumes that the from and the to will be given.
    """
    to_list = forms.ModelMultipleChoiceField(
        queryset=LdapUser.objects.all(),
        widget=FilteredSelectMultiple('Receipents', False))
    from_user = forms.ModelChoiceField(
        queryset=DjangoUser.objects.all(), widget=forms.HiddenInput)
    subject = forms.CharField(
        max_length=128, widget=forms.TextInput(attrs={'size': 90}))
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 18,
            'cols': 65
        }))

    @property
    def media(self):
        js = [
            'jquery.js', 'jquery.init.js', "core.js", "SelectBox.js",
            "SelectFilter2.js"
        ]
        return forms.Media(js=[static("admin/js/%s" % path) for path in js])

    def send_email(self):
        """
        The form is assumed to be valid at the point this is called.
        Return the number of messages sent.
        """
        from_user = self.cleaned_data['from_user']
        to_list = self.cleaned_data['to_list']
        from_email = from_user.get_full_name() + ' <' + from_user.email + '>'
        subject = self.cleaned_data['subject']
        message = self.cleaned_data['message']

        count = 0
        for to_obj in to_list:
            headers = {'To': to_obj.full_name + ' <' + to_obj.email + '>'}
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[
                    to_obj.email,
                ],
                headers=headers)
            count += email.send()
        return count


################################################################
