from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from iiif_api_services.serializers.ActivitySerializer import ActivitySerializer, ActivityEmbeddedSerializer
from iiif_api_services.models.ActivityModel import Activity
from rest_framework import permissions
from datetime import datetime
from datetime import timedelta
from iiif_api_services.helpers.ProcessSearchQuery import process_search_query


class CustomActivityPermission(permissions.BasePermission):
    message = "You don't have the necessary permission to perform this action. Please contact your admin."

    def has_permission(self, request, view):
        if request.method == "DELETE":
            return (request.user and request.user.is_superuser)
        else:
            return True


class ActivityViewSet(ViewSet):

    permission_classes = (CustomActivityPermission, )

    # GET /discovery or /discovery-n
    def discovery(self, request, page=None, format=None, date_range=None):
        try:
            if date_range:
                try:
                    data_range_query_text = "/?from=" + \
                        date_range[0] + "&to=" + date_range[1]
                    from_date = datetime.strptime(date_range[0], '%Y-%m-%d')
                    to_date = datetime.strptime(
                        date_range[1], '%Y-%m-%d') + timedelta(days=1)
                    activities = Activity.objects(
                        endTime__lte=to_date, endTime__gte=from_date, responseCode__lt=300).order_by('-id')
                except Exception:
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "The date range query format is invalid."})
            else:
                activities = Activity.objects(
                    responseCode__lt=300).order_by('-id')
            context = ["http://iiif.io/api/presentation/3/context.json",
                       "https://www.w3.org/ns/activitystreams"]
            total = activities.count()
            last_page = (total + 20 - 1) // 20
            if page:
                # Construct a specific Collection Page
                if int(page[1:]) == 0:  # Page number must be grater than 0
                    return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Discovery with page '0' does not exist."})
                if int(page[1:]) > last_page:  # Requested page is out of range
                    return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Discovery with page '"+page[1:]+"' does not exist."})
                type = "CollectionPage"
                if date_range:
                    id = settings.IIIF_BASE_URL + "/discovery" + page + data_range_query_text
                    part_of = {"id": settings.IIIF_BASE_URL +
                               "/discovery" + data_range_query_text, "type": "Collection"}
                else:
                    id = settings.IIIF_BASE_URL + "/discovery" + page
                    part_of = {"id": settings.IIIF_BASE_URL +
                               "/discovery", "type": "Collection"}
                label = "{0} IIIF Discovery Collection: Page{1}".format(
                    settings.TOP_LEVEL_COLLECTION_LABEL, page)
                first = None
                last = None
                if date_range:
                    next = {"id": settings.IIIF_BASE_URL + "/discovery-" + str(int(
                        page[1:]) + 1) + data_range_query_text, "type": "CollectionPage"} if int(page[1:]) + 1 <= last_page else None
                else:
                    next = {"id": settings.IIIF_BASE_URL + "/discovery-" + str(int(
                        page[1:]) + 1), "type": "CollectionPage"} if int(page[1:]) + 1 <= last_page else None

                items = []
                method_mapping = {"POST": "Create",
                                  "PUT": "Update", "DELETE": "Delete"}
                # Get only the required (20 or less) activities that belong to this page sorted by endTime.
                start_index = (int(page[1:])-1)*20
                end_index = start_index + 20
                if activities:
                    activities = activities[start_index:end_index]
                else:
                    activities = Activity.objects(responseCode__lt=300)[
                        start_index:end_index]  # pragma: no cover
                for activity in activities:
                    items.append({
                        "id": settings.IIIF_BASE_URL + "/activity/" + str(activity.id),
                        "type": method_mapping[activity.requestMethod],
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
                if date_range:
                    id = settings.IIIF_BASE_URL + "/discovery" + data_range_query_text
                else:
                    id = settings.IIIF_BASE_URL + "/discovery"
                part_of = None
                label = "{0} IIIF Discovery Collection".format(
                    settings.TOP_LEVEL_COLLECTION_LABEL)
                count = None
                if date_range:
                    first = {"id": settings.IIIF_BASE_URL + "/discovery-1" +
                             data_range_query_text, "type": "CollectionPage"}
                    last = {"id": settings.IIIF_BASE_URL + "/discovery-" +
                            str(last_page) + data_range_query_text, "type": "CollectionPage"}
                else:
                    first = {"id": settings.IIIF_BASE_URL +
                             "/discovery-1", "type": "CollectionPage"}
                    last = {"id": settings.IIIF_BASE_URL + "/discovery-" +
                            str(last_page), "type": "CollectionPage"}
                next = None
                items = None
                if last_page == 0:
                    last = first
                if (first["id"] == last["id"]):
                    last = {}
                if (total == 0):
                    first = {}
            # Render the response
            discovery = {
                "@context": context,
                "id": id,
                "type": type,
                "partOf": part_of,
                "label": label,
                "total": total,
                "count": count,
                "first": first,
                "last": last,
                "next": next,
                "items": items
            }
            return Response(status=status.HTTP_200_OK, data=discovery)
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /discovery/?from=2017-01-01&to=2017-01-25
    def discovery_date_range(self, request, page=None, format=None):
        try:
            search_query = request.GET
            if search_query:
                from_date = search_query["from"]
                to_date = search_query["to"]
                return self.discovery(request, page=page, format=None, date_range=[from_date, to_date])
            else:
                return self.discovery(request, page=page, format=None)
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /activity/:id
    def activity(self, request, id=None, format=None):
        try:
            activity = Activity.objects.get(id=id)
            activity_serializer = ActivitySerializer(
                activity, context={'request': request})
            return Response(activity_serializer.data)
        except Activity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Activity with id '" + id + "' does not exist."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /activity
    def view_all(self, request, format=None):
        try:
            query = process_search_query(request.GET)
            serializer = ActivityEmbeddedSerializer(Activity.objects(
                **query).order_by('-id'), context={'request': request}, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e.message)})

    # DELETE /activity/:id
    def delete(self, request, id=None, format=None):
        try:
            activity = Activity.objects.get(id=id)
            activity.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted the Activity with id '" + id + "'."})
        except Activity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "Activity with id '" + id + "' does not exist."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # DELETE /activity
    def delete_all(self, request, format=None):
        try:
            Activity.objects.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted all Activities."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})
