from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.CanvasModel import Canvas


class CanvasSerializer(DocumentSerializer):
    class Meta:
        model = Canvas
        fields = '__all__'


class CanvasViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    images = serializers.ListField()
    otherContent = serializers.ListField()

    class Meta:
        model = Canvas
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely', 'belongsTo', 'hidden', 'ownedBy', 'children', )


class CanvasEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Canvas
        fields = ('ATid', 'ATtype', 'label', )
