import os
import json
import base64
from django.conf import settings
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response


class ImageUploadViewSet(ViewSet):
    # POST /images
    def upload_image(self, request, type=None, format=None):
        image_data = json.loads(request.body)
        if "imageContent" not in image_data or "filename" not in image_data:
            return Response(data={'error': "Both 'resourceContent' and 'filename' fields are required."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            filename = image_data["filename"]
            image_content = image_data["imageContent"]

        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.gif')):
            return Response(data={'error': "Resource filename should have a valid extension (.png, .jpg, .jpeg, .tiff, .gif"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:  # Upload the content and get imageURL
            image_url = local_image_upload(image_content, filename)
        except Exception as e:  # pragma: no cover
            return Response(data={'error': "Something went wrong while uploading the image. Make sure its a valid base64 encoded string.", "additionalError": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Success
        return Response(data={"url": image_url}, status=status.HTTP_201_CREATED)


def local_image_upload(resource_content, filename):
    '''
    Upload the image to a local loris server and return the full url
    '''
    directory = settings.LORIS_DIRECTORY
    original_umask = os.umask(0)
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.umask(original_umask)
    path = os.path.join(directory, filename)
    with open(path, "wb") as fh:
        fh.write(base64.decodestring(resource_content))
    fh.close()
    resource_url = settings.LORIS_URL + filename
    return resource_url
