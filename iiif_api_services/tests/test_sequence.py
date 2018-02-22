import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation


SEQUENCE_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'sequence', 'sequenceFull.json')
SEQUENCE_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'sequence', 'sequenceMedium.json')
SEQUENCE_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'sequence', 'sequenceShort.json')
URL = '/book1/sequence'
MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'sequence', 'manifestFull.json')


class Sequence_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Sequence(label="sequence1", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence/sequence1").save()
        Sequence(label="sequence2", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2").save()
        Sequence(label="sequence3", identifier="book1", name="sequence3", ATid="http://example.org/iiif/book1/sequence/sequence3").save()

    def test_to_get_all_sequences_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_sequence_of_an_item(self):
        response = self.client.get(URL+"/sequence2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:Sequence')
        self.assertEqual(response.data["label"], 'sequence2')

    def test_a_sequence_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_sequence_cannot_be_updated(self):
        response = self.client.put(URL+"/sequence1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_sequence_cannot_be_deleted(self):
        response = self.client.delete(URL+"/sequence1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class Sequence_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_sequence_can_be_successfully_created_with_no_nested_structures(self):
        data = {"sequence": json.loads(open(SEQUENCE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(response.data["responseBody"]["@id"], settings.IIIF_BASE_URL+"/book1/sequence/normal")
        self.assertEqual(Sequence.objects()[0].label, 'Current Page Order')


    def test_a_sequence_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects()[0].label, 'Current Page Order')
        self.assertEqual(len(Canvas.objects()), 3)
        self.assertEqual(Canvas.objects()[1].ATid, settings.IIIF_BASE_URL + "/book1/canvas/p2")
        createdSequenceID = settings.IIIF_BASE_URL + "/book1/sequence/normal"
        self.assertEqual(createdSequenceID in Canvas.objects.get(identifier='book1', name='p1').belongsTo, True)
        self.assertEqual(createdSequenceID in Canvas.objects.get(identifier='book1', name='p2').belongsTo, True)
        self.assertEqual(createdSequenceID in Canvas.objects.get(identifier='book1', name='p3').belongsTo, True)

    def test_a_sequence_cannot_be_created_with_errors_in_nested_structures(self):
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        data["sequence"]["canvases"][0]["height"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['height'][0], 'A valid integer is required.')
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_nested_structures_created_previously_before_errors_will_be_cleaned_if_error_happens_after(self):
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        data["sequence"]["canvases"][2]["height"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['height'][0], 'A valid integer is required.')
        self.assertEqual(len(Sequence.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)


    def test_a_sequence_can_be_successfully_created_along_with_multi_level_nested_structures(self):
        data = {"sequence": json.loads(open(SEQUENCE_FULL).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects()[0].label, 'Sequence s0')
        self.assertEqual(Sequence.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/sequence/s0")
        self.assertEqual(len(Canvas.objects()), 2)
        self.assertEqual(Canvas.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/canvas/c0")
        self.assertEqual(len(Annotation.objects()), 2)
        self.assertEqual(Annotation.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/annotation/a1")
        self.assertEqual(Annotation.objects()[0].on, settings.IIIF_BASE_URL + "/book1/canvas/c0")
        createdSequenceID = settings.IIIF_BASE_URL + "/book1/sequence/s0"
        self.assertEqual(createdSequenceID in Canvas.objects.get(identifier='book1', name='c0').belongsTo, True)
        self.assertEqual(createdSequenceID in Canvas.objects.get(identifier='book1', name='c1').belongsTo, True)
        createdAnnotationID1 = settings.IIIF_BASE_URL + "/book1/annotation/a1"
        createdAnnotationID2 = settings.IIIF_BASE_URL + "/book1/annotation/a2"


    def test_a_duplicate_sequence_cannot_be_created(self):
        data = {"sequence": json.loads(open(SEQUENCE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')


    def test_a_sequence_with_no_id_given_can_be_successfully_created(self):
        data = {"sequence": json.loads(open(SEQUENCE_SHORT).read())}
        del data["sequence"]["@id"]
        response = self.client.post("/UofT/sequence", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects()[0].label, 'Current Page Order')


    def test_a_sequence_cannot_be_created_if_id_does_not_match_with_identifier(self):
        data = {"sequence": json.loads(open(SEQUENCE_SHORT).read())}
        response = self.client.post("/UofT/sequence", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "Sequence identifier must match with the identifier in @id.")


    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        canvas = Canvas.objects.get(identifier='book1', name='p1')
        canvas.hidden = True
        canvas.save()
        response = self.client.get("/book1/sequence/normal")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["canvases"]), 2)


    def test_an_already_existing_sequence_will_be_updated_from_a_POST_of_manifest(self):
        data = {"sequence": json.loads(open(SEQUENCE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Sequence.objects.get(identifier="book1", name="normal").viewingDirection, "left-to-right")
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Sequence.objects.get(identifier="book1", name="normal").belongsTo)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        data["manifest"]["sequences"][1]["@id"] = "http://example.org/iiif/book1/sequence/normal"
        data["manifest"]["sequences"][1]["viewingDirection"] = "NEW"
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects.get(identifier="book1", name="normal").viewingDirection, "NEW")
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/manifest" in Sequence.objects.get(identifier="book1", name="normal").belongsTo)


    def test_a_new_sequence_will_created_from_a_POST_of_manifest(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Sequence.objects.get(identifier="book1", name="sequence2").viewingDirection, "right-to-left")


    def test_a_sequence_will_update_its_user_permissions_field(self):
        self.user = User.create_user('testStaff', 'testemail@mail.com', 'testStaffpass', False)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED) 
        self.assertEqual(Sequence.objects.get(identifier="book1", name="normal").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="p1").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="p2").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="p3").ownedBy, ["testStaff"]) 


class Sequence_Test_GET(APIMongoTestCase):
    def setUp(self):
        Sequence(label="sequence1", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence/sequence1").save()

    def test_a_sequence_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/sequence/sequence1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Sequence with name 'sequence1' does not exist in identifier 'nonExistingItem'.")

    def test_a_sequence_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingSequence")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Sequence with name 'nonExistingSequence' does not exist in identifier 'book1'.")

    def test_a_sequence_can_be_viewed(self):
        response = self.client.get("/book1/sequence/sequence1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_to_view_a_sequence_not_embedded_entirely_in_manifest(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        data["manifest"]["sequences"].append({"@id": "http://example.org/iiif/book1/sequence/normal2", "label": "2nd Sequence", "viewingDirection": "right-to-left"})
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        self.assertEqual(Sequence.objects().get(identifier="book1", name="normal2").viewingDirection, "right-to-left")
        response = self.client.get('/book1/manifest')
        self.assertFalse("viewingDirection" in response.data["sequences"][1])


class Sequence_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        Sequence(label="sequence1", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence/sequence1").save()
        Sequence(label="sequence2", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2").save()
        Sequence(label="sequence3", identifier="book1", name="sequence3", ATid="http://example.org/iiif/book1/sequence/sequence3").save()

    def test_all_sequences_from_an_item_is_returned(self):
        response = self.client.get("/book1/sequence")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/sequence/sequence1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/sequence/sequence3")

    def test_a_sequence_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/sequence")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class Sequence_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Sequence(label="sequence1", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence/sequence1").save()
        Sequence(label="sequence2", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2").save()

    def test_a_sequence_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/sequence1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Sequence 'sequence1' from identifier 'book1'.")

    def test_a_sequence_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/sequence/sequence1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Sequence with name 'sequence1' does not exist in identifier 'nonExistingItem'.")

    def test_a_sequence_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingSequence")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Sequence with name 'nonExistingSequence' does not exist in identifier 'book1'.")

    def test_deleting_a_sequence_will_delete_all_of_its_nested_objects(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/normal")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Sequence 'normal' from identifier 'book1'.")
        self.assertEqual(len(Canvas.objects), 0)


class Sequence_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Sequence(label="sequence1", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence/sequence1", viewingHint="paged").save()
        Sequence(label="sequence2", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence/sequence2").save()

    def test_a_sequence_can_be_updated_sucessfully(self):
        data = {"sequence": {"label": "new_sequence1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/sequence1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Sequence.objects.get(identifier="book1", name="sequence1").label, 'new_sequence1')
        self.assertEqual(Sequence.objects.get(identifier="book1", name="sequence1").viewingHint, 'non-paged')

    def test_a_sequence_with_invalid_data_cannot_be_updated(self):
        data = {"sequence": {"label": "new_sequence1", "viewingHint": ["invalid"]}}
        response = self.client.put(URL+"/sequence1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], 'Not a valid string.')

    def test_a_sequence_that_does_not_exist_cannot_be_updated(self):
        data = {"sequence": {"label": "new_sequence1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingSequence", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Sequence with name 'nonExistingSequence' does not exist in identifier 'book1'.")

    def test_a_sequence_with_new_id_can_be_updated_successfully(self):
        data = {"sequence": {"@id": "http://example.org/iiif/new_book1/sequence/new_sequence1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/sequence1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Sequence.objects.get(identifier="new_book1", name="new_sequence1").ATid, settings.IIIF_BASE_URL + "/new_book1/sequence/new_sequence1")

    def test_a_sequence_with_nested_objects_can_be_updated_successfully(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Canvas.objects.get(identifier="book1", name="p1").label, "p. 1")
        data["sequence"]["canvases"][0]["label"] = 'NEW LABEL'
        response = self.client.put(URL+"/normal", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="p1").label, "NEW LABEL")

    def test_a_sequence_with_invalid_nested_objects_cannot_be_updated_successfully(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["sequence"]["canvases"][0]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/normal", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY) 
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], "Not a valid string.")

    def test_a_sequence_with_new_id_will_update_its_nested_objects_belongsTo_field(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p1').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/normal")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/normal")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p3').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/normal")
        data["sequence"]["@id"] = "http://example.org/iiif/book1/sequence/not-normal"
        response = self.client.put(URL+"/normal", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p1').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/not-normal")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/not-normal")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='p3').belongsTo[0], settings.IIIF_BASE_URL+"/book1/sequence/not-normal")

    def test_a_sequence_cannot_be_updated_with_errors_in_nested_structures(self):
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["sequence"]["canvases"][0]["height"] = "invalid"
        response = self.client.put(URL+"/normal", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['height'][0], 'A valid integer is required.')
        self.assertEqual(len(Sequence.objects), 3)
        self.assertEqual(len(Canvas.objects), 3)

    def test_a_sequence_can_be_updated_with_a_new_belongsTo_field_will_replace_existing_values(self):
        Sequence(label="p1", identifier="book1", name="normal", ATid="http://example.org/iiif/book1/sequence/normal", belongsTo=[settings.IIIF_BASE_URL +"/book1/manifest"]).save()
        self.assertEqual(Sequence.objects.get(identifier='book1', name="normal").belongsTo, [settings.IIIF_BASE_URL + "/book1/manifest"])
        self.assertFalse("http://example.org/iiif/book2/manifest" in Sequence.objects.get(identifier='book1', name="normal").belongsTo)
        data = {"sequence": {"belongsTo": ["http://example.org/iiif/book2/manifest"]}}
        response = self.client.put('/book1/sequence/normal', data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Sequence.objects.get(identifier='book1', name="normal").belongsTo)
        self.assertTrue("http://example.org/iiif/book2/manifest" in Sequence.objects.get(identifier='book1', name="normal").belongsTo)

    def test_an_embedded_canvas_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Canvas(label="normal", identifier="book1", name="p1", ATid="http://example.org/iiif/book1/canvas/p1", belongsTo=[settings.IIIF_BASE_URL +"/book1/sequence/normal2"]).save()
        self.assertEqual(Canvas.objects.get(identifier='book1', name="p1").belongsTo, [settings.IIIF_BASE_URL + "/book1/sequence/normal2"])
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/sequence/normal" in Canvas.objects.get(identifier='book1', name="p1").belongsTo)
        data = {"sequence": json.loads(open(SEQUENCE_MEDIUM).read())}
        response = self.client.post("/book1/sequence", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED) 
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/sequence/normal2" in Canvas.objects.get(identifier='book1', name="p1").belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/sequence/normal" in Canvas.objects.get(identifier='book1', name="p1").belongsTo)

