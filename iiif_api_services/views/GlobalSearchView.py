from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.serializers.LayerSerializer import *
from iiif_api_services.serializers.ResourceSerializer import *

from iiif_api_services.models.CollectionModel import *
from iiif_api_services.models.ManifestModel import *
from iiif_api_services.models.SequenceModel import *
from iiif_api_services.models.CanvasModel import *
from iiif_api_services.models.AnnotationModel import *
from iiif_api_services.models.AnnotationListModel import *
from iiif_api_services.models.RangeModel import *
from iiif_api_services.models.LayerModel import *
from iiif_api_services.models.ResourceModel import *

from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status
from itertools import chain
from collections import OrderedDict


class GlobalSearchViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows anything in the repository to be searched
    '''
    def retrieve(self, request, query=None, format=None):
        '''
        Search for Collections matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()

            collections = Collection.objects(**query)
            manifests = Manifest.objects(**query)
            sequences = Sequence.objects(**query)
            canvases = Canvas.objects(**query)
            annotations = Annotation.objects(**query)
            annotationlists = AnnotationList.objects(**query)
            ranges = Range.objects(**query)
            layers = Layer.objects(**query)
            resources = Resource.objects(**query)

            result_list = list(chain(
                collections,
                manifests,
                sequences,
                canvases,
                annotations,
                annotationlists,
                ranges,
                layers,
                resources
                ))

            if result_list:
                collections_serializer = EmbeddedCollectionSerializer(collections, context={'request': request}, many=True)
                manifests_serializer = EmbeddedManifestSerializer(manifests, context={'request': request}, many=True)
                sequences_serializer = EmbeddedSequenceSerializer(sequences, context={'request': request}, many=True)
                canvases_serializer = EmbeddedCanvasSerializer(canvases, context={'request': request}, many=True)
                annotations_serializer = EmbeddedAnnotationSerializer(annotations, context={'request': request}, many=True)
                annotationlists_serializer = EmbeddedAnnotationListSerializer(annotationlists, context={'request': request}, many=True)
                ranges_serializer = EmbeddedRangeSerializer(ranges, context={'request': request}, many=True)
                layers_serializer = EmbeddedLayerSerializer(layers, context={'request': request}, many=True)
                resources_serializer = EmbeddedResourceSerializer(resources, context={'request': request}, many=True)

                KEY_ORDER = ["Collections", "Manifests", "Sequences", "Canvases", "Annotations", "AnnotationLists", "Ranges",
                             "Layers", "Resoources", ]
                KEY_ORDER_HASH = dict([(KEY_ORDER[x],x) for x in range(len(KEY_ORDER))])
                return_reponse = {
                    'Collections': collections_serializer.data,
                    'Manifests': manifests_serializer.data,
                    'Sequences': sequences_serializer.data,
                    'Canvases': canvases_serializer.data,
                    'Annotations': annotations_serializer.data,
                    'AnnotationLists': annotationlists_serializer.data,
                    'Ranges': ranges_serializer.data,
                    'Layers': layers_serializer.data,
                    'Resoources': resources_serializer.data,}
                return_reponse = OrderedDict(sorted(return_reponse.items(), key=lambda x: KEY_ORDER_HASH.get(x[0], 1000)))
                return Response(return_reponse)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No data found in any resources matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
