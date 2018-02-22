from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class AnnotationViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Annotation to be created, viewed, edited or deleted
    '''
    serializer_class = AnnotationSerializer
    queryset = Annotation.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Annotation for this item
        '''
        try:
            name = request.data['label'].replace(" ", "")
            annotation = Annotation.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Annotation name already exist in this item."})
        except:
            data = request.data
            serializer = AnnotationSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all Annotations in this item
        '''
        try:
            annotation = Annotation.objects(item=item)
            if annotation:
                serializer = EmbeddedAnnotationSerializer(annotation, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Annotation to Update or Delete
        '''
        try:
            annotation = Annotation.objects.get(item=item, name=name)
            serializer = AnnotationSerializer(annotation, context={'request': request})
            return Response(serializer.data)
        except Annotation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Annotation exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Annotation
        '''
        try:
            annotation = Annotation.objects.get(item=item, name=name)
            serializer = AnnotationSerializer(annotation, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_annotation_name = annotation.name
                new_annotation_name = request.data['label'].replace(" ", "")
                if old_annotation_name != new_annotation_name:
                    try:
                        Annotation.objects.get(item=item, name=new_annotation_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate Annotation within the same Item."})
                    except:
                        pass
                serializer.save(name=new_annotation_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Annotation.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Annotation
        '''
        try:
            annotation = Annotation.objects.get(item=item, name=name)
            annotation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this Annotation within the Item."})
        except Annotation.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class SearchAnnotationViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Annotations to be searched
    '''
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Annotations matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            annotations = Annotation.objects(**query)
            if annotations:
                serializer = EmbeddedAnnotationSerializer(annotations, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Annotation.DoesNotExist
        except Annotation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Annotations found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
