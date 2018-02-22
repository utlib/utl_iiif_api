from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get REGISTER_SECRET_KEY
from iiif_api_services.models.User import User



class User_Test_Login(APIMongoTestCase):
    def setUp(self):
        User.create_user('user1', 'test@mail.com', 'user1password')

    def test_to_login_user_successfully(self):
        data = {"username": "user1", "password": "user1password"}
        response = self.client.post('/login', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("token" in response.data, True)

    def test_to_login_a_user_with_invalid_username(self):
        data = {"username": "invalid", "password": "user2password"}
        response = self.client.post('/login', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], 'Unable to log in with provided credentials.')

    def test_to_login_a_user_with_invalid_passwrod(self):
        data = {"username": "user1", "password": "invalid"}
        response = self.client.post('/login', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], 'Unable to log in with provided credentials.')
