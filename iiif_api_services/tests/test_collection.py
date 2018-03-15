import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.models.ManifestModel import Manifest
from django.test import override_settings


COLLECTION_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'collection', 'collectionMedium.json')
COLLECTION_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'collection', 'collectionShort.json')
URL = '/collections'


class Collection_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collections/book1").save()
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        Collection(label="collection3", name="book3", ATid="http://example.org/iiif/collections/book3").save()

    def test_to_get_a_specific_collection_of_an_name(self):
        response = self.client.get('/collections/book1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:Collection')
        self.assertEqual(response.data["label"], 'collection1')

    def test_a_collection_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_collection_cannot_be_updated(self):
        response = self.client.put('/collections/book2', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_collection_cannot_be_deleted(self):
        response = self.client.delete('/collections/book3', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings()
class Collection_Test_POST_Without_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False

    def test_a_collection_can_be_successfully_created_with_no_nested_structures(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label parent')
        self.assertEqual(Collection.objects()[0].ATid, settings.IIIF_BASE_URL + "/collections/book1")


    def test_a_collection_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label child')
        self.assertEqual(Collection.objects()[0].ATid, settings.IIIF_BASE_URL + "/collections/top6")
        self.assertEqual(len(Collection.objects()), 4)
        self.assertEqual(len(Manifest.objects()), 3)
        createdCollectionID = settings.IIIF_BASE_URL + "/collections/book1"
        self.assertEqual(createdCollectionID in Collection.objects.get(name='top6').belongsTo, True)
        self.assertEqual(createdCollectionID in Manifest.objects.get(identifier='book1').belongsTo, True)

    def test_a_duplicate_collection_cannot_be_created(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["name"], ['This field must be unique.'])

    def test_a_collection_with_no_id_given_can_be_successfully_created(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        del data["collection"]["@id"]
        response = self.client.post("/collections", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label parent')

    def test_a_collection_cannot_be_created_with_id_being_top_level_collection_name(self):
        data = {"collection": {"@id": settings.IIIF_BASE_URL + "/collections/"+settings.TOP_LEVEL_COLLECTION_NAME}}
        response = self.client.post("/collections", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "Collection name cannot be: "+settings.TOP_LEVEL_COLLECTION_NAME+".")

    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.get("/collections/book1")
        self.assertEqual(len(response.data["manifests"]), 3)
        manifest = Manifest.objects.get(identifier='book1')
        manifest.hidden = True
        manifest.save()
        response = self.client.get("/collections/book1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["collections"]), 3)
        self.assertEqual(len(response.data["manifests"]), 2)

    def test_an_exisinting_child_collection_will_be_updated_on_parent_creation(self):
        Collection(label="top6", name="top6", ATid="http://example.org/iiif/collections/top6", ownedBy=["staff"]).save()
        self.assertEqual(Collection.objects.get(name="top6").label, "top6")
        self.assertFalse(settings.IIIF_BASE_URL + "/collections/book1" in Collection.objects.get(name="top6").belongsTo)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.get(name="top6").label, "some collection label child")
        self.assertTrue(settings.IIIF_BASE_URL + "/collections/book1" in Collection.objects.get(name="top6").belongsTo)

    def test_a_collection_cannot_be_created_with_errors_in_nested_collections(self):
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["collections"][1]["total"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['total'][0], 'A valid integer is required.')
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)

    def test_a_collection_cannot_be_created_with_errors_in_nested_manifests(self):
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["manifests"][1]["viewingDirection"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingDirection'][0], 'Not a valid string.')
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)


    def test_a_collection_cannot_be_created_with_errors_in_nested_members(self):
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["members"][1]["total"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['total'][0], 'A valid integer is required.')
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)

    def test_a_collection_cannot_be_created_with_errors_in_nested_members_with_missing_type(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        del data["collection"]["members"][1]["@type"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type is required for member object.')

    def test_a_collection_cannot_be_created_with_errors_in_nested_members_with_invalid_type(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        data["collection"]["members"][1]["@type"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type must be sc:Collection or sc:Manifest.')

    def test_a_collection_created_with_errors_in_nested_members_will_clean_previous_members(self):
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        data["collection"]["members"][0]["viewingDirection"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingDirection"][0], 'Not a valid string.')
        self.assertEqual(len(Collection.objects), 0)
        self.assertEqual(len(Manifest.objects), 0)

    def test_a_collection_with_will_create_its_user_permissions_field(self):
        self.user = User.create_user('testStaff', 'testemail@mail.com', 'testStaffpass', False)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.get(name="book1").ownedBy, ["testStaff"]) 
        self.assertEqual(Collection.objects.get(name="top6").ownedBy, ["testStaff"]) 
        self.assertEqual(Collection.objects.get(name="top98").ownedBy, ["testStaff"]) 
        self.assertEqual(Collection.objects.get(name="top6666").ownedBy, ["testStaff"]) 
        self.assertEqual(Manifest.objects.get(identifier="book1").ownedBy, ["testStaff"]) 
        self.assertEqual(Manifest.objects.get(identifier="book2").ownedBy, ["testStaff"]) 
        self.assertEqual(Manifest.objects.get(identifier="book3").ownedBy, ["testStaff"]) 


@override_settings()
class Collection_Test_POST_With_THREAD_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'

    def test_a_collection_can_be_successfully_created_with_no_nested_structures(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label parent')
        self.assertEqual(Collection.objects()[0].ATid, settings.IIIF_BASE_URL + "/collections/book1")


@override_settings()
class Collection_Test_POST_With_PROCESS_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'

    def test_a_collection_can_be_successfully_created_with_no_nested_structures(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label parent')
        self.assertEqual(Collection.objects()[0].ATid, settings.IIIF_BASE_URL + "/collections/book1")


@override_settings()
class Collection_Test_POST_With_CELERY_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'

    def test_a_collection_can_be_successfully_created_with_no_nested_structures(self):
        data = {"collection": json.loads(open(COLLECTION_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects()[0].label, 'some collection label parent')
        self.assertEqual(Collection.objects()[0].ATid, settings.IIIF_BASE_URL + "/collections/book1")



class Collection_Test_GET(APIMongoTestCase):
    def setUp(self):
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collections/book1").save()

    def test_a_collection_from_an_name_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/collections/nonExistingCollection")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Collection with name 'nonExistingCollection' does not exist.")

    def test_default_top_level_collection_can_be_viewed(self):
        response = self.client.get("/collections/"+settings.TOP_LEVEL_COLLECTION_NAME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + "/collections/"+settings.TOP_LEVEL_COLLECTION_NAME)

    def test_default_uoft_collection_can_be_viewed_from_root_endpoint(self):
        response = self.client.get("/collections")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATid"], settings.IIIF_BASE_URL + "/collections/"+settings.TOP_LEVEL_COLLECTION_NAME)

    def test_a_collection_can_be_viewed(self):
        response = self.client.get("/collections/book1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings()
class Collection_Test_DELETE_Without_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False

    def test_a_collection_can_be_deleted_sucessfully(self):
        response = self.client.delete("/collections/book2")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Collection 'book2'.")

    def test_a_collection_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/collections/nonExistingItem")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Collection with name 'nonExistingItem' does not exist.")

    def test_deleting_a_collection_will_delete_all_of_its_nested_objects(self):
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Collection.objects), 1)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete("/collections/book1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Collection 'book1'.")
        self.assertEqual(len(Manifest.objects), 0)
        self.assertEqual(len(Collection.objects), 1)


@override_settings()
class Collection_Test_DELETE_With_THREAD_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'

    def test_a_collection_can_be_deleted_sucessfully(self):
        response = self.client.delete("/collections/book2")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Collection 'book2'.")



@override_settings()
class Collection_Test_DELETE_With_PROCESS_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'

    def test_a_collection_can_be_deleted_sucessfully(self):
        response = self.client.delete("/collections/book2")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Collection 'book2'.")



@override_settings()
class Collection_Test_DELETE_With_CELERY_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'

    def test_a_collection_can_be_deleted_sucessfully(self):
        response = self.client.delete("/collections/book2")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Collection 'book2'.")


@override_settings()
class Collection_Test_PUT_Without_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collectionsShort/book1", viewingHint="paged").save()
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = False
        settings.QUEUE_PUT_ENABLED = False
        settings.QUEUE_DELETE_ENABLED = False

    def test_a_collection_can_be_updated_sucessfully(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects()[0].label, 'new_collection1')
        self.assertEqual(Collection.objects()[0].viewingHint, 'non-paged')

    def test_a_collection_cannot_be_updated_with_invalid_data(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": ["non-paged"]}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_an_name_collection_that_does_not_exist_cannot_be_updated(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/nonExistingCollection", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Collection with name 'nonExistingCollection' does not exist.")

    def test_a_collection_with_new_id_can_be_updated_successfully(self):
        data = {"collection": {"@id": "http://example.org/iiif/collections/new_book1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL + "/collections/new_book1")

    def test_the_top_level_collection_cannot_be_updated(self):
        data = {"collection": {"@id": "http://example.org/iiif/collections/new_book1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/"+settings.TOP_LEVEL_COLLECTION_NAME, data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        print response.data["responseBody"]
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "Top level Collection cannot be edited.")

    def test_a_collection_with_nested_objects_can_be_updated_successfully(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Collection.objects()[2].label, 'some collection label child')
        data["collection"]["collections"][0]["label"] = 'NEW LABEL'
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects()[2].label, "NEW LABEL")

    def test_a_collection_with_nested_objects_no_id_can_be_updated_successfully(self):
        self.assertEqual(len(Manifest.objects), 0)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(len(Manifest.objects), 3)
        del data["collection"]["members"][0]["@id"]
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Manifest.objects), 4)

    def test_a_collection_with_new_id_will_update_its_nested_objects_belongsTo_field(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Collection.objects.get(name='top6').belongsTo[0], settings.IIIF_BASE_URL + "/collections/book3")
        self.assertEqual(Collection.objects.get(name='top98').belongsTo[0], settings.IIIF_BASE_URL + "/collections/book3")
        self.assertEqual(Collection.objects.get(name='top6666').belongsTo[0], settings.IIIF_BASE_URL + "/collections/book3")
        data["collection"]["@id"] = "http://example.org/iiif/collections/not-book3"
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects.get(name='top6').belongsTo[0], settings.IIIF_BASE_URL + "/collections/not-book3")
        self.assertEqual(Collection.objects.get(name='top98').belongsTo[0], settings.IIIF_BASE_URL + "/collections/not-book3")
        self.assertEqual(Collection.objects.get(name='top6666').belongsTo[0], settings.IIIF_BASE_URL + "/collections/not-book3")

    def test_a_collection_with_new_id_will_update_its_parent_objects_children_field(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book35"
        data["collection"]['members'][1]['collections'] = [{"@id": "http://example.org/iiif/collection/book_3_child"}]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Collection.objects.get(name='book_3_child').belongsTo[0], settings.IIIF_BASE_URL + "/collections/top6666")
        self.assertEqual(Collection.objects.get(name='top6666').children[0], settings.IIIF_BASE_URL + "/collections/book_3_child")
        data = {"collection": {"@id": "http://example.org/iiif/collections/not_book3_child"}}
        response = self.client.put(URL+"/book_3_child", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects.get(name='not_book3_child').belongsTo[0], settings.IIIF_BASE_URL + "/collections/top6666")
        self.assertEqual(Collection.objects.get(name='top6666').children[0], settings.IIIF_BASE_URL + "/collections/not_book3_child")

    def test_a_collection_cannot_be_updated_with_errors_in_nested_collections(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["collection"]["collections"][1]["total"] = "invalid"
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['total'][0], 'A valid integer is required.')

    def test_a_collection_cannot_be_updated_with_errors_in_nested_collections(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["collection"]["collections"][1]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_a_collection_can_be_updated_with_nested_members_with_missing_id(self):
        self.assertEqual(len(Collection.objects), 2)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(len(Collection.objects), 6)
        del data["collection"]["members"][1]["@id"]
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(len(Collection.objects), 7)

    def test_a_collection_cannot_be_updated_with_errors_in_nested_members_with_missing_type(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        del data["collection"]["members"][1]["@type"]
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type is required for member object.')

    def test_a_collection_cannot_be_updated_with_errors_in_nested_members_with_invalid_type(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["collection"]["members"][1]["@type"] = "invalid"
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type must be sc:Collection or sc:Manifest.')

    def test_a_collection_cannot_be_updated_with_errors_in_nested_manifests(self):
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["collection"]["manifests"][1]["viewingDirection"] = ["invalid"]
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingDirection'][0], 'Not a valid string.')

    def test_a_collection_can_be_updated_with_a_new_belongsTo_field_will_replace_existing_values(self):
        Collection(label="collection2", name="book3", ATid="http://example.org/iiif/collections/book3", belongsTo=[settings.IIIF_BASE_URL +"/collections/book1"]).save()
        self.assertEqual(Collection.objects.get(name='book3').belongsTo, [settings.IIIF_BASE_URL + "/collections/book1"])
        self.assertFalse("http://example.org/iiif/collections/book2" in Collection.objects.get(name='book3').belongsTo)
        data = {"collection": {"belongsTo": ["http://example.org/iiif/collections/book2"]}}
        response = self.client.put(URL+"/book3", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertFalse(settings.IIIF_BASE_URL + "/collections/book1" in Collection.objects.get(name='book3').belongsTo)
        self.assertTrue("http://example.org/iiif/collections/book2" in Collection.objects.get(name='book3').belongsTo)

    def test_an_embedded_collection_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Collection(label="top6", name="top6", ATid="http://example.org/iiif/collections/top6", belongsTo=[settings.IIIF_BASE_URL +"/collections/book156"]).save()
        self.assertEqual(Collection.objects.get(name='top6').belongsTo, [settings.IIIF_BASE_URL + "/collections/book156"])
        self.assertFalse(settings.IIIF_BASE_URL + "/collections/book3" in Collection.objects.get(name='top6').belongsTo)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertTrue(settings.IIIF_BASE_URL + "/collections/book3" in Collection.objects.get(name='top6').belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL +"/collections/book156" in Collection.objects.get(name='top6').belongsTo)

    def test_an_embedded_manifest_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Manifest(label="top6", identifier="book1", ATid="http://example.org/iiif/book1/manifest", belongsTo=[settings.IIIF_BASE_URL +"/collections/book156"]).save()
        self.assertEqual(Manifest.objects.get(identifier='book1').belongsTo, [settings.IIIF_BASE_URL + "/collections/book156"])
        self.assertFalse(settings.IIIF_BASE_URL + "/collections/book3" in Manifest.objects.get(identifier='book1').belongsTo)
        data = {"collection": json.loads(open(COLLECTION_MEDIUM).read())}
        data["collection"]["@id"] = "http://example.org/iiif/collections/book3"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertTrue(settings.IIIF_BASE_URL + "/collections/book3" in Manifest.objects.get(identifier='book1').belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL +"/collections/book156" in Manifest.objects.get(identifier='book1').belongsTo)


@override_settings()
class Collection_Test_PUT_With_THREAD_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collectionsShort/book1", viewingHint="paged").save()
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'THREAD'

    def test_a_collection_can_be_updated_sucessfully(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects()[0].label, 'new_collection1')
        self.assertEqual(Collection.objects()[0].viewingHint, 'non-paged')



@override_settings()
class Collection_Test_PUT_With_PROCESS_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collectionsShort/book1", viewingHint="paged").save()
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'PROCESS'

    def test_a_collection_can_be_updated_sucessfully(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects()[0].label, 'new_collection1')
        self.assertEqual(Collection.objects()[0].viewingHint, 'non-paged')



@override_settings()
class Collection_Test_PUT_With_CELERY_QUEUE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Collection(label="collection1", name="book1", ATid="http://example.org/iiif/collectionsShort/book1", viewingHint="paged").save()
        Collection(label="collection2", name="book2", ATid="http://example.org/iiif/collections/book2").save()
        settings.QUEUE_POST_ENABLED = True
        settings.QUEUE_PUT_ENABLED = True
        settings.QUEUE_DELETE_ENABLED = True
        settings.QUEUE_RUNNER = 'CELERY'

    def test_a_collection_can_be_updated_sucessfully(self):
        data = {"collection": {"label": "new_collection1", "viewingHint": "non-paged"}}
        response = self.client.put("/collections/book1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Collection.objects()[0].label, 'new_collection1')
        self.assertEqual(Collection.objects()[0].viewingHint, 'non-paged')