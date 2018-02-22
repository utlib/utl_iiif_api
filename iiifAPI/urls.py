from django.conf.urls import url, include


urlpatterns = [
	url(r'', include("iiif_api_services.urls")),
]
