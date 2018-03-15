import json
from django.conf import settings
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.serializers.LayerSerializer import *
from iiif_api_services.serializers.ActivitySerializer import *
from iiif_api_services.helpers.ProcessRequest import view_annotation
from iiif_api_services.helpers.ProcessSearchQuery import process_search_query


class SearchViewSet(ViewSet):
    # GET /search/?type=sc:Collection&....
    def retrieve(self, request, type=None, format=None):
        map_urls_to_models = {
            "collection": [Collection, CollectionEmbeddedSerializer],
            "manifest": [Manifest, ManifestEmbeddedSerializer],
            "sequence": [Sequence, SequenceEmbeddedSerializer],
            "canvas": [Canvas, CanvasEmbeddedSerializer],
            "annotation": [Annotation, AnnotationEmbeddedSerializer],
            "list": [AnnotationList, AnnotationListEmbeddedSerializer],
            "range": [Range, RangeEmbeddedSerializer],
            "layer": [Layer, LayerEmbeddedSerializer],
            "activity": [Activity, ActivityEmbeddedSerializer]
        }
        try:
            matchingObjects = map_urls_to_models[type][0].objects(
                **process_search_query(request.GET))[:50]
            if matchingObjects:
                serializer = map_urls_to_models[type][1](
                    matchingObjects, context={'request': request}, many=True)
                return Response(serializer.data)
            raise ValueError
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No matching objects found for " + type + "."})
        except Exception:
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The search query format is invalid."})

    # GET {identifier}/manifest/search/?q=bird&motivation=painting ...
    def iiif_search_within_manifest(self, request, identifier=None, type=None, format=None):
        try:
            search_query = request.GET
            if "q" not in search_query:
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The parameter 'q' is required."})
            manifest = Manifest.objects.get(identifier=identifier)
            sequences = [item.to_mongo() for item in Sequence.objects(
                ATid__in=manifest.children, hidden=False).order_by('order')]
            ranges = [item.to_mongo() for item in Range.objects(
                ATid__in=manifest.children, hidden=False).order_by('order')]
            required_range_ids = []
            for range_object in ranges:
                required_range_ids += [
                    child for child in range_object["children"] if "range" in child]
            ranges += [item.to_mongo() for item in Range.objects(
                ATid__in=required_range_ids, hidden=False).order_by('order')]
            required_canvas_ids = []
            for sequence in sequences:
                required_canvas_ids += [
                    child for child in sequence["children"] if "canvas" in child]
            for range_object in ranges:
                required_canvas_ids += [
                    child for child in range_object["children"] if "canvas" in child]
            required_canvas_ids = list(set(required_canvas_ids))
            canvases = [item.to_mongo() for item in Canvas.objects(
                ATid__in=required_canvas_ids, hidden=False).order_by('order')]
            required_annotation_ids = []
            for canvas in canvases:
                required_annotation_ids += [
                    child for child in canvas["children"] if "annotation" in child]
            annotations = []
            for q in search_query["q"].split(" "):
                if "motivation" in search_query:
                    annotations += [item for item in Annotation.objects(ATid__in=required_annotation_ids, hidden=False,
                                                                        motivation__icontains=search_query["motivation"], resource__chars__icontains=q).order_by('order')]
                else:
                    annotations += [item for item in Annotation.objects(
                        ATid__in=required_annotation_ids, hidden=False, resource__chars__icontains=q).order_by('order')]
            matching_annotations = []
            unique_annotation_ids = []
            for anno in annotations:
                if anno.ATid not in unique_annotation_ids:
                    matching_annotations.append(anno)
                    unique_annotation_ids.append(anno.ATid)
            annotation_list = AnnotationList(identifier=settings.TOP_LEVEL_COLLECTION_NAME,
                                             name="searchResults", ATid=settings.IIIF_BASE_URL+request.get_full_path())
            annotation_list.resources = []
            for sub_annotation in matching_annotations:
                annotation_list.resources.append(
                    view_annotation(sub_annotation))
            annotation_list.ATcontext = "http://iiif.io/api/presentation/2/context.json"
            annotation_list_serializer = AnnotationListViewSerializer(
                annotation_list, context={'request': request})
            return Response(annotation_list_serializer.data)
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "'" + identifier + "' does not have a Manifest."})
        except Exception:  # pragma: no cover
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The search query format is invalid."})
