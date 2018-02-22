from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class ManifestViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Identifiers to be viewed or edited
    '''
    lookup_field = 'item'
    serializer_class = ManifestSerializer
    queryset = Manifest.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Manifest for this item
        '''
        try:
            manifest = Manifest.objects.get(item=item)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item already exists"})
        except:
            data = request.data
            serializer = ManifestSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save(item=item)
                return self.retrieve(request, item=item, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, item=None, format=None):
        '''
        Update the Manifest for this item
        '''
        try:
            manifest = Manifest.objects.get(item=item)
            old_item_name = manifest.item
            serializer = ManifestSerializer(manifest, data=request.data, context={'request': request})
            if serializer.is_valid():
                try:
                    new_item_name = request.data['label']
                    if manifest != Manifest.objects.get(item=request.data['label']):
                        new_item_name = request.data['label']+request.data['label']
                finally:
                    serializer.save(item=new_item_name)
                    return Response(serializer.data)
                    # Browser URL doesn't seem to change to new URL. Only issue in Browsable API.
                    # JSON reponse updates to the corect updated @id URL. 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class SearchManifestViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Manifests to be searched
    '''
    queryset = Manifest.objects.all()
    serializer_class = ManifestSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Manifests matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            manifests = Manifest.objects(**query)
            if manifests:
                serializer = EmbeddedManifestSerializer(manifests, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Manifest.DoesNotExist
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Manifests found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
