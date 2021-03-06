from rest_framework import serializers
from iiif_api_services.models.ActivityModel import Activity
from rest_framework_mongoengine.serializers import DocumentSerializer


class ActivitySerializer(DocumentSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='activity', lookup_field="id")

    class Meta:
        model = Activity
        fields = '__all__'


class ActivityEmbeddedSerializer(DocumentSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='activity', lookup_field="id")

    class Meta:
        model = Activity
        fields = ('id', 'requestMethod', 'requestPath',
                  'responseCode', 'startTime', 'endTime', )
