from django.conf.urls import url, include
from .views.CollectionView import CollectionViewSet
from .views.ManifestView import ManifestViewSet
from .views.SequenceView import SequenceViewSet
from .views.CanvasView import CanvasViewSet
from .views.AnnotationView import AnnotationViewSet
from .views.AnnotationListView import AnnotationListViewSet
from .views.RangeView import RangeViewSet
from .views.LayerView import LayerViewSet
from .views.SearchView import SearchViewSet
from .views.ImageUploadView import ImageUploadViewSet
from .views.ActivityView import ActivityViewSet
from .views.QueueView import QueueViewSet
from .views.AdminView import AdminView
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import verify_jwt_token
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from rest_framework.urlpatterns import format_suffix_patterns


def docs(request, path=''):
  """
  Render the interactive documentation
  """
  return render(request, 'docs.html')


def invalid_api_endpoint(request):
    """
    return an invalid endpoint response message
    """
    return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "This API endpoint is invalid."})


admin_register = AdminView.as_view({
    'post': 'createAdmin',
})

staff_list = AdminView.as_view({
    'post': 'createStaff',
    'get': 'viewStaffs',
})

staff_detail = AdminView.as_view({
    'put': 'updateStaff',
    'delete': 'deleteStaff',
})

update_permission = AdminView.as_view({
    'put': 'updatePermission',
})

collection_list = CollectionViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

collection_detail = CollectionViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


manifest_detail = ManifestViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
    'post': 'createBackground',
})


sequence_list = SequenceViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

sequence_detail = SequenceViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


canvas_list = CanvasViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

canvas_detail = CanvasViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


annotation_list = AnnotationViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

annotation_detail = AnnotationViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


annotationlist_list = AnnotationListViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

annotationlist_detail = AnnotationListViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


range_list = RangeViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

range_detail = RangeViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


layer_list = LayerViewSet.as_view({
    'get': 'list',
    'post': 'createBackground',
})

layer_detail = LayerViewSet.as_view({
    'get': 'retrieve',
    'put': 'updateBackground',
    'delete': 'destroyBackground',
})


discovery = ActivityViewSet.as_view({
    'get': 'discovery',
})

discoveryDateRange = ActivityViewSet.as_view({
    'get': 'discoveryDateRange',
})

activity = ActivityViewSet.as_view({
    'get': 'activity',
    'delete': 'delete',
})

activityDeleteAll = ActivityViewSet.as_view({
    'get': 'viewAll',
    'delete': 'deleteAll',
})

queue = QueueViewSet.as_view({
    'get': 'retrieve',
})

queueViewAll = QueueViewSet.as_view({
    'get': 'viewAll',
})

search = SearchViewSet.as_view({
    'get': 'retrieve',
})

iiifSearchWithinManifest = SearchViewSet.as_view({
    'get': 'iiifSearchWithinManifest',
})

imageUpload = ImageUploadViewSet.as_view({
    'post': 'uploadImage'    
})


urlpatterns = [
    # API Docs Endpoint
    url(r'^$', docs),

    # Auth Endpoints
    url(r'^auth/admin$', admin_register, name="user-register"),
    url(r'^auth/admin/updatePermission$', update_permission, name="update_permission"),
    url(r'^auth/staff$', staff_list, name="staff-list"),
    url(r'^auth/staff/(?P<id>[a-zA-Z0-9_:-]+)$', staff_detail, name="staff-details"),
    url(r'^login$', obtain_jwt_token, name="obtain-jwt-token"),
    url(r'^verifyToken$', verify_jwt_token),

    # Collection Endpoints
    url(r'^collections$', collection_list, name="collection-list"),
    url(r'^collection$', collection_list, name="collection-list"),
    url(r'^collections/(?P<name>[a-zA-Z0-9_:-]+)$', collection_detail, name="collection-detail"),
    url(r'^collection/(?P<name>[a-zA-Z0-9_:-]+)$', collection_detail, name="collection-detail"),

    # Manifest Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/manifest$', manifest_detail, name="manifest-detail"),

    # Sequence Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/sequence$', sequence_list, name="sequence-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/sequence/(?P<name>[a-zA-Z0-9_:-]+)$', sequence_detail, name="sequence-detail"),

    # Canvas Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/canvas$', canvas_list, name="canvas-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/canvas/(?P<name>[a-zA-Z0-9_:-=,\#]+)$', canvas_detail, name="canvas-detail"),

    # Annotation Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/annotation$', annotation_list, name="annotation-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/annotation/(?P<name>[a-zA-Z0-9_:-]+)$', annotation_detail, name="annotation-detail"),

    # Annotationlist Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/list$', annotationlist_list, name="annotationlist-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/list/(?P<name>[a-zA-Z0-9_:-]+)$', annotationlist_detail, name="annotationlist-detail"),

    # Range Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/range$', range_list, name="range-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/range/(?P<name>[a-zA-Z0-9_:-]+)$', range_detail, name="range-detail"),

    # Layer Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/layer$', layer_list, name="layer-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/layer/(?P<name>[a-zA-Z0-9_:-]+)$', layer_detail, name="layer-detail"),
   
    # Search Endpoint
    url(r'^search/(?P<type>[a-zA-Z0-9]+)/', search, name="search"),

    # Discovery Endpoint
    url(r'^discovery(?P<page>\s{0}|[-]{1}[0-9]+)$', discovery, name="discovery"),
    url(r'^discovery(?P<page>\s{0}|[-]{1}[0-9]+)/', discoveryDateRange, name="discoveryDateRange"),

    # Activity Endpoints
    url(r'^activity/(?P<id>[a-zA-Z0-9]+)$', activity, name="activity"),
    url(r'^activity$', activityDeleteAll, name="activityDeleteAll"),

    # Queue Endpoints
    url(r'^queue/(?P<id>[a-zA-Z0-9]+)$', queue, name="queue"),
    url(r'^queue$', queueViewAll, name="queueViewAll"),

    # Image Upload
    url(r'^images$', imageUpload, name="imageUpload"),

    # IIIF Search API Endpoint - Search Annotations within a Manifest
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/manifest/search/', iiifSearchWithinManifest, name="iiifSearchWithinManifest"),

    # Invalid Endpoint
    url(r'.*', invalid_api_endpoint),
]

urlpatterns = format_suffix_patterns(urlpatterns)

