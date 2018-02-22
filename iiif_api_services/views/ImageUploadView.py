import json
import os
import base64
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings # import the settings file to get IIIF_BASE_URL


class ImageUploadViewSet(ViewSet):
    # POST /images
    def uploadImage(self, request, type=None, format=None):
        imageData = json.loads(request.body)
        if "imageContent" not in imageData or "filename" not in imageData:
            return Response(data={'error': "Both 'resourceContent' and 'filename' fields are required."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            filename = imageData["filename"]
            imageContent = imageData["imageContent"]

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.gif')):
            return Response(data={'error': "Resource filename should have a valid extension (.png, .jpg, .jpeg, .tiff, .gif"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try: # Upload the content and get imageURL
            imageURL = localImageUpload(imageContent, filename)
        except Exception as e: # pragma: no cover
            return Response(data={'error': "Something went wrong while uploading the image. Make sure its a valid base64 encoded string.", "additionalError": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Success
        return Response(data={"url": imageURL}, status=status.HTTP_201_CREATED)




def localImageUpload(resourceContent, filename):
    '''
    Upload the iiif image to a local loris server and return the full url
    '''
    directory = settings.LORIS_DIRECTORY
    original_umask = os.umask(0)
    if not os.path.exists(directory):
        os.makedirs(directory) 
    os.umask(original_umask)
    path = os.path.join(directory, filename)
    with open(path, "wb") as fh:
        fh.write(base64.decodestring(resourceContent))
    fh.close()
    resourceURL = settings.LORIS_URL + filename
    return resourceURL