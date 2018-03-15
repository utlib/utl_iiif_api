from rest_framework import serializers
from iiif_api_services.models.CollectionModel import Collection
from rest_framework_mongoengine.serializers import DocumentSerializer


class CollectionSerializer(DocumentSerializer):
    class Meta:
        model = Collection
        fields = '__all__'


class CollectionViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    collections = serializers.ListField()
    manifests = serializers.ListField()

    class Meta:
        model = Collection
        exclude = ('id', 'name', 'order', 'embeddedEntirely',
                   'belongsTo', 'hidden', 'ownedBy', 'children', )


class CollectionEmbeddedSerializer(DocumentSerializer):
    class Meta:
        model = Collection
        fields = ('ATid', 'ATtype', 'label', )
