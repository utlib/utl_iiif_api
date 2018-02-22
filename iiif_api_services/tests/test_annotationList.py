import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.AnnotationModel import Annotation


ANNOTATIONLIST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'annotationList', 'annotationListFull.json')
ANNOTATIONLIST_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'annotationList', 'annotationListMedium.json')
ANNOTATIONLIST_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'annotationList', 'annotationListShort.json')
URL = '/book1/list'


class AnnotationList_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        AnnotationList(label="annotationList1", identifier="book1", name="annotationList1", ATid="http://example.org/iiif/book1/list/annotationList1").save()
        AnnotationList(label="annotationList2", identifier="book1", name="annotationList2", ATid="http://example.org/iiif/book1/list/annotationList2").save()
        AnnotationList(label="annotationList3", identifier="book1", name="annotationList3", ATid="http://example.org/iiif/book1/list/annotationList3").save()

    def test_to_get_all_annotationLists_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_annotationList_of_an_item(self):
        response = self.client.get(URL+"/annotationList2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:AnnotationList')
        self.assertEqual(response.data["label"], 'annotationList2')

    def test_a_annotationList_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_annotationList_cannot_be_updated(self):
        response = self.client.put(URL+"/annotationList1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_annotationList_cannot_be_patched(self):
        response = self.client.patch(URL+"/annotationList1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_annotationList_cannot_be_deleted(self):
        response = self.client.delete(URL+"/annotationList1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class AnnotationList_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'testemail@mail.com', 'user1pass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_annotationList_can_be_successfully_created_with_no_nested_structures(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(AnnotationList.objects()[0].label, 'Awesome annotation list')
        self.assertEqual(AnnotationList.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/list/p100")

    def test_a_annotationList_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_MEDIUM).read())}
        self.assertEqual(len(Annotation.objects()), 0)
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(AnnotationList.objects()[0].label, 'Awesome annotation list')
        self.assertEqual(AnnotationList.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/list/p100")
        self.assertEqual(len(Annotation.objects()), 2)
        self.assertEqual(AnnotationList.objects()[0].ATid in Annotation.objects()[0].belongsTo, True)

    def test_a_annotationList_can_be_successfully_created_along_with_multi_level_nested_structures(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_FULL).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(AnnotationList.objects()[0].label, 'Awesome annotation list')
        self.assertEqual(AnnotationList.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/list/p100")
        self.assertEqual(len(Annotation.objects()), 9)
        self.assertEqual(Annotation.objects.get(name="a0t3").ATid, settings.IIIF_BASE_URL + "/book1/annotation/a0t3")
        self.assertEqual(Annotation.objects.get(name="a0t3").on, "https://wellcomelibrary.org/iiif/b28928118/canvas/c0#xywh=1,1719,1772,64")
        createdAnnotationListID = settings.IIIF_BASE_URL + "/book1/list/p100"
        self.assertEqual(createdAnnotationListID in Annotation.objects.get(identifier='book1', name='a0t3').belongsTo, True)
        self.assertEqual(AnnotationList.objects()[0].ATid in Annotation.objects.get(name="a0t3").belongsTo, True)

    def test_a_duplicate_annotationList_cannot_be_created(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')

    def test_a_annotationList_with_no_id_given_can_be_successfully_created(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_SHORT).read())}
        del data["annotationList"]["@id"]
        response = self.client.post("/UofT/list", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(AnnotationList.objects()[0].label, 'Awesome annotation list')

    def test_a_annotationList_cannot_be_created_if_id_does_not_match_with_identifier(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_SHORT).read())}
        response = self.client.post("/UofT/list", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "AnnotationList identifier must match with the identifier in @id.")

    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        annotation = Annotation.objects()[0]
        annotation.hidden = True
        annotation.save()
        response = self.client.get("/book1/list/p100")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["resources"]), 1)


class AnnotationList_Test_GET(APIMongoTestCase):
    def setUp(self):
        AnnotationList(label="annotationList1", identifier="book1", name="annotationList1", ATid="http://example.org/iiif/book1/list/annotationList1").save()

    def test_a_annotationList_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/list/annotationList1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "AnnotationList with name 'annotationList1' does not exist in identifier 'nonExistingItem'.")

    def test_a_annotationList_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingAnnotationList")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "AnnotationList with name 'nonExistingAnnotationList' does not exist in identifier 'book1'.")

    def test_a_annotationList_can_be_viewed(self):
        response = self.client.get("/book1/list/annotationList1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class AnnotationList_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        AnnotationList(label="annotationList1", identifier="book1", name="annotationList1", ATid="http://example.org/iiif/book1/list/annotationList1").save()
        AnnotationList(label="annotationList2", identifier="book1", name="annotationList2", ATid="http://example.org/iiif/book1/list/annotationList2").save()
        AnnotationList(label="annotationList3", identifier="book1", name="annotationList3", ATid="http://example.org/iiif/book1/list/annotationList3").save()

    def test_all_annotationLists_from_an_item_is_returned(self):
        response = self.client.get("/book1/list")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/list/annotationList1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/list/annotationList3")

    def test_a_annotationList_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/list")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class AnnotationList_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'testemail@mail.com', 'user1pass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        AnnotationList(label="annotationList1", identifier="book1", name="annotationList1", ATid="http://example.org/iiif/book1/list/annotationList1", ownedBy=["user1"]).save()
        AnnotationList(label="annotationList2", identifier="book1", name="annotationList2", ATid="http://example.org/iiif/book1/list/annotationList2", ownedBy=["user1"]).save()

    def test_a_annotationList_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/annotationList1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted AnnotationList 'annotationList1' from identifier 'book1'.")

    def test_a_annotationList_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/list/annotationList1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "AnnotationList with name 'annotationList1' does not exist in identifier 'nonExistingItem'.")

    def test_a_annotationList_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingAnnotationList")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "AnnotationList with name 'nonExistingAnnotationList' does not exist in identifier 'book1'.")

    def test_deleting_a_annotationList_will_delete_all_of_its_nested_objects(self):
        data = {"annotationList": json.loads(open(ANNOTATIONLIST_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/p100")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted AnnotationList 'p100' from identifier 'book1'.")
        self.assertEqual(len(Annotation.objects), 0)



class AnnotationList_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('user1', 'testemail@mail.com', 'user1pass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        AnnotationList(label="annotationList1", identifier="book1", name="annotationList1", ATid="http://example.org/iiif/book1/list/annotationList1", viewingHint="paged", ownedBy=["user1"]).save()
        AnnotationList(label="annotationList2", identifier="book1", name="annotationList2", ATid="http://example.org/iiif/book1/list/annotationList2", ownedBy=["user1"]).save()

    def test_a_annotationList_can_be_updated_sucessfully(self):
        data = {"annotationList": {"label": "new_annotationList1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/annotationList1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(AnnotationList.objects()[0].label, 'new_annotationList1')
        self.assertEqual(AnnotationList.objects()[0].viewingHint, 'non-paged')

    def test_a_annotationList_that_does_not_exist_cannot_be_updated(self):
        data = {"annotationList": {"label": "new_annotationList1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingAnnotationList", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "AnnotationList with name 'nonExistingAnnotationList' does not exist in identifier 'book1'.")

    def test_a_annotationList_with_new_id_can_be_updated_successfully(self):
        data = {"annotationList": {"@id": "http://example.org/iiif/new_book1/list/new_annotationList1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/annotationList1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(AnnotationList.objects()[0].ATid, settings.IIIF_BASE_URL + "/new_book1/list/new_annotationList1")

