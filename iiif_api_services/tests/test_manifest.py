import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.QueueModel import Queue
from iiif_api_services.models.ActivityModel import Activity
from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.models.ManifestModel import Manifest
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.RangeModel import Range
from django.test import override_settings


MANIFEST_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'manifest', 'manifestShort.json')
MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'manifest', 'manifestFull.json')


class Manifest_Simple_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest").save()

    def test_to_view_a_manifest_without_authentication(self):
        response = self.client.get('/book1/manifest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], 'http://example.org/iiif/book1/manifest')
        self.assertEqual(response.data["ATtype"], 'sc:Manifest')
        self.assertEqual(response.data["label"], 'manifest1')

    def test_a_manifest_cannot_be_created_without_authentication(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.post('/book2/manifest', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(Manifest.objects()), 1)

    def test_a_manifest_cannot_be_updated_without_authentication(self):
        self.assertEqual(Manifest.objects().first().label, "manifest1")
        response = self.client.put('/book1/manifest', {"manifest": {"label": "New Label"}})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Manifest.objects().first().label, "manifest1")

    def test_a_manifest_cannot_be_deleted_without_authentication(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.delete('/book1/manifest')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(Manifest.objects()), 1)



class Manifest_Simple_Test_With_Authentication_And_Correct_Staff_Permission(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest", ownedBy=["staff"]).save()
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_view_a_manifest_with_authentication_and_correct_staff_permission(self):
        response = self.client.get('/book1/manifest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], 'http://example.org/iiif/book1/manifest')
        self.assertEqual(response.data["ATtype"], 'sc:Manifest')
        self.assertEqual(response.data["label"], 'manifest1')

    def test_a_manifest_can_be_created_with_authentication_and_correct_staff_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.post('/book2/manifest', {"manifest": {}})
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book2/manifest")
        self.assertEqual(len(Manifest.objects()), 2)

    def test_a_manifest_can_be_updated_with_authentication_and_correct_staff_permission(self):
        self.assertEqual(Manifest.objects().first().label, "manifest1")
        response = self.client.put('/book1/manifest', {"manifest": {"label": "New Label"}})
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().first().label, "New Label")

    def test_a_manifest_can_be_deleted_with_authentication_and_correct_staff_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.delete('/book1/manifest')
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Manifest.objects()), 0)

    def test_a_manifest_owned_by_many_cannot_be_deleted_with_authentication_and_correct_staff_permission(self):
        Manifest(label="manifest1", identifier="book2", ATid="http://example.org/iiif/book2/manifest", ownedBy=["staff", "anotherStaff"]).save()
        self.assertEqual(len(Manifest.objects()), 2)
        response = self.client.delete('/book2/manifest')
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["responseBody"]["error"], "This object is owned by many users. Please contact your admin to perform this action.")
        self.assertEqual(len(Manifest.objects()), 2)


class Manifest_Simple_Test_With_Authentication_And_Incorrect_Staff_Permission(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest").save()
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_view_a_manifest_with_authentication_and_incorrect_staff_permission(self):
        response = self.client.get('/book1/manifest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], 'http://example.org/iiif/book1/manifest')
        self.assertEqual(response.data["ATtype"], 'sc:Manifest')
        self.assertEqual(response.data["label"], 'manifest1')

    def test_a_manifest_can_be_created_with_authentication_and_no_staff_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.post('/book2/manifest', {"manifest": {}})
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book2/manifest")
        self.assertEqual(len(Manifest.objects()), 2)

    def test_a_manifest_cannot_be_updated_with_authentication_and_incorrect_staff_permission(self):
        self.assertEqual(Manifest.objects().first().label, "manifest1")
        response = self.client.put('/book1/manifest', {"manifest": {"label": "New Label"}})
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["responseBody"]["error"], "You don't have the necessary permission to perform this action. Please contact your admin.")
        self.assertEqual(Manifest.objects().first().label, "manifest1")

    def test_a_manifest_cannot_be_deleted_with_authentication_and_incorrect_staff_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.delete('/book1/manifest')
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["responseBody"]["error"], "You don't have the necessary permission to perform this action. Please contact your admin.")
        self.assertEqual(len(Manifest.objects()), 1)


