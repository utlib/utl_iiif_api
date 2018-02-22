from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class AnnotationListViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows AnnotationList to be created, viewed, edited or deleted
    '''
    serializer_class = AnnotationListSerializer
    queryset = AnnotationList.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a AnnotationList for this item
        '''
        try:
            name = request.data['label'].replace(" ", "")
            annotationlist = AnnotationList.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "AnnotationList name already exist in this item."})
        except:
            data = request.data
            serializer = AnnotationListSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all AnnotationLists in this item
        '''
        try:
            annotationlist = AnnotationList.objects(item=item)
            if annotationlist:
                serializer = EmbeddedAnnotationListSerializer(annotationlist, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this AnnotationList to Update or Delete
        '''
        try:
            annotationlist = AnnotationList.objects.get(item=item, name=name)
            serializer = AnnotationListSerializer(annotationlist, context={'request': request})
            return Response(serializer.data)
        except AnnotationList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such AnnotationList exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this AnnotationList
        '''
        try:
            annotationlist = AnnotationList.objects.get(item=item, name=name)
            serializer = AnnotationListSerializer(annotationlist, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_annotationlist_name = annotationlist.name
                new_annotationlist_name = request.data['label'].replace(" ", "")
                if old_annotationlist_name != new_annotationlist_name:
                    try:
                        AnnotationList.objects.get(item=item, name=new_annotationlist_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate AnnotationList within the same Item."})
                    except:
                        pass
                serializer.save(name=new_annotationlist_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AnnotationList.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this AnnotationList
        '''
        try:
            annotationlist = AnnotationList.objects.get(item=item, name=name)
            annotationlist.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this AnnotationList within the Item."})
        except AnnotationList.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




class SearchAnnotationListViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows AnnotationLists to be searched
    '''
    queryset = AnnotationList.objects.all()
    serializer_class = AnnotationListSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for AnnotationLists matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            annotationlists = AnnotationList.objects(**query)
            if annotationlists:
                serializer = EmbeddedAnnotationListSerializer(annotationlists, context={'request': request}, many=True)
                return Response(serializer.data)
            raise AnnotationList.DoesNotExist
        except AnnotationList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No AnnotationLists found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
