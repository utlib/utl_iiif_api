import json
from datetime import datetime
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.views.SequenceView import SequenceViewSet
from iiif_api_services.views.RangeView import RangeViewSet
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity
from iiif_api_services.views.BackgroundProcessing import viewManifest, createManifest, updateManifest, destroyManifest
if settings.QUEUE_RUNNER=="PROCESS":
    from multiprocessing import Process as Runner
elif settings.QUEUE_RUNNER=="THREAD":
    from threading import Thread as Runner



def initializeNewBulkActions():
    return {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}



class ManifestViewSet(ViewSet):
    # GET /:identifier/manifest
    def retrieve(self, request, identifier=None, format=None):
        try:
            manifest = Manifest.objects.get(identifier=identifier)
            return Response(viewManifest(manifest))
        except Manifest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "'" + identifier + "' does not have a Manifest."}) 
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    def createBackground(self, request, identifier=None, format=None):
        try:
            requestBody = json.loads(request.body)["manifest"]
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_POST_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.requestBody = requestBody
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=createManifest, args=(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())).start()
                else:
                    createManifest.delay(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.requestBody = requestBody
                activity.save()
                result = createManifest(user, identifier, requestBody, False, None, str(activity.id), initializeNewBulkActions())
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 


    def updateBackground(self, request, identifier=None, format=None):
        try:
            requestBody = json.loads(request.body)["manifest"]
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_PUT_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.requestBody = requestBody
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=updateManifest, args=(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())).start()
                else:
                    updateManifest.delay(user, identifier, requestBody, False, str(queue.id), str(activity.id), initializeNewBulkActions())
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.requestBody = requestBody
                activity.save()
                result = updateManifest(user, identifier, requestBody, False, None, str(activity.id), initializeNewBulkActions())
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 


    def destroyBackground(self, request, identifier=None, format=None):
        try:
            activity = Activity(username=request.user.username, requestPath=request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR'], startTime=datetime.now())
            user = request.user.to_mongo()
            del user["_id"]
            if settings.QUEUE_DELETE_ENABLED:
                queue = Queue(status="Pending", activity=activity.to_mongo()).save()
                activity.save()
                if settings.QUEUE_RUNNER != "CELERY":
                    Runner(target=destroyManifest, args=(user, identifier, False, str(queue.id), str(activity.id))).start()
                else:
                    destroyManifest.delay(user, identifier, False, str(queue.id), str(activity.id))
                return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
            else:
                activity.save()
                result = destroyManifest(user, identifier, False, None, str(activity.id))
                return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 

