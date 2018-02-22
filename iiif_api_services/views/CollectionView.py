from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect


class CollectionViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Collections to be viewed or edited
    '''
    lookup_field = 'name'
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    pagination_class = None


    def create(self, request, format=None):
        '''
        Create a new Collection. \n
        #### Error Codes
        * `200` **Success** The Collection was successfully created. \n
        * `400` **Client Error** The data sent has validation errors. \n
        * `500` **Server Error** Internal Server Error.
        '''
        try:
            serializer = CollectionSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label']
                serializer.save(name=name.replace(" ", ""))
                return Response(serializer.data)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Collection name already exist."})


    def list(self, request, format=None):
        '''
        View a Top Level Collection of all Collections & Manifests in the Organization
        '''
        rootCollection = Collection(label="Organization", id="Organization", name="Organization")
        for c in Collection.objects(label__ne="Organization"):
            serializer = EmbeddedCollectionSerializer(c, context={'request': request})
            rootCollection.collections.append(serializer.data)
            rootCollection.members.append(serializer.data)

        for m in Manifest.objects.all():
            serializer = EmbeddedManifestSerializer(m, context={'request': request})
            rootCollection.manifests.append(serializer.data)
            rootCollection.members.append(serializer.data)

        rootCollection.total = len(rootCollection.members)

        serializer = CollectionSerializer(rootCollection, context={'request': request})
        return Response(serializer.data)


    def retrieve(self, request, name=None, format=None):
        '''
        View a specific Collection to Edit, Update or Delete
        '''
        if name == "Organization":
            return redirect('api-root')
        else:
            try:
                rootCollection = Collection.objects.get(name=name)
                for c in Collection.objects(name__ne=name):
                    if not c.within:
                        continue
                    collection_name = c.within.split("/")[4]
                    if collection_name != rootCollection.name:
                        continue
                    serializer = EmbeddedCollectionSerializer(c, context={'request': request})
                    rootCollection.collections.append(serializer.data)
                    rootCollection.members.append(serializer.data)
                for m in Manifest.objects(within=rootCollection.within):
                    if not m.within:
                        continue
                    collection_name = m.within.split("/")[4]
                    if collection_name != rootCollection.name:
                        continue
                    serializer = EmbeddedManifestSerializer(m, context={'request': request})
                    rootCollection.manifests.append(serializer.data)
                    rootCollection.members.append(serializer.data)
                rootCollection.total = len(rootCollection.members)
                serializer = CollectionSerializer(rootCollection, context={'request': request})
                return Response(serializer.data)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND) 
        return Response(status=status.HTTP_404_NOT_FOUND)




    def update(self, request, name=None, format=None):
        '''
        Update this Collection
        '''
        if name == "Organization":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Top level Organization Cannot be edited."})
        try:
            collection = Collection.objects.get(name=name)
            old_name = collection.name
            serializer = CollectionSerializer(collection, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(name=request.data['label'].replace(" ", ""))
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message})




class SearchCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Collections to be searched
    '''
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    pagination_class = None

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
            if collections:
                serializer = EmbeddedCollectionSerializer(collections, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Collection.DoesNotExist
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Collections found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
