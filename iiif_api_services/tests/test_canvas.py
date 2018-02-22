import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation


CANVAS_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'canvas', 'canvasFull.json')
CANVAS_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'canvas', 'canvasMedium.json')
CANVAS_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'canvas', 'canvasShort.json')
URL = '/book1/canvas'


class Canvas_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Canvas(label="canvas1", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas/canvas1").save()
        Canvas(label="canvas2", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas/canvas2").save()
        Canvas(label="canvas3", identifier="book1", name="canvas3", ATid="http://example.org/iiif/book1/canvas/canvas3").save()

    def test_to_get_all_canvass_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_canvas_of_an_item(self):
        response = self.client.get(URL+"/canvas2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:Canvas')
        self.assertEqual(response.data["label"], 'canvas2')

    def test_a_canvas_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_canvas_cannot_be_updated(self):
        response = self.client.put(URL+"/canvas1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_canvas_cannot_be_deleted(self):
        response = self.client.delete(URL+"/canvas1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class Canvas_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_canvas_can_be_successfully_created_with_no_nested_structures(self):
        data = {"canvas": json.loads(open(CANVAS_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Canvas.objects()[0].label, 'p. 1')
        self.assertEqual(Canvas.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/canvas/p1")

    def test_a_canvas_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"canvas": json.loads(open(CANVAS_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Canvas.objects()[0].label, 'p. 1')
        self.assertEqual(Canvas.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/canvas/p1")
        self.assertEqual(len(Annotation.objects()), 1)
        self.assertEqual(Canvas.objects()[0].ATid in Annotation.objects()[0].belongsTo, True)

    def test_a_canvas_can_be_successfully_created_along_with_multi_level_nested_structures(self):
        data = {"canvas": json.loads(open(CANVAS_FULL).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Canvas.objects()[0].label, 'Canvas c0')
        self.assertEqual(Canvas.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/canvas/c0")
        self.assertEqual(len(Annotation.objects()), 1)
        self.assertEqual(len(Annotation.objects()[0].on), 37)
        self.assertEqual(Canvas.objects()[0].ATid in Annotation.objects.get(identifier='book1', name='anno-1').belongsTo, True)

    def test_a_duplicate_canvas_cannot_be_created(self):
        data = {"canvas": json.loads(open(CANVAS_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')

    def test_a_canvas_with_no_id_given_can_be_successfully_created(self):
        data = {"canvas": json.loads(open(CANVAS_SHORT).read())}
        del data["canvas"]["@id"]
        response = self.client.post("/UofT/canvas", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Canvas.objects()[0].label, 'p. 1')

    def test_a_canvas_cannot_be_created_if_id_does_not_match_with_identifier(self):
        data = {"canvas": json.loads(open(CANVAS_SHORT).read())}
        response = self.client.post("/UofT/canvas", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(response.data["responseBody"]["error"], "Canvas identifier must match with the identifier in @id.")

    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"canvas": json.loads(open(CANVAS_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        annotation = Annotation.objects()[0]
        annotation.hidden = True
        annotation.save()
        response = self.client.get("/book1/canvas/p1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["images"]), 0)


class Canvas_Test_GET(APIMongoTestCase):
    def setUp(self):
        Canvas(label="canvas1", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas/canvas1").save()

    def test_a_canvas_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/canvas/canvas1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Canvas with name 'canvas1' does not exist in identifier 'nonExistingItem'.")

    def test_a_canvas_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingCanvas")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Canvas with name 'nonExistingCanvas' does not exist in identifier 'book1'.")

    def test_a_canvas_can_be_viewed(self):
        response = self.client.get("/book1/canvas/canvas1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class Canvas_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        Canvas(label="canvas1", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas/canvas1").save()
        Canvas(label="canvas2", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas/canvas2").save()
        Canvas(label="canvas3", identifier="book1", name="canvas3", ATid="http://example.org/iiif/book1/canvas/canvas3").save()

    def test_all_canvass_from_an_item_is_returned(self):
        response = self.client.get("/book1/canvas")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/canvas/canvas1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/canvas/canvas3")

    def test_a_canvas_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/canvas")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class Canvas_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Canvas(label="canvas1", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas/canvas1").save()
        Canvas(label="canvas2", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas/canvas2").save()

    def test_a_canvas_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/canvas1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Canvas 'canvas1' from identifier 'book1'.")

    def test_a_canvas_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/canvas/canvas1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Canvas with name 'canvas1' does not exist in identifier 'nonExistingItem'.")

    def test_a_canvas_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingCanvas")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Canvas with name 'nonExistingCanvas' does not exist in identifier 'book1'.")

    def test_deleting_a_canvas_will_delete_all_of_its_nested_objects(self):
        data = {"canvas": json.loads(open(CANVAS_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/p1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Canvas 'p1' from identifier 'book1'.")
        self.assertEqual(len(Annotation.objects), 0)



class Canvas_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Canvas(label="canvas1", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas/canvas1", viewingHint="paged").save()
        Canvas(label="canvas2", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas/canvas2").save()

    def test_a_canvas_can_be_updated_sucessfully(self):
        data = {"canvas": {"label": "new_canvas1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/canvas1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Canvas.objects()[0].label, 'new_canvas1')
        self.assertEqual(Canvas.objects()[0].viewingHint, 'non-paged')

    def test_a_canvas_that_does_not_exist_cannot_be_updated(self):
        data = {"canvas": {"label": "new_canvas1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingCanvas", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Canvas with name 'nonExistingCanvas' does not exist in identifier 'book1'.")

    def test_a_canvas_with_new_id_can_be_updated_successfully(self):
        data = {"canvas": {"@id": "http://example.org/iiif/new_book1/canvas/new_canvas1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/canvas1", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Canvas.objects()[0].ATid, settings.IIIF_BASE_URL + "/new_book1/canvas/new_canvas1")

