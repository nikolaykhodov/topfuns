# -*- coding: utf-8 -*-
'''
http://djangosnippets.org/snippets/377/
'''

from django.db import models
from vk.basedict import BaseDict
from django.core.serializers.json import DjangoJSONEncoder
import json

 
class BaseDictField(models.TextField):
    """BaseDictField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return BaseDict(json.loads(value))
        except ValueError:
            pass

        return value

    def get_db_prep_save(self, value):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        return super(BaseDictField, self).get_db_prep_save(value)
