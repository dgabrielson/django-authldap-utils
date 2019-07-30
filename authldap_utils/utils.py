###############################################################
from __future__ import print_function, unicode_literals

import hashlib
import os
import random
from base64 import decodestring as decode
from base64 import encodestring as encode
from string import ascii_letters, digits

import passlib.hash
from django.utils import six

###############################################################
# As per https://stackoverflow.com/a/36503802


def make_lm_password(s):
    return passlib.hash.lmhash.encrypt(s).upper()


def make_nt_password(s):
    return passlib.hash.nthash.encrypt(s).upper()


###############################################################

symbols = "@#$%^&*()_+=[]{};',./|\\"

HASH_ALPHABET = ascii_letters + digits + '/+'
HASH_LENGTH = 38

RANDPASS_ALPHABET = ascii_letters + digits + symbols

###############################################################


def make_ssha_password(password):
    """
    Take a plaintext password and convert it to {SSHA}
    Source: http://www.openldap.org/faq/data/cache/347.html
    """
    salt = os.urandom(4)
    h = hashlib.sha1(password.encode('utf-8'))
    h.update(salt)
    partial_b = encode(h.digest() + salt)[:-1]
    partial = partial_b.decode('utf-8')
    secret = "{SSHA}" + partial
    return secret


###############################################################


def is_ssha_password_usable(secret):
    """
    Check that this is valid {SSHA} password
    """
    if not isinstance(secret, six.string_types):
        return False
    if not secret.startswith('{SSHA}'):
        return False
    if len(secret) != HASH_LENGTH:
        return False
    for c in secret[6:]:
        if c not in HASH_ALPHABET:
            return False
    # it *might* be a usable password...
    return True


###############################################################


def generate_random_password(length=32):
    """
    Generate a random password for new users, and allow them to reset.
    """
    return ''.join([random.choice(RANDPASS_ALPHABET) for n in range(length)])


###############################################################