class Manifest_Simple_Test_With_Authentication_And_Admin_Permission(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest").save()
        self.user = User.create_user('admin', 'admin@mail.com', 'password', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_to_view_a_manifest_with_authentication_and_admin_permission(self):
        response = self.client.get('/book1/manifest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], 'http://example.org/iiif/book1/manifest')
        self.assertEqual(response.data["ATtype"], 'sc:Manifest')
        self.assertEqual(response.data["label"], 'manifest1')

    def test_a_manifest_can_be_created_with_authentication_admin_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.post('/book2/manifest', {"manifest": {}})
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book2/manifest")
        self.assertEqual(len(Manifest.objects()), 2)

    def test_a_manifest_can_be_updated_with_authentication_and_admin_permission(self):
        self.assertEqual(Manifest.objects().first().label, "manifest1")
        response = self.client.put('/book1/manifest', {"manifest": {"label": "New Label"}})
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().first().label, "New Label")

    def test_a_manifest_can_be_deleted_with_authentication_and_admin_permission(self):
        self.assertEqual(len(Manifest.objects()), 1)
        response = self.client.delete('/book1/manifest')
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Manifest.objects()), 0)

    def test_a_manifest_owned_by_many_can_be_deleted_with_authentication_and_admin_permission(self):
        Manifest(label="manifest1", identifier="book2", ATid="http://example.org/iiif/book2/manifest", ownedBy=["staff", "anotherStaff"]).save()
        self.assertEqual(len(Manifest.objects()), 2)
        response = self.client.delete('/book2/manifest')
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Manifest.objects()), 1)


