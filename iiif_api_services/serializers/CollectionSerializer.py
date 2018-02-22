from rest_framework import serializers as rest_serializers
from rest_framework_mongoengine import serializers as rest_mongo_serializers
from iiif_api_services.models.CollectionModel import Collection
from mongoengine import fields


class CollectionSerializer(rest_mongo_serializers.DocumentSerializer):
    id = rest_serializers.HyperlinkedIdentityField(view_name='collection-detail', lookup_field='name')
    context = rest_serializers.URLField(initial='http://iiif.io/api/presentation/2/context.json')
    type = rest_serializers.CharField(initial='sc:Collection')

    class Meta:
        model = Collection
        exclude = ('name',)

        
class EmbeddedCollectionSerializer(rest_mongo_serializers.EmbeddedDocumentSerializer):
    id = rest_serializers.HyperlinkedIdentityField(view_name='collection-detail', lookup_field='name')
    type = rest_serializers.CharField(initial='sc:Collection')

    class Meta:
        model = Collection
        fields = ('id', 'type', 'label', 'viewingHint', 'members')