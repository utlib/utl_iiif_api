from iiif_api_services.helpers.BackgroundProcess import process_result
from iiif_api_services.helpers.BulkOperations import bulkCreate, bulkDelete, bulkUpdatePermissions
from rest_framework import status
import uuid
import json
import urllib
from django.conf import settings # import the settings file to get IIIF_BASE_URL
from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.LayerSerializer import *
from celery.decorators import task


def updatePermission(requestObject):
    if "collections" not in requestObject: requestObject["collections"] = []
    if "manifests" not in requestObject: requestObject["manifests"] = []
    bulkUpdates = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    try:
        for ATid in requestObject["collections"]:
            try:
                collection = Collection.objects.get(ATid=ATid)
                bulkUpdates["Collection"].append(collection.ATid)
                nestedChildren = getRequiredChildren(collection=collection)
                bulkUpdates["Collection"] += [collection["ATid"] for collection in nestedChildren["Collection"]]
                bulkUpdates["Manifest"] += [manifest["ATid"] for manifest in nestedChildren["Manifest"]]
            except Exception: pass
    except Exception: pass
    try:
        for ATid in list(set((requestObject["manifests"]+bulkUpdates["Manifest"]))):
            try:
                manifest = Manifest.objects.get(ATid=ATid)
                bulkUpdates["Manifest"].append(manifest.ATid)
                nestedChildren = getRequiredChildren(manifest=manifest)
                bulkUpdates["Sequence"] += [sequence["ATid"] for sequence in nestedChildren["Sequence"]]
                bulkUpdates["Range"] += [rangeObject["ATid"] for rangeObject in nestedChildren["Range"]]
                bulkUpdates["Canvas"] += [canvas["ATid"] for canvas in nestedChildren["Canvas"]]
                bulkUpdates["Annotation"] += [annotation["ATid"] for annotation in nestedChildren["Annotation"]]
                bulkUpdates["AnnotationList"] += [annotationList["ATid"] for annotationList in nestedChildren["AnnotationList"]]
                bulkUpdates["Layer"] += [layer["ATid"] for layer in nestedChildren["Layer"]]
            except Exception: pass
    except Exception: pass
    # Remove duplicate ATids
    bulkUpdates["Collection"] = list(set(bulkUpdates["Collection"]))
    bulkUpdates["Manifest"] = list(set(bulkUpdates["Manifest"]))
    bulkUpdates["Sequence"] = list(set(bulkUpdates["Sequence"]))
    bulkUpdates["Canvas"] = list(set(bulkUpdates["Canvas"]))
    bulkUpdates["Range"] = list(set(bulkUpdates["Range"]))
    bulkUpdates["Annotation"] = list(set(bulkUpdates["Annotation"]))
    bulkUpdates["AnnotationList"] = list(set(bulkUpdates["AnnotationList"]))
    bulkUpdates["Layer"] = list(set(bulkUpdates["Layer"]))
    if requestObject["action"] == 'ADD':
        bulkUpdatePermissions(bulkUpdates, requestObject["username"], '$addToSet')
    else:
        bulkUpdatePermissions(bulkUpdates, requestObject["username"], '$pull')


# Remove all internal properties from the GET response
def cleanObject(object):
    if "_id" in object: del object["_id"]
    if "id" in object: del object["id"]
    if "identifier" in object: del object["identifier"]
    if "name" in object: del object["name"]
    if "order" in object: del object["order"]
    if "embeddedEntirely" in object: del object["embeddedEntirely"]
    # if "belongsTo" in object: del object["belongsTo"] # will be removed at JSONLDRenderer
    # if "children" in object: del object["children"] # will be removed at JSONLDRenderer
    if "hidden" in object: del object["hidden"]
    if "ownedBy" in object: del object["ownedBy"]
    return object


# Return the shortened embedded object
def getEmbeddedObject(object):
    return {
        "@id": object["ATid"],
        "@type": object["ATtype"],
        "label": object["label"] if "label" in object else None
    }


# Return all the relevant child objects for a specific parent object
def getRequiredChildren(collection=None, manifest=None, sequence=None, rangeObject=None, canvas=None, annotation=None, annotationList=None, layer=None):
    requiredObjects = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}

    if collection:
        requiredObjects["Collection"] = Collection.objects(belongsTo__contains=collection.ATid, hidden=False).order_by('order')
        requiredObjects["Manifest"] = Manifest.objects(belongsTo__contains=collection.ATid, hidden=False).order_by('order')

    elif manifest:
        requiredObjects["Sequence"] = [cleanObject(item.to_mongo()) for item in Sequence.objects(ATid__in=manifest.children, hidden=False).order_by('order')]
        requiredObjects["Range"] = [cleanObject(item.to_mongo()) for item in Range.objects(ATid__in=manifest.children, hidden=False).order_by('order')]
        requiredRangeIDs = []
        for rangeObject in requiredObjects["Range"]:
            requiredRangeIDs += [child for child in rangeObject["children"] if "range" in child]
        requiredObjects["Range"] += [cleanObject(item.to_mongo()) for item in Range.objects(ATid__in=requiredRangeIDs, hidden=False).order_by('order')]
        requiredCanvasIDs = []
        for sequence in requiredObjects["Sequence"]:
            requiredCanvasIDs += [child for child in sequence["children"] if "canvas" in child]
        for rangeObject in requiredObjects["Range"]:
            requiredCanvasIDs += [child for child in rangeObject["children"] if "canvas" in child]
        requiredCanvasIDs = list(set(requiredCanvasIDs))
        requiredObjects["Canvas"] = [cleanObject(item.to_mongo()) for item in Canvas.objects(ATid__in=requiredCanvasIDs, hidden=False).order_by('order')]
        requiredAnnotationIDs = []
        requiredAnnotationListIDs = []
        for canvas in requiredObjects["Canvas"]:
            requiredAnnotationIDs += [child for child in canvas["children"] if "annotation" in child]
            requiredAnnotationListIDs += [child for child in canvas["children"] if "list" in child]
        requiredObjects["Annotation"] = [cleanObject(item.to_mongo()) for item in Annotation.objects(ATid__in=requiredAnnotationIDs, hidden=False).order_by('order')]
        requiredObjects["AnnotationList"] = [cleanObject(item.to_mongo()) for item in AnnotationList.objects(ATid__in=requiredAnnotationListIDs, hidden=False).order_by('order')]

    elif sequence:
        requiredObjects["Canvas"] = [cleanObject(item.to_mongo()) for item in Canvas.objects(ATid__in=sequence.children, hidden=False).order_by('order')]
        requiredAnnotationIDs = []
        requiredAnnotationListIDs = []
        for canvas in requiredObjects["Canvas"]:
            requiredAnnotationIDs += [child for child in canvas["children"] if "annotation" in child]
            requiredAnnotationListIDs += [child for child in canvas["children"] if "list" in child]
        requiredObjects["Annotation"] = [cleanObject(item.to_mongo()) for item in Annotation.objects(ATid__in=requiredAnnotationIDs, hidden=False).order_by('order')]
        requiredObjects["AnnotationList"] = [cleanObject(item.to_mongo()) for item in AnnotationList.objects(ATid__in=requiredAnnotationListIDs, hidden=False).order_by('order')]

    elif canvas:
        requiredObjects["Annotation"] = [cleanObject(item.to_mongo()) for item in Annotation.objects(ATid__in=canvas.children, hidden=False).order_by('order')]
        requiredAnnotationLists = [cleanObject(item.to_mongo()) for item in AnnotationList.objects(ATid__in=canvas.children, hidden=False).order_by('order')]

    elif rangeObject:
        requiredObjects["Canvas"] = Canvas.objects(belongsTo__contains=rangeObject.ATid, hidden=False).order_by('order')
        requiredObjects["Range"] = Range.objects(belongsTo__contains=rangeObject.ATid, hidden=False).order_by('order')

    elif annotationList:
        requiredObjects["Annotation"] = Annotation.objects(belongsTo__contains=annotationList.ATid, hidden=False).order_by('order')

    elif layer:
        requiredObjects["AnnotationList"] = AnnotationList.objects(belongsTo__contains=layer.ATid, hidden=False).order_by('order')

    return requiredObjects


# --------------------------------- Begin GET Methods ----------------------------------------------- #

def viewCollection(collection, subCollections=None, subManifests=None):
    # Grab all required objects from DB
    if not subCollections and not subManifests:
        requiredObjects = getRequiredChildren(collection=collection)
    else:
        requiredObjects = {}
        requiredObjects["Collection"] = subCollections
        requiredObjects["Manifest"] = subManifests
    collection.collections = []
    for subCollection in requiredObjects["Collection"]:
        collection.collections.append(CollectionEmbeddedSerializer(subCollection).data)
    collection.manifests = []    
    for subManifest in requiredObjects["Manifest"]:
        collection.manifests.append(ManifestEmbeddedSerializer(subManifest).data)
    collection.total = len(collection.collections+collection.manifests)
    collection.ATcontext = settings.IIIF_CONTEXT
    collectionSerializer = CollectionViewSerializer(collection)               
    return collectionSerializer.data


