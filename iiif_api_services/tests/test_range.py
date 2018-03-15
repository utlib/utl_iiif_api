import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas


RANGE_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'range', 'rangeMedium.json')
RANGE_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'range', 'rangeShort.json')
URL = '/book1/range'
MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'manifest', 'manifestFull.json')


class Range_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1").save()
        Range(label="range2", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range/range2").save()
        Range(label="range3", identifier="book1", name="range3", ATid="http://example.org/iiif/book1/range/range3").save()

    def test_to_get_all_ranges_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_range_of_an_item(self):
        response = self.client.get(URL+"/range2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:Range')
        self.assertEqual(response.data["label"], 'range2')

    def test_a_range_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_range_cannot_be_updated(self):
        response = self.client.put(URL+"/range1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_range_cannot_be_deleted(self):
        response = self.client.delete(URL+"/range1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class Range_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_range_can_be_successfully_created_with_no_nested_structures(self):
        data = {"range": json.loads(open(RANGE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Range.objects()[0].label, 'Table of Contents')
        self.assertEqual(Range.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/range/r0")

    def test_a_range_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(len(Range.objects()), 4)
        self.assertEqual(len(Canvas.objects()), 4)
        createdRangeID = settings.IIIF_BASE_URL + "/book1/range/r0"
        self.assertEqual(createdRangeID in Canvas.objects.get(identifier='book1', name='cover').belongsTo, True)
        self.assertEqual(createdRangeID in Canvas.objects.get(identifier='book1', name='backCover').belongsTo, True)

    def test_a_duplicate_range_cannot_be_created(self):
        data = {"range": json.loads(open(RANGE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')

    def test_a_range_with_no_id_given_can_be_successfully_created(self):
        data = {"range": json.loads(open(RANGE_SHORT).read())}
        del data["range"]["@id"]
        response = self.client.post("/identifier/range", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Range.objects()[0].label, 'Table of Contents')

    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        canvas = Canvas.objects.get(identifier='book1', name='cover')
        canvas.hidden = True
        canvas.save()
        response = self.client.get("/book1/range/r0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["members"]), 6)

    def test_an_already_existing_range_will_be_updated_from_a_POST_of_manifest(self):
        data = {"range": json.loads(open(RANGE_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(Range.objects.get(name="r0", identifier="book1").label, "Table of Contents")
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Range.objects.get(identifier="book1", name="r0").belongsTo)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        data["manifest"]["structures"][0]["@id"] = "http://example.org/iiif/book1/range/r0"
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Range.objects.get(name="r0", identifier="book1").label, "Range 1")
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/manifest" in Range.objects.get(identifier="book1", name="r0").belongsTo)

    def test_a_new_range_will_be_reated_from_a_POST_of_manifest(self):
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(len(Range.objects()), 4)

    def test_an_exisinting_child_canvas_will_be_updated_on_parent_creation(self):
        Canvas(label="cover", identifier="book1", name="cover", ATid="http://example.org/iiif/book1/canvas/cover").save()
        self.assertEqual(Canvas.objects.get(identifier="book1", name="cover").label, "cover")
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/range/r0" in Canvas.objects.get(identifier="book1", name="cover").belongsTo)
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="cover").label, "Front Cover")
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/r0" in Canvas.objects.get(identifier="book1", name="cover").belongsTo)

    def test_a_range_cannot_be_created_with_errors_in_nested_canvases(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["canvases"][1]["viewingHint"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_cannot_be_created_with_errors_in_nested_ranges(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["ranges"][1]["viewingHint"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_cannot_be_created_with_errors_in_nested_canvas(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["members"][1]["viewingHint"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_cannot_be_created_with_errors_in_nested_range(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["members"][2]["viewingHint"] = ["invalid"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_cannot_be_created_with_errors_in_nested_members_with_missing_type(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        del data["range"]["members"][2]["@type"]
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type is required for member object.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_cannot_be_created_with_errors_in_nested_members_with_invalid_type(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["members"][2]["@type"] = "invalid"
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type must be sc:Canvas or sc:Range.')
        self.assertEqual(len(Range.objects), 0)
        self.assertEqual(len(Canvas.objects), 0)

    def test_a_range_will_update_its_user_permissions_field(self):
        self.user = User.create_user('testStaff', 'testemail@mail.com', 'testStaffpass', False)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r0").ownedBy, ["testStaff"]) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r1").ownedBy, ["testStaff"]) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r2").ownedBy, ["testStaff"]) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r3").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="cover").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="backCover").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="coverBack").ownedBy, ["testStaff"]) 
        self.assertEqual(Canvas.objects.get(identifier="book1", name="coverBack2").ownedBy, ["testStaff"]) 


class Range_Test_GET(APIMongoTestCase):
    def setUp(self):
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1").save()

    def test_a_range_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/range/range1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "range with name 'range1' does not exist in identifier 'nonExistingItem'.")

    def test_a_range_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingRange")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "range with name 'nonExistingRange' does not exist in identifier 'book1'.")

    def test_a_range_can_be_viewed(self):
        response = self.client.get("/book1/range/range1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class Range_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1").save()
        Range(label="range2", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range/range2").save()
        Range(label="range3", identifier="book1", name="range3", ATid="http://example.org/iiif/book1/range/range3").save()

    def test_all_ranges_from_an_item_is_returned(self):
        response = self.client.get("/book1/range")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/range/range1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/range/range3")

    def test_a_range_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/range")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class Range_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1").save()
        Range(label="range2", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range/range2").save()

    def test_a_range_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/range1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Range 'range1' from identifier 'book1'.")

    def test_a_range_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/range/range1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Range with name 'range1' does not exist in identifier 'nonExistingItem'.")

    def test_a_range_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingRange")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Range with name 'nonExistingRange' does not exist in identifier 'book1'.")

    def test_deleting_a_range_will_delete_all_of_its_nested_objects(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/r0")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Range 'r0' from identifier 'book1'.")
        self.assertEqual(len(Canvas.objects), 0)



class Range_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Range(label="range1", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range/range1", viewingHint="paged").save()
        Range(label="range2", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range/range2").save()


    def test_a_range_can_be_updated_sucessfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        data["range"]["label"] = "new_range1"
        data["range"]["viewingHint"] = "non-paged"
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Range.objects.get(identifier="book1", name="r0").label, 'new_range1')
        self.assertEqual(Range.objects.get(identifier="book1", name="r0").viewingHint, 'non-paged')

    def test_a_range_with_invalid_data_cannot_be_updated_sucessfully(self):
        data = {"range": {"label": "new_range1", "viewingHint": ["non-paged"]}}
        response = self.client.put(URL+"/range1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], 'Not a valid string.')

    def test_a_range_that_does_not_exist_cannot_be_updated(self):
        data = {"range": {"label": "new_range1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingRange", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Range with name 'nonExistingRange' does not exist in identifier 'book1'.")

    def test_a_range_with_new_id_can_be_updated_successfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        data = {"range": {"@id": "http://example.org/iiif/new_book1/range/new_range1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Range.objects.get(identifier="new_book1", name="new_range1").ATid, settings.IIIF_BASE_URL + "/new_book1/range/new_range1")

    def test_a_range_with_nested_objects_can_be_updated_successfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r1").label, "Introduction")
        data["range"]["members"][1]["label"] = 'NEW LABEL'
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertEqual(Range.objects.get(identifier="book1", name="r1").label, "NEW LABEL")

    def test_a_range_with_invalid_nested_canvas_cannot_be_updated_successfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        data["range"]["canvases"][1]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY) 
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], 'Not a valid string.')

    def test_a_range_with_invalid_nested_range_cannot_be_updated_successfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        data["range"]["ranges"][1]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY) 
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], 'Not a valid string.')

    def test_a_range_with_invalid_nested_member_cannot_be_updated_successfully(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["members"][2]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY) 
        self.assertEqual(response.data["responseBody"]["error"]["viewingHint"][0], 'Not a valid string.')

    def test_a_range_with_new_id_will_update_its_nested_objects_belongsTo_field(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"])
        self.assertEqual(Canvas.objects.get(identifier='book1', name='cover').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='backCover').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='coverBack').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='coverBack2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r1').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r3').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/r0")
        data["range"]["@id"] = "http://example.org/iiif/book1/range/not-r0"
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertEqual(Canvas.objects.get(identifier='book1', name='cover').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='backCover').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='coverBack').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Canvas.objects.get(identifier='book1', name='coverBack2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r1').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r2').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")
        self.assertEqual(Range.objects.get(identifier='book1', name='r3').belongsTo[0], settings.IIIF_BASE_URL+"/book1/range/not-r0")

    def test_a_range_cannot_be_updated_with_errors_in_nested_canvas(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["canvases"][0]["height"] = "invalid"
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['height'][0], 'A valid integer is required.')

    def test_a_range_cannot_be_updated_with_errors_in_nested_range(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["ranges"][0]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')

    def test_a_range_cannot_be_updated_with_errors_in_nested_member_canvas(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["members"][2]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')

    def test_a_range_cannot_be_updated_with_errors_in_nested_member_range(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["members"][1]["viewingHint"] = ["invalid"]
        response = self.client.put(URL+"/r0", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], 'Not a valid string.')

    def test_a_range_can_be_updated_with_a_new_belongsTo_field_will_replace_existing_values(self):
        Range(label="p1", identifier="book1", name="r0", ATid="http://example.org/iiif/book1/range/r0", belongsTo=[settings.IIIF_BASE_URL +"/book1/manifest"]).save()
        self.assertEqual(Range.objects.get(identifier='book1', name="r0").belongsTo, [settings.IIIF_BASE_URL + "/book1/manifest"])
        self.assertFalse("http://example.org/iiif/book2/manifest" in Range.objects.get(identifier='book1', name="r0").belongsTo)
        data = {"range": {"belongsTo": ["http://example.org/iiif/book2/manifest"]}}
        response = self.client.put('/book1/range/r0', data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK) 
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/manifest" in Range.objects.get(identifier='book1', name="r0").belongsTo)
        self.assertTrue("http://example.org/iiif/book2/manifest" in Range.objects.get(identifier='book1', name="r0").belongsTo)

    def test_an_embedded_canvas_updated_with_a_new_belongsTo_field_will_append_existing_values(self):
        Canvas(label="normal", identifier="book1", name="cover", ATid="http://example.org/iiif/book1/canvas/cover", belongsTo=[settings.IIIF_BASE_URL +"/book1/range/r2"]).save()
        self.assertEqual(Canvas.objects.get(identifier='book1', name="cover").belongsTo, [settings.IIIF_BASE_URL + "/book1/range/r2"])
        self.assertFalse(settings.IIIF_BASE_URL + "/book1/range/r0" in Canvas.objects.get(identifier='book1', name="cover").belongsTo)
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post("/book1/range", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED) 
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/r2" in Canvas.objects.get(identifier='book1', name="cover").belongsTo)
        self.assertTrue(settings.IIIF_BASE_URL + "/book1/range/r0" in Canvas.objects.get(identifier='book1', name="cover").belongsTo)

    def test_a_range_cannot_be_updated_with_errors_in_nested_members_with_missing_type(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        del data["range"]["members"][2]["@type"]
        response = self.client.put('/book1/range/r0', data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type is required for member object.')

    def test_a_range_cannot_be_updated_with_errors_in_nested_members_with_invalid_type(self):
        data = {"range": json.loads(open(RANGE_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        data["range"]["members"][2]["@type"] = "invalid"
        response = self.client.put('/book1/range/r0', data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"], 'Field @type must be sc:Canvas or sc:Range.')
