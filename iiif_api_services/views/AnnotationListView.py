import json
from datetime import datetime
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.views.AnnotationView import AnnotationViewSet
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity
from iiif_api_services.views.BackgroundProcessing import viewAnnotationList, createAnnotationList, updateAnnotationList, destroyAnnotationList
if settings.QUEUE_RUNNER=="PROCESS":
    from multiprocessing import Process as Runner
elif settings.QUEUE_RUNNER=="THREAD":
    from threading import Thread as Runner


def initializeNewBulkActions():
    return {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}



class AnnotationListViewSet(ViewSet):
    # GET /:identifier/annotationList
    def list(self, request, identifier=None, format=None):
        try:
            annotationLists = AnnotationList.objects(identifier=identifier)
            if annotationLists:
                annotationListsSerializer = AnnotationListEmbeddedSerializer(annotationLists, context={'request': request}, many=True)
                return Response(annotationListsSerializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Item with name '" + identifier + "' does not exist."})           
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 


    # GET /:identifier/annotationList/:name
    def retrieve(self, request, identifier=None, name=None, format=None):
        try:
            annotationList = AnnotationList.objects.get(identifier=identifier, name=name)
            return Response(viewAnnotationList(annotationList))
        except AnnotationList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "AnnotationList with name '" + name + "' does not exist in identifier '" + identifier + "'."}) 
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    def createBackground(self, request, identifier=None, format=None):
        try:
            requestBody = json.loads(request.body)["annotationList"]
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_POST_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.requestBody = requestBody
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=createAnnotationList, args=(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())).start()
                else:
                    createAnnotationList.delay(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.requestBody = requestBody
                activity.save()
                result = createAnnotationList(user, identifier, requestBody, False, None, str(activity.id), initializeNewBulkActions())
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 


    def updateBackground(self, request, identifier=None, name=None, format=None):
        try:
            requestBody = json.loads(request.body)["annotationList"]
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_PUT_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.requestBody = requestBody
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=updateAnnotationList, args=(user, identifier, name, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())).start()
                else:
                    updateAnnotationList.delay(user, identifier, name, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.requestBody = requestBody
                activity.save()
                result = updateAnnotationList(user, identifier, name, requestBody, False, None, str(activity.id), initializeNewBulkActions())
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 


    def destroyBackground(self, request, identifier=None, name=None, format=None):
        try:
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_DELETE_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=destroyAnnotationList, args=(user, identifier, name, False, str(queue.id), str(activity.id))).start()
                else:
                    destroyAnnotationList.delay(user, identifier, name, False, str(queue.id), str(activity.id))
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.save()
                result = destroyAnnotationList(user, identifier, name, False, None, str(activity.id))
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})

        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 

