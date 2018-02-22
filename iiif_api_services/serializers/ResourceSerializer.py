from rest_framework import serializers as rest_serializers
from rest_framework_mongoengine import serializers as rest_mongo_serializers
from iiif_api_services.models.ResourceModel import Resource
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


class ResourceSerializer(rest_mongo_serializers.DocumentSerializer):
    resource = rest_serializers.FileField(write_only=True, allow_null=True)
    id = CustomHyperlinkedIdentityField(view_name='resource-detail')
    context = rest_serializers.URLField(initial='http://iiif.io/api/presentation/2/context.json')
    res_url = rest_serializers.CharField(initial='', allow_blank=True)

    class Meta:
        model = Resource
        exclude = ('item', 'name')

    def create(self, validated_data):
        data = validated_data.pop('resource')
        return Resource.objects.create(**validated_data)




class EmbeddedResourceSerializer(rest_mongo_serializers.EmbeddedDocumentSerializer):
    id = CustomHyperlinkedIdentityField(view_name='resource-detail')

    class Meta:
        model = Resource
        fields = ('id', 'res_url', 'label', 'type', 'format', 'height', 'width',)



class ResourceSerializerView(rest_mongo_serializers.DocumentSerializer):
    id = CustomHyperlinkedIdentityField(view_name='resource-detail')

    class Meta:
        model = Resource
        exclude = ('item', 'name', )

