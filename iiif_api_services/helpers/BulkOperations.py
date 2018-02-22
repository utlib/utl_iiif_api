from iiif_api_services.models.CollectionModel import Collection
from iiif_api_services.models.ManifestModel import Manifest
from iiif_api_services.models.SequenceModel import Sequence
from iiif_api_services.models.RangeModel import Range
from iiif_api_services.models.CanvasModel import Canvas
from iiif_api_services.models.AnnotationModel import Annotation
from iiif_api_services.models.AnnotationListModel import AnnotationList
from iiif_api_services.models.LayerModel import Layer
from django.conf import settings # import the settings file to get IIIF_BASE_URL


def bulkCreate(bulkActions):
    collectionsNew, manifestsNew, sequencesNew, rangesNew, canvasesNew, annotationsNew, annotationListsNew, layersNew = {}, {}, {}, {}, {}, {}, {}, {}
    collectionsUpdate, manifestsUpdate, sequencesUpdate, rangesUpdate, canvasesUpdate, annotationsUpdate, annotationListsUpdate, layersUpdate = [], [], [], [], [], [], [], []

    if bulkActions["Collection"]:
        for data in bulkActions["Collection"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = False
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Collection"
            key = data["name"]
            if key not in collectionsNew:
                collectionsNew[key] = data.copy()  
            else:
                collectionsUpdate.append({"name": data["name"], "data": data.copy()})
        bulk = Collection._get_collection().initialize_unordered_bulk_op()
        for key, val in collectionsNew.iteritems(): bulk.insert(val)
        bulk.execute()



    if bulkActions["Manifest"]:
        for data in bulkActions["Manifest"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = False
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Manifest"
            key = data["identifier"]
            if key not in manifestsNew:
                manifestsNew[key] = data.copy()  
            else:
                manifestsUpdate.append({"identifier": data["identifier"], "data": data.copy()})     
        bulk = Manifest._get_collection().initialize_unordered_bulk_op()         
        for key, val in manifestsNew.iteritems(): bulk.insert(val)
        bulk.execute()



    if bulkActions["Sequence"]:
        for data in bulkActions["Sequence"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Sequence"
            key = data["identifier"]+"_"+data["name"]
            if key not in sequencesNew:
                sequencesNew[key] = data.copy()  
            else:
                sequencesUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = Sequence._get_collection().initialize_unordered_bulk_op()
        for key, val in sequencesNew.iteritems(): bulk.insert(val)
        bulk.execute()


    if bulkActions["Range"]:
        for data in bulkActions["Range"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Range"
            key = data["identifier"]+"_"+data["name"]
            if key not in rangesNew:
                rangesNew[key] = data.copy()
            else:
                rangesUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = Range._get_collection().initialize_unordered_bulk_op()
        for key, val in rangesNew.iteritems(): bulk.insert(val)
        bulk.execute()


    if bulkActions["Canvas"]:
        for data in bulkActions["Canvas"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Canvas"
            key = data["identifier"]+"_"+data["name"]
            if key not in canvasesNew:
                canvasesNew[key] = data.copy()  
            else:
                canvasesUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = Canvas._get_collection().initialize_unordered_bulk_op()
        for key, val in canvasesNew.iteritems(): bulk.insert(val)
        bulk.execute()


    if bulkActions["Annotation"]:
        for data in bulkActions["Annotation"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "oa:Annotation"
            if "on" not in data: data["on"] = settings.IIIF_BASE_URL+'/UofT/canvas/default'
            key = data["identifier"]+"_"+data["name"]
            if key not in annotationsNew:
                annotationsNew[key] = data.copy()  
            else:
                annotationsUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = Annotation._get_collection().initialize_unordered_bulk_op()
        for key, val in annotationsNew.iteritems(): bulk.insert(val)
        bulk.execute()



    if bulkActions["AnnotationList"]:
        for data in bulkActions["AnnotationList"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:AnnotationList"
            key = data["identifier"]+"_"+data["name"]
            if key not in annotationListsNew:
                annotationListsNew[key] = data.copy()  
            else:
                annotationListsUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = AnnotationList._get_collection().initialize_unordered_bulk_op()
        for key, val in annotationListsNew.iteritems(): bulk.insert(val)
        bulk.execute()


    if bulkActions["Layer"]:
        for data in bulkActions["Layer"]: 
            # Add default values
            if "order" not in data: data["order"] = 0
            if "embeddedEntirely" not in data: data["embeddedEntirely"] = True
            if "belongsTo" not in data: data["belongsTo"] = []
            if "hidden" not in data: data["hidden"] = False
            if "ownedBy" not in data: data["ownedBy"] = []
            if "ATtype" not in data: data["ATtype"] = "sc:Layer"
            key = data["identifier"]+"_"+data["name"]
            if key not in layersNew:
                layersNew[key] = data.copy()  
            else:
                layersUpdate.append({"identifier": data["identifier"], "name": data["name"], "data": data.copy()})
        bulk = Layer._get_collection().initialize_unordered_bulk_op()
        for key, val in layersNew.iteritems(): bulk.insert(val)
        bulk.execute()



    toUpdate = {
        "Collection": collectionsUpdate,
        "Manifest": manifestsUpdate,
        "Sequence": sequencesUpdate,
        "Range": rangesUpdate,
        "Canvas": canvasesUpdate,
        "Annotation": annotationsUpdate,
        "AnnotationList": annotationListsUpdate,
        "Layer": layersUpdate
    }

    return toUpdate



def bulkDelete(bulkActions):
    if bulkActions["Collection"]:
        Collection.objects(ATid__in=bulkActions["Collection"]).delete()
    if bulkActions["Manifest"]:
        Manifest.objects(ATid__in=bulkActions["Manifest"]).delete()
    if bulkActions["Sequence"]:
        Sequence.objects(ATid__in=bulkActions["Sequence"]).delete()
    if bulkActions["Range"]:
        Range.objects(ATid__in=bulkActions["Range"]).delete()
    if bulkActions["Canvas"]:
        Canvas.objects(ATid__in=bulkActions["Canvas"]).delete()
    if bulkActions["Annotation"]:
        Annotation.objects(ATid__in=bulkActions["Annotation"]).delete()
    if bulkActions["AnnotationList"]:
        AnnotationList.objects(ATid__in=bulkActions["AnnotationList"]).delete()
    if bulkActions["Layer"]:
        Layer.objects(ATid__in=bulkActions["Layer"]).delete()


def bulkUpdatePermissions(bulkActions, username, action):
    if bulkActions["Collection"]:
        bulk = Collection._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Collection"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Manifest"]:
        bulk = Manifest._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Manifest"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Sequence"]:
        bulk = Sequence._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Sequence"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Range"]:
        bulk = Range._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Range"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Canvas"]:
        bulk = Canvas._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Canvas"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Annotation"]:
        bulk = Annotation._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Annotation"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["AnnotationList"]:
        bulk = AnnotationList._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["AnnotationList"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()
    if bulkActions["Layer"]:
        bulk = Layer._get_collection().initialize_unordered_bulk_op()
        for ATid in bulkActions["Layer"]:
            bulk.find( { 'ATid':  ATid}).update({ action: {  "ownedBy" : username }})
        bulk.execute()