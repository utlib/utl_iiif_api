import json
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity
if settings.QUEUE_RUNNER=="THREAD":
    from threading import Thread as Runner
else:
    from multiprocessing import Process as Runner


def initialize_new_bulk_actions():
    return {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}


def process_create_or_update_request(request, create_or_update_function, request_top_level_key, identifier=None, name=None):
    try:
      request_body = json.loads(request.body)[request_top_level_key]
      # Create the Activity object
      activity = Activity(username=request.user.username, requestPath=settings.IIIF_BASE_URL+request.get_full_path(), requestBody=request_body, requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR']).save()
      user = request.user.to_mongo()
      del user["_id"] # Mongo ObjectID is not serializable
      request_body["identifier"], request_body["name"] = identifier, name # Include these url fields with the requestBody
      if (request.method == "POST" and settings.QUEUE_POST_ENABLED) or (request.method == "PUT" and settings.QUEUE_PUT_ENABLED):
          queue = Queue(status="Pending", activity=activity.to_mongo()).save() # Create the Queue object
          queue_activity = "{0}_{1}".format(queue.id, activity.id) # link the Queue and Activity object
          queue_status_url = "{0}/queue/{1}".format(settings.IIIF_BASE_URL, queue.id) # Get the Queue status url
          if settings.QUEUE_RUNNER != "CELERY": # Either 'PROCESS' or 'THREAD' imported as 'Runner'
              Runner(target=create_or_update_function, args=(user, request_body, False, queue_activity, initialize_new_bulk_actions())).start()
          else:
              create_or_update_function.delay(user, request_body, False, queue_activity, initialize_new_bulk_actions())
          return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": queue_status_url})
      else:
          result = create_or_update_function(user, request_body, False, "_"+str(activity.id), initialize_new_bulk_actions())
          return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
    except Exception as e: # pragma: no cover
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 
            

def process_delete_request(request, delete_function, identifier="", name=""):
    try:
        activity = Activity(username=request.user.username, requestPath=settings.IIIF_BASE_URL+request.get_full_path(), requestMethod=request.method, remoteAddress=request.META['REMOTE_ADDR']).save()
        user = request.user.to_mongo()
        del user["_id"] # Mongo ObjectID is not serializable
        if settings.QUEUE_DELETE_ENABLED:
            queue = Queue(status="Pending", activity=activity.to_mongo()).save() # Create the Queue object
            queue_activity = "{0}_{1}".format(queue.id, activity.id) # link the Queue and Activity object
            if settings.QUEUE_RUNNER != "CELERY": # Either 'PROCESS' or 'THREAD' imported as 'Runner'
                Runner(target=delete_function, args=(user, identifier+"__"+name, queue_activity)).start()
            else:
                delete_function.delay(user, identifier+"__"+name, queue_activity)
            return Response(status=status.HTTP_202_ACCEPTED, data={'message': "Request Accepted", "status": settings.IIIF_BASE_URL + '/queue/' + str(queue.id)})
        else:
            result = delete_function(user, identifier+"__"+name, "_"+str(activity.id))
            return Response(status=result["status"], data={"responseBody": result["data"], "responseCode": result["status"]})
    except Exception as e: # pragma: no cover
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': e.message}) 
