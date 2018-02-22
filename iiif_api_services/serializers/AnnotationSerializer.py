from rest_framework import serializers as rest_serializers
from rest_framework_mongoengine import serializers as rest_mongo_serializers
from iiif_api_services.models.AnnotationModel import Annotation
from mongoengine import fields


class CustomHyperlinkedIdentityField(rest_serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.
        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if obj.name is None:
            return None

        return self.reverse(view_name,
            kwargs={
                'item': obj.item,
                'name': obj.name,
            },
            request=request,
            format=format,
        )


class AnnotationSerializer(rest_mongo_serializers.DocumentSerializer):
    id = CustomHyperlinkedIdentityField(view_name='annotation-detail')
    context = rest_serializers.URLField(initial='http://iiif.io/api/presentation/2/context.json')
    type = rest_serializers.CharField(initial='oa:Annotation')
    motivation = rest_serializers.CharField(initial='sc:painting')

    class Meta:
        model = Annotation
        exclude = ('item', 'name')


class EmbeddedAnnotationSerializer(rest_mongo_serializers.EmbeddedDocumentSerializer):
    id = CustomHyperlinkedIdentityField(view_name='annotation-detail')
    type = rest_serializers.CharField(initial='oa:Annotation')

    class Meta:
        model = Annotation
        fields = ('id', 'type', 'label', 'motivation', 'on')

