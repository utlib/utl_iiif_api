from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class RangeViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Range to be created, viewed, edited or deleted
    '''
    serializer_class = RangeSerializer
    queryset = Range.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Range for this item
        '''
        try:
            name = request.data['label'].replace(" ", "")
            range = Range.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Range name already exist in this item."})
        except:
            data = request.data
            serializer = RangeSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all Ranges in this item
        '''
        try:
            range = Range.objects(item=item)
            if range:
                serializer = EmbeddedRangeSerializer(range, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Range to Update or Delete
        '''
        try:
            range = Range.objects.get(item=item, name=name)
            serializer = RangeSerializer(range, context={'request': request})
            return Response(serializer.data)
        except Range.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Range exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Range
        '''
        try:
            range = Range.objects.get(item=item, name=name)
            serializer = RangeSerializer(range, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_range_name = range.name
                new_range_name = request.data['label'].replace(" ", "")
                if old_range_name != new_range_name:
                    try:
                        Range.objects.get(item=item, name=new_range_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate Range within the same Item."})
                    except:
                        pass
                serializer.save(name=new_range_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Range.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Range
        '''
        try:
            range = Range.objects.get(item=item, name=name)
            range.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this Range within the Item."})
        except Range.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




class SearchRangeViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Ranges to be searched
    '''
    queryset = Range.objects.all()
    serializer_class = RangeSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Ranges matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            ranges = Range.objects(**query)
            if ranges:
                serializer = EmbeddedRangeSerializer(ranges, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Range.DoesNotExist
        except Range.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Ranges found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
