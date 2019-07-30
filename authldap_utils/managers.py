"""
Managers for the authldap_utils application.
"""
#######################################################################
from __future__ import print_function, unicode_literals

from django.db import models

# from .querysets import Authldap_UtilsModelQuerySet

#######################################################################
#######################################################################
#######################################################################


class CustomQuerySetManager(models.Manager):
    """
    Custom Manager for an arbitrary model, just a wrapper for returning
    a custom QuerySet
    """
    use_for_related_fields = False
    queryset_class = models.query.QuerySet
    always_select_related = None

    # use always_select_related when the unicode()/str() method for a model
    #   pull foreign keys.

    def get_queryset(self):
        """
        Return the custom QuerySet
        """
        queryset = self.queryset_class(self.model)
        if self.always_select_related is not None:
            queryset = queryset.select_related(*self.always_select_related)
        return queryset

    def __getattr__(self, name):
        """
        If a method/attribute etc. cannot be located, proxy to the QuerySet.
        """
        return getattr(self.get_queryset(), name)


#######################################################################
#######################################################################
#######################################################################

# class Authldap_UtilsModelManager(CustomQuerySetManager):
#     use_for_related_fields = True
#     queryset_class = Authldap_UtilsModelQuerySet

#######################################################################
