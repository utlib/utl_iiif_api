from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.models.ManifestModel import Manifest
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.LayerModel import Layer


def __bulk_insert(bulk_actions, model, at_type, embedded_entirely=True):
    unique_objects, duplicate_objects = {}, []
    for data in bulk_actions:
        # Add default values
        if "order" not in data:
            data["order"] = 0
        if "embeddedEntirely" not in data:
            data["embeddedEntirely"] = embedded_entirely
        if "belongsTo" not in data:
            data["belongsTo"] = []
        if "hidden" not in data:
            data["hidden"] = False
        if "ownedBy" not in data:
            data["ownedBy"] = []
        if "ATtype" not in data:
            data["ATtype"] = at_type
        if "identifier" in data and "name" in data:
            key = data["identifier"]+"_"+data["name"]
        elif "identifier" in data:
            key = data["identifier"]
        elif "name" in data:
            key = data["name"]
        if key not in unique_objects:
            unique_objects[key] = data.copy()
        else:
            duplicate_objects.append(data.copy())
    bulk = model._get_collection().initialize_unordered_bulk_op()
    for key, val in unique_objects.iteritems():
        bulk.insert(val)
    bulk.execute()
    return duplicate_objects


def bulk_create(bulk_actions):
    collections_duplicate, manifests_duplicate, sequences_duplicate, ranges_duplicate, canvases_duplicate, annotations_duplicate, annotation_lists_duplicate, layers_duplicate = [], [], [], [], [], [], [], []

    if bulk_actions["Collection"]:
        collections_duplicate = __bulk_insert(
            bulk_actions["Collection"], Collection, "sc:Collection", embedded_entirely=False)
    if bulk_actions["Manifest"]:
        manifests_duplicate = __bulk_insert(
            bulk_actions["Manifest"], Manifest, "sc:Manifest", embedded_entirely=False)
    if bulk_actions["Sequence"]:
        sequences_duplicate = __bulk_insert(
            bulk_actions["Sequence"], Sequence, "sc:Sequence")
    if bulk_actions["Range"]:
        ranges_duplicate = __bulk_insert(
            bulk_actions["Range"], Range, "sc:Range")
    if bulk_actions["Canvas"]:
        canvases_duplicate = __bulk_insert(
            bulk_actions["Canvas"], Canvas, "sc:Canvas")
    if bulk_actions["Annotation"]:
        annotations_duplicate = __bulk_insert(
            bulk_actions["Annotation"], Annotation, "oa:Annotation")
    if bulk_actions["AnnotationList"]:
        annotation_lists_duplicate = __bulk_insert(
            bulk_actions["AnnotationList"], AnnotationList, "sc:AnnotationList")
    if bulk_actions["Layer"]:
        layers_duplicate = __bulk_insert(
            bulk_actions["Layer"], Layer, "sc:Layer")

    update_duplicates = {
        "Collection": collections_duplicate,
        "Manifest": manifests_duplicate,
        "Sequence": sequences_duplicate,
        "Range": ranges_duplicate,
        "Canvas": canvases_duplicate,
        "Annotation": annotations_duplicate,
        "AnnotationList": annotation_lists_duplicate,
        "Layer": layers_duplicate
    }
    return update_duplicates


def bulk_delete(bulk_actions):
    for model in ["Collection", "Manifest", "Sequence", "Range", "Canvas", "Annotation", "AnnotationList", "Layer"]:
        if model in bulk_actions and bulk_actions[model]:
            exec(model+".objects(ATid__in=bulk_actions[model]).delete()")


def bulk_update_permissions(bulk_actions, username, action):
    for model in ["Collection", "Manifest", "Sequence", "Range", "Canvas", "Annotation", "AnnotationList", "Layer"]:
        if model in bulk_actions and bulk_actions[model]:
            exec("bulk = "+model+"._get_collection().initialize_unordered_bulk_op()")
            for at_id in bulk_actions[model]:
                bulk.find({'ATid': at_id}).update(
                    {action: {"ownedBy": username}})
            bulk.execute()
