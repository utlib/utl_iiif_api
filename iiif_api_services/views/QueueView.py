from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from iiif_api_services.serializers.QueueSerializer import *
from iiif_api_services.serializers.ActivitySerializer import *


class QueueViewSet(ViewSet):

    # GET /queue/:id
    def retrieve(self, request, id=None, format=None):
        try:
            queue = Queue.objects.get(id=id)
            queueSerializer = QueueSerializer(queue, context={'request': request})
            return Response(queueSerializer.data)
        except Queue.DoesNotExist:
            # Try to find the queue id in Activity
            try: 
                activity = Activity.objects.get(queueID=id)
                activitySerializer = ActivitySerializer(activity, context={'request': request})
                return Response(activitySerializer.data, status=status.HTTP_301_MOVED_PERMANENTLY)
            except Activity.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Queue with id '" + id + "' does not exist."}) 
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /queue 
    def viewAll(self, request, format=None):
        try:
            query = {}
            searchQuery = request.GET
            for key, val in searchQuery.items():
                if ("=" in key): # pragma: no cover
                    val = key.split("=")[1] if len(key.split("=")) > 1 else ""
                    key = key.split("=")[0]
                query[key.strip()+'__istartswith'] = val.strip()
            serializer = QueueSerializer(Queue.objects(**query).order_by('-id'), context={'request': request}, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e.message)})
