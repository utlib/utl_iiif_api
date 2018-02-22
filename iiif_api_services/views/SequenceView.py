from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status


class SequenceViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Sequences to be created, viewed, edited or deleted
    '''
    serializer_class = SequenceSerializer
    queryset = Sequence.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Sequence for this item
        '''
        try:
            name = request.data['label'].replace(" ", "")
            sequence = Sequence.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Sequence name already exist in this item."})
        except:
            data = request.data
            serializer = SequenceSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                name = request.data['label'].replace(" ", "")
                serializer.save(name=name, item=item)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all Sequences in this item
        '''
        try:
            sequence = Sequence.objects(item=item)
            if sequence:
                serializer = EmbeddedSequenceSerializer(sequence, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Sequence to Update or Delete
        '''
        try:
            sequence = Sequence.objects.get(item=item, name=name)
            serializer = SequenceSerializer(sequence, context={'request': request})
            return Response(serializer.data)
        except Sequence.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Sequence exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Sequence
        '''
        try:
            sequence = Sequence.objects.get(item=item, name=name)
            serializer = SequenceSerializer(sequence, data=request.data, context={'request': request})
            if serializer.is_valid():
                old_sequence_name = sequence.name
                new_sequence_name = request.data['label'].replace(" ", "")
                if old_sequence_name != new_sequence_name:
                    try:
                        Sequence.objects.get(item=item, name=new_sequence_name)
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Cannot create a duplicate Sequence within the same Item."})
                    except:
                        pass
                serializer.save(name=new_sequence_name, item=item)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Sequence.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error', e.message})




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Sequence
        '''
        try:
            sequence = Sequence.objects.get(item=item, name=name)
            sequence.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this Sequence within the Item."})
        except Sequence.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class SearchSequenceViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Sequences to be searched
    '''
    queryset = Sequence.objects.all()
    serializer_class = SequenceSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Sequences matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            sequences = Sequence.objects(**query)
            if sequences:
                serializer = EmbeddedSequenceSerializer(sequences, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Sequence.DoesNotExist
        except Sequence.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Sequences found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
