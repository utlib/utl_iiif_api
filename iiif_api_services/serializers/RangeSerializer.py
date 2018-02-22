from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.RangeModel import Range


class RangeSerializer(DocumentSerializer):
    class Meta:
        model = Range
        fields = '__all__'


class RangeViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    members = serializers.ListField()

    class Meta:
        model = Range
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely', 'belongsTo', 'hidden', 'ownedBy', )


class RangeEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Range
        fields = ('ATid', 'ATtype', 'label', 'contentLayer', )
