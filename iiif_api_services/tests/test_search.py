from test_addons import APIMongoTestCase
from rest_framework import status
from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.models.ManifestModel import Manifest
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.LayerModel import Layer
from iiif_api_services.models.RangeModel import Range



class Search_Collections_Test(APIMongoTestCase):
    def setUp(self):
        Collection(label="cool sequence", name="collection1", ATid="http://example.org/iiif/collection/collection1").save()
        Collection(label="not so cool collection", name="collection2", ATid="http://example.org/iiif/collection/collection2").save()
        Collection(label="cool collection", name="collection3", ATid="http://example.org/iiif/collection/collection3").save()
        self.url = "/search/collection/"

    def test_to_search_all_collections(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/collection/collection2')

    def test_to_search_specific_collections(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/collection/collection2')

    def test_to_search_collections_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for collection.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Manifests_Test(APIMongoTestCase):
    def setUp(self):
        Manifest(label="cool sequence", identifier="item1", ATid="http://example.org/iiif/item1/manifest").save()
        Manifest(label="not so cool manifest", identifier="item2", ATid="http://example.org/iiif/item2/manifest").save()
        Manifest(label="cool manifest", identifier="item3", ATid="http://example.org/iiif/item3/manifest").save()
        self.url = "/search/manifest/"

    def test_to_search_all_manifests(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/item2/manifest')

    def test_to_search_specific_manifests(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/item2/manifest')

    def test_to_search_manifests_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for manifest.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Sequences_Test(APIMongoTestCase):
    def setUp(self):
        Sequence(label="cool sequence", identifier="book1", name="sequence1", ATid="http://example.org/iiif/book1/sequence1").save()
        Sequence(label="not so cool sequence", identifier="book1", name="sequence2", ATid="http://example.org/iiif/book1/sequence2").save()
        Sequence(label="cool sequence", identifier="book2", name="sequence3", ATid="http://example.org/iiif/book2/sequence3").save()
        self.url = "/search/sequence/"

    def test_to_search_all_sequences(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/sequence2')

    def test_to_search_specific_sequences(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/sequence2')

    def test_to_search_sequences_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for sequence.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Ranges_Test(APIMongoTestCase):
    def setUp(self):
        Range(label="cool range", identifier="book1", name="range1", ATid="http://example.org/iiif/book1/range1").save()
        Range(label="not so cool range", identifier="book1", name="range2", ATid="http://example.org/iiif/book1/range2").save()
        Range(label="cool range", identifier="book2", name="range3", ATid="http://example.org/iiif/book2/range3").save()
        self.url = "/search/range/"

    def test_to_search_all_ranges(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/range2')

    def test_to_search_specific_ranges(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/range2')

    def test_to_search_ranges_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for range.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Canvases_Test(APIMongoTestCase):
    def setUp(self):
        Canvas(label="cool canvas", identifier="book1", name="canvas1", ATid="http://example.org/iiif/book1/canvas1").save()
        Canvas(label="not so cool canvas", identifier="book1", name="canvas2", ATid="http://example.org/iiif/book1/canvas2").save()
        Canvas(label="cool canvas", identifier="book2", name="canvas3", ATid="http://example.org/iiif/book2/canvas3").save()
        self.url = "/search/canvas/"

    def test_to_search_all_canvases(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/canvas2')

    def test_to_search_specific_canvases(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/canvas2')

    def test_to_search_canvass_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for canvas.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Annotations_Test(APIMongoTestCase):
    def setUp(self):
        Annotation(label="cool annotation", identifier="book1", name="annotation1", ATid="http://example.org/iiif/book1/annotation1").save()
        Annotation(label="not so cool annotation", identifier="book1", name="annotation2", ATid="http://example.org/iiif/book1/annotation2").save()
        Annotation(label="cool annotation", identifier="book2", name="annotation3", ATid="http://example.org/iiif/book2/annotation3").save()
        self.url = "/search/annotation/"

    def test_to_search_all_annotations(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/annotation2')

    def test_to_search_specific_annotations(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/annotation2')

    def test_to_search_annotations_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for annotation.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_AnnotationLists_Test(APIMongoTestCase):
    def setUp(self):
        AnnotationList(label="cool list", identifier="book1", name="list1", ATid="http://example.org/iiif/book1/list1").save()
        AnnotationList(label="not so cool list", identifier="book1", name="list2", ATid="http://example.org/iiif/book1/list2").save()
        AnnotationList(label="cool list", identifier="book2", name="list3", ATid="http://example.org/iiif/book2/list3").save()
        self.url = "/search/list/"

    def test_to_search_all_lists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/list2')

    def test_to_search_specific_lists(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/list2')

    def test_to_search_lists_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for list.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')


class Search_Layers_Test(APIMongoTestCase):
    def setUp(self):
        Layer(label="cool layer", identifier="book1", name="layer1", ATid="http://example.org/iiif/book1/layer1").save()
        Layer(label="not so cool layer", identifier="book1", name="layer2", ATid="http://example.org/iiif/book1/layer2").save()
        Layer(label="cool layer", identifier="book2", name="layer3", ATid="http://example.org/iiif/book2/layer3").save()
        self.url = "/search/layer/"

    def test_to_search_all_layers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/layer2')

    def test_to_search_specific_layers(self):
        response = self.client.get(self.url+"?label=cool")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[1]["@id"], 'http://example.org/iiif/book1/layer2')

    def test_to_search_layers_with_no_matching_query(self):
        response = self.client.get(self.url+"?label=noMatch")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], 'No matching objects found for layer.')

    def test_to_search_with_invalid_query_param(self):
        response = self.client.get(self.url+"?invalid=cool")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"], 'The search query format is invalid.')

