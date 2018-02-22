from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from iiif_api_services.models.User import User
import os
import json
from iiif_api_services.models.ManifestModel import Manifest
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.RangeModel import Range

MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'permission', 'manifestFull.json')


class User_Staff_Test_POST_Permission(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_verify_objects_are_created_with_staff_usernames(self):
        self.assertEqual(User.objects.get(username='user1').user_permissions, [])
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1"]) 
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1"]) 
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1"]) 
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1"])
        self.assertEqual(AnnotationList.objects[0].ownedBy, ["user1"])


class User_Staff_Test_PUT_PERMISSION(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)


    def test_to_verify_another_staff_cannot_update_an_object_not_owned(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.user = User.create_user('user2', 'test2@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.put('/book1/sequence/s0', {"sequence": data})
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["responseBody"]["error"], "You don't have the necessary permission to perform this action. Please contact your admin.")


    def test_to_verify_an_admin_can_update_any_object(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.user = User.create_user('admin', 'admin@mail.com', 'adminpassword', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"sequence": {"@id": settings.IIIF_BASE_URL + "/book1/sequence/newSequenceName"}}
        response = self.client.put('/book1/sequence/s0', data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL + "/book1/sequence/newSequenceName")



class User_Staff_Test_DELETE_PERMISSION(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_verify_object_can_be_deleted_in_staff_user_permissions(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/sequence/s0')
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)

    def test_to_verify_another_staff_cannot_delete_an_object_not_owned(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.user = User.create_user('user2', 'test2@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.delete('/book1/sequence/s0')
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["responseBody"]["error"], "You don't have the necessary permission to perform this action. Please contact your admin.")

    def test_to_verify_an_admin_can_delete_any_object(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.user = User.create_user('admin', 'admin@mail.com', 'adminpassword', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        response = self.client.delete('/book1/sequence/s0', data)
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)


class Test_Admin_Update_Staff_Permission(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'test@mail.com', 'user1password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes

    def test_an_admin_can_update_a_nested_manifest_user_permissions(self):
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1"])
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1"])
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1"])
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1"])
        self.assertEqual(Range.objects[0].ownedBy, ["user1"])
        self.user = User.create_user('admin', 'admin@mail.com', 'adminpassword', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"collections": ["somecollectionID"], "manifests":[settings.IIIF_BASE_URL+'/book1/manifest'], "username": "NEWSTAFF", "action": "ADD"}
        response = self.client.put('/auth/admin/updatePermission', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1", "NEWSTAFF"])
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1", "NEWSTAFF"])
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1", "NEWSTAFF"])
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1", "NEWSTAFF"])
        self.assertEqual(Range.objects[0].ownedBy, ["user1", "NEWSTAFF"])

    def test_an_admin_cannot_update_a_nested_manifest_user_permissions_with_validation_errors(self):
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1"])
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1"])
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1"])
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1"])
        self.assertEqual(Range.objects[0].ownedBy, ["user1"])
        self.user = User.create_user('admin', 'admin@mail.com', 'adminpassword', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifests":[settings.IIIF_BASE_URL+'/book1/manifest'], "username": "NEWSTAFF", "action": "SOMETHING"}
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1"])
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1"])
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1"])
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1"])
        self.assertEqual(Range.objects[0].ownedBy, ["user1"])

    def test_an_admin_can_remove_a_nested_manifest_user_permissions(self):
        self.assertEqual(Manifest.objects[0].ownedBy, ["user1"])
        self.assertEqual(Canvas.objects[0].ownedBy, ["user1"])
        self.assertEqual(Sequence.objects[0].ownedBy, ["user1"])
        self.assertEqual(Annotation.objects[0].ownedBy, ["user1"])
        self.assertEqual(Range.objects[0].ownedBy, ["user1"])
        self.user = User.create_user('admin', 'admin@mail.com', 'adminpassword', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"collections": ["somecollectionID"], "manifests":[settings.IIIF_BASE_URL+'/book1/manifest'], "username": "user1", "action": "REMOVE"}
        response = self.client.put('/auth/admin/updatePermission', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Manifest.objects[0].ownedBy, [])
        self.assertEqual(Canvas.objects[0].ownedBy, [])
        self.assertEqual(Sequence.objects[0].ownedBy, [])
        self.assertEqual(Annotation.objects[0].ownedBy, [])
        self.assertEqual(Range.objects[0].ownedBy, [])