from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.serializers.ManifestSerializer import ManifestEmbeddedSerializer
from iiif_api_services.serializers.SequenceSerializer import SequenceEmbeddedSerializer
from iiif_api_services.serializers.RangeSerializer import RangeEmbeddedSerializer
from iiif_api_services.serializers.CanvasSerializer import CanvasEmbeddedSerializer
from iiif_api_services.serializers.AnnotationSerializer import AnnotationEmbeddedSerializer
from iiif_api_services.serializers.AnnotationListSerializer import AnnotationListEmbeddedSerializer
from iiif_api_services.serializers.LayerSerializer import LayerEmbeddedSerializer
from iiif_api_services.helpers.PreProcessRequest import process_create_or_update_request, process_delete_request
from iiif_api_services.helpers.ProcessRequest import *


class CollectionViewSet(ViewSet):
    # GET /collection
    def list(self, request, format=None):
        # View the top level Collection.
        collection = Collection(
            label=settings.TOP_LEVEL_COLLECTION_LABEL,
            name=settings.TOP_LEVEL_COLLECTION_NAME,
            ATid="{0}/collections/{1}".format(settings.IIIF_BASE_URL,
                                              settings.TOP_LEVEL_COLLECTION_NAME)
        )
        return Response(view_collection(collection, root=True))

    # GET /collections/:name
    def retrieve(self, request, name=None, format=None, top_collection=None):
        try:
            if name == settings.TOP_LEVEL_COLLECTION_NAME:
                return self.list(request)
            collection = Collection.objects.get(name=name)
            return Response(view_collection(collection))
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Collection with name '{0}' does not exist.".format(name)})

    # POST /collections
    def create(self, request, format=None):
        return process_create_or_update_request(request, create_collection, "collection")

    # PUT /collections/:name
    def update(self, request, name=None, format=None):
        return process_create_or_update_request(request, update_collection, "collection", name=name)

    # DELETE /collections/:name
    def destroy(self, request, name=None, format=None):
        return process_delete_request(request, destroy_collection, name=name)


class ManifestViewSet(ViewSet):
    # GET /:identifier/manifest
    def retrieve(self, request, identifier=None, format=None):
        try:
            manifest = Manifest.objects.get(identifier=identifier)
            return Response(view_manifest(manifest))
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "'{0}' does not have a Manifest.".format(identifier)})

    # POST /:identifier/manifest
    def create(self, request, identifier=None, format=None):
        return process_create_or_update_request(request, create_manifest, "manifest", identifier=identifier)

    # PUT /:identifier/manifest
    def update(self, request, identifier=None, format=None):
        return process_create_or_update_request(request, update_manifest, "manifest", identifier=identifier)

    # DELETE /:identifier/manifest
    def destroy(self, request, identifier=None, format=None):
        return process_delete_request(request, destroy_manifest, identifier=identifier)


map_generic_iiif_objects = {
    "sequence": {
        "model": Sequence,
        "request_body_key": "sequence",
        "serializer": SequenceEmbeddedSerializer,
        "retrieve": view_sequence,
        "create": create_sequence,
        "update": update_sequence,
        "destroy": destroy_sequence
    },
    "canvas": {
        "model": Canvas,
        "request_body_key": "canvas",
        "serializer": CanvasEmbeddedSerializer,
        "retrieve": view_canvas,
        "create": create_canvas,
        "update": update_canvas,
        "destroy": destroy_canvas
    },
    "annotation": {
        "model": Annotation,
        "request_body_key": "annotation",
        "serializer": AnnotationEmbeddedSerializer,
        "retrieve": view_annotation,
        "create": create_annotation,
        "update": update_annotation,
        "destroy": destroy_annotation
    },
    "list": {
        "model": AnnotationList,
        "request_body_key": "annotationList",
        "serializer": AnnotationListEmbeddedSerializer,
        "retrieve": view_annotation_list,
        "create": create_annotation_list,
        "update": update_annotation_list,
        "destroy": destroy_annotation_list
    },
    "range": {
        "model": Range,
        "request_body_key": "range",
        "serializer": RangeEmbeddedSerializer,
        "retrieve": view_range,
        "create": create_range,
        "update": update_range,
        "destroy": destroy_range
    },
    "layer": {
        "model": Layer,
        "request_body_key": "layer",
        "serializer": LayerEmbeddedSerializer,
        "retrieve": view_layer,
        "create": create_layer,
        "update": update_layer,
        "destroy": destroy_layer
    }
}


class GenericViewSet(ViewSet):

    # GET /:identifier/<iiif_object_type>/:name
    def retrieve(self, request, identifier=None, name=None, format=None):
        try:
            # Get the object from the DB. (eg): Canvas.objects.get(identifier=identifier, name=name)
            iiif_object_type = get_iiif_object_type(
                request.get_full_path())  # Identify the IIIF Object type
            iiif_object = iiif_object_type['model'].objects.get(
                identifier=identifier, name=name)
            # Call the matching view method for this object. (eg): Response(view_canvas(canvas))
            return Response(iiif_object_type['retrieve'](iiif_object))
        # Catch object not found. (eg): except Canvas.DoesNotExist:
        except Exception:
            error_message = "{0} with name '{1}' does not exist in identifier '{2}'.".format(
                iiif_object_type['request_body_key'], name, identifier)
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': error_message})

    # GET /:identifier/<object_type>
    def list(self, request, identifier=None, format=None):
        try:
            iiif_object_type = get_iiif_object_type(
                request.get_full_path())  # Identify the IIIF Object type
            iiif_objects = iiif_object_type['model'].objects(
                identifier=identifier)
            if iiif_objects:
                iiif_objects_serializer = iiif_object_type['serializer'](
                    iiif_objects, context={'request': request}, many=True)
                return Response(iiif_objects_serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Item with name '{0}' does not exist.".format(identifier)})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # POST /:identifier/<object_type>
    def create(self, request, identifier=None, format=None):
        iiif_object_type = get_iiif_object_type(
            request.get_full_path())  # Identify the IIIF Object type
        return process_create_or_update_request(request, iiif_object_type['create'], iiif_object_type['request_body_key'], identifier=identifier)

    # PUT /:identifier/range/:name
    def update(self, request, identifier=None, name=None, format=None):
        iiif_object_type = get_iiif_object_type(
            request.get_full_path())  # Identify the IIIF Object type
        return process_create_or_update_request(request, iiif_object_type['update'], iiif_object_type['request_body_key'], identifier=identifier, name=name)

    # DELETE /:identifier/range/:name
    def destroy(self, request, identifier=None, name=None, format=None):
        iiif_object_type = get_iiif_object_type(
            request.get_full_path())  # Identify the IIIF Object type
        return process_delete_request(request, iiif_object_type['destroy'], identifier=identifier, name=name)


# Identify and return the IIIF Object type from parsing the request_path
def get_iiif_object_type(request_path):
    for key in map_generic_iiif_objects:
        if key in request_path:
            return map_generic_iiif_objects[key]
