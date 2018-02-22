from rest_framework import serializers as rest_serializers
from rest_framework_mongoengine import serializers as rest_mongo_serializers
from iiif_api_services.models.ManifestModel import Manifest
from mongoengine import fields


class ManifestSerializer(rest_mongo_serializers.DocumentSerializer):
    id = rest_serializers.HyperlinkedIdentityField(view_name='manifest-detail', lookup_field='item')
    context = rest_serializers.URLField(initial='http://iiif.io/api/presentation/2/context.json')
    type = rest_serializers.CharField(initial='sc:Manifest')

    class Meta:
        model = Manifest
        exclude = ('item',)


class EmbeddedManifestSerializer(rest_mongo_serializers.EmbeddedDocumentSerializer):
    id = rest_serializers.HyperlinkedIdentityField(view_name='manifest-detail', lookup_field='item')
    type = rest_serializers.CharField(initial='sc:Manifest')

    class Meta:
        model = Manifest
        fields = ('id', 'type', 'label')