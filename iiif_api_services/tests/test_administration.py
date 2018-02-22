from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get REGISTER_SECRET_KEY
from iiif_api_services.models.User import User

URL = '/auth/admin'


class User_Admin_Test_Registration(APIMongoTestCase):
    def setUp(self):
        User.create_user('user1', 'test@mail.com', 'user1password')

    def test_to_register_a_new_admin_successfully(self):
        data = {"username": "user2", "email": "example@mail.com", "password": "user2password", "secretKey": settings.REGISTER_SECRET_KEY}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], 'user2')
        self.assertEqual(User.objects.get(username='user2').username, 'user2')
        self.assertEqual(User.objects.get(username='user2').is_superuser, True)

    def test_to_register_a_new_admin_with_no_secret_key_provided(self):
        data = {"username": "user2", "password": "user2password"}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'Param secretKey is required.')

    def test_to_register_a_new_admin_with_invalid_secret_key_provided(self):
        data = {"username": "user2", "password": "user2password", "secretKey": "somethingInvalid"}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'Invalid secretKey provided.')

    def test_to_register_a_new_admin_with_existing_username(self):
        data = {"username": "user1", "password": "user2password", "secretKey": settings.REGISTER_SECRET_KEY}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'User with username already exists.')

    def test_to_register_a_new_admin_with_existing_email(self):
        data = {"username": "usernew", "password": "user2password", "email": "test@mail.com"}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'User with email already exists.')

    def test_to_register_a_new_admin_with_no_password_field(self):
        data = {"username": "user2", "secretKey": settings.REGISTER_SECRET_KEY}
        response = self.client.post('/auth/admin', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["password"][0], 'This field is required.')


class User_Staff_Test_Registration(APIMongoTestCase):
    def setUp(self):
        User.create_user('user1', 'test@mail.com', 'user1password')
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_register_a_new_staff_successfully(self):
        data = {"username": "user2", "email": "example@mail.com", "password": "user2password"}
        response = self.client.post('/auth/staff', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], 'user2')
        self.assertEqual(User.objects.get(username='user2').username, 'user2')
        self.assertEqual(User.objects.get(username='user2').is_superuser, False)

    def test_to_register_a_new_staff_with_existing_username(self):
        data = {"username": "user1", "password": "user2password"}
        response = self.client.post('/auth/staff', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'User with username already exists.')

    def test_to_register_a_new_staff_with_existing_email(self):
        data = {"username": "usernew", "password": "user2password", "email": "test@mail.com"}
        response = self.client.post('/auth/staff', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'User with email already exists.')

    def test_to_register_a_new_staff_with_no_password_field(self):
        data = {"username": "user2"}
        response = self.client.post('/auth/staff', data)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["password"][0], 'This field is required.')


class User_Staff_Test_Registration_With_No_Authentication(APIMongoTestCase):

    def test_to_register_a_new_staff_successfully(self):
        data = {"username": "user2", "email": "example@mail.com", "password": "user2password"}
        response = self.client.post('/auth/staff', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], 'Authentication credentials were not provided.')


class User_Staff_Test_Update_With_Staff_Authentication(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_update_a_staff_with_staff_privileges(self):
        data = {"username": "newUserName"}
        response = self.client.put('/auth/staff/'+str(self.user.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "You don't have the necessary permission to perform this action. Please contact your admin.")

    def test_to_update_a_staff_with_admin_privileges(self):
        staffID = str(self.user.id)
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"username": "newUserName"}
        response = self.client.put('/auth/staff/'+staffID, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "newUserName")

    def test_to_update_a_staff_with_admin_privileges_with_invalid_userID(self):
        staffID = "InvalidID"
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"username": "newUserName"}
        response = self.client.put('/auth/staff/'+staffID, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "User with id 'InvalidID' does not exist.")


class User_Staff_Test_Delete_With_Staff_Authentication(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_delete_a_staff_with_staff_privileges(self):
        response = self.client.delete('/auth/staff/'+str(self.user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "You don't have the necessary permission to perform this action. Please contact your admin.")

    def test_to_delete_a_staff_with_admin_privileges(self):
        staffID = str(self.user.id)
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.delete('/auth/staff/'+staffID)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully deleted user with id '" + staffID + "'.")

    def test_to_delete_a_staff_with_admin_privileges_with_invalid_userID(self):
        staffID = "InvalidID"
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.delete('/auth/staff/'+staffID)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "User with id 'InvalidID' does not exist.")



class User_Staff_Test_GET_All_With_Staff_Authentication(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_get_all_staffs_with_staff_privileges(self):
        response = self.client.get('/auth/staff')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "You don't have the necessary permission to perform this action. Please contact your admin.")

    def test_to_get_all_staffs_with_admin_privileges(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.get('/auth/staff')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['username'], 'user1')

    def test_to_get_all_staffs_with_admin_privileges_where_no_staffs_are_present(self):
        User.objects.delete()
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.get('/auth/staff')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No staff users found.')
