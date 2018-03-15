import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.LayerModel import Layer
from iiif_api_services.models.AnnotationListModel import AnnotationList


LAYER_MEDIUM = os.path.join(os.path.dirname(__file__), 'testData', 'layer', 'layerMedium.json')
LAYER_SHORT = os.path.join(os.path.dirname(__file__), 'testData', 'layer', 'layerShort.json')
URL = '/book1/layer'


class Layer_Test_Without_Authentication(APIMongoTestCase):
    def setUp(self):
        Layer(label="layer1", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer/layer1").save()
        Layer(label="layer2", identifier="book1", name="layer2", ATid="http://example.org/iiif/book1/layer/layer2").save()
        Layer(label="layer3", identifier="book1", name="layer3", ATid="http://example.org/iiif/book1/layer/layer3").save()

    def test_to_get_all_layers_of_an_item(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_to_get_a_specific_layer_of_an_item(self):
        response = self.client.get(URL+"/layer2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ATtype"], 'sc:Layer')
        self.assertEqual(response.data["label"], 'layer2')

    def test_a_layer_cannot_be_created(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_layer_cannot_be_updated(self):
        response = self.client.put(URL+"/layer1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_layer_cannot_be_deleted(self):
        response = self.client.delete(URL+"/layer1", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class Layer_Test_POST(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_a_layer_can_be_successfully_created_with_no_nested_structures(self):
        data = {"layer": json.loads(open(LAYER_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Layer.objects()[0].label, 'Diplomatic Transcription')
        self.assertEqual(Layer.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/layer/transcription")


    def test_a_layer_can_be_successfully_created_with_one_level_nested_structures(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Layer.objects()[0].label, 'Diplomatic Transcription')
        self.assertEqual(Layer.objects()[0].ATid, settings.IIIF_BASE_URL + "/book1/layer/transcription")
        self.assertEqual(len(AnnotationList.objects()), 4)
        self.assertEqual(AnnotationList.objects.get(name="l2").ATid, settings.IIIF_BASE_URL + "/book1/list/l2")
        self.assertEqual(Layer.objects()[0].ATid in AnnotationList.objects.get(identifier='book1', name='l1').belongsTo, True)
        self.assertEqual(Layer.objects()[0].ATid in AnnotationList.objects.get(identifier='book1', name='l2').belongsTo, True)
        self.assertEqual(Layer.objects()[0].ATid in AnnotationList.objects.get(identifier='book1', name='l3').belongsTo, True)
        self.assertEqual(Layer.objects()[0].ATid in AnnotationList.objects.get(identifier='book1', name='l4').belongsTo, True)

    def test_a_duplicate_layer_cannot_be_created(self):
        data = {"layer": json.loads(open(LAYER_SHORT).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        print response.data
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]["ATid"][0], 'This field must be unique.')

    def test_a_layer_with_no_id_given_can_be_successfully_created(self):
        data = {"layer": json.loads(open(LAYER_SHORT).read())}
        del data["layer"]["@id"]
        response = self.client.post("/identifier/layer", data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_201_CREATED)
        self.assertEqual(Layer.objects()[0].label, 'Diplomatic Transcription')

    def test_a_hidden_child_cannot_be_viewed(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        annotationList = AnnotationList.objects.get(identifier='book1', name='l1')
        annotationList.hidden = True
        annotationList.save()
        response = self.client.get("/book1/layer/transcription")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["otherContent"]), 3)

    def test_a_layer_with_invalid_field_cannot_be_created(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        data["layer"]['viewingHint'] = ['invalid']
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], "Not a valid string.")

    def test_a_layer_with_invalid_sub_member_cannot_be_created(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        data["layer"]['otherContent'][0] = {"viewingHint": ['invalid']}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], "Not a valid string.")

class Layer_Test_GET(APIMongoTestCase):
    def setUp(self):
        Layer(label="layer1", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer/layer1").save()

    def test_a_layer_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/layer/layer1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "layer with name 'layer1' does not exist in identifier 'nonExistingItem'.")

    def test_a_layer_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get(URL+"/nonExistingLayer")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "layer with name 'nonExistingLayer' does not exist in identifier 'book1'.")

    def test_a_layer_can_be_viewed(self):
        response = self.client.get("/book1/layer/layer1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)



class Layer_Test_GET_ALL(APIMongoTestCase):
    def setUp(self):
        Layer(label="layer1", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer/layer1").save()
        Layer(label="layer2", identifier="book1", name="layer2", ATid="http://example.org/iiif/book1/layer/layer2").save()
        Layer(label="layer3", identifier="book1", name="layer3", ATid="http://example.org/iiif/book1/layer/layer3").save()

    def test_all_layers_from_an_item_is_returned(self):
        response = self.client.get("/book1/layer")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["@id"], "http://example.org/iiif/book1/layer/layer1")
        self.assertEqual(response.data[2]["@id"], "http://example.org/iiif/book1/layer/layer3")

    def test_a_layer_from_an_item_that_does_not_exist_cannot_be_viewed(self):
        response = self.client.get("/nonExistingItem/layer")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Item with name 'nonExistingItem' does not exist.")



class Layer_Test_DELETE(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Layer(label="layer1", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer/layer1").save()
        Layer(label="layer2", identifier="book1", name="layer2", ATid="http://example.org/iiif/book1/layer/layer2").save()

    def test_a_layer_can_be_deleted_sucessfully(self):
        response = self.client.delete(URL+"/layer1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Layer 'layer1' from identifier 'book1'.")

    def test_a_layer_from_an_item_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete("/nonExistingItem/layer/layer1")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Layer with name 'layer1' does not exist in identifier 'nonExistingItem'.")

    def test_a_layer_that_does_not_exist_cannot_be_deleted(self):
        response = self.client.delete(URL+"/nonExistingLayer")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Layer with name 'nonExistingLayer' does not exist in identifier 'book1'.")

    def test_deleting_a_layer_will_delete_all_of_its_nested_objects(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete(URL+"/transcription")
        if settings.QUEUE_DELETE_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["responseBody"]['message'], "Successfully deleted Layer 'transcription' from identifier 'book1'.")
        self.assertEqual(len(AnnotationList.objects), 0)



class Layer_Test_PUT(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        Layer(label="layer1", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer/layer1", viewingHint="paged").save()
        Layer(label="layer2", identifier="book1", name="layer2", ATid="http://example.org/iiif/book1/layer/layer2").save()
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        response = self.client.post(URL, data)
        if settings.QUEUE_POST_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 

    def test_a_layer_can_be_updated_sucessfully(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        data["layer"]["label"] = "new_layer1"
        data["layer"]["viewingHint"] = "non-paged"
        response = self.client.put(URL+"/transcription", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Layer.objects()[2].label, 'new_layer1')
        self.assertEqual(Layer.objects()[2].viewingHint, "non-paged")

    def test_a_layer_with_invalid_field_cannot_be_updated(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        data["layer"]['viewingHint'] = ['invalid']
        response = self.client.put(URL+"/transcription", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], "Not a valid string.")

    def test_a_layer_that_does_not_exist_cannot_be_updated(self):
        data = {"layer": {"label": "new_layer1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/nonExistingLayer", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["responseBody"]["error"], "Layer with name 'nonExistingLayer' does not exist in identifier 'book1'.")

    def test_a_layer_with_invalid_sub_member_cannot_be_updated(self):
        data = {"layer": json.loads(open(LAYER_MEDIUM).read())}
        data["layer"]['otherContent'][0] = {"viewingHint": ['invalid']}
        response = self.client.put(URL+"/transcription", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["responseBody"]["error"]['viewingHint'][0], "Not a valid string.")

    def test_a_layer_with_new_id_can_be_updated_successfully(self):
        data = {"layer": {"@id": "http://example.org/iiif/new_book1/layer/new_layer1", "viewingHint": "non-paged"}}
        response = self.client.put(URL+"/transcription", data)
        if settings.QUEUE_PUT_ENABLED:
            while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
            response = self.client.get(response.data["status"]) 
        self.assertEqual(response.data["responseCode"], status.HTTP_200_OK)
        self.assertEqual(Layer.objects()[2].ATid, settings.IIIF_BASE_URL + "/new_book1/layer/new_layer1")

