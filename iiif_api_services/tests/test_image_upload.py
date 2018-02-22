import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from iiif_api_services.models.User import User
from django.conf import settings  # import the settings file to get REGISTER_SECRET_KEY


URL = '/images'
SHIBA_INU = os.path.join(os.path.dirname(__file__), 'testData', 'image', 'imageShibaInu.json')


class Image_Upload_Test_Without_Authentication(APIMongoTestCase):
    def test_to_upload_an_image_successfully(self):
        data = json.loads(open(SHIBA_INU).read())
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class Image_Upload_Test_With_Authentication(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_upload_an_image_successfully(self):
        data = json.loads(open(SHIBA_INU).read())
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["url"], settings.LORIS_URL+"shiba.jpg")

    def test_to_upload_an_image_with_missing_filename(self):
        data = json.loads(open(SHIBA_INU).read())
        del data["filename"]
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], "Both 'resourceContent' and 'filename' fields are required.")


    def test_to_upload_an_image_with_missing_content(self):
        data = json.loads(open(SHIBA_INU).read())
        del data["imageContent"]
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], "Both 'resourceContent' and 'filename' fields are required.")


    def test_to_upload_an_image_with_invalid_file_extention(self):
        data = json.loads(open(SHIBA_INU).read())
        data["filename"] = "shibu.invalid"
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], "Resource filename should have a valid extension (.png, .jpg, .jpeg, .tiff, .gif")


    def test_to_upload_an_image_with_invalid_content(self):
        data = json.loads(open(SHIBA_INU).read())
        data["imageContent"] = "not base 64 something invalid"
        response = self.client.post(URL, data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], "Something went wrong while uploading the image. Make sure its a valid base64 encoded string.")