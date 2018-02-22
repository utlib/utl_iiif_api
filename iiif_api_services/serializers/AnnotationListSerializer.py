from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.AnnotationListModel import AnnotationList


class AnnotationListSerializer(DocumentSerializer):
    class Meta:
        model = AnnotationList
        fields = '__all__'


class AnnotationListViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)
    resources = serializers.ListField()

    class Meta:
        model = AnnotationList
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely', 'belongsTo', 'hidden', 'ownedBy', 'children', )


class AnnotationListEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = AnnotationList
        fields = ('ATid', 'ATtype', 'label', )
