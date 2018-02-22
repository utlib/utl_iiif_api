from iiif_api_services.serializers.LayerSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class LayerViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Layer to be created, viewed, edited or deleted
    '''
    serializer_class = LayerSerializer
    queryset = Layer.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Layer for this item
        '''
        try:
            name = request.data['label'].replace(" ", "")
            layer = Layer.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Layer name already exist in this item."})
        except:
            data = request.data
            serializer = LayerSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all Layers in this item
        '''
        try:
            layer = Layer.objects(item=item)
            if layer:
                serializer = EmbeddedLayerSerializer(layer, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Layer to Update or Delete
        '''
        try:
            layer = Layer.objects.get(item=item, name=name)
            serializer = LayerSerializer(layer, context={'request': request})
            return Response(serializer.data)
        except Layer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Layer exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Layer
        '''
        try:
            layer = Layer.objects.get(item=item, name=name)
            serializer = LayerSerializer(layer, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_layer_name = layer.name
                new_layer_name = request.data['label'].replace(" ", "")
                if old_layer_name != new_layer_name:
                    try:
                        Layer.objects.get(item=item, name=new_layer_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate Layer within the same Item."})
                    except:
                        pass
                serializer.save(name=new_layer_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Layer.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Layer
        '''
        try:
            layer = Layer.objects.get(item=item, name=name)
            layer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this Layer within the Item."})
        except Layer.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class SearchLayerViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Layers to be searched
    '''
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Layers matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            layers = Layer.objects(**query)
            if layers:
                serializer = EmbeddedLayerSerializer(layers, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Layer.DoesNotExist
        except Layer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Layers found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
