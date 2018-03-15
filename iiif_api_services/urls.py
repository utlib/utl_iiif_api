from django.conf.urls import url, include
from iiif_api_services.views.IIIFView import CollectionViewSet
from iiif_api_services.views.IIIFView import ManifestViewSet
from iiif_api_services.views.IIIFView import GenericViewSet
from iiif_api_services.views.SearchView import SearchViewSet
from iiif_api_services.views.ImageUploadView import ImageUploadViewSet
from iiif_api_services.views.ActivityView import ActivityViewSet
from iiif_api_services.views.QueueView import QueueViewSet
from iiif_api_services.views.AdminView import AdminView
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import verify_jwt_token
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status
from rest_framework.urlpatterns import format_suffix_patterns


# Render the interactive documentation
def docs(request, path=''):
    return render(request, 'docs.html')


# Render an invalid endpoint response
def invalid_api_endpoint(request):
    return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "This API endpoint is invalid."})


generic_list = GenericViewSet.as_view({'get': 'list', 'post': 'create'})
generic_detail = GenericViewSet.as_view(
    {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})


urlpatterns = [
    # API Docs Endpoint
    url(r'^$', docs),

    # Auth Endpoints
    url(r'^auth/admin$',
        AdminView.as_view({'post': 'create_user'}), name="admin-register"),
    url(r'^auth/staff$',
        AdminView.as_view({'post': 'create_user', 'get': 'view_staffs'}), name="staff-list"),
    url(r'^auth/staff/(?P<id>[a-zA-Z0-9_:-]+)$', AdminView.as_view(
        {'put': 'update_staff', 'delete': 'delete_staff'}), name="staff-details"),
    url(r'^login$', obtain_jwt_token, name="obtain-jwt-token"),
    url(r'^verifyToken$', verify_jwt_token),
    url(r'^auth/admin/updatePermission$',
        AdminView.as_view({'put': 'update_permission'}), name="update_permission"),

    # Collection Endpoints
    url(r'^collections$', CollectionViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name="collection-list"),
    url(r'^collections/(?P<name>[a-zA-Z0-9_:-]+)$', CollectionViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="collection-detail"),

    # Manifest Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/manifest$', ManifestViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'delete': 'destroy', 'post': 'create'}), name="manifest-detail"),

    # Sequence Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/sequence$',
        generic_list, name="sequence-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/sequence/(?P<name>[a-zA-Z0-9_:-]+)$',
        generic_detail, name="sequence-detail"),

    # Canvas Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/canvas$',
        generic_list, name="canvas-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/canvas/(?P<name>[a-zA-Z0-9_:-=,\#]+)$',
        generic_detail, name="canvas-detail"),

    # Annotation Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/annotation$',
        generic_list, name="annotation-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/annotation/(?P<name>[a-zA-Z0-9_:-]+)$',
        generic_detail, name="annotation-detail"),

    # Annotationlist Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/list$',
        generic_list, name="annotationlist-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/list/(?P<name>[a-zA-Z0-9_:-]+)$',
        generic_detail, name="annotationlist-detail"),

    # Range Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/range$',
        generic_list, name="range-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/range/(?P<name>[a-zA-Z0-9_:-]+)$',
        generic_detail, name="range-detail"),

    # Layer Endpoints
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/layer$',
        generic_list, name="layer-list"),
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/layer/(?P<name>[a-zA-Z0-9_:-]+)$',
        generic_detail, name="layer-detail"),

    # Search Endpoint
    url(r'^search/(?P<type>[a-zA-Z0-9]+)/',
        SearchViewSet.as_view({'get': 'retrieve'}), name="search"),

    # Discovery Endpoint
    url(r'^discovery(?P<page>\s{0}|[-]{1}[0-9]+)$',
        ActivityViewSet.as_view({'get': 'discovery'}), name="discovery"),
    url(r'^discovery(?P<page>\s{0}|[-]{1}[0-9]+)/', ActivityViewSet.as_view(
        {'get': 'discovery_date_range'}), name="discovery_date_range"),

    # Activity Endpoints
    url(r'^activity/(?P<id>[a-zA-Z0-9]+)$', ActivityViewSet.as_view(
        {'get': 'activity', 'delete': 'delete'}), name="activity"),
    url(r'^activity$', ActivityViewSet.as_view(
        {'get': 'view_all', 'delete': 'delete_all'}), name="activityDeleteAll"),

    # Queue Endpoints
    url(r'^queue/(?P<id>[a-zA-Z0-9]+)$',
        QueueViewSet.as_view({'get': 'retrieve'}), name="queue"),
    url(r'^queue$', QueueViewSet.as_view(
        {'get': 'view_all'}), name="queueViewAll"),

    # Image Upload
    url(r'^images$', ImageUploadViewSet.as_view(
        {'post': 'upload_image'}), name="imageUpload"),

    # IIIF Search API Endpoint - Search Annotations within a Manifest
    url(r'^(?P<identifier>[a-zA-Z0-9_:-]+)/manifest/search/', SearchViewSet.as_view(
        {'get': 'iiif_search_within_manifest'}), name="iiif_search_within_manifest"),

    # Invalid Endpoint
    url(r'.*', invalid_api_endpoint),
]

urlpatterns = format_suffix_patterns(urlpatterns)
