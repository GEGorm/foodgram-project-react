import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework import serializers

from recipes.models import Tag


class TagsField(serializers.Field):

    def to_representation(self, value):
        tag = get_object_or_404(Tag, id=value)
        return model_to_dict(tag)

    def to_internal_value(self, data):
        return data


class ImageField(serializers.Field):

    def to_representation(self, value):
        return value.url

    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
