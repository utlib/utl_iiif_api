from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from iiif_api_services.models.AnnotationModel import Annotation


class AnnotationSerializer(DocumentSerializer):
    class Meta:
        model = Annotation
        fields = '__all__'


class AnnotationViewSerializer(DocumentSerializer):
    ATcontext = serializers.URLField(allow_blank=True)

    class Meta:
        model = Annotation
        exclude = ('id', 'identifier', 'name', 'order', 'embeddedEntirely', 'belongsTo', 'hidden', 'ownedBy', 'children', )


class AnnotationEmbeddedSerializer(DocumentSerializer):

    class Meta:
        model = Annotation
        fields = ('ATid', 'ATtype', 'label', )
