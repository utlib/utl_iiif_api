from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from iiif_api_services.serializers.ActivitySerializer import *
from rest_framework import permissions
from datetime import datetime
from datetime import timedelta


class CustomActivityPermission(permissions.BasePermission):
    message ="You don't have the necessary permission to perform this action. Please contact your admin."

    def has_permission(self, request, view):
        if request.method=="DELETE":
            return (request.user and request.user.is_superuser)
        else:
            return True


class ActivityViewSet(ViewSet):

    permission_classes = (CustomActivityPermission, )

    # GET /discovery or /discovery-n
    def discovery(self, request, page=None, format=None, dateRange=None):
        try:
            if dateRange:
                try:
                    dataRangeQueryText = "/?from=" + dateRange[0] + "&to=" + dateRange[1]
                    fromDate = datetime.strptime(dateRange[0], '%Y-%m-%d')
                    toDate = datetime.strptime(dateRange[1], '%Y-%m-%d') + timedelta(days=1)
                    activities = Activity.objects(endTime__lte=toDate, endTime__gte=fromDate, responseCode__lt=300).order_by('-id')
                except Exception:
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The date range query format is invalid."})
            else:
                activities = Activity.objects(responseCode__lt=300).order_by('-id')
            context = ["http://iiif.io/api/presentation/3/context.json", "https://www.w3.org/ns/activitystreams"]
            total = activities.count()
            lastPage = (total + 20 -1) // 20
            if page:
                # Construct a specific Collection Page
                if int(page[1:]) == 0: # Page number must be grater than 0
                    return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Discovery with page '0' does not exist."})
                if int(page[1:]) > lastPage: # Requested page is out of range
                    return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Discovery with page '"+page[1:]+"' does not exist."})
                type = "CollectionPage"
                if dateRange:
                    id = settings.IIIF_BASE_URL + "/discovery" + page + dataRangeQueryText
                    partOf = {"id": settings.IIIF_BASE_URL +
                              "/discovery" + dataRangeQueryText, "type": "Collection"}
                else:
                    id = settings.IIIF_BASE_URL + "/discovery" + page
                    partOf = {"id": settings.IIIF_BASE_URL + "/discovery", "type": "Collection"}
                label = "University of Toronto IIIF Discovery Collection: Page" + page
                first = None
                last = None
                if dateRange:
                    next = {"id": settings.IIIF_BASE_URL + "/discovery-" + str(int(
                        page[1:]) + 1) + dataRangeQueryText, "type": "CollectionPage"} if int(page[1:]) + 1 <= lastPage else None
                else:
                    next = {"id": settings.IIIF_BASE_URL + "/discovery-" + str(int(page[1:]) + 1), "type": "CollectionPage"} if int(page[1:]) + 1 <= lastPage else None

                items = []
                methodMapping = {"POST": "Create", "PUT": "Update", "DELETE": "Delete"}
                # Get only the required (20 or less) acitivites that belong to this page sorted by endTime. 
                startIndex = (int(page[1:])-1)*20
                endIndex = startIndex + 20
                if activities:
                    activities = activities[startIndex:endIndex]
                else:
                    activities = Activity.objects(responseCode__lt=300)[startIndex:endIndex]  # pragma: no cover
                for activity in activities:
                    items.append({
                        "id": settings.IIIF_BASE_URL + "/activity/" + str(activity.id),
                        "type": methodMapping[activity.requestMethod],
                        "object": {
                            "id": activity.responseBody["@id"],
                            "type": activity.responseBody["@type"]
                        },
                        "actor": activity.username,
                        "startTime": activity.startTime,
                        "endTime": activity.endTime
                    })
                count = len(items)
            else:
                # Construct the Top Level Discovery Collection
                type = "Collection"
                if dateRange:
                    id = settings.IIIF_BASE_URL + "/discovery" + dataRangeQueryText
                else:
                    id = settings.IIIF_BASE_URL + "/discovery"
                partOf = None
                label = "University of Toronto IIIF Discovery Collection"
                total = total
                count = None
                if dateRange:
                    first = {"id": settings.IIIF_BASE_URL + "/discovery-1" +
                             dataRangeQueryText, "type": "CollectionPage"}
                    last = {"id": settings.IIIF_BASE_URL + "/discovery-" +
                            str(lastPage) + dataRangeQueryText, "type": "CollectionPage"}
                else:
                    first = {"id": settings.IIIF_BASE_URL +"/discovery-1", "type": "CollectionPage"}
                    last = {"id": settings.IIIF_BASE_URL + "/discovery-" +str(lastPage), "type": "CollectionPage"}
                next = None
                items = None
                if lastPage==0:
                     last = first
                if (first["id"]==last["id"]):
                    last = {}
                if (total==0):
                    first = {}
            # Render the reponse
            Discovery = {
                "@context": context,
                "id": id,
                "type": type,
                "partOf": partOf,
                "label": label,
                "total": total,
                "count": count,
                "first": first,
                "last": last,
                "next": next,
                "items": items
            }
            return Response(status=status.HTTP_200_OK, data=Discovery)
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})



    # GET /discovery/?from=2017-01-01&to=2017-01-25
    def discoveryDateRange(self, request, page=None, format=None):
        try:
            searchQuery = request.GET
            if searchQuery:
                fromDate = searchQuery["from"]
                toDate = searchQuery["to"]
                return self.discovery(request, page=page, format=None, dateRange=[fromDate, toDate])
            else:
                return self.discovery(request, page=page, format=None)
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})



    # GET /activity/:id
    def activity(self, request, id=None, format=None):
        try:
            activity = Activity.objects.get(id=id)
            activitySerializer = ActivitySerializer(activity, context={'request': request})
            return Response(activitySerializer.data)
        except Activity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Activity with id '" + id + "' does not exist."}) 
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    # GET /activity 
    def viewAll(self, request, format=None):
        try:
            query = {}
            searchQuery = request.GET
            for key, val in searchQuery.items():
                if ("=" in key): # pragma: no cover
                    val = key.split("=")[1] if len(key.split("=")) > 1 else ""
                    key = key.split("=")[0]
                query[key.strip()+'__istartswith'] = val.strip()
            serializer = ActivityEmbeddedSerializer(Activity.objects(**query).order_by('-id'), context={'request': request}, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e.message)})



    # DELETE /activity/:id
    def delete(self, request, id=None, format=None):
        try:
            activity = Activity.objects.get(id=id)
            activity.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted the Activity with id '" + id + "'."})
        except Activity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Activity with id '" + id + "' does not exist."}) 
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    # DELETE /activity
    def deleteAll(self, request, format=None):
        try:
            Activity.objects.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted all Activities."})
        except Exception as e: # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})