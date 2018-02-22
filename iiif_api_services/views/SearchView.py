import json
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.serializers.LayerSerializer import *
from iiif_api_services.serializers.ActivitySerializer import *
from iiif_api_services.views.BackgroundProcessing import viewAnnotation


class SearchViewSet(ViewSet):
    # GET /search/?type=sc:Collection&....
    def retrieve(self, request, type=None, format=None):
        searchQuery = request.GET
        mapTypesToModelsSearializer = {
            "collection": ["Collection", "CollectionEmbeddedSerializer"],
            "manifest": ["Manifest", "ManifestEmbeddedSerializer"],
            "sequence": ["Sequence", "SequenceEmbeddedSerializer"],
            "canvas": ["Canvas", "CanvasEmbeddedSerializer"],
            "annotation": ["Annotation", "AnnotationEmbeddedSerializer"],
            "list": ["AnnotationList", "AnnotationListEmbeddedSerializer"],
            "range": ["Range", "RangeEmbeddedSerializer"],
            "layer": ["Layer", "LayerEmbeddedSerializer"],
            "activity": ["Activity", "ActivityEmbeddedSerializer"]
        }
        try:
            fields = searchQuery.iteritems()
            query = {}
            for key, val in fields:
                if ("=" in key): # pragma: no cover
                    val = key.split("=")[1] if len(key.split("=")) > 1 else ""
                    key = key.split("=")[0]
                query[key.strip()+'__icontains'] = val.strip()
            exec "matchingObjects = "+mapTypesToModelsSearializer[type][0]+".objects(**query)[:50]"
            if matchingObjects:
                exec "serializer = "+mapTypesToModelsSearializer[type][1]+"(matchingObjects, context={'request': request}, many=True)"
                return Response(serializer.data)
            raise ValueError
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No matching objects found for " + type + "."})
        except Exception as e:
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The search query format is invalid."})


    # GET {identifier}/manifest/search/?q=bird&motivation=painting ...
    def iiifSearchWithinManifest(self, request, identifier=None, type=None, format=None):
        try:
            searchQuery = request.GET
            if "q" not in searchQuery:
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The parameter 'q' is required."})
            manifest = Manifest.objects.get(identifier=identifier)
            sequences = [item.to_mongo() for item in Sequence.objects(ATid__in=manifest.children, hidden=False).order_by('order')]
            ranges = [item.to_mongo() for item in Range.objects(ATid__in=manifest.children, hidden=False).order_by('order')]
            requiredRangeIDs = []
            for rangeObject in ranges:
                requiredRangeIDs += [child for child in rangeObject["children"] if "range" in child]
            ranges += [item.to_mongo() for item in Range.objects(ATid__in=requiredRangeIDs, hidden=False).order_by('order')]
            requiredCanvasIDs = []
            for sequence in sequences:
                requiredCanvasIDs += [child for child in sequence["children"] if "canvas" in child]
            for rangeObject in ranges:
                requiredCanvasIDs += [child for child in rangeObject["children"] if "canvas" in child]
            requiredCanvasIDs = list(set(requiredCanvasIDs))
            canvases = [item.to_mongo() for item in Canvas.objects(ATid__in=requiredCanvasIDs, hidden=False).order_by('order')]
            requiredAnnotationIDs = []
            for canvas in canvases:
                requiredAnnotationIDs += [child for child in canvas["children"] if "annotation" in child]
            annotations = []
            for q in searchQuery["q"].split(" "):
                if "motivation" in searchQuery:
                    annotations += [item for item in Annotation.objects(ATid__in=requiredAnnotationIDs, hidden=False, motivation__icontains=searchQuery["motivation"], resource__chars__icontains=q).order_by('order')]
                else:
                    annotations += [item for item in Annotation.objects(ATid__in=requiredAnnotationIDs, hidden=False, resource__chars__icontains=q).order_by('order')]
            matchingAnnotations = []
            uniqueAnnotationIDs = []
            for anno in annotations:
                if anno.ATid not in uniqueAnnotationIDs:
                    matchingAnnotations.append(anno)
                    uniqueAnnotationIDs.append(anno.ATid)
            annotationList = AnnotationList(identifier="UofT", name="searchResults", ATid=settings.IIIF_BASE_URL+request.get_full_path())
            annotationList.resources = []
            for subAnnotation in matchingAnnotations:
                annotationList.resources.append(viewAnnotation(subAnnotation))
            annotationList.ATcontext = "http://iiif.io/api/presentation/2/context.json"
            annotationListSerializer = AnnotationListViewSerializer(annotationList, context={'request': request})
            return Response(annotationListSerializer.data)
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "'" + identifier + "' does not have a Manifest."}) 
        except Exception as e: # pragma: no cover
            print e.message 
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The search query format is invalid."})