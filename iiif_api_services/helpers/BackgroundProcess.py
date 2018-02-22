from datetime import datetime
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity

def process_result(response, activityID, queueID):
    # Update reponse to be consistent with Queueing and Non-Queueing responses
    if response["status"] >= 400:
        while "data" in response["data"] or "error" in response["data"]:
            if "data" in response["data"]:
                response["data"] = response["data"]["data"]
            else:
                response["data"] = response["data"]["error"]
        response["data"] = {"error": response["data"]}
    if queueID:
        try: # Delete the queue
            Queue.objects.get(id=queueID).delete()
        except Exception: # pragma: no cover
            pass
    try: # Update the activity
        activity = Activity.objects.get(id=activityID)
        activity.responseBody = response["data"]
        activity.responseCode = response["status"]
        activity.endTime = datetime.now()
        activity.queueID = queueID
        activity.save()
    except Exception: # pragma: no cover
        pass
    return {"status": response["status"], "data": response["data"]}
