import os
import json
from test_addons import APIMongoTestCase
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.conf import settings  # import the settings file to get IIIF_BASE_URL & IIIF_CONTEXT
from iiif_api_services.models.User import User
from iiif_api_services.models.ActivityModel import Activity
from datetime import datetime


MANIFEST_FULL = os.path.join(os.path.dirname(__file__), 'testData', 'activity', 'manifestFull.json')


class Activty_Test_With_Full_Nested_Manifest_Creation(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.delete('/book1/manifest')
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.post('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        response = self.client.put('/book1/manifest', data)
        while self.client.get(response.data["status"]).status_code!=status.HTTP_301_MOVED_PERMANENTLY: pass # Wait till background process finishes
        self.assertEqual(len(Activity.objects), 28)


       
class Activty_Test_Multiple(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('staff', 'staff@mail.com', 'staffpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        data = {"manifest": json.loads(open(MANIFEST_FULL).read())}
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=422, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=404, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=404, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="DELETE", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=204, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="POST", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=201, endTime=datetime.now()).save()
        Activity(username="staff", requestMethod="PUT", responseBody={"@id": "http://localhost:8000/book1-6565/manifest", "@type": "someType"}, responseCode=200, endTime=datetime.now()).save()


    def test_to_view_all_activities(self):
        response = self.client.get('/activity')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 28)

    def test_to_get_top_level_discovery_collection(self):
        response = self.client.get('/discovery')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery")
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection".format(settings.TOP_LEVEL_COLLECTION_LABEL))
        self.assertEqual(response.data["first"]["id"], settings.IIIF_BASE_URL+"/discovery-1")
        self.assertEqual(response.data["last"]["id"], settings.IIIF_BASE_URL+"/discovery-2")

    def test_to_get_top_level_discovery_collection_with_empty_date_range(self):
        response = self.client.get('/discovery/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery")
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection".format(settings.TOP_LEVEL_COLLECTION_LABEL))
        self.assertEqual(response.data["first"]["id"], settings.IIIF_BASE_URL+"/discovery-1")
        self.assertEqual(response.data["last"]["id"], settings.IIIF_BASE_URL+"/discovery-2")

    def test_to_get_top_level_discovery_collection_within_a_date_range(self):
        toDate = (datetime.now()).strftime("%Y-%m-%d")
        response = self.client.get("/discovery/?from=2018-01-01&to="+toDate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery/?from=2018-01-01&to="+toDate)
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection".format(settings.TOP_LEVEL_COLLECTION_LABEL))
        self.assertEqual(response.data["first"]["id"], settings.IIIF_BASE_URL+"/discovery-1/?from=2018-01-01&to="+toDate)
        self.assertEqual(response.data["last"]["id"], settings.IIIF_BASE_URL+"/discovery-2/?from=2018-01-01&to="+toDate)

    def test_to_get_top_level_discovery_collection_within_an_invalid_date_range(self):
        response = self.client.get('/discovery/?from=2018-01-01&to=INVALID')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The date range query format is invalid.')

    def test_to_get_a_specific_discovery_collection_page(self):
        response = self.client.get('/discovery-1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery-1")
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["count"], 20)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection: Page-{1}".format(settings.TOP_LEVEL_COLLECTION_LABEL, 1))
        self.assertEqual(response.data["next"]["id"], settings.IIIF_BASE_URL+"/discovery-2")
        self.assertEqual(response.data["partOf"]["id"], settings.IIIF_BASE_URL+"/discovery")
        self.assertEqual(len(response.data["items"]), 20)
        self.assertEqual(response.data["items"][0]["type"], "Update")
        self.assertEqual(response.data["items"][1]["type"], "Create")
        self.assertEqual(response.data["items"][2]["type"], "Delete")

    def test_to_get_a_specific_discovery_collection_page_within_a_date_range(self):
        toDate = (datetime.now()).strftime("%Y-%m-%d")
        response = self.client.get('/discovery-1/?from=2018-01-01&to='+toDate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery-1/?from=2018-01-01&to="+toDate)
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["count"], 20)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection: Page-{1}".format(settings.TOP_LEVEL_COLLECTION_LABEL, 1))
        self.assertEqual(response.data["next"]["id"], settings.IIIF_BASE_URL+"/discovery-2/?from=2018-01-01&to="+toDate)
        self.assertEqual(response.data["partOf"]["id"], settings.IIIF_BASE_URL+"/discovery/?from=2018-01-01&to="+toDate)
        self.assertEqual(len(response.data["items"]), 20)
        self.assertEqual(response.data["items"][0]["type"], "Update")
        self.assertEqual(response.data["items"][1]["type"], "Create")
        self.assertEqual(response.data["items"][2]["type"], "Delete")

    def test_to_get_a_specific_discovery_collection_page_within_an_invalid_date_range(self):
        response = self.client.get('/discovery-2/?from=2018-01-01&to=INVALID')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The date range query format is invalid.')

    def test_to_get_a_specific_discovery_collection_page_that_does_not_exist(self):
        response = self.client.get('/discovery-6987')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Discovery with page '6987' does not exist.")

    def test_to_get_a_specific_discovery_collection_page_with_0_does_not_exist(self):
        response = self.client.get('/discovery-0')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Discovery with page '0' does not exist.")

    def test_to_get_a_specific_activity(self):
        response = self.client.get('/discovery-1')
        activityID = response.data["items"][0]["id"].split("/")[-1]
        response = self.client.get('/activity/'+activityID)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], "http://testserver/activity/"+activityID)

    def test_to_get_a_specific_activity_that_does_not_exist(self):
        response = self.client.get('/activity/5a381fe63b0eb74d720584d6')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Activity with id '5a381fe63b0eb74d720584d6' does not exist.")


class Activty_Test_Emtpy_Activities(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_if_any_activities_were_recorded(self):
        self.assertEqual(len(Activity.objects), 0)

    def test_to_get_top_level_discovery_collection(self):
        response = self.client.get('/discovery')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["@context"][0], 'http://iiif.io/api/presentation/3/context.json')
        self.assertEqual(response.data["id"], settings.IIIF_BASE_URL+"/discovery")
        self.assertEqual(response.data["total"], 0)
        self.assertEqual(response.data["label"], "{0} IIIF Discovery Collection".format(settings.TOP_LEVEL_COLLECTION_LABEL))
        self.assertEqual(response.data["first"], {})
        self.assertEqual(response.data["last"], {})

    def test_to_get_a_specific_discovery_collection_page(self):
        response = self.client.get('/discovery-1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Discovery with page '1' does not exist.")


class Activty_Test_Delete_Activities(APIMongoTestCase):
    def setUp(self):
        self.user = User.create_user('testadmin', 'testemail@mail.com', 'testadminpass', True)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)

    def test_if_any_activities_were_recorded(self):
        self.assertEqual(len(Activity.objects), 0)

    def test_to_delete_a_specific_activity(self):
        activity = Activity(responseCode=200).save()
        self.assertEqual(len(Activity.objects), 1)
        response = self.client.delete('/activity/'+str(activity.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Successfully deleted the Activity with id '" + str(activity.id) + "'.")
        self.assertEqual(len(Activity.objects), 0)

    def test_to_delete_a_specific_activity_with_staff_user(self):
        self.user = User.create_user('teststaff', 'testemail2@mail.com', 'teststaffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        activity = Activity(responseCode=200).save()
        response = self.client.delete('/activity/'+str(activity.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "You don't have the necessary permission to perform this action. Please contact your admin.")
        self.assertEqual(len(Activity.objects), 1)

    def test_to_delete_an_invalid_activity(self):
        activity2 = Activity(responseCode=200).save()
        activity2.delete()
        response = self.client.delete('/activity/'+str(activity2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Activity with id '" + str(activity2.id) + "' does not exist.")

    def test_to_delete_all_activities(self):
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        self.assertEqual(len(Activity.objects), 4)
        response = self.client.delete('/activity')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Successfully deleted all Activities.")
        self.assertEqual(len(Activity.objects), 0)

    def test_to_delete_all_activities_with_staff(self):
        self.user = User.create_user('teststaff', 'testemail2@mail.com', 'teststaffpass')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        activity = Activity(responseCode=200).save()
        self.assertEqual(len(Activity.objects), 4)
        response = self.client.delete('/activity')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "You don't have the necessary permission to perform this action. Please contact your admin.")
        self.assertEqual(len(Activity.objects), 4)



class Queue_Test_View_All(APIMongoTestCase):
    def test_to_view_all_pending_queue(self):
        response = self.client.get('/queue')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

