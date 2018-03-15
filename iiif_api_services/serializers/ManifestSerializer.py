from rest_framework import serializers
from iiif_api_services.models.ManifestModel import Manifest
from rest_framework_mongoengine.serializers import DocumentSerializer


class ManifestSerializer(DocumentSerializer):
    class Meta:
        model = Manifest
        fields = '__all__'


class ManifestViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    sequences = serializers.ListField()
    structures = serializers.ListField()

    class Meta:
        model = Manifest
        exclude = ('id', 'identifier', 'order', 'embeddedEntirely',
                   'belongsTo', 'hidden', 'ownedBy', 'children', )


class ManifestEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Manifest
        fields = ('ATid', 'ATtype', 'label', )
