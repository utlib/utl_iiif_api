from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from iiif_api_services.serializers.QueueSerializer import *
from iiif_api_services.serializers.ActivitySerializer import *
from iiif_api_services.helpers.ProcessSearchQuery import process_search_query


class QueueViewSet(ViewSet):

    # GET /queue/:id
    def retrieve(self, request, id=None, format=None):
        try:
            queue = Queue.objects.get(id=id)
            queue_serializer = QueueSerializer(
                queue, context={'request': request})
            return Response(queue_serializer.data)
        except Queue.DoesNotExist:
            try:  # Try to find the queue id in Activity
                activity = Activity.objects.get(queueID=id)
                activity_serializer = ActivitySerializer(
                    activity, context={'request': request})
                return Response(activity_serializer.data, status=status.HTTP_301_MOVED_PERMANENTLY)
            except Activity.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Queue with id '" + id + "' does not exist."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /queue
    def view_all(self, request, format=None):
        try:
            query = process_search_query(request.GET)
            serializer = QueueSerializer(Queue.objects(
                **query).order_by('-id'), context={'request': request}, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e.message)})