def viewManifest(manifest):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(manifest=manifest)
    # Build the required manifest
    manifestObject = cleanObject(manifest.to_mongo())
    manifestObject["sequences"] = [{} for i in range(len(requiredObjects["Sequence"]))]
    for sequenceIndex, sequence in enumerate(requiredObjects["Sequence"]):
        if sequenceIndex == 0:
            manifestObject["sequences"][sequenceIndex] = sequence
        else:
            manifestObject["sequences"][sequenceIndex] = getEmbeddedObject(sequence)
        subCanvases = [item for item in requiredObjects["Canvas"] if sequence["ATid"] in item["belongsTo"]]
        manifestObject["sequences"][sequenceIndex]["canvases"] = [{} for i in range(len(subCanvases))]
        for canvasIndex, canvas in enumerate(subCanvases):
            manifestObject["sequences"][sequenceIndex]["canvases"][canvasIndex] = canvas
            manifestObject["sequences"][sequenceIndex]["canvases"][canvasIndex]["images"] = [item for item in requiredObjects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
            subAnnotationLists = [item for item in requiredObjects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
            manifestObject["sequences"][sequenceIndex]["canvases"][canvasIndex]["otherContent"] = [{} for i in range(len(subAnnotationLists))]
            for annotationListIndex, annotationList in enumerate(subAnnotationLists):
                manifestObject["sequences"][sequenceIndex]["canvases"][canvasIndex]["otherContent"][annotationListIndex] = annotationList
    subRanges = [item for item in requiredObjects["Range"] if manifest["ATid"] in item["belongsTo"]]    
    manifestObject["structures"] = [{} for i in range(len(subRanges))]
    for rangeIndex, rangeObject in enumerate(subRanges):
        manifestObject["structures"][rangeIndex] = cleanObject(rangeObject)
        subCanvases = [item for item in requiredObjects["Canvas"] if rangeObject["ATid"] in item["belongsTo"]]
        subRanges = [item for item in requiredObjects["Range"] if rangeObject["ATid"] in item["belongsTo"]]
        manifestObject["structures"][rangeIndex]["members"] = [{} for i in range(len(subCanvases) + len(subRanges))]
        memberCount = 0
        for member in subCanvases:
            manifestObject["structures"][rangeIndex]["members"][memberCount] = getEmbeddedObject(member)
            memberCount += 1
        for member in subRanges:
            manifestObject["structures"][rangeIndex]["members"][memberCount] = getEmbeddedObject(member)
            memberCount += 1
    manifestObject["ATcontext"] = settings.IIIF_CONTEXT
    return manifestObject


def viewSequence(sequence):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(sequence=sequence)
    # Build the required sequence
    sequenceObject = cleanObject(sequence.to_mongo())
    subCanvases = [item for item in requiredObjects["Canvas"] if sequence["ATid"] in item["belongsTo"]]
    sequenceObject["canvases"] = [{} for i in range(len(subCanvases))]
    for canvasIndex, canvas in enumerate(subCanvases):
        sequenceObject["canvases"][canvasIndex] = canvas
        sequenceObject["canvases"][canvasIndex]["images"] = [item for item in requiredObjects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
        subAnnotationLists = [item for item in requiredObjects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
        sequenceObject["canvases"][canvasIndex]["otherContent"] = [{} for i in range(len(subAnnotationLists))]
        for annotationListIndex, annotationList in enumerate(subAnnotationLists):
            sequenceObject["canvases"][canvasIndex]["otherContent"][annotationListIndex] = annotationList
    sequenceObject["ATcontext"] = settings.IIIF_CONTEXT
    return sequenceObject


def viewRange(rangeObject):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(rangeObject=rangeObject)
    rangeObject.members = []
    for subCanvas in requiredObjects["Canvas"]:
        rangeObject.members.append(CanvasEmbeddedSerializer(subCanvas).data)
    for subRange in requiredObjects["Range"]:
        rangeObject.members.append(RangeEmbeddedSerializer(subRange).data)
    rangeObject.ATcontext = settings.IIIF_CONTEXT
    rangeSerializer = RangeViewSerializer(rangeObject)
    return rangeSerializer.data


def viewCanvas(canvas):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(canvas=canvas)
    # Build the required canvas
    canvasObject = cleanObject(canvas.to_mongo())
    canvasObject["images"] = [item for item in requiredObjects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
    subAnnotationLists = [item for item in requiredObjects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
    canvasObject["otherContent"] = [{} for i in range(len(subAnnotationLists))]
    for annotationListIndex, annotationList in enumerate(subAnnotationLists):
        canvasObject["otherContent"][annotationListIndex] = annotationList
    canvasObject["ATcontext"] = settings.IIIF_CONTEXT
    return canvasObject


def viewAnnotation(annotation):
    annotation.ATcontext = settings.IIIF_CONTEXT
    annotationSerializer = AnnotationViewSerializer(annotation)
    return annotationSerializer.data


def viewAnnotationList(annotationList):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(annotationList=annotationList)
    annotationList.resources = []
    for annotationIndex, subAnnotation in enumerate(requiredObjects["Annotation"]):
        if subAnnotation.embeddedEntirely:
            annotationList.resources.append(viewAnnotation(subAnnotation))
            del annotationList.resources[annotationIndex]["ATcontext"]
        else:
            annotationList.resources.append(AnnotationEmbeddedSerializer(subAnnotation).data)
    annotationList.ATcontext = settings.IIIF_CONTEXT
    annotationListSerializer = AnnotationListViewSerializer(annotationList)
    return annotationListSerializer.data


def viewLayer(layer):
    # Grab all required objects from DB
    requiredObjects = getRequiredChildren(layer=layer)
    layer.otherContent = []
    for subAnnotationList in requiredObjects["AnnotationList"]:
        if subAnnotationList.embeddedEntirely:
            layer.otherContent.append(viewAnnotationList(subAnnotationList))
        else:
            layer.otherContent.append(AnnotationListEmbeddedSerializer(subAnnotationList).data)
    layer.ATcontext = settings.IIIF_CONTEXT
    layerSerializer = LayerViewSerializer(layer)
    return layerSerializer.data


# --------------------------------- End GET Methods ----------------------------------------------- #





# --------------------------------- Begin POST Methods ----------------------------------------------- #
@task(name="createCollection")
def createCollection(user, collectionData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        # check for any nested structures
        subCollections = subManifests = subMembers = False
        if 'collections' in collectionData:
            subCollections = collectionData.pop("collections")
        if 'manifests' in collectionData:
            subManifests = collectionData.pop("manifests")
        if 'members' in collectionData:
            subMembers = collectionData.pop("members")
        if "@id" in collectionData: # {scheme}://{host}/{prefix}/collections/{name}
            collectionData["name"] = collectionData.pop("@id").split("/")[-1].strip()
        else:
            collectionData["name"] = 'collection_'+str(uuid.uuid4())
        if collectionData["name"]=="UofT":
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Collection name cannot be: UofT.", "object": collectionData}}
            return process_result(response, activity, queue)
        collectionData["ATid"] = settings.IIIF_BASE_URL+'/collections/'+collectionData["name"]
        # Add the current user as an owner for this object
        if not user["is_superuser"]: collectionData["ownedBy"] = [user["username"]]
        collectionSerializer = CollectionSerializer(data=collectionData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                collection = Collection.objects.get(name=collectionData["name"])
                itemExists = True
            except Collection.DoesNotExist:
                pass
        if not itemExists:
            if collectionSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subCollections:
                    result = collection_create_sub_collections(user, subCollections, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subCollectionsIDs"]
                if subManifests:
                    result = collection_create_sub_manifests(user, subManifests, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subManifestsIDs"]
                if subMembers:
                    result = collection_create_sub_members(user, subMembers, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subCollectionsIDs"]
                        children += result["subManifestsIDs"]
                responseData = collectionSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Collection"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": collectionSerializer.errors, "object": collectionData}}
                return process_result(response, activity, queue)
        else: # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: collectionData.pop("ownedBy")
            if subCollections: canvasData["collections"] = subCollections
            if subManifests: canvasData["manifests"] = subManifests
            if subMembers: canvasData["members"] = subMembers
            return updateCollection(user, collectionData["name"], collectionData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createManifest")
def createManifest(user, identifier, manifestData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        if identifier=="UofT":
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Item name cannot be: UofT.", "object": manifestData}}
            return process_result(response, activity, queue)
        # Check for any nested structures
        subSequences = subRanges = False
        if 'sequences' in manifestData:
            subSequences = manifestData.pop("sequences")
        if 'structures' in manifestData:
            subRanges = manifestData.pop("structures")
        if "@id" in manifestData: # {scheme}://{host}/{prefix}/{identifier}/manifest
            manifestData["identifier"] = manifestData.pop("@id").split("/")[-2].strip()
        else:
            manifestData["identifier"] = identifier
        # Check if the request url and the given @id have the same identifier name
        if identifier and identifier!= "Unknown" and manifestData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Manifest identifier must match with the identifier in @id.", 'object': manifestData}}
            return process_result(response, activity, queue)
        manifestData["ATid"] = settings.IIIF_BASE_URL+'/'+manifestData["identifier"]+'/manifest'
        # Add current user as an owner for this object
        if not user["is_superuser"]: manifestData["ownedBy"] = [user["username"]]
        manifestSerializer = ManifestSerializer(data=manifestData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                manifest = Manifest.objects.get(identifier=manifestData["identifier"])
                itemExists = True
            except Manifest.DoesNotExist:
                pass
        if not itemExists:
            if manifestSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subSequences:
                    result = manifest_create_sub_sequences(user, subSequences, manifestData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subSequencesIDs"]
                if subRanges:
                    result = manifest_create_sub_ranges(user, subRanges, manifestData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subRangesIDs"]
                responseData = manifestSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Manifest"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": manifestSerializer.errors, "object": manifestData}}
                return process_result(response, activity, queue)
        else: # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: manifestData.pop("ownedBy")
            if subSequences: manifestData["sequences"] = subSequences
            if subRanges: manifestData["structures"] = subRanges
            return updateManifest(user, manifestData["identifier"], manifestData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createSequence")
def createSequence(user, identifier, sequenceData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        # check for any nested structures
        subCanvases = False
        if 'canvases' in sequenceData:
            subCanvases = sequenceData.pop("canvases")
            if "embeddedEntirely" not in sequenceData: sequenceData["embeddedEntirely"] = True
        sequenceData["ATid"] = sequenceData.pop("@id") if "@id" in sequenceData else settings.IIIF_BASE_URL+'/UofT'+'/sequence/sequence_'+str(uuid.uuid4())
        sequenceData["name"] = sequenceData["ATid"].split("/")[-1].strip()
        sequenceData["identifier"] = sequenceData["belongsTo"][0].split("/")[-2].strip() if 'belongsTo' in sequenceData else sequenceData["ATid"].split("/")[-3].strip()
        sequenceData["ATid"] = settings.IIIF_BASE_URL+'/'+sequenceData["identifier"]+'/sequence/'+sequenceData["name"]
        # Check if the request url and the given @id have the same identifier name
        if identifier and identifier!= "Unknown" and sequenceData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Sequence identifier must match with the identifier in @id.", 'object': sequenceData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: sequenceData["ownedBy"] = [user["username"]]
        sequenceSerializer = SequenceSerializer(data=sequenceData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                sequence = Sequence.objects.get(identifier=sequenceData["identifier"], name=sequenceData["name"])
                itemExists = True
            except Sequence.DoesNotExist:
                pass
        if not itemExists:
            if sequenceSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subCanvases:
                    result = sequence_create_sub_canvases(user, subCanvases, sequenceData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subCanvasesIDs"]
                responseData = sequenceSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Sequence"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}   
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": sequenceSerializer.errors, "object": sequenceData}}
                return process_result(response, activity, queue)
        else:  # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: sequenceData.pop("ownedBy")
            if subCanvases: sequenceData["canvases"] = subCanvases
            return updateSequence(user, sequenceData["identifier"], sequenceData["name"], sequenceData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createRange")
def createRange(user, identifier, rangeData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        # check for any nested structures
        subCanvases = subRanges = subMembers = False
        if 'canvases' in rangeData:
            subCanvases = rangeData.pop("canvases")
            if "embeddedEntirely" not in rangeData: rangeData["embeddedEntirely"] = True
        if 'ranges' in rangeData:
            subRanges = rangeData.pop("ranges")
            if "embeddedEntirely" not in rangeData: rangeData["embeddedEntirely"] = True
        if 'members' in rangeData:
            subMembers = rangeData.pop("members")
            if "embeddedEntirely" not in rangeData: rangeData["embeddedEntirely"] = True
        rangeData["ATid"] = rangeData.pop("@id") if "@id" in rangeData else settings.IIIF_BASE_URL+'/UofT'+'/range/range_'+str(uuid.uuid4())
        rangeData["name"] = rangeData["ATid"].split("/")[-1].strip()
        if 'belongsTo' in rangeData:
            # Special case for Manifest ID
            rangeData["identifier"] = rangeData["belongsTo"][0].split("/")[-2].strip() if 'manifest' in rangeData["belongsTo"][0] else rangeData["belongsTo"][0].split("/")[-3].strip()
        else:
            rangeData["identifier"] = rangeData["ATid"].split("/")[-3].strip()
        rangeData["ATid"] = settings.IIIF_BASE_URL+'/'+rangeData["identifier"]+'/range/'+rangeData["name"]
        if identifier and identifier!= "Unknown" and rangeData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Range identifier must match with the identifier in @id.", 'object': rangeData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: rangeData["ownedBy"] = [user["username"]]
        rangeSerializer = RangeSerializer(data=rangeData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                range = Range.objects.get(identifier=rangeData["identifier"], name=rangeData["name"])
                itemExists = True
            except Range.DoesNotExist:
                pass
        if not itemExists:
            if rangeSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subCanvases:
                    result = range_create_sub_canvases(user, subCanvases, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subCanvasesIDs"]
                if subRanges:
                    result = range_create_sub_ranges(user, subRanges, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subRangesIDs"]
                if subMembers:
                    result = range_create_sub_members(user, subMembers, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subCanvasesIDs"]
                        children += result["subRangesIDs"]
                responseData = rangeSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Range"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation: 
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
   
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": rangeSerializer.errors, "object": rangeData}}
                return process_result(response, activity, queue)
        else: # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: rangeData.pop("ownedBy")
            if subCanvases: rangeData["canvases"] = subCanvases
            if subRanges: rangeData["ranges"] = subRanges
            if subMembers: rangeData["members"] = subMembers
            return updateRange(user, rangeData["identifier"], rangeData["name"], rangeData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createCanvas")
def createCanvas(user, identifier, canvasData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        # check for any nested structures
        subAnnotations = subAnnotationLists = False
        if 'images' in canvasData:
            subAnnotations = canvasData.pop("images")
            if "embeddedEntirely" not in canvasData: canvasData["embeddedEntirely"] = True
        if 'otherContent' in canvasData:
            subAnnotationLists = canvasData.pop("otherContent")
            if "embeddedEntirely" not in canvasData: canvasData["embeddedEntirely"] = True
        canvasData["ATid"] = canvasData.pop("@id") if "@id" in canvasData else settings.IIIF_BASE_URL+'/UofT'+'/canvas/canvas_'+str(uuid.uuid4())
        canvasData["name"] = canvasData["ATid"].split("/")[-1].strip()
        canvasData["identifier"] = canvasData["belongsTo"][0].split("/")[-3].strip() if 'belongsTo' in canvasData else canvasData["ATid"].split("/")[-3].strip()
        canvasData["ATid"] = settings.IIIF_BASE_URL+'/'+canvasData["identifier"]+'/canvas/'+canvasData["name"]
        if identifier and identifier!= "Unknown" and canvasData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Canvas identifier must match with the identifier in @id.", 'object': canvasData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: canvasData["ownedBy"] = [user["username"]]
        canvasSerializer = CanvasSerializer(data=canvasData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                canvas = Canvas.objects.get(identifier=canvasData["identifier"], name=canvasData["name"])
                itemExists = True
            except Canvas.DoesNotExist:
                pass
        if not itemExists:
            if canvasSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subAnnotations:
                    result = canvas_create_sub_annotations(user, subAnnotations, canvasData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subAnnotationsIDs"]
                if subAnnotationLists:
                    result = canvas_create_sub_annotationLists(user, subAnnotationLists, canvasData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subAnnotationListsIDs"]
                responseData = canvasSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Canvas"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
   
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": canvasSerializer.errors, "object": canvasData}}
                return process_result(response, activity, queue)
        else: # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: canvasData.pop("ownedBy")
            if subAnnotations: canvasData["images"] = subAnnotations
            if subAnnotationLists: canvasData["otherContent"] = subAnnotationLists
            return updateCanvas(user, canvasData["identifier"], canvasData["name"], canvasData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createAnnotation")
def createAnnotation(user, identifier, annotationData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        if 'resource' in annotationData:
            if "embeddedEntirely" not in annotationData: annotationData["embeddedEntirely"] = True
        annotationData["ATid"] = annotationData.pop("@id") if "@id" in annotationData else settings.IIIF_BASE_URL+'/UofT'+'/annotation/annotation_'+str(uuid.uuid4())
        annotationData["name"] = annotationData["ATid"].split("/")[-1].strip()
        annotationData["identifier"] = annotationData["belongsTo"][0].split("/")[-3].strip() if 'belongsTo' in annotationData else annotationData["ATid"].split("/")[-3].strip()
        annotationData["ATid"] = settings.IIIF_BASE_URL+'/'+annotationData["identifier"]+'/annotation/'+annotationData["name"]
        if identifier and identifier!= "Unknown" and annotationData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Annotation identifier must match with the identifier in @id.", 'object': annotationData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: annotationData["ownedBy"] = [user["username"]]
        annotationSerializer = AnnotationSerializer(data=annotationData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                annotation = Annotation.objects.get(identifier=annotationData["identifier"], name=annotationData["name"])
                itemExists = True
            except Annotation.DoesNotExist:
                pass
        if not itemExists:
            if annotationSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                responseData = annotationSerializer.validated_data
                bulkCreateActions["Annotation"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotationSerializer.errors, "object": annotationData}}
                return process_result(response, activity, queue)
        else:  # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: annotationData.pop("ownedBy")
            return updateAnnotation(user, annotationData["identifier"], annotationData["name"], annotationData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createAnnotationList")
def createAnnotationList(user, identifier, annotationListData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        subAnnotations = False
        if 'resources' in annotationListData:
            subAnnotations = annotationListData.pop("resources")
            if "embeddedEntirely" not in annotationListData: annotationListData["embeddedEntirely"] = True
        annotationListData["ATid"] = annotationListData.pop("@id") if "@id" in annotationListData else settings.IIIF_BASE_URL+'/UofT'+'/list/list_'+str(uuid.uuid4())
        annotationListData["name"] = annotationListData["ATid"].split("/")[-1].strip()
        annotationListData["identifier"] = annotationListData["belongsTo"][0].split("/")[-3].strip() if 'belongsTo' in annotationListData else annotationListData["ATid"].split("/")[-3].strip()
        annotationListData["ATid"] = settings.IIIF_BASE_URL+'/'+annotationListData["identifier"]+'/list/'+annotationListData["name"]
        if identifier and identifier!= "Unknown" and annotationListData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "AnnotationList identifier must match with the identifier in @id.", 'object': annotationListData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: annotationListData["ownedBy"] = [user["username"]]
        annotationListSerializer = AnnotationListSerializer(data=annotationListData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                annotationList = AnnotationList.objects.get(identifier=annotationListData["identifier"], name=annotationListData["name"])
                itemExists = True
            except AnnotationList.DoesNotExist:
                pass
        if not itemExists:
            if annotationListSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subAnnotations:
                    result = annotation_list_create_sub_annotations(user, subAnnotations, annotationListData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subAnnotationsIDs"]
                responseData = annotationListSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["AnnotationList"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
   
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotationListSerializer.errors, "object": annotationListData}}
                return process_result(response, activity, queue)
        else:  # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: annotationListData.pop("ownedBy")
            if subAnnotations: annotationListData["resources"] = subAnnotations
            return updateAnnotationList(user, annotationListData["identifier"], annotationListData["name"], annotationListData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="createLayer")
def createLayer(user, identifier, layerData, embeddedCreation, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        children = []
        subAnnotationLists = False
        if 'otherContent' in layerData:
            subAnnotationLists = layerData.pop("otherContent")
            if "embeddedEntirely" not in layerData: layerData["embeddedEntirely"] = True
        layerData["ATid"] = layerData.pop("@id") if "@id" in layerData else settings.IIIF_BASE_URL+'/UofT'+'/layer/layer_'+str(uuid.uuid4())+'_'+str(len(Layer.objects)+1)
        layerData["name"] = layerData["ATid"].split("/")[-1].strip()
        layerData["identifier"] = layerData["belongsTo"][0].split("/")[-3].strip() if 'belongsTo' in layerData else layerData["ATid"].split("/")[-3].strip()
        layerData["ATid"] = settings.IIIF_BASE_URL+'/'+layerData["identifier"]+'/layer/'+layerData["name"]
        if identifier and identifier!= "Unknown" and layerData["identifier"]!=identifier and not embeddedCreation:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Layer identifier must match with the identifier in @id.", 'object': layerData}}
            return process_result(response, activity, queue)
        # Add current user as an owner for this object
        if not user["is_superuser"]: layerData["ownedBy"] = [user["username"]]
        layerSerializer = LayerSerializer(data=layerData)
        itemExists = False
        if embeddedCreation:
            # If this object is being created from a parent object and this identifier already exists,
            # ignore creating this identifier. Instead, update with given data.
            try:
                layer = Layer.objects.get(identifier=layerData["identifier"], name=layerData["name"])
                itemExists = True
            except Layer.DoesNotExist:
                pass
        if not itemExists:
            if layerSerializer.is_valid(): # Validations for object passed. Nested validations pending.
                if subAnnotationLists:
                    result = layer_create_sub_annotationLists(user, subAnnotationLists, layerData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                    if result["status"]=="fail":
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, activity, queue)
                    else:
                        children += result["subAnnotationListsIDs"]
                responseData = layerSerializer.validated_data
                responseData["children"] = list(set(children))
                bulkCreateActions["Layer"].append(responseData)
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
                if not embeddedCreation:
                    postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
   
                    return process_result(response, activity, queue)
                else:
                    return response
            else: # Validation error occured
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": layerSerializer.errors, "object": layerData}}
                return process_result(response, activity, queue)
        else:  # Ignore creating this identifier if it already exists. Instead update the exisiting identifier.
            if not user["is_superuser"]: layerData.pop("ownedBy")
            if subAnnotationLists: layerData["otherContent"] = subAnnotationLists
            return updateLayer(user, layerData["identifier"], layerData["name"], layerData, True, queue, activity, bulkCreateActions, fromPostCreate)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)

# --------------------------------- End POST Methods ----------------------------------------------- #



# --------------------------------- Begin PUT Methods ----------------------------------------------- #

@task(name="updateCollection")
def updateCollection(user, name, collectionData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subCollections = subManifests = subMembers = False
        if fromPostCreate:
            collection = Collection.objects.get(name=name)
            if "_id" in collectionData: del collectionData["_id"]
        else:
            if name=="UofT":
                response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Top level UofT Collection cannot be edited.", "object": collectionData}}
                return process_result(response, activity, queue)
            collection = Collection.objects.get(name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in collection.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            # check for any nested structures
            if 'collections' in collectionData:
                subCollections = collectionData.pop("collections")
            if 'manifests' in collectionData:
                subManifests = collectionData.pop("manifests")
            if 'members' in collectionData:
                subMembers = collectionData.pop("members")
            if "@id" in collectionData: # {scheme}://{host}/{prefix}/collections/{name}
                collectionData["name"] = collectionData.pop("@id").split("/")[-1].strip()
            else:
                collectionData["name"] = name
            collectionData["ATid"] = settings.IIIF_BASE_URL+'/collections/'+collectionData["name"]
        # If this is an embeddedUpdate, append belongsTo if this collection already has another belongsTo
        if embeddedUpdate and 'belongsTo' in collectionData and collection.belongsTo != []:
            collectionData['belongsTo'] += collection.belongsTo
            collectionData['belongsTo'] = set(collectionData['belongsTo'])
        if embeddedUpdate and 'children' in collectionData and collection.children != []:
            collectionData['children'] += collection.children
            collectionData['children'] = set(collectionData['children'])
        collectionSerializer = CollectionSerializer(collection, data=collectionData, partial=True)
        if collectionSerializer.is_valid():
            # Update all Collections & Manifests that 'belongsTo' this Collection if @id(name) has been changed
            if collectionData["name"]!=name:
                for belongsToCollection in Collection.objects(belongsTo__contains=collection.ATid):
                    belongsToCollection.belongsTo.remove(collection.ATid)
                    belongsToCollection.belongsTo.append(collectionData["ATid"])
                    belongsToCollection.save()
                for belongsToManifest in Manifest.objects(belongsTo__contains=collection.ATid):
                    belongsToManifest.belongsTo.remove(collection.ATid)
                    belongsToManifest.belongsTo.append(collectionData["ATid"])
                    belongsToManifest.save()
                for parentCollection in Collection.objects(children__contains=collection.ATid):
                    parentCollection.children.remove(collection.ATid)
                    parentCollection.children.append(collectionData["ATid"])
                    parentCollection.save()
            # Update all subCollections, submanifests and subMembers
            if subCollections:
                result = collection_update_sub_collections(user, subCollections, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subManifests:
                result = collection_update_sub_manifests(user, subManifests, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subMembers:
                result = collection_update_sub_members(user, subMembers, collectionData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            collectionSerializer.save()
            responseData = collectionSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": collectionSerializer.errors, "object": collectionData}}
            return process_result(response, activity, queue)
    except Collection.DoesNotExist:
        if embeddedUpdate:
            return createCollection(user, collectionData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Collection with name '" + name + "' does not exist."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateManifest")
def updateManifest(user, identifier, manifestData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subSequences = subRanges = False
        if fromPostCreate:
            manifest = Manifest.objects.get(identifier=identifier)
            if "_id" in manifestData: del manifestData["_id"]
        else:
            if identifier=="UofT":
                response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Item name cannot be: UofT.", "object": manifestData}}
                return process_result(response, activity, queue)
            manifest = Manifest.objects.get(identifier=identifier)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in manifest.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            # Check for any nested structures
            if 'sequences' in manifestData:
                subSequences = manifestData.pop("sequences")
            if 'structures' in manifestData:
                subRanges = manifestData.pop("structures")
            if "@id" in manifestData:
                manifestData["identifier"] = manifestData.pop("@id").split("/")[-2].strip()
            else:
                manifestData["identifier"] = identifier
            manifestData["ATid"] = settings.IIIF_BASE_URL+'/'+manifestData["identifier"]+'/manifest'
        # If this is an embeddedUpdate, append belongsTo if this manifest already has another belongsTo
        if embeddedUpdate and 'belongsTo' in manifestData and manifest.belongsTo != []:
            manifestData['belongsTo'] += manifest.belongsTo
            manifestData['belongsTo'] = set(manifestData['belongsTo'])
        if embeddedUpdate and 'children' in manifestData and manifest.children != []:
            manifestData['children'] += manifest.children
            manifestData['children'] = set(manifestData['children'])
        manifestSerializer = ManifestSerializer(manifest, data=manifestData, partial=True)
        if manifestSerializer.is_valid():
            # Update all Sequences & Ranges that 'belongsTo' this Manifest if @id(identifier) has been changed
            if manifestData["identifier"]!=identifier:
                for belongsToSequence in Sequence.objects(belongsTo__contains=manifest.ATid):
                    belongsToSequence.belongsTo.remove(manifest.ATid)
                    belongsToSequence.belongsTo.append(manifestData["ATid"])
                    belongsToSequence.save()
                for belongsToRange in Range.objects(belongsTo__contains=manifest.ATid):
                    belongsToRange.belongsTo.remove(manifest.ATid)
                    belongsToRange.belongsTo.append(manifestData["ATid"])
                    belongsToRange.save()
                for parentCollection in Collection.objects(children__contains=manifest.ATid):
                    parentCollection.children.remove(manifest.ATid)
                    parentCollection.children.append(manifestData["ATid"])
                    parentCollection.save()
            # Update all subSequences and subRanges
            if subSequences:
                result = manifest_update_sub_sequences(user, subSequences, manifestData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subRanges:
                result = manifest_update_sub_ranges(user, subRanges, manifestData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            manifestSerializer.save()
            responseData = manifestSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": manifestSerializer.errors, "object": manifestData}}
            return process_result(response, activity, queue)
    except Manifest.DoesNotExist as e:
        if embeddedUpdate:
            return createManifest(user, identifier, manifestData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "'" + identifier + "' does not have a Manifest."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateSequence")
def updateSequence(user, identifier, name, sequenceData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subCanvases = False
        if fromPostCreate:
            sequence = Sequence.objects.get(identifier=identifier, name=name)
            if "_id" in sequenceData: del sequenceData["_id"]
        else:
            sequence = Sequence.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in sequence.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            if 'canvases' in sequenceData:
                subCanvases = sequenceData.pop("canvases")
            if "@id" in sequenceData:
                sequenceData["ATid"] = sequenceData.pop("@id")
                sequenceData["name"] = sequenceData["ATid"].split("/")[-1].strip()
                sequenceData["identifier"] = sequenceData["ATid"].split("/")[-3].strip()
            else:
                sequenceData["identifier"] = identifier
                sequenceData["name"] = name
            sequenceData["ATid"] = settings.IIIF_BASE_URL+'/'+sequenceData["identifier"]+'/sequence/'+sequenceData["name"]
        # If this is an embeddedUpdate, append belongsTo if this sequence already has another belongsTo
        if embeddedUpdate and 'belongsTo' in sequenceData and sequence.belongsTo != []:
            sequenceData['belongsTo'] += sequence.belongsTo
            sequenceData['belongsTo'] = set(sequenceData['belongsTo'])
        if embeddedUpdate and 'children' in sequenceData and sequence.children != []:
            sequenceData['children'] += sequence.children
            sequenceData['children'] = set(sequenceData['children'])
        sequenceSerializer = SequenceSerializer(sequence, data=sequenceData, partial=True)
        if sequenceSerializer.is_valid():
            # Update all Canvaes that 'belongsTo' Sequence if @id(identifier or name) has been changed
            if sequenceData["identifier"]!=identifier or sequenceData["name"]!=name:
                for belongsToCanvas in Canvas.objects(belongsTo__contains=sequence.ATid):
                    belongsToCanvas.belongsTo.remove(sequence.ATid)
                    belongsToCanvas.belongsTo.append(sequenceData["ATid"])
                    belongsToCanvas.save()
                for parentManifest in Manifest.objects(children__contains=sequence.ATid):
                    parentManifest.children.remove(sequence.ATid)
                    parentManifest.children.append(sequenceData["ATid"])
                    parentManifest.save()
            if subCanvases:
                result = sequence_update_sub_canvases(user, subCanvases, sequenceData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            sequenceSerializer.save()
            responseData = sequenceSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": sequenceSerializer.errors, "object": sequenceData}}
            return process_result(response, activity, queue)
    except Sequence.DoesNotExist as e:
        if embeddedUpdate:
            return createSequence(user, identifier, sequenceData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Sequence with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateRange")
def updateRange(user, identifier, name, rangeData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subCanvases = subRanges = subMembers = False
        if fromPostCreate:
            range = Range.objects.get(identifier=identifier, name=name)
            if "_id" in rangeData: del rangeData["_id"]
        else:
            range = Range.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in range.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            # Check for nested objects
            if 'canvases' in rangeData:
                subCanvases = rangeData.pop("canvases")
            if 'ranges' in rangeData:
                subRanges = rangeData.pop("ranges")
            if 'members' in rangeData:
                subMembers = rangeData.pop("members")
            if "@id" in rangeData:
                rangeData["ATid"] = rangeData.pop("@id")
                rangeData["name"] = rangeData["ATid"].split("/")[-1].strip()
                rangeData["identifier"] = rangeData["ATid"].split("/")[-3].strip()
            else:
                rangeData["identifier"] = identifier
                rangeData["name"] = name
            rangeData["ATid"] = settings.IIIF_BASE_URL+'/'+rangeData["identifier"]+'/range/'+rangeData["name"]
        # If this is an embeddedUpdate, append belongsTo if this range already has another belongsTo
        if embeddedUpdate and 'belongsTo' in rangeData and range.belongsTo != []:
            rangeData['belongsTo'] += range.belongsTo
            rangeData['belongsTo'] = set(rangeData['belongsTo'])
        if embeddedUpdate and 'children' in rangeData and range.children != []:
            rangeData['children'] += range.children
            rangeData['children'] = set(rangeData['children'])
        rangeSerializer = RangeSerializer(range, data=rangeData, partial=True)
        if rangeSerializer.is_valid():
            # Update all Canvaes & Ranges that 'belongsTo' this Range if @id(identifier or name) has been changed
            if rangeData["identifier"]!=identifier or rangeData["name"]!=name:
                for belongsToCanvas in Canvas.objects(belongsTo__contains=range.ATid):
                    belongsToCanvas.belongsTo.remove(range.ATid)
                    belongsToCanvas.belongsTo.append(rangeData["ATid"])
                    belongsToCanvas.save()
                for belongsToRange in Range.objects(belongsTo__contains=range.ATid):
                    belongsToRange.belongsTo.remove(range.ATid)
                    belongsToRange.belongsTo.append(rangeData["ATid"])
                    belongsToRange.save()
                for parentManifest in Manifest.objects(children__contains=range.ATid):
                    parentManifest.children.remove(range.ATid)
                    parentManifest.children.append(rangeData["ATid"])
                    parentManifest.save()
                for parentRange in Range.objects(children__contains=range.ATid):
                    parentRange.children.remove(range.ATid)
                    parentRange.children.append(rangeData["ATid"])
                    parentRange.save()
            if subCanvases:
                result = range_update_sub_canvases(user, subCanvases, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subRanges:
                result = range_update_sub_ranges(user, subRanges, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subMembers:
                result = range_update_sub_members(user, subMembers, rangeData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            rangeSerializer.save()
            responseData = rangeSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": rangeSerializer.errors, "object": rangeData}}
            return process_result(response, activity, queue)
    except Range.DoesNotExist as e:
        if embeddedUpdate:
            return createRange(user, identifier, rangeData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Range with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateCanvas")
def updateCanvas(user, identifier, name, canvasData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subAnnotations = subAnnotationLists = False
        if fromPostCreate:
            canvas = Canvas.objects.get(identifier=identifier, name=name)
            if "_id" in canvasData: del canvasData["_id"]
        else:
            canvas = Canvas.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in canvas.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            # Check for nested objects
            if 'images' in canvasData:
                subAnnotations = canvasData.pop("images")
            if 'otherContent' in canvasData:
                subAnnotationLists = canvasData.pop("otherContent")
            if "@id" in canvasData:
                canvasData["ATid"] = canvasData.pop("@id")
                canvasData["name"] = canvasData["ATid"].split("/")[-1].strip()
                canvasData["identifier"] = canvasData["ATid"].split("/")[-3].strip()
            else:
                canvasData["identifier"] = identifier
                canvasData["name"] = name
            canvasData["ATid"] = settings.IIIF_BASE_URL+'/'+canvasData["identifier"]+'/canvas/'+canvasData["name"]
        # If this is an embeddedUpdate, append belongsTo if this canvas already has another belongsTo
        if embeddedUpdate and 'belongsTo' in canvasData and canvas.belongsTo != []:
            canvasData['belongsTo'] += canvas.belongsTo
            canvasData['belongsTo'] = set(canvasData['belongsTo'])
        if embeddedUpdate and 'children' in canvasData and canvas.children != []:
            canvasData['children'] += canvas.children
            canvasData['children'] = set(canvasData['children'])
        canvasSerializer = CanvasSerializer(canvas, data=canvasData, partial=True)
        if canvasSerializer.is_valid():
            # Update all Annotations & AnnotationLists that 'belongsTo' this Canvas if @id(identifier or name) has been changed
            if canvasData["identifier"]!=identifier or canvasData["name"]!=name:
                for belongsToAnnotation in Annotation.objects(belongsTo__contains=canvas.ATid):
                    belongsToAnnotation.belongsTo.remove(canvas.ATid)
                    belongsToAnnotation.belongsTo.append(canvasData["ATid"])
                    belongsToAnnotation.save()
                for belongsToAnnotationList in AnnotationList.objects(belongsTo__contains=canvas.ATid):
                    belongsToAnnotationList.belongsTo.remove(canvas.ATid)
                    belongsToAnnotationList.belongsTo.append(canvasData["ATid"])
                    belongsToAnnotationList.save()
                for parentSequence in Sequence.objects(children__contains=canvas.ATid):
                    parentSequence.children.remove(canvas.ATid)
                    parentSequence.children.append(canvasData["ATid"])
                    parentSequence.save()
                for parentRange in Range.objects(children__contains=canvas.ATid):
                    parentRange.children.remove(canvas.ATid)
                    parentRange.children.append(canvasData["ATid"])
                    parentRange.save()
            if subAnnotations:
                result = canvas_update_sub_annotations(user, subAnnotations, canvasData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            if subAnnotationLists:
                result = canvas_update_sub_annotationLists(user, subAnnotationLists, canvasData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            canvasSerializer.save()
            responseData = canvasSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": canvasSerializer.errors, "object": canvasData}}
            return process_result(response, activity, queue)
    except Canvas.DoesNotExist as e:
        if embeddedUpdate:
            return createCanvas(user, identifier, canvasData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Canvas with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateAnnotation")
def updateAnnotation(user, identifier, name, annotationData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        if fromPostCreate:
            annotation = Annotation.objects.get(identifier=identifier, name=name)
            if "_id" in annotationData: del annotationData["_id"]
        else:
            annotation = Annotation.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in annotation.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            if "@id" in annotationData:
                annotationData["ATid"] = annotationData.pop("@id")
                annotationData["name"] = annotationData["ATid"].split("/")[-1].strip()
                annotationData["identifier"] = annotationData["ATid"].split("/")[-3].strip()
            else:
                annotationData["identifier"] = identifier
                annotationData["name"] = name
            annotationData["ATid"] = settings.IIIF_BASE_URL+'/'+annotationData["identifier"]+'/annotation/'+annotationData["name"]
        # Update belongsTo if this annotation already has another belongsTo
        if embeddedUpdate and 'belongsTo' in annotationData and annotation.belongsTo != [] and annotationData['belongsTo'][0] not in annotation.belongsTo:
            annotationData['belongsTo'] += annotation.belongsTo
            annotationData['belongsTo'] = set(annotationData['belongsTo'])
        if embeddedUpdate and 'children' in annotationData and annotation.children != [] and annotationData['children'][0] not in annotation.children:
            annotationData['children'] += annotation.children
            annotationData['children'] = set(annotationData['children'])
        annotationSerializer = AnnotationSerializer(annotation, data=annotationData, partial=True)
        if annotationSerializer.is_valid():
            # Update all Resources that 'belongsTo' this Annotation if @id(identifier or name) has been changed
            if annotationData["identifier"]!=identifier or annotationData["name"]!=name:
                for parentCanvas in Canvas.objects(children__contains=annotation.ATid):
                    parentCanvas.children.remove(annotation.ATid)
                    parentCanvas.children.append(annotationData["ATid"])
                    parentCanvas.save()
                for parentAnnotationList in AnnotationList.objects(children__contains=annotation.ATid):
                    parentAnnotationList.children.remove(annotation.ATid)
                    parentAnnotationList.children.append(annotationData["ATid"])
                    parentAnnotationList.save()
            annotationSerializer.save()
            responseData = annotationSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotationSerializer.errors, "object": annotationData}}
            return process_result(response, activity, queue)
    except Annotation.DoesNotExist as e:
        if embeddedUpdate:
            return createAnnotation(user, identifier, annotationData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Annotation with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateAnnotationList")
def updateAnnotationList(user, identifier, name, annotationListData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subAnnotations = False
        if fromPostCreate:
            annotationList = AnnotationList.objects.get(identifier=identifier, name=name)
            if "_id" in annotationListData: del annotationListData["_id"]
        else:
            annotationList = AnnotationList.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in annotationList.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            if 'resources' in annotationListData:
                subAnnotations = annotationListData.pop("resources")
            if "@id" in annotationListData:
                annotationListData["ATid"] = annotationListData.pop("@id")
                annotationListData["name"] = annotationListData["ATid"].split("/")[-1].strip()
                annotationListData["identifier"] = annotationListData["ATid"].split("/")[-3].strip()
            else:
                annotationListData["identifier"] = identifier
                annotationListData["name"] = name
            annotationListData["ATid"] = settings.IIIF_BASE_URL+'/'+annotationListData["identifier"]+'/list/'+annotationListData["name"]
        # If this is an embeddedUpdate, append belongsTo if this annotationList already has another belongsTo
        if embeddedUpdate and 'belongsTo' in annotationListData and annotationList.belongsTo != [] and annotationListData['belongsTo'][0] not in annotationList.belongsTo:
            annotationListData['belongsTo'] += annotationList.belongsTo
            annotationListData['belongsTo'] = set(annotationListData['belongsTo'])
        if embeddedUpdate and 'children' in annotationListData and annotationList.children != [] and annotationListData['children'][0] not in annotationList.children:
            annotationListData['children'] += annotationList.children
            annotationListData['children'] = set(annotationListData['children'])
        annotationListSerializer = AnnotationListSerializer(annotationList, data=annotationListData, partial=True)
        if annotationListSerializer.is_valid():
            # Update all Annotations that 'belongsTo' this AnnotationList if @id(identifier or name) has been changed
            if annotationListData["identifier"]!=identifier or annotationListData["name"]!=name:
                for belongsToAnnotation in Annotation.objects(belongsTo=annotationList.ATid):
                    belongsToAnnotation.belongsTo.remove(annotationList.ATid)
                    belongsToAnnotation.belongsTo.append(annotationListData["ATid"])
                    belongsToAnnotation.save()
                for parentCanvas in Canvas.objects(children__contains=annotationList.ATid):
                    parentCanvas.children.remove(annotationList.ATid)
                    parentCanvas.children.append(annotationListData["ATid"])
                    parentCanvas.save()
                for parentLayer in Layer.objects(children__contains=annotationList.ATid):
                    parentLayer.children.remove(annotationList.ATid)
                    parentLayer.children.append(annotationListData["ATid"])
                    parentLayer.save()
            if subAnnotations:
                result = annotation_list_update_sub_annotations(user, subAnnotations, annotationListData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            annotationListSerializer.save()
            responseData = annotationListSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotationListSerializer.errors, "object": annotationListData}}
            return process_result(response, activity, queue)
    except AnnotationList.DoesNotExist as e:
        if embeddedUpdate:
            return createAnnotationList(user, identifier, annotationListData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "AnnotationList with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="updateLayer")
def updateLayer(user, identifier, name, layerData, embeddedUpdate, queue, activity, bulkCreateActions, fromPostCreate=False):
    try:
        subAnnotationLists = False
        if fromPostCreate:
            layer = Layer.objects.get(identifier=identifier, name=name)
            if "_id" in layerData: del layerData["_id"]
        else:
            layer = Layer.objects.get(identifier=identifier, name=name)
            # Check if current user has permission for this object
            if not user["is_superuser"] and user["username"] not in layer.ownedBy:
                response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
                return process_result(response, activity, queue)
            if 'otherContent' in layerData:
                subAnnotationLists = layerData.pop("otherContent")
            if "@id" in layerData:
                layerData["ATid"] = layerData.pop("@id")
                layerData["name"] = layerData["ATid"].split("/")[-1].strip()
                layerData["identifier"] = layerData["ATid"].split("/")[-3].strip()
            else:
                layerData["identifier"] = identifier
                layerData["name"] = name
            layerData["ATid"] = settings.IIIF_BASE_URL+'/'+layerData["identifier"]+'/layer/'+layerData["name"]
        # If this is an embeddedUpdate, append belongsTo if this layer already has another belongsTo
        if embeddedUpdate and 'belongsTo' in layerData and layer.belongsTo != []:
            layerData['belongsTo'] += layer.belongsTo
            layerData['belongsTo'] = set(layerData['belongsTo'])
        if embeddedUpdate and 'children' in layerData and layer.children != []:
            layerData['children'] += layer.children
            layerData['children'] = set(layerData['children'])
        layerSerializer = LayerSerializer(layer, data=layerData, partial=True)
        if layerSerializer.is_valid():
            # Update all Canvaes & Layers that 'belongsTo' this Layer if @id(identifier or name) has been changed
            if layerData["identifier"]!=identifier or layerData["name"]!=name:
                for belongsToAnnotationList in AnnotationList.objects(belongsTo__contains=layer.ATid):
                    belongsToAnnotationList.belongsTo.remove(layer.ATid)
                    belongsToAnnotationList.belongsTo.append(layerData["ATid"])
                    belongsToAnnotationList.save()
                for parentRange in Range.objects(children__contains=layer.ATid):
                    parentRange.children.remove(layer.ATid)
                    parentRange.children.append(layerData["ATid"])
                    parentRange.save()
            if subAnnotationLists:
                result = layer_update_sub_annotationLists(user, subAnnotationLists, layerData["ATid"], queue, activity, bulkCreateActions, fromPostCreate)
                if result["status"]=="fail":
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, activity, queue)
            layerSerializer.save()
            responseData = layerSerializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            if not embeddedUpdate:
                postBulkInsertUpdate(bulkCreate(bulkCreateActions), user, activity, queue)
                return process_result(response, activity, queue)
            else:
                return response
        else: # Validation error occured
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": layerSerializer.errors, "object": layerData}}
            return process_result(response, activity, queue)
    except Layer.DoesNotExist as e:
        if embeddedUpdate:
            return createLayer(user, identifier, layerData, True, queue, activity, bulkCreateActions, fromPostCreate)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Layer with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
            return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


# --------------------------------- End PUT Methods ----------------------------------------------- #



# --------------------------------- Begin DELETE Methods ----------------------------------------------- #

@task(name="destroyCollection")
def destroyCollection(user, name, embeddedDelete, queue, activity):
    try:
        collection = Collection.objects.get(name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in collection.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(collection.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all Collections & Manifests that 'belongsTo' this Collection.
        requiredChildren = getRequiredChildren(collection=collection)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Collection"].append(collection.ATid)
        if not embeddedDelete:
            responseData = collection
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Collection '" + name + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Collection.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Collection with name '" + name + "' does not exist."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyManifest")
def destroyManifest(user, identifier, embeddedDelete, queue, activity):
    try:
        manifest = Manifest.objects.get(identifier=identifier)
        # Check if current user has permission for this object
        if not user["is_superuser"] and user["username"] not in manifest.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if not user["is_superuser"] and len(manifest.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all children of this Manifest.
        requiredChildren = getRequiredChildren(manifest=manifest)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Manifest"].append(manifest.ATid)
        if not embeddedDelete:
            responseData = manifest
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted the Manifest of '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Manifest.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "'" + identifier + "' does not have a Manifest."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroySequence")
def destroySequence(user, identifier, name, embeddedDelete, queue, activity):
    try:
        sequence = Sequence.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in sequence.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(sequence.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all Canvases that 'belongsTo' this Sequence.
        requiredChildren = getRequiredChildren(sequence=sequence)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Sequence"].append(sequence.ATid)
        if not embeddedDelete:
            responseData = sequence
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Sequence '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Sequence.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Sequence with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyRange")
def destroyRange(user, identifier, name, embeddedDelete, queue, activity):
    try:
        rangeObject = Range.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in rangeObject.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(rangeObject.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all Canvases & Ranges that 'belongsTo' this Range.
        requiredChildren = getRequiredChildren(rangeObject=rangeObject)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Range"].append(rangeObject.ATid)
        if not embeddedDelete:
            responseData = rangeObject
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Range '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Range.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Range with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyCanvas")
def destroyCanvas(user, identifier, name, embeddedDelete, queue, activity):
    try:
        canvas = Canvas.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in canvas.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(canvas.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all Annotations & AnnotationLists that 'belongsTo' this Canvas.
        requiredChildren = getRequiredChildren(canvas=canvas)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Canvas"].append(canvas.ATid)
        if not embeddedDelete:
            responseData = canvas
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Canvas '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Canvas.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Canvas with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyAnnotation")
def destroyAnnotation(user, identifier, name, embeddedDelete, queue, activity):
    try:
        annotation = Annotation.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in annotation.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(annotation.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        annotation.delete()
        if not embeddedDelete:
            responseData = annotation
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Annotation '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            return process_result(response, activity, queue)
    except Annotation.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Annotation with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyAnnotationList")
def destroyAnnotationList(user, identifier, name, embeddedDelete, queue, activity):
    try:
        annotationList = AnnotationList.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in annotationList.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(annotationList.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all Annotationes that 'belongsTo' this AnnotationList.
        requiredChildren = getRequiredChildren(annotationList=annotationList)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["AnnotationList"].append(annotationList.ATid)
        if not embeddedDelete:
            responseData = annotationList
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted AnnotationList '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except AnnotationList.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "AnnotationList with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


@task(name="destroyLayer")
def destroyLayer(user, identifier, name, embeddedDelete, queue, activity):
    try:
        layer = Layer.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        if  not user["is_superuser"] and user["username"] not in layer.ownedBy:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
            return process_result(response, activity, queue)
        # Check if this object belongs to another User
        if  not user["is_superuser"] and len(layer.ownedBy) > 1:
            response = {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}
            return process_result(response, activity, queue)
        # Delete/Update all AnnotationLists that 'belongsTo' this Layer.
        requiredChildren = getRequiredChildren(layer=layer)
        bulkDeleteActions = {}
        bulkDeleteActions["Collection"] = [item["ATid"] for item in requiredChildren["Collection"]]
        bulkDeleteActions["Manifest"] = [item["ATid"] for item in requiredChildren["Manifest"]]
        bulkDeleteActions["Sequence"] = [item["ATid"] for item in requiredChildren["Sequence"]]
        bulkDeleteActions["Range"] = [item["ATid"] for item in requiredChildren["Range"]]
        bulkDeleteActions["Canvas"] = [item["ATid"] for item in requiredChildren["Canvas"]]
        bulkDeleteActions["Annotation"] = [item["ATid"] for item in requiredChildren["Annotation"]]
        bulkDeleteActions["AnnotationList"] = [item["ATid"] for item in requiredChildren["AnnotationList"]]
        bulkDeleteActions["Layer"] = [item["ATid"] for item in requiredChildren["Layer"]]
        bulkDeleteActions["Layer"].append(layer.ATid)
        if not embeddedDelete:
            responseData = layer
            response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': "Successfully deleted Layer '" + name + "' from identifier '" + identifier + "'.", "@id": responseData["ATid"], "@type": responseData["ATtype"]}}
            bulkDelete(bulkDeleteActions)
            return process_result(response, activity, queue)
    except Layer.DoesNotExist as e:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Layer with name '" + name + "' does not exist in identifier '" + identifier + "'."}}
        return process_result(response, activity, queue)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, activity, queue)


# --------------------------------- End DELETE Methods ----------------------------------------------- #




# --------------------------------- Begin Helper Functions ----------------------------------------------- #

def collection_create_sub_collections(user, collections, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCollectionsIDs = []
    for index, collection in enumerate(collections):
        collection["belongsTo"] = [belongsTo]
        collection["order"] = index+1
        userBody = collection
        subCollection = createCollection(user, collection, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCollection["status"] >= 400: 
            return {"status": "fail", "errors": subCollection}
        else:
            subCollectionsIDs.append(subCollection["data"]["@id"])
    return {"status": "success", "subCollectionsIDs": subCollectionsIDs}


def collection_create_sub_manifests(user, manifests, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subManifestsIDs = []
    for index, manifest in enumerate(manifests):
        manifest["belongsTo"] = [belongsTo]
        manifest["order"] = index+1
        subManifest = createManifest(user, None, manifest, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subManifest["status"] >= 400: 
            return {"status": "fail", "errors": subManifest}
        else:
            subManifestsIDs.append(subManifest["data"]["@id"])
    return {"status": "success", "subManifestsIDs": subManifestsIDs}


def collection_create_sub_members(user, members, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCollections = []
    subManifests = []
    subCollectionsIDs = []
    subManifestsIDs = []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongsTo]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}
        else:
            if member["@type"] not in ["sc:Collection", "sc:Manifest"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Collection or sc:Manifest.'}}
        if member["@type"]=="sc:Collection":
            subCollections.append(member)
        else:
            subManifests.append(member)
    result = collection_create_sub_collections(user, subCollections, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"]=="fail":
        return result
    else:
        subCollectionsIDs = result["subCollectionsIDs"]
    result = collection_create_sub_manifests(user, subManifests, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"]=="fail":
        return result
    else:
        subManifestsIDs = result["subManifestsIDs"] 
    return {"status": "success", "subCollectionsIDs": subCollectionsIDs, "subManifestsIDs": subManifestsIDs}


def collection_update_sub_collections(user, collections, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCollectionsIDs = []
    for index, collection in enumerate(collections):
        try:
            name = 'Unknown';
            if "@id" in collection:
                name = collection["@id"].split("/")[-1].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        collection["belongsTo"] = [belongsTo]
        collection["order"] = index+1
        subCollection = updateCollection(user, name, collection, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCollection["status"] >= 400: 
            return {"status": "fail", "errors": subCollection}
        else:
            subCollectionsIDs.append(subCollection["data"]["@id"])
    return {"status": "success", "subCollectionsIDs": subCollectionsIDs}


def collection_update_sub_manifests(user, manifests, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subManifestsIDs = []
    for index, manifest in enumerate(manifests):
        try:
            identifier = 'Unknown';
            if "@id" in manifest:
                identifier = manifest["@id"].split("/")[-2].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        manifest["belongsTo"] = [belongsTo]
        manifest["order"] = index+1
        subManifest = updateManifest(user, identifier, manifest, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subManifest["status"] >= 400: 
            return {"status": "fail", "errors": subManifest}
        else:
            subManifestsIDs.append(subManifest["data"]["@id"])
    return {"status": "success", "subManifestsIDs": subManifestsIDs}


def collection_update_sub_members(user, members, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCollections = []
    subManifests = []
    subCollectionsIDs = []
    subManifestsIDs = []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongsTo]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}
        else:
            if member["@type"] not in ["sc:Collection", "sc:Manifest"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Collection or sc:Manifest.'}}
        if member["@type"]=="sc:Collection":
            subCollections.append(member)
        else:
            subManifests.append(member)
    result = collection_update_sub_collections(user, subCollections, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"]=="fail":
        return result
    else:
        subCollectionsIDs = result["subCollectionsIDs"]
    result =  collection_update_sub_manifests(user, subManifests, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"]=="fail":
        return result
    else:
        subManifestsIDs = result["subManifestsIDs"] 
    return {"status": "success", "subCollectionsIDs": subCollectionsIDs, "subManifestsIDs": subManifestsIDs}


def manifest_create_sub_sequences(user, sequences, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subSequencesIDs = []
    for index, sequence in enumerate(sequences):
        sequence["belongsTo"] = [belongsTo]
        sequence["order"] = index+1
        sequence["embeddedEntirely"] = True if index==0 else False
        subSequence = createSequence(user, None, sequence, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subSequence["status"] >= 400: 
            return {"status": "fail", "errors": subSequence}
        else:
            subSequencesIDs.append(subSequence["data"]["@id"])
    return {"status": "success", "subSequencesIDs": subSequencesIDs}


def manifest_create_sub_ranges(user, ranges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subRangesIDs = []
    for index, rangeObject in enumerate(ranges):
        rangeObject["belongsTo"] = [belongsTo]
        rangeObject["order"] = index+1
        subRange = createRange(user, None, rangeObject, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subRange["status"] >= 400:  
            return {"status": "fail", "errors": subRange} 
        else:
            subRangesIDs.append(subRange["data"]["@id"])
    return {"status": "success", "subRangesIDs": subRangesIDs}


def manifest_update_sub_sequences(user, sequences, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subSequencesIDs = []
    for index, sequence in enumerate(sequences):
        try:
            name = identifier = 'Unknown';
            if "@id" in sequence:
                name = sequence["@id"].split("/")[-1].strip()
                identifier = sequence["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        sequence["belongsTo"] = [belongsTo]
        sequence["order"] = index+1
        sequence["embeddedEntirely"] = True if index==0 else False
        subSequence = updateSequence(user, identifier, name, sequence, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subSequence["status"] >= 400: 
            return {"status": "fail", "errors": subSequence}
        else:
            subSequencesIDs.append(subSequence["data"]["@id"])
    return {"status": "success", "subSequencesIDs": subSequencesIDs}


def manifest_update_sub_ranges(user, ranges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subRangesIDs = []
    for index, rangeObject in enumerate(ranges):
        try:
            name = identifier = 'Unknown';
            if "@id" in rangeObject:
                name = rangeObject["@id"].split("/")[-1].strip()
                identifier = rangeObject["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        rangeObject["belongsTo"] = [belongsTo]
        rangeObject["order"] = index+1
        subRange = updateRange(user, identifier, name, rangeObject, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subRange["status"] >= 400:  
            return {"status": "fail", "errors": subRange} 
        else:
            subRangesIDs.append(subRange["data"]["@id"])
    return {"status": "success", "subRangesIDs": subRangesIDs}


def sequence_create_sub_canvases(user, canvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvasesIDs = []
    for index, canvas in enumerate(canvases):
        canvas["belongsTo"] = [belongsTo]
        canvas["order"] = index+1
        subCanvas = createCanvas(user, None, canvas, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCanvas["status"] >= 400:  
            return {"status": "fail", "errors": subCanvas} 
        else:
            subCanvasesIDs.append(subCanvas["data"]["@id"])
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs}


def sequence_update_sub_canvases(user, canvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvasesIDs = []
    for index, canvas in enumerate(canvases):
        try:
            name = identifier = 'Unknown';
            if "@id" in canvas:
                name = canvas["@id"].split("/")[-1].strip()
                identifier = canvas["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        canvas["belongsTo"] = [belongsTo]
        canvas["order"] = index+1
        subCanvas = updateCanvas(user, identifier, name, canvas, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCanvas["status"] >= 400:  
            return {"status": "fail", "errors": subCanvas} 
        else:
            subCanvasesIDs.append(subCanvas["data"]["@id"])
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs}


def range_create_sub_canvases(user, canvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvasesIDs = []
    for index, canvas in enumerate(canvases):
        if isinstance(canvas, basestring):
            canvas = {"@id": canvas}
        canvas["belongsTo"] = [belongsTo]
        canvas["order"] = index+1
        subCanvas = createCanvas(user, None, canvas, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCanvas["status"] >= 400:  
            return {"status": "fail", "errors": subCanvas} 
        else:
            subCanvasesIDs.append(subCanvas["data"]["@id"])
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs}


def range_create_sub_ranges(user, ranges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subRangesIDs = []
    for index, rangeObject in enumerate(ranges):
        if isinstance(rangeObject, basestring):
            rangeObject = {"@id": rangeObject}
        rangeObject["belongsTo"] = [belongsTo]
        rangeObject["order"] = index+1
        subRange = createRange(user, None, rangeObject, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subRange["status"] >= 400:  
            return {"status": "fail", "errors": subRange}
        else:
            subRangesIDs.append(subRange["data"]["@id"])
    return {"status": "success", "subRangesIDs": subRangesIDs}


def range_create_sub_members(user, members, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvases = []
    subRanges = []
    subCanvasesIDs = []
    subRangesIDs = []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongsTo]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}
        else:
            if member["@type"] not in ["sc:Canvas", "sc:Range"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Canvas or sc:Range.'}}
        if member["@type"]=="sc:Canvas":
            subCanvases.append(member)
        else:
            subRanges.append(member)
    result = range_create_sub_canvases(user, subCanvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"] == "fail":  
        return result 
    else:
        subCanvasesIDs = result["subCanvasesIDs"]
    result =  range_create_sub_ranges(user, subRanges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"] == "fail":  
        return result
    else:
        subRangesIDs = result["subRangesIDs"]
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs, "subRangesIDs": subRangesIDs}


def range_update_sub_canvases(user, canvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvasesIDs = []
    for index, canvas in enumerate(canvases):
        if isinstance(canvas, basestring):
            canvas = {"@id": canvas}
        try:
            name = identifier = 'Unknown';
            if "@id" in canvas:
                name = canvas["@id"].split("/")[-1].strip()
                identifier = canvas["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        canvas["belongsTo"] = [belongsTo]
        canvas["order"] = index+1
        subCanvas = updateCanvas(user, identifier, name, canvas, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subCanvas["status"] >= 400:  
            return {"status": "fail", "errors": subCanvas} 
        else:
            subCanvasesIDs.append(subCanvas["data"]["@id"])
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs}


def range_update_sub_ranges(user, ranges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subRangesIDs = []
    for index, rangeObject in enumerate(ranges):
        if isinstance(rangeObject, basestring):
            rangeObject = {"@id": rangeObject}
        try:
            name = identifier = 'Unknown';
            if "@id" in rangeObject:
                name = rangeObject["@id"].split("/")[-1].strip()
                identifier = rangeObject["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        rangeObject["belongsTo"] = [belongsTo]
        rangeObject["order"] = index+1
        subRange = updateRange(user, identifier, name, rangeObject, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subRange["status"] >= 400:  
            return {"status": "fail", "errors": subRange}
        else:
            subRangesIDs.append(subRange["data"]["@id"])
    return {"status": "success", "subRangesIDs": subRangesIDs}


def range_update_sub_members(user, members, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subCanvases = []
    subRanges = []
    subCanvasesIDs = []
    subRangesIDs = []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongsTo]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}
        else:
            if member["@type"] not in ["sc:Canvas", "sc:Range"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Canvas or sc:Range.'}}
        if member["@type"]=="sc:Canvas":
            subCanvases.append(member)
        else:
            subRanges.append(member)
    result = range_update_sub_canvases(user, subCanvases, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"] == "fail":  
        return result 
    else:
        subCanvasesIDs = result["subCanvasesIDs"]
    result =  range_update_sub_ranges(user, subRanges, belongsTo, queue, activity, bulkCreateActions, fromPostCreate)
    if result["status"] == "fail":  
        return result
    else:
        subRangesIDs = result["subRangesIDs"]
    return {"status": "success", "subCanvasesIDs": subCanvasesIDs, "subRangesIDs": subRangesIDs}


def canvas_create_sub_annotations(user, annotations, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationsIDs = []
    for index, annotation in enumerate(annotations):
        annotation["belongsTo"] = [belongsTo]
        annotation["order"] = index+1
        annotation["on"] = belongsTo
        subAnnotation = createAnnotation(user, None, annotation, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotation["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotation} 
        else:
            subAnnotationsIDs.append(subAnnotation["data"]["@id"])
    return {"status": "success", "subAnnotationsIDs": subAnnotationsIDs}


def canvas_create_sub_annotationLists(user, annotationLists, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationListsIDs = []
    for index, annotationList in enumerate(annotationLists):
        annotationList["belongsTo"] = [belongsTo]
        annotationList["order"] = index+1
        subAnnotationList = createAnnotationList(user, None, annotationList, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotationList["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotationList} 
        else:
            subAnnotationListsIDs.append(subAnnotationList["data"]["@id"])
    return {"status": "success", "subAnnotationListsIDs": subAnnotationListsIDs}


def canvas_update_sub_annotations(user, annotations, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationsIDs = []
    for index, annotation in enumerate(annotations):
        try:
            name = identifier = 'Unknown';
            if "@id" in annotation:
                name = annotation["@id"].split("/")[-1].strip()
                identifier = annotation["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        annotation["belongsTo"] = [belongsTo]
        annotation["order"] = index+1
        annotation["on"] = belongsTo
        subAnnotation = updateAnnotation(user, identifier, name, annotation, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotation["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotation} 
        else:
            subAnnotationsIDs.append(subAnnotation["data"]["@id"])
    return {"status": "success", "subAnnotationsIDs": subAnnotationsIDs}


def canvas_update_sub_annotationLists(user, annotationLists, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationListsIDs = []
    for index, annotationList in enumerate(annotationLists):
        try:
            name = identifier = 'Unknown';
            if "@id" in annotationList:
                name = annotationList["@id"].split("/")[-1].strip()
                identifier = annotationList["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        annotationList["belongsTo"] = [belongsTo]
        annotationList["order"] = index+1
        subAnnotationList = updateAnnotationList(user, identifier, name, annotationList, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotationList["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotationList} 
        else:
            subAnnotationListsIDs.append(subAnnotationList["data"]["@id"])
    return {"status": "success", "subAnnotationListsIDs": subAnnotationListsIDs}


def annotation_list_create_sub_annotations(user, annotations, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationsIDs = []
    for index, annotation in enumerate(annotations):
        annotation["belongsTo"] = [belongsTo]
        annotation["order"] = index+1
        if "height" not in annotation:
            annotation["height"] = 500
        if "width" not in annotation:
            annotation["width"] = 500
        subAnnotation = createAnnotation(user, None, annotation, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotation["status"] >= 400: 
            return {"status": "fail", "errors": subAnnotation} 
        else:
            subAnnotationsIDs.append(subAnnotation["data"]["@id"])
    return {"status": "success", "subAnnotationsIDs": subAnnotationsIDs}


def annotation_list_update_sub_annotations(user, annotations, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationsIDs = []
    for index, annotation in enumerate(annotations):
        try:
            name = identifier = 'Unknown';
            if "@id" in annotation:
                name = annotation["@id"].split("/")[-1].strip()
                identifier = annotation["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        annotation["belongsTo"] = [belongsTo]
        annotation["order"] = index+1
        if "height" not in annotation:
            annotation["height"] = 500
        if "width" not in annotation:
            annotation["width"] = 500
        subAnnotation = updateAnnotation(user, identifier, name, annotation, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotation["status"] >= 400: 
            return {"status": "fail", "errors": subAnnotation} 
        else:
            subAnnotationsIDs.append(subAnnotation["data"]["@id"])
    return {"status": "success", "subAnnotationsIDs": subAnnotationsIDs}


def layer_create_sub_annotationLists(user, annotationLists, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationListsIDs = []
    for index, annotationListID in enumerate(annotationLists):
        annotationList = {"@id": annotationListID}
        annotationList["belongsTo"] = [belongsTo]
        annotationList["order"] = index+1
        if "height" not in annotationList:
            annotationList["height"] = 500
        if "width" not in annotationList:
            annotationList["width"] = 500
        subAnnotationList = createAnnotationList(user, None, annotationList, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotationList["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotationList} 
        else:
            subAnnotationListsIDs.append(subAnnotationList["data"]["@id"])
    return {"status": "success", "subAnnotationListsIDs": subAnnotationListsIDs}


def layer_update_sub_annotationLists(user, annotationLists, belongsTo, queue, activity, bulkCreateActions, fromPostCreate):
    subAnnotationListsIDs = []
    for index, annotationListID in enumerate(annotationLists):
        annotationList = {"@id": annotationListID}
        try:
            name = identifier = 'Unknown';
            if "@id" in annotationList:
                name = annotationList["@id"].split("/")[-1].strip()
                identifier = annotationList["@id"].split("/")[-3].strip()
        except Exception as e: # pragma: no cover
            return {"status": "fail", "errors": e.message}
        annotationList["belongsTo"] = [belongsTo]
        annotationList["order"] = index+1
        subAnnotationList = updateAnnotationList(user, identifier, name, annotationList, True, queue, activity, bulkCreateActions, fromPostCreate)
        if subAnnotationList["status"] >= 400:  
            return {"status": "fail", "errors": subAnnotationList} 
        else:
            subAnnotationListsIDs.append(subAnnotationList["data"]["@id"])
    return {"status": "success", "subAnnotationListsIDs": subAnnotationListsIDs}

# --------------------------------- End Helper Functions ----------------------------------------------- #



# Update duplicate entires after Bulk insert
def postBulkInsertUpdate(toUpdate, user, activity, queue):
    if toUpdate["Collection"]:
        for obj in toUpdate["Collection"]:
            updateCollection(user, obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Manifest"]:
        for obj in toUpdate["Manifest"]:
            updateManifest(user, obj["identifier"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Sequence"]:
        for obj in toUpdate["Sequence"]:
            updateSequence(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Range"]:
        for obj in toUpdate["Range"]:
            updateRange(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Canvas"]:
        for obj in toUpdate["Canvas"]:
            updateCanvas(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Annotation"]:
        for obj in toUpdate["Annotation"]:
            updateAnnotation(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["AnnotationList"]:
        for obj in toUpdate["AnnotationList"]:
            updateAnnotationList(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)

    if toUpdate["Layer"]:
        for obj in toUpdate["Layer"]:
            updateLayer(user, obj["identifier"], obj["name"], obj["data"], True, queue, activity, None, True)
