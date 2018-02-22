from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class CanvasViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Canvas to be created, viewed, edited or deleted
    '''
    serializer_class = CanvasSerializer
    queryset = Canvas.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Canvas for this item. \n
        #### Error Codes
        * `200` **Success** The Canvas was successfully created. \n
        * `400` **Client Error** The data sent has validation errors. \n
        * `500` **Server Error** Internal Server Error.
        '''
        try:
            name = request.data['label'].replace(" ", "")
            canvas = Canvas.objects.get(item=item, name=name)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Canvas name already exist in this item."})
        except Canvas.DoesNotExist:
            data = request.data
            serializer = CanvasSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': "Internal Server Error."})



    def list(self, request, item=None, format=None):
        '''
        View all Canvass in this item
        '''
        try:
            canvas = Canvas.objects(item=item)
            if canvas:
                serializer = EmbeddedCanvasSerializer(canvas, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Canvas to Update or Delete
        '''
        try:
            canvas = Canvas.objects.get(item=item, name=name)
            serializer = CanvasSerializer(canvas, context={'request': request})
            return Response(serializer.data)
        except Canvas.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Canvas exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Canvas
        '''
        try:
            canvas = Canvas.objects.get(item=item, name=name)
            serializer = CanvasSerializer(canvas, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_canvas_name = canvas.name
                new_canvas_name = request.data['label'].replace(" ", "")
                if old_canvas_name != new_canvas_name:
                    try:
                        Canvas.objects.get(item=item, name=new_canvas_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate Canvas within the same Item."})
                    except:
                        pass
                serializer.save(name=new_canvas_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Canvas.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Canvas
        '''
        try:
            canvas = Canvas.objects.get(item=item, name=name)
            canvas.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Successfully deleted this Canvas within the Item."})
        except Canvas.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class SearchCanvasViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Canvass to be searched
    '''
    queryset = Canvas.objects.all()
    serializer_class = CanvasSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Canvass matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            canvases = Canvas.objects(**query)
            if canvases:
                serializer = EmbeddedCanvasSerializer(canvases, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Canvas.DoesNotExist
        except Canvas.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Canvass found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
