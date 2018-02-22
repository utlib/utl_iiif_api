from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.LayerModel import Layer


class LayerSerializer(DocumentSerializer):
    class Meta:
        model = Layer
        fields = '__all__'


class LayerViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    otherContent = serializers.ListField()

    class Meta:
        model = Layer
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely', 'belongsTo', 'hidden', 'ownedBy', 'children', )


class LayerEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Layer
        fields = ('ATid', 'ATtype', 'label', )
