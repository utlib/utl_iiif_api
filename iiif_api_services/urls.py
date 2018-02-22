from django.conf.urls import url, include
from .views.CollectionView import CollectionViewSet, SearchCollectionViewSet
from .views.ManifestView import ManifestViewSet, SearchManifestViewSet
from .views.SequenceView import SequenceViewSet, SearchSequenceViewSet
from .views.CanvasView import CanvasViewSet, SearchCanvasViewSet
from .views.AnnotationView import AnnotationViewSet, SearchAnnotationViewSet
from .views.AnnotationListView import AnnotationListViewSet, SearchAnnotationListViewSet
from .views.RangeView import RangeViewSet, SearchRangeViewSet
from .views.LayerView import LayerViewSet, SearchLayerViewSet
from .views.ResourceView import ResourceViewSet, SearchResourceViewSet
from .views.GlobalSearchView import GlobalSearchViewSet

from django.http import JsonResponse
from rest_framework import status

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.documentation import include_docs_urls


def invalid_api_endpoint(request):
	return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data={'error': "This API endpoint is invalid."})


api_root = CollectionViewSet.as_view({
	'get': 'list',
	})

collection_list = CollectionViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

collection_detail = CollectionViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

collection_search = SearchCollectionViewSet.as_view({
	'get': 'retrieve',
	})


manifest_detail = ManifestViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	'post': 'create',
	})

manifest_search = SearchManifestViewSet.as_view({
	'get': 'retrieve',
	})


sequence_list = SequenceViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

sequence_detail = SequenceViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

sequence_search = SearchSequenceViewSet.as_view({
	'get': 'retrieve',
	})


canvas_list = CanvasViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

canvas_detail = CanvasViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

canvas_search = SearchCanvasViewSet.as_view({
	'get': 'retrieve',
	})


annotation_list = AnnotationViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

annotation_detail = AnnotationViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

annotation_search = SearchAnnotationViewSet.as_view({
	'get': 'retrieve',
	})

annotationlist_list = AnnotationListViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

annotationlist_detail = AnnotationListViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

annotationlist_search = SearchAnnotationListViewSet.as_view({
	'get': 'retrieve',
	})


range_list = RangeViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

range_detail = RangeViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})


range_search = SearchRangeViewSet.as_view({
	'get': 'retrieve',
	})


layer_list = LayerViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

layer_detail = LayerViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})

layer_search = SearchLayerViewSet.as_view({
	'get': 'retrieve',
	})


resource_list = ResourceViewSet.as_view({
	'get': 'list',
	'post': 'create',
	})

resource_detail = ResourceViewSet.as_view({
	'get': 'retrieve',
	'put': 'update',
	'delete': 'destroy',
	})


resource_search = SearchResourceViewSet.as_view({
	'get': 'retrieve',
	})


global_search = GlobalSearchViewSet.as_view({
	'get': 'retrieve',
	})



urlpatterns = [
	url(r'^$', api_root, name="api-root"),

	url(r'^collections/$', collection_list, name="collection-list"),
	url(r'^collections/(?P<name>[a-zA-Z0-9_]+)/$', collection_detail, name="collection-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/manifest/$', manifest_detail, name="manifest-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/sequence/$', sequence_list, name="sequence-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/sequence/(?P<name>[a-zA-Z0-9_]+)$', sequence_detail, name="sequence-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/canvas/$', canvas_list, name="canvas-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/canvas/(?P<name>[a-zA-Z0-9_]+)$', canvas_detail, name="canvas-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/annotation/$', annotation_list, name="annotation-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/annotation/(?P<name>[a-zA-Z0-9_]+)$', annotation_detail, name="annotation-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/list/$', annotationlist_list, name="annotationlist-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/list/(?P<name>[a-zA-Z0-9_]+)$', annotationlist_detail, name="annotationlist-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/range/$', range_list, name="range-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/range/(?P<name>[a-zA-Z0-9_]+)$', range_detail, name="range-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/layer/$', layer_list, name="layer-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/layer/(?P<name>[a-zA-Z0-9_]+)$', layer_detail, name="layer-detail"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/res/$', resource_list, name="resource-list"),
	url(r'^(?P<item>[a-zA-Z0-9_]+)/res/(?P<name>[\w.]+)$', resource_detail, name="resource-detail"),


	url(r'^search/collections/(?P<query>[a-zA-Z0-9 _=&]+)$', collection_search, name="collection-search"),
	url(r'^search/manifests/(?P<query>[a-zA-Z0-9 _=&]+)$', manifest_search, name="manifest-search"),
	url(r'^search/sequences/(?P<query>[a-zA-Z0-9 _=&]+)$', sequence_search, name="sequence-search"),
	url(r'^search/canvases/(?P<query>[a-zA-Z0-9 _=&]+)$', canvas_search, name="canvas-search"),
	url(r'^search/annotations/(?P<query>[a-zA-Z0-9 _=&]+)$', annotation_search, name="annotation-search"),
	url(r'^search/list/(?P<query>[a-zA-Z0-9 _=&]+)$', annotationlist_search, name="annotationlist-search"),
	url(r'^search/ranges/(?P<query>[a-zA-Z0-9 _=&]+)$', range_search, name="range-search"),
	url(r'^search/layers/(?P<query>[a-zA-Z0-9 _=&]+)$', layer_search, name="layer-search"),
	url(r'^search/res/(?P<query>[a-zA-Z0-9 _=&]+)$', resource_search, name="resource-search"),

	url(r'^search/(?P<query>[a-zA-Z0-9 _=&]+)$', global_search, name="global-search"),


    url(r'^docs/', include_docs_urls(title='University of Toronto')),


	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),


	url(r'.*', invalid_api_endpoint),
]


urlpatterns = format_suffix_patterns(urlpatterns)




