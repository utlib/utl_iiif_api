from iiif_api_services.serializers.ResourceSerializer import *
from iiif_api_services.models import *
from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from rest_framework import status
import os

class ResourceViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows Resource to be created, viewed, edited or deleted
    '''
    serializer_class = ResourceSerializer
    queryset = Resource.objects.all()
    pagination_class = None


    def create(self, request, item=None, format=None):
        '''
        Create a Resource for this item
        '''
        try:
            name = request.data['resource'].name
            resource = Resource.objects.get(item=item, name=name)
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Resource name already exist in this item."})
        except:
            data = request.data
            serializer = ResourceSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                res_url = request.data['res_url']
                if request.data['resource']:
                    name = request.data['resource'].name
                    content_type = request.data['resource'].content_type
                    # Upload the Resource to Loris if the image type is "dctypes:Image"
                    res_url = None
                    if request.data['type'] == "dctypes:Image":
                        res_url = _handle_loris_upload(request, name, item)
                else: # No Resource was uploaded, use the given res_url.
                    name = request.data['res_url'].split("/")[-1]
                    if not name: # Assign a custom name for the resource if no res_url was given
                        no_of_resources_in_this_item = Resource.objects.filter(item=item).count()
                        name = item+"_"+str(no_of_resources_in_this_item+1)
                    content_type = request.data['format']
                     
                serializer.save(name=name, item=item, format=content_type, res_url=res_url)
                return self.retrieve(request, item=item, name=name, format=format)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def list(self, request, item=None, format=None):
        '''
        View all Resources in this item
        '''
        try:
            resource = Resource.objects(item=item)
            if resource:
                serializer = EmbeddedResourceSerializer(resource, context={'request': request}, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Item exist."})           
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 



    def retrieve(self, request, item=None, name=None, format=None):
        '''
        View this Resource to Update or Delete
        '''
        self.serializer_class = ResourceSerializerView
        try:
            resource = Resource.objects.get(item=item, name=name)
            serializer = ResourceSerializerView(resource, context={'request': request})
            return Response(serializer.data)
        except Resource.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No such Resource exist in this item."})
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 




    def update(self, request, item=None, name=None, format=None):
        '''
        Update this Resource
        '''
        self.serializer_class = ResourceSerializerView
        try:
            resource = Resource.objects.get(item=item, name=name)
            serializer = ResourceSerializerView(resource, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Resource.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message})




    def destroy(self, request, item=None, name=None, format=None):
        '''
        Delete this Resource
        '''
        self.serializer_class = ResourceSerializerView
        try:
            resource = Resource.objects.get(item=item, name=name)
            resource.delete()
            return Response(status=status.HTTP_204_NO_CONTENT, data={'message': "Sucessfully deleted this Resource within the Item."})
        except Resource.DoesNotExist:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "Item does not exist"})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)



def _handle_loris_upload(request, name, item):
    directory = '/home/rajakumaj/Pictures/loris/iiifAPI/' + item
    if not os.path.exists(directory):
        os.makedirs(directory)
    path = os.path.join(directory, name)
    file = open(path, 'wb')
    resource_file = request.data['resource']
    resource_file.seek(0)
    while 1:
        data = resource_file.read(2<<16)
        if not data:
            break
        file.write(data)
    file.close()
    res_url = 'http://localhost/loris/iiifAPI/' + item + '/' + name
    return res_url



class SearchResourceViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows Resources to be searched
    '''
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    pagination_class = None

    def retrieve(self, request, query=None, format=None):
        '''
        Search for Resources matching the query
        '''
        try:
            fields = query.split("&")
            query = {}
            for field in fields:
                q = field.split("=")
                query[q[0].strip()+'__icontains'] = q[1].strip()
            resources = Resource.objects(**query)
            if resources:
                serializer = EmbeddedResourceSerializer(resources, context={'request': request}, many=True)
                return Response(serializer.data)
            raise Resource.DoesNotExist
        except Resource.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No Resources found matching the query."})
        except IndexError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "The search query format is invalid."})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 
