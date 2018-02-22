from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.QueueModel import Queue


class QueueSerializer(DocumentSerializer):
  id = serializers.HyperlinkedIdentityField(view_name='queue', lookup_field="id")

  class Meta:
    model = Queue
    fields = '__all__'