@override_settings()
class Manifest_Short_Test_POST_Without_Queue(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_created(self):
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        createdManifest = Manifest.objects.get(identifier="book1")
        self.assertEqual(createdManifest.label, 'Book 1')
        self.assertEqual(len(createdManifest.metadata), 4)
        self.assertEqual(createdManifest.metadata[1]["value"][1]["@language"], 'fr')
        self.assertEqual(createdManifest.thumbnail["service"]["@id"], 'http://example.org/images/book1-page1')
        self.assertEqual(createdManifest.viewingDirection, 'right-to-left')
        self.assertEqual(createdManifest.logo["service"]["@id"], 'http://example.org/service/inst1')
        self.assertEqual(createdManifest.related["@id"], 'http://example.org/videos/video-book1.mpg')
        self.assertEqual(createdManifest.service["@id"], 'http://example.org/service/example')
        self.assertEqual(createdManifest.seeAlso["@id"], 'http://example.org/library/catalog/book1.xml')
        self.assertEqual(createdManifest.rendering["@id"], 'http://example.org/iiif/book1.pdf')
        self.assertEqual(createdManifest.within, 'http://example.org/collections/books')


@override_settings()
class Manifest_Short_Test_POST_With_THREAD_Queue(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_created(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        createdManifest = Manifest.objects.get(identifier="book1")
        self.assertEqual(createdManifest.label, 'Book 1')
        self.assertEqual(len(createdManifest.metadata), 4)
        self.assertEqual(createdManifest.metadata[1]["value"][1]["@language"], 'fr')
        self.assertEqual(createdManifest.thumbnail["service"]["@id"], 'http://example.org/images/book1-page1')
        self.assertEqual(createdManifest.viewingDirection, 'right-to-left')
        self.assertEqual(createdManifest.logo["service"]["@id"], 'http://example.org/service/inst1')
        self.assertEqual(createdManifest.related["@id"], 'http://example.org/videos/video-book1.mpg')
        self.assertEqual(createdManifest.service["@id"], 'http://example.org/service/example')
        self.assertEqual(createdManifest.seeAlso["@id"], 'http://example.org/library/catalog/book1.xml')
        self.assertEqual(createdManifest.rendering["@id"], 'http://example.org/iiif/book1.pdf')
        self.assertEqual(createdManifest.within, 'http://example.org/collections/books')


@override_settings()
class Manifest_Short_Test_POST_With_PROCESS_Queue(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_created(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        createdManifest = Manifest.objects.get(identifier="book1")
        self.assertEqual(createdManifest.label, 'Book 1')
        self.assertEqual(len(createdManifest.metadata), 4)
        self.assertEqual(createdManifest.metadata[1]["value"][1]["@language"], 'fr')
        self.assertEqual(createdManifest.thumbnail["service"]["@id"], 'http://example.org/images/book1-page1')
        self.assertEqual(createdManifest.viewingDirection, 'right-to-left')
        self.assertEqual(createdManifest.logo["service"]["@id"], 'http://example.org/service/inst1')
        self.assertEqual(createdManifest.related["@id"], 'http://example.org/videos/video-book1.mpg')
        self.assertEqual(createdManifest.service["@id"], 'http://example.org/service/example')
        self.assertEqual(createdManifest.seeAlso["@id"], 'http://example.org/library/catalog/book1.xml')
        self.assertEqual(createdManifest.rendering["@id"], 'http://example.org/iiif/book1.pdf')
        self.assertEqual(createdManifest.within, 'http://example.org/collections/books')


@override_settings()
class Manifest_Short_Test_POST_With_CELERY_Queue(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_created(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        createdManifest = Manifest.objects.get(identifier="book1")
        self.assertEqual(createdManifest.label, 'Book 1')
        self.assertEqual(len(createdManifest.metadata), 4)
        self.assertEqual(createdManifest.metadata[1]["value"][1]["@language"], 'fr')
        self.assertEqual(createdManifest.thumbnail["service"]["@id"], 'http://example.org/images/book1-page1')
        self.assertEqual(createdManifest.viewingDirection, 'right-to-left')
        self.assertEqual(createdManifest.logo["service"]["@id"], 'http://example.org/service/inst1')
        self.assertEqual(createdManifest.related["@id"], 'http://example.org/videos/video-book1.mpg')
        self.assertEqual(createdManifest.service["@id"], 'http://example.org/service/example')
        self.assertEqual(createdManifest.seeAlso["@id"], 'http://example.org/library/catalog/book1.xml')
        self.assertEqual(createdManifest.rendering["@id"], 'http://example.org/iiif/book1.pdf')
        self.assertEqual(createdManifest.within, 'http://example.org/collections/books')


class Manifest_Full_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")


    def test_a_full_manifest_can_be_successfully_created_with_its_own_metadata(self):
        createdManifest = Manifest.objects.get(identifier="book1")
        self.assertEqual(createdManifest.label, 'Book 1')
        self.assertEqual(len(createdManifest.metadata), 4)
        self.assertEqual(createdManifest.metadata[1]["value"][1]["@language"], 'fr')
        self.assertEqual(createdManifest.thumbnail["service"]["@id"], 'http://example.org/images/book1-page1')
        self.assertEqual(createdManifest.viewingDirection, 'right-to-left')
        self.assertEqual(createdManifest.logo["service"]["@id"], 'http://example.org/service/inst1')
        self.assertEqual(createdManifest.related["@id"], 'http://example.org/videos/video-book1.mpg')
        self.assertEqual(createdManifest.service["@id"], 'http://example.org/service/example')
        self.assertEqual(createdManifest.seeAlso["@id"], 'http://example.org/library/catalog/book1.xml')
        self.assertEqual(createdManifest.rendering["@id"], 'http://example.org/iiif/book1.pdf')
        self.assertEqual(createdManifest.within, 'http://example.org/collections/books')
        self.assertEqual(createdManifest.ownedBy, ["staff"])

    def test_a_full_manifest_can_be_successfully_created_with_its_nested_sequences(self):
        self.assertEqual(len(Sequence.objects()), 3)
        sequence3 = Sequence.objects().get(identifier="book1", name="sequence3")
        self.assertEqual(sequence3.ATid, settings.IIIF_BASE_URL + "/book1/sequence/sequence3")
        self.assertEqual(sequence3.ownedBy, ["staff"])

    def test_a_full_manifest_can_be_successfully_created_with_its_nested_ranges(self):
        self.assertEqual(len(Range.objects()), 4)
        range1 = Range.objects().get(identifier="book1", name="range1")
        range2 = Range.objects().get(identifier="book1", name="range2")
        range3 = Range.objects().get(identifier="book1", name="range3")
        range4 = Range.objects().get(identifier="book1", name="range4")
        self.assertEqual(range1.ATid, settings.IIIF_BASE_URL + "/book1/range/range1")
        self.assertEqual(range2.ATid, settings.IIIF_BASE_URL + "/book1/range/range2")
        self.assertEqual(range3.ATid, settings.IIIF_BASE_URL + "/book1/range/range3")
        self.assertEqual(range4.ATid, settings.IIIF_BASE_URL + "/book1/range/range4")
        self.assertEqual(len(range2.belongsTo), 2)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range1" in range2.belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in range2.belongsTo)
        self.assertEqual(range2.ownedBy, ["staff"])

    def test_a_full_manifest_can_be_successfully_created_with_its_nested_canvases(self):
        self.assertEqual(len(Canvas.objects()), 7)
        canvas1 = Canvas.objects().get(identifier="book1", name="canvas1")
        canvas2 = Canvas.objects().get(identifier="book1", name="canvas2")
        canvas3 = Canvas.objects().get(identifier="book1", name="canvas3")
        canvas4 = Canvas.objects().get(identifier="book1", name="canvas4")
        canvas5 = Canvas.objects().get(identifier="book1", name="canvas5")
        canvas6 = Canvas.objects().get(identifier="book1", name="canvas3#xywh=0,0,750,300")
        canvas7 = Canvas.objects().get(identifier="book1", name="canvas2#xywh=0,0,500,500")
        self.assertEqual(canvas1.label, "Canvas 1")
        self.assertEqual(len(canvas1.belongsTo), 2)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in canvas1.belongsTo)
        self.assertEqual(len(canvas2.belongsTo), 3)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range1" in canvas2.belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in canvas2.belongsTo)
        self.assertEqual(len(canvas7.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range4" in canvas7.belongsTo)
        self.assertEqual(canvas7.ownedBy, ["staff"])

    def test_a_full_manifest_can_be_successfully_created_with_its_nested_annotations(self):
        self.assertEqual(len(Annotation.objects()), 7)
        annotation4 = Annotation.objects().get(identifier="book1", name="anno4")
        annotation5 = Annotation.objects().get(identifier="book1", name="anno5")
        annotation6 = Annotation.objects().get(identifier="book1", name="anno6")
        annotation7 = Annotation.objects().get(identifier="book1", name="anno7")
        self.assertEqual(len(annotation4.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas3" in annotation4.belongsTo)
        self.assertEqual(len(annotation7.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas5" in annotation7.belongsTo)
        self.assertEqual(annotation7.ownedBy, ["staff"])

    def test_a_full_manifest_can_be_successfully_created_with_its_nested_annotationLists(self):
        self.assertEqual(len(AnnotationList.objects()), 2)
        list1 = AnnotationList.objects().get(identifier="book1", name="list1")
        list2 = AnnotationList.objects().get(identifier="book1", name="list2")
        self.assertEqual(len(list1.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas1" in list1.belongsTo)
        self.assertEqual(len(list2.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas2" in list2.belongsTo)
        self.assertEqual(list2.ownedBy, ["staff"])



class Manifest_Full_Test_POST_With_Validation_Errors_In_Manifest(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}

    def test_a_full_manifest_cannot_be_successfully_created_with_duplicate_identifier(self):
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["identifier"][0], "This field must be unique.")


class Manifest_Full_Test_POST_With_Validation_Errors_In_Nested_Objects(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}

    def test_a_full_manifest_cannot_be_successfully_created_with_validation_errors_in_nested_sequences(self):
        self.data["manifest"]["sequences"][0]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_all_related_objects_will_be_deleted_if_errors_in_nested_sequences(self):
        self.data["manifest"]["sequences"][2]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


    def test_all_related_objects_will_be_deleted_if_errors_in_nested_ranges(self):
        self.data["manifest"]["structures"][2]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


    def test_all_related_objects_will_be_deleted_if_errors_in_nested_canvases(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


    def test_all_related_objects_will_be_deleted_if_errors_in_nested_annotations(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["images"][1]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


    def test_all_related_objects_will_be_deleted_if_errors_in_nested_annotationLists(self):
        self.data["manifest"]["sequences"][0]["canvases"][0]["otherContent"][0]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


    def test_all_related_objects_will_be_deleted_if_errors_in_nested_resources(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["images"][0]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")
        self.assertEqual(len(Manifest.objects()), 0)
        self.assertEqual(len(Sequence.objects()), 0)
        self.assertEqual(len(Range.objects()), 0)
        self.assertEqual(len(Canvas.objects()), 0)
        self.assertEqual(len(Annotation.objects()), 0)
        self.assertEqual(len(AnnotationList.objects()), 0)


class Manifest_Full_Test_POST_With_Already_Existing_Nested_Objects(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}

    def test_a_manifest_post_with_already_existing_sequence_will_be_updated(self):
        Sequence(label="Sequence 2", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2", ownedBy=["staff"]).save()
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").label, "Sequence 2")
        self.data["manifest"]["sequences"][1]["label"] = "New Sequence 2"
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").label, "New Sequence 2")
        self.assertEqual(len(Sequence.objects()), 3)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 7)
        self.assertEqual(len(Annotation.objects()), 7)
        self.assertEqual(len(AnnotationList.objects()), 2)

    def test_a_manifest_post_with_already_existing_range_will_be_updated(self):
        Range(label="Range 2", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range/range2", ownedBy=["staff"]).save()
        self.assertEqual(Range.objects().get(identifier="book1", name="range2").label, "Range 2")
        self.data["manifest"]["structures"][0]["members"][1]["label"] = "New Range 2"
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Range.objects().get(identifier="book1", name="range2").label, "New Range 2")
        self.assertEqual(len(Sequence.objects()), 3)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 7)
        self.assertEqual(len(Annotation.objects()), 7)
        self.assertEqual(len(AnnotationList.objects()), 2)

    def test_a_manifest_post_with_already_existing_canvas_will_be_updated(self):
        Canvas(label="Canvas 2", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas/canvas2", ownedBy=["staff"]).save()
        self.assertEqual(Canvas.objects().get(identifier="book1", name="canvas2").label, "Canvas 2")
        self.data["manifest"]["sequences"][0]["canvases"][1]["label"] = "New Canvas 2"
        self.data["manifest"]["structures"][0]["members"][0]["label"] = "New Canvas 2"
        self.assertEqual(len(Annotation.objects()), 0)
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Canvas.objects().get(identifier="book1", name="canvas2").label, "New Canvas 2")
        self.assertEqual(len(Sequence.objects()), 3)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 7)
        self.assertEqual(len(Annotation.objects()), 7)
        self.assertEqual(len(AnnotationList.objects()), 2)

    def test_a_manifest_post_with_already_existing_annotation_will_be_updated(self):
        Annotation(label="Annotation 4", identifier="book1", name="anno4", ATid="http://example.org/iiif/book1/annotation/anno4", ownedBy=["staff"]).save()
        self.assertEqual(Annotation.objects().get(identifier="book1", name="anno4").label, "Annotation 4")
        self.data["manifest"]["sequences"][0]["canvases"][2]["images"][0]["label"] = "New Annotation 4"
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Annotation.objects().get(identifier="book1", name="anno4").label, "New Annotation 4")
        self.assertEqual(len(Sequence.objects()), 3)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 7)
        self.assertEqual(len(Annotation.objects()), 7)
        self.assertEqual(len(AnnotationList.objects()), 2)

    def test_a_manifest_post_with_already_existing_annotationList_will_be_updated(self):
        AnnotationList(label="AnnotationList 1", identifier="book1", name="list1", ATid="http://example.org/iiif/book1/list/list1", ownedBy=["staff"]).save()
        self.assertEqual(AnnotationList.objects().get(identifier="book1", name="list1").label, "AnnotationList 1")
        self.data["manifest"]["sequences"][0]["canvases"][0]["otherContent"][0]["label"] = "New AnnotationList 1"
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(AnnotationList.objects().get(identifier="book1", name="list1").label, "New AnnotationList 1")
        self.assertEqual(len(Sequence.objects()), 3)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 7)
        self.assertEqual(len(Annotation.objects()), 7)
        self.assertEqual(len(AnnotationList.objects()), 2)


class Manifest_Test_POST_Miscellaneous(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_manifest_with_no_id_given_can_be_successfully_created(self):
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        del data["manifest"]["@id"]
        response = self.client.post("/book1/manifest", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")


@override_settings()
class Manifest_Short_Test_PUT_Without_QUEUE(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_updated(self):
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "Book 1")
        data["manifest"]["label"] = "NEW LABEL"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "NEW LABEL")


@override_settings()
class Manifest_Short_Test_PUT_With_THREAD_QUEUE(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_updated(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "Book 1")
        data["manifest"]["label"] = "NEW LABEL"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "NEW LABEL")



@override_settings()
class Manifest_Short_Test_PUT_With_PROCESS_QUEUE(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_updated(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "Book 1")
        data["manifest"]["label"] = "NEW LABEL"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "NEW LABEL")



@override_settings()
class Manifest_Short_Test_PUT_With_CELERY_QUEUE(APIMongoTestCase):
    def test_a_short_manifest_can_be_successfully_updated(self):
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_SHORT).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "Book 1")
        data["manifest"]["label"] = "NEW LABEL"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "NEW LABEL")


class Manifest_full_Test_PUT(APIMongoTestCase):

    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")


    def test_a_full_manifest_can_be_successfully_updated_with_new_manifest_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "Book 1")
        self.assertEqual(Manifest.objects().get(identifier="book1").description, "A longer description of this example book. It should give some real information.")
        data["manifest"]["label"] = "NEW LABEL"
        data["manifest"]["description"] = "NEW DESCRIPTION"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Manifest.objects().get(identifier="book1").label, "NEW LABEL")
        self.assertEqual(Manifest.objects().get(identifier="book1").description, "NEW DESCRIPTION")


    def test_a_full_manifest_can_be_successfully_updated_with_new_sequence_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").label, "Sequence 2")
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").viewingDirection, "right-to-left")
        data["manifest"]["sequences"][1]["label"] = "NEW LABEL"
        data["manifest"]["sequences"][1]["viewingDirection"] = "NEW viewingDirection"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").label, "NEW LABEL")
        self.assertEqual(Sequence.objects().get(identifier="book1", name="sequence2").viewingDirection, "NEW viewingDirection")


    def test_a_full_manifest_can_be_successfully_updated_with_new_range_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(Range.objects().get(identifier="book1", name="range1").label, "Range 1")
        self.assertEqual(Range.objects().get(identifier="book1", name="range1").viewingHint, "top")
        data["manifest"]["structures"][0]["label"] = "NEW LABEL"
        data["manifest"]["structures"][0]["viewingHint"] = "NEW viewingHint"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Range.objects().get(identifier="book1", name="range1").label, "NEW LABEL")
        self.assertEqual(Range.objects().get(identifier="book1", name="range1").viewingHint, "NEW viewingHint")


    def test_a_full_manifest_can_be_successfully_updated_with_new_canvas_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(Canvas.objects().get(identifier="book1", name="canvas1").height, 1000)
        data["manifest"]["sequences"][0]["canvases"][0]["height"] = 500
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Canvas.objects().get(identifier="book1", name="canvas1").height, 500)


    def test_a_full_manifest_can_be_successfully_updated_with_new_annotation_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(Annotation.objects().get(identifier="book1", name="anno4").motivation, "sc:painting")
        data["manifest"]["sequences"][0]["canvases"][2]["images"][0]["motivation"] = "NEW motivation"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        
        self.assertEqual(Annotation.objects().get(identifier="book1", name="anno4").motivation, "NEW motivation")


    def test_a_full_manifest_can_be_successfully_updated_with_new_annotationList_metadata(self):
        data = {"manifest": self.client.get('/book1/manifest').data}
        self.assertEqual(AnnotationList.objects().get(identifier="book1", name="list1").label, None)
        data["manifest"]["sequences"][0]["canvases"][0]["otherContent"][0]["label"] = "NEW label"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(AnnotationList.objects().get(identifier="book1", name="list1").label, "NEW label")


class Manifest_Full_Test_PUT_With_New_Nested_Objects(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest", ownedBy=["staff"]).save()
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_full_manifest_can_be_successfully_updated_with_new_nested_sequences(self):
        self.assertEqual(len(Sequence.objects()), 0)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Sequence.objects()), 3)
        sequence3 = Sequence.objects().get(identifier="book1", name="sequence3")
        self.assertEqual(sequence3.ATid, settings.IIIF_BASE_URL + "/book1/sequence/sequence3")
        self.assertEqual(sequence3.ownedBy, ["staff"])


    def test_a_full_manifest_can_be_successfully_updated_with_new_nested_ranges(self):
        self.assertEqual(len(Range.objects()), 0)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Range.objects()), 4)
        range1 = Range.objects().get(identifier="book1", name="range1")
        range2 = Range.objects().get(identifier="book1", name="range2")
        range3 = Range.objects().get(identifier="book1", name="range3")
        range4 = Range.objects().get(identifier="book1", name="range4")
        self.assertEqual(range1.ATid, settings.IIIF_BASE_URL + "/book1/range/range1")
        self.assertEqual(range2.ATid, settings.IIIF_BASE_URL + "/book1/range/range2")
        self.assertEqual(range3.ATid, settings.IIIF_BASE_URL + "/book1/range/range3")
        self.assertEqual(range4.ATid, settings.IIIF_BASE_URL + "/book1/range/range4")
        self.assertEqual(len(range2.belongsTo), 2)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range1" in range2.belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in range2.belongsTo)
        self.assertEqual(range2.ownedBy, ["staff"])


    def test_a_full_manifest_can_be_successfully_updated_with_new_nested_canvases(self):
        self.assertEqual(len(Canvas.objects()), 0)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Canvas.objects()), 7)
        canvas1 = Canvas.objects().get(identifier="book1", name="canvas1")
        canvas2 = Canvas.objects().get(identifier="book1", name="canvas2")
        canvas3 = Canvas.objects().get(identifier="book1", name="canvas3")
        canvas4 = Canvas.objects().get(identifier="book1", name="canvas4")
        canvas5 = Canvas.objects().get(identifier="book1", name="canvas5")
        canvas6 = Canvas.objects().get(identifier="book1", name="canvas3#xywh=0,0,750,300")
        canvas7 = Canvas.objects().get(identifier="book1", name="canvas2#xywh=0,0,500,500")
        self.assertEqual(canvas1.label, "Canvas 1")
        self.assertEqual(len(canvas1.belongsTo), 2)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in canvas1.belongsTo)
        self.assertEqual(len(canvas2.belongsTo), 3)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range1" in canvas2.belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range3" in canvas2.belongsTo)
        self.assertEqual(len(canvas7.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/range4" in canvas7.belongsTo)
        self.assertEqual(canvas7.ownedBy, ["staff"])


    def test_a_full_manifest_can_be_successfully_updated_with_new_nested_annotations(self):
        self.assertEqual(len(Annotation.objects()), 0)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        print response.data
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Annotation.objects()), 7)
        annotation4 = Annotation.objects().get(identifier="book1", name="anno4")
        annotation5 = Annotation.objects().get(identifier="book1", name="anno5")
        annotation6 = Annotation.objects().get(identifier="book1", name="anno6")
        annotation7 = Annotation.objects().get(identifier="book1", name="anno7")
        self.assertEqual(len(annotation6.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas4" in annotation6.belongsTo)
        self.assertEqual(len(annotation7.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas5" in annotation7.belongsTo)
        self.assertEqual(annotation7.ownedBy, ["staff"])


    def test_a_full_manifest_can_be_successfully_updated_with_new_nested_annotationLists(self):
        self.assertEqual(len(AnnotationList.objects()), 0)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(AnnotationList.objects()), 2)
        list1 = AnnotationList.objects().get(identifier="book1", name="list1")
        list2 = AnnotationList.objects().get(identifier="book1", name="list2")
        self.assertEqual(len(list1.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas1" in list1.belongsTo)
        self.assertEqual(len(list2.belongsTo), 1)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/canvas/canvas2" in list2.belongsTo)
        self.assertEqual(list2.ownedBy, ["staff"])



class Manifest_Full_Test_PUT_With_Validation_Errors_In_Nested_Objects(APIMongoTestCase):
    def setUp(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest", ownedBy=["staff"]).save()
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}

    def test_a_full_manifest_cannot_be_successfully_updated_with_validation_errors_in_nested_sequences(self):
        self.data["manifest"]["sequences"][0]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_manifest_update_with_errors_errors_in_nested_sequences(self):
        self.data["manifest"]["sequences"][2]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_manifest_update_with_errors_errors_in_nested_ranges(self):
        self.data["manifest"]["structures"][2]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_manifest_update_with_errors_in_nested_canvases(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def _manifest_update_with_errors_in_nested_annotations(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["images"][1]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def _manifest_update_with_errors_in_nested_annotationLists(self):
        self.data["manifest"]["sequences"][0]["canvases"][0]["otherContent"][0]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        print response.data
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def _manifest_update_with_errors_in_nested_resources(self):
        self.data["manifest"]["sequences"][0]["canvases"][3]["images"][1]["resource"]["viewingHint"] = [123456789]  # Field must be a String
        response = self.client.put('/book1/manifest', self.data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")



class Manifest_Test_PUT_Miscellaneous(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)


    def test_an_item_manifest_that_does_not_exist_cannot_be_updated(self):
        data = {"manifest": {"label": "new_manifest1", "viewingHint": "non-paged"}}
        response = self.client.put("/nonExistingItem/manifest", data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "'nonExistingItem' does not have a Manifest.")


    def test_a_manifest_with_new_id_can_be_updated_successfully(self):
        Manifest(label="manifest1", identifier="book1", ATid="http://example.org/iiif/book1/manifest", ownedBy=["staff"]).save()
        data = {"manifest": {"@id": "http://example.org/iiif/new_book1/manifest", "viewingHint": "non-paged"}}
        response = self.client.put("/book1/manifest", data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL + "/new_book1/manifest")


    def test_a_manifest_with_new_id_will_update_its_nested_objects_belongsTo_field(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence2').belongsTo[0], settings.IIIF_BASE_URL + "/book1/manifest")
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence3').belongsTo[0], settings.IIIF_BASE_URL + "/book1/manifest")
        data["manifest"]["@id"] = "http://example.org/iiif/not-book1/manifest"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence2').belongsTo[0], settings.IIIF_BASE_URL + "/not-book1/manifest")
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence3').belongsTo[0], settings.IIIF_BASE_URL + "/not-book1/manifest")

    def test_a_manifest_with_new_id_will_update_its_parent_objects_children_field(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/collections', {"collection": {"@id": settings.IIIF_BASE_URL + '/collections/parent', "manifests": [{"@id": settings.IIIF_BASE_URL + "/book1/manifest"}]}})
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence2').belongsTo[0], settings.IIIF_BASE_URL + "/book1/manifest")
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence3').belongsTo[0], settings.IIIF_BASE_URL + "/book1/manifest")
        self.assertEqual(Collection.objects.get(name="parent").children[0], settings.IIIF_BASE_URL + "/book1/manifest")
        data["manifest"]["@id"] = "http://example.org/iiif/not-book1/manifest"
        response = self.client.put('/book1/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence2').belongsTo[0], settings.IIIF_BASE_URL + "/not-book1/manifest")
        self.assertEqual(Sequence.objects.get(identifier="book1", name='sequence3').belongsTo[0], settings.IIIF_BASE_URL + "/not-book1/manifest")
        self.assertEqual(Collection.objects.get(name="parent").children[0], settings.IIIF_BASE_URL + "/not-book1/manifest")

    def test_a_manifest_can_be_updated_with_a_new_belongsTo_field_will_replace_existing_values(self):
        Manifest(label="book1", identifier="book3", ATid="http://example.org/iiif/book3/manifest", belongsTo=[settings.IIIF_BASE_URL +"/collection/book1"], ownedBy=["staff"]).save()
        self.assertEqual(Manifest.objects.get(identifier='book3').belongsTo, [settings.IIIF_BASE_URL + "/collection/book1"])
        self.assertFalse("http://example.org/iiif/collection/book2" in Manifest.objects.get(identifier='book3').belongsTo)
        data = {"manifest": {"belongsTo": ["http://example.org/iiif/collection/book2"]}}
        response = self.client.put('/book3/manifest', data)
        if settings.QUEUE_PUT_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertFalse(settings.IIIF_BASE_URL + "/collection/book1" in Manifest.objects.get(identifier='book3').belongsTo)
        self.assertTrue("http://example.org/iiif/collection/book2" in Manifest.objects.get(identifier='book3').belongsTo)


    def test_an_embedded_sequence_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Sequence(label="normal", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2", belongsTo=[settings.IIIF_BASE_URL +"/book156/manifest"], ownedBy=["staff"]).save()
        self.assertEqual(Sequence.objects.get(identifier='book1', name="sequence2").belongsTo, [settings.IIIF_BASE_URL + "/book156/manifest"])
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Sequence.objects.get(identifier='book1', name="sequence2").belongsTo)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post("/book1/manifest", data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/manifest" in Sequence.objects.get(identifier='book1', name="sequence2").belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL +"/book156/manifest" in Sequence.objects.get(identifier='book1', name="sequence2").belongsTo)


    def test_an_embedded_range_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1", belongsTo=[settings.IIIF_BASE_URL +"/book156/manifest"], ownedBy=["staff"]).save()
        self.assertEqual(Range.objects.get(identifier='book1', name="range1").belongsTo, [settings.IIIF_BASE_URL + "/book156/manifest"])
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Range.objects.get(identifier='book1', name="range1").belongsTo)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post("/book1/manifest", data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/manifest" in Range.objects.get(identifier='book1', name="range1").belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL +"/book156/manifest" in Range.objects.get(identifier='book1', name="range1").belongsTo)


@override_settings()
class Manifest_Test_DELETE_Without_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        self.data = {"manifest": self.client.get('/book1/manifest').data}
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False


    def test_a_manifest_can_be_deleted_sucessfully(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")

    def test_a_manifest_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]['error'], "'nonExistingItem' does not have a Manifest.")


    def test_deleting_a_manifest_will_delete_all_of_its_nested_objects(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        self.assertEqual(len(Annotation.objects), 0)
        self.assertEqual(len(AnnotationList.objects), 0)


@override_settings()
class Manifest_Test_DELETE_With_THREAD_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        self.data = {"manifest": self.client.get('/book1/manifest').data}
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'


    def test_a_manifest_can_be_deleted_sucessfully(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")

    def test_a_manifest_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]['error'], "'nonExistingItem' does not have a Manifest.")


    def test_deleting_a_manifest_will_delete_all_of_its_nested_objects(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        self.assertEqual(len(Annotation.objects), 0)
        self.assertEqual(len(AnnotationList.objects), 0)



@override_settings()
class Manifest_Test_DELETE_With_PROCESS_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        self.data = {"manifest": self.client.get('/book1/manifest').data}
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'


    def test_a_manifest_can_be_deleted_sucessfully(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")

    def test_a_manifest_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]['error'], "'nonExistingItem' does not have a Manifest.")


    def test_deleting_a_manifest_will_delete_all_of_its_nested_objects(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        self.assertEqual(len(Annotation.objects), 0)
        self.assertEqual(len(AnnotationList.objects), 0)



@override_settings()
class Manifest_Test_DELETE_With_CELERY_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        self.data = {"manifest": self.client.get('/book1/manifest').data}
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'


    def test_a_manifest_can_be_deleted_sucessfully(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")

    def test_a_manifest_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]['error'], "'nonExistingItem' does not have a Manifest.")


    def test_deleting_a_manifest_will_delete_all_of_its_nested_objects(self):
        response = self.client.delete("/book1/manifest")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted the Manifest of 'book1'.")
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        self.assertEqual(len(Annotation.objects), 0)
        self.assertEqual(len(AnnotationList.objects), 0)



class Manifest_Test_GET(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'password')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        self.data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', self.data)
        if settings.QUEUE_POST_ENABLED:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/manifest")
        self.data = {"manifest": self.client.get('/book1/manifest').data}


    def test_a_manifest_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/manifest")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "'nonExistingItem' does not have a Manifest.")

    def test_a_full_manifest_can_be_viewed(self):
        response = self.client.get("/book1/manifest")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["metadata"]), 4)
        self.assertEqual(len(response.data["sequences"]), 3)
        self.assertEqual(len(response.data["sequences"][0]["canvases"]), 5)
        self.assertEqual(len(response.data["sequences"][0]["canvases"][3]["images"]), 2)
        self.assertEqual(len(response.data["sequences"][0]["canvases"][2]["images"][0]["resource"]), 2)
        self.assertEqual(len(response.data["structures"]), 3)

    def test_a_full_sequence_can_be_viewed(self):
        sequence_name = Sequence.objects.get(label="Sequence1").name
        response = self.client.get("/book1/sequence/"+sequence_name)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["canvases"]), 5)
        self.assertEqual(len(response.data["canvases"][3]["images"]), 2)
        self.assertEqual(len(response.data["canvases"][2]["images"][0]["resource"]), 2)

    def test_a_full_canvas_can_be_viewed(self):
        response = self.client.get("/book1/canvas/canvas1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["images"]), 1)
        self.assertEqual(response.data["images"][0]["resource"]["@id"], 'http://example.org/iiif/book1/res/page1.jpg')

    def test_a_full_annotation_list_can_be_viewed(self):
        response = self.client.get("/book1/list/list1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], "sc:AnnotationList")

    def test_a_hidden_child_cannot_be_viewed(self):
        range1 = Range.objects.get(identifier='book1', name='range1')
        range1.hidden = True
        range1.save()
        response = self.client.get("/book1/manifest")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["structures"]), 2)
