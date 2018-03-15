from rest_framework import serializers
from iiif_api_services.models.SequenceModel import Sequence
from rest_framework_mongoengine.serializers import DocumentSerializer


class SequenceSerializer(DocumentSerializer):
    class Meta:
        model = Sequence
        fields = '__all__'


class SequenceViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    canvases = serializers.ListField()

    class Meta:
        model = Sequence
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely',
                   'belongsTo', 'hidden', 'ownedBy', 'children', )


class SequenceEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Sequence
        fields = ('ATid', 'ATtype', 'label', )
