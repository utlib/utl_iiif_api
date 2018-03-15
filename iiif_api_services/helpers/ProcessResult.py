from datetime import datetime
from django.conf import settings
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity


def process_result(response, queue_activity):
    queue_id, activity_id = queue_activity.split("_")

    # Update response with errors in nested children to be consistent with error response in parent
    if response["status"] >= 400:
        while "data" in response["data"] or "error" in response["data"]:
            if "data" in response["data"]:
                response["data"] = response["data"]["data"]
            else:
                response["data"] = response["data"]["error"]
        response["data"] = {"error": response["data"]}

    if queue_id:
        try:  # Delete the queue
            Queue.objects.get(id=queue_id).delete()
        except Exception:  # pragma: no cover
            pass

    try:  # Update the activity
        activity = Activity.objects.get(id=activity_id)
        activity.responseBody = response["data"]
        activity.responseCode = response["status"]
        activity.endTime = datetime.now()
        activity.queueID = queue_id
        activity.save()
    except Exception:
        pass  # pragma: no cover

    return {"status": response["status"], "data": response["data"]}
