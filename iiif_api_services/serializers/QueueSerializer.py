from rest_framework import serializers
from iiif_api_services.models.QueueModel import Queue
from rest_framework_mongoengine.serializers import DocumentSerializer


class QueueSerializer(DocumentSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='queue', lookup_field="id")

    class Meta:
        model = Queue
        exclude = ('requestBody', )
