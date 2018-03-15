import uuid
from django.conf import settings
from rest_framework import status
from celery.decorators import task
from iiif_api_services.serializers.CollectionSerializer import *
from iiif_api_services.serializers.ManifestSerializer import *
from iiif_api_services.serializers.SequenceSerializer import *
from iiif_api_services.serializers.RangeSerializer import *
from iiif_api_services.serializers.CanvasSerializer import *
from iiif_api_services.serializers.AnnotationSerializer import *
from iiif_api_services.serializers.AnnotationListSerializer import *
from iiif_api_services.serializers.LayerSerializer import *
from iiif_api_services.helpers.ProcessResult import process_result
from iiif_api_services.helpers.BulkOperations import bulk_create, bulk_delete, bulk_update_permissions


# Bulk update user permissions for Collections & Manifests recursively
# PUT /auth/admin/updatePermission
def update_permission(request_object):
    if "collections" not in request_object: request_object["collections"] = []
    if "manifests" not in request_object: request_object["manifests"] = []
    bulk_updates = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    try:
        for at_id in request_object["collections"]: # Get every children of each Collection
            collection = Collection.objects.get(ATid=at_id)
            __merge_two_dictionaries(bulk_updates, __get_children_ids_for_bulk_action(collection, __get_collection_children))
            bulk_updates["Collection"].append(collection.ATid)
        for at_id in request_object["manifests"]: # Get every children of each Manifest
            manifest = Manifest.objects.get(ATid=at_id)
            if manifest.ATid not in bulk_updates["Manifest"]:
                __merge_two_dictionaries(bulk_updates, __get_children_ids_for_bulk_action(manifest, __get_manifest_children))
                bulk_updates["Manifest"].append(manifest.ATid)
    except Collection.DoesNotExist:
        return {'status': status.HTTP_404_NOT_FOUND, 'data': {'error': "Collection with @id '{0}' does not exist.".format(at_id)}}
    except Manifest.DoesNotExist:
        return {'status': status.HTTP_404_NOT_FOUND, 'data': {'error': "Manifest with @id '{0}' does not exist.".format(at_id)}}
    except Exception as e: # pragma: no cover
        raise e
    if request_object["action"] == 'ADD':
        bulk_update_permissions(bulk_updates, request_object["username"], '$addToSet')
    else: # action is 'REMOVE'
        bulk_update_permissions(bulk_updates, request_object["username"], '$pull')
    return {'status': status.HTTP_200_OK, 'data': {'message': "Successfully updated user permissions for given objects."}}



# --------------------------------- Begin GET Methods ----------------------------------------------- #

def view_collection(collection, root=False):
    if not root:
        required_objects = __get_collection_children(collection.to_mongo()) # Grab only the necessary children to view this object.
    else: # Grab all sub-collections and sub-manifests that belongs to nothing.
        required_objects = {}
        required_objects["Collection"] = [__clean_object(item.to_mongo()) for item in Collection.objects(belongsTo=[], hidden=False).order_by('order')]
        required_objects["Manifest"] = [__clean_object(item.to_mongo()) for item in Manifest.objects(belongsTo=[], hidden=False).order_by('order')]
    collection_object = __clean_object(collection.to_mongo()) # Build the required Collection
    collection_object['collections'] = []
    for sub_collection in required_objects["Collection"]:
        collection_object['collections'].append(__get_embedded_object(sub_collection))
    collection_object['manifests'] = []
    for sub_manifest in required_objects["Manifest"]:
        collection_object['manifests'].append(__get_embedded_object(sub_manifest))
    collection_object['total'] = len(collection_object['collections'])+len(collection_object['manifests']) 
    collection_object['ATcontext'] = settings.IIIF_CONTEXT
    return collection_object


def view_manifest(manifest):
    required_objects = __get_manifest_children(manifest.to_mongo()) # Grab only the necessary children to view this object.
    manifest_object = __clean_object(manifest.to_mongo()) # Build the required Manifest
    manifest_object["sequences"] = [{} for i in range(len(required_objects["Sequence"]))]
    for sequence_index, sequence in enumerate(required_objects["Sequence"]):
        if sequence_index == 0:
            manifest_object["sequences"][sequence_index] = sequence
        else:
            manifest_object["sequences"][sequence_index] = __get_embedded_object(sequence)
        sub_canvases = [item for item in required_objects["Canvas"] if sequence["ATid"] in item["belongsTo"]]
        manifest_object["sequences"][sequence_index]["canvases"] = [{} for i in range(len(sub_canvases))]
        for canvas_index, canvas in enumerate(sub_canvases):
            manifest_object["sequences"][sequence_index]["canvases"][canvas_index] = canvas
            manifest_object["sequences"][sequence_index]["canvases"][canvas_index]["images"] = [item for item in required_objects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
            sub_annotation_lists = [item for item in required_objects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
            manifest_object["sequences"][sequence_index]["canvases"][canvas_index]["otherContent"] = [{} for i in range(len(sub_annotation_lists))]
            for annotation_list_index, annotation_list in enumerate(sub_annotation_lists):
                manifest_object["sequences"][sequence_index]["canvases"][canvas_index]["otherContent"][annotation_list_index] = annotation_list
    sub_ranges = [item for item in required_objects["Range"] if manifest["ATid"] in item["belongsTo"]]    
    manifest_object["structures"] = [{} for i in range(len(sub_ranges))]
    for range_index, range_object in enumerate(sub_ranges):
        manifest_object["structures"][range_index] = __clean_object(range_object)
        sub_canvases = [item for item in required_objects["Canvas"] if range_object["ATid"] in item["belongsTo"]]
        sub_ranges = [item for item in required_objects["Range"] if range_object["ATid"] in item["belongsTo"]]
        manifest_object["structures"][range_index]["members"] = [{} for i in range(len(sub_canvases) + len(sub_ranges))]
        member_count = 0
        for member in sub_canvases:
            manifest_object["structures"][range_index]["members"][member_count] = __get_embedded_object(member)
            member_count += 1
        for member in sub_ranges:
            manifest_object["structures"][range_index]["members"][member_count] = __get_embedded_object(member)
            member_count += 1
    manifest_object["ATcontext"] = settings.IIIF_CONTEXT
    return manifest_object


def view_sequence(sequence):
    required_objects = __get_sequence_children(sequence.to_mongo()) # Grab only the necessary children to view this object.
    sequence_object = __clean_object(sequence.to_mongo()) # Build the required Sequence
    sub_canvases = [item for item in required_objects["Canvas"] if sequence["ATid"] in item["belongsTo"]]
    sequence_object["canvases"] = [{} for i in range(len(sub_canvases))]
    for canvas_index, canvas in enumerate(sub_canvases):
        sequence_object["canvases"][canvas_index] = canvas
        sequence_object["canvases"][canvas_index]["images"] = [item for item in required_objects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
        sub_annotation_lists = [item for item in required_objects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
        sequence_object["canvases"][canvas_index]["otherContent"] = [{} for i in range(len(sub_annotation_lists))]
        for annotation_list_index, annotation_list in enumerate(sub_annotation_lists):
            sequence_object["canvases"][canvas_index]["otherContent"][annotation_list_index] = annotation_list
    sequence_object["ATcontext"] = settings.IIIF_CONTEXT
    return sequence_object


def view_range(range):
    required_objects = __get_range_children(range.to_mongo()) # Grab only the necessary children to view this object.
    range_object = __clean_object(range.to_mongo()) # Build the required Range
    range_object['members'] = []
    for sub_canvas in required_objects["Canvas"]:
        range_object['members'].append(__get_embedded_object(sub_canvas))
    for sub_range in required_objects["Range"]:
        range_object['members'].append(__get_embedded_object(sub_range))
    range_object['ATcontext'] = settings.IIIF_CONTEXT
    return range_object


def view_canvas(canvas):
    required_objects = __get_canvas_children(canvas.to_mongo()) # Grab only the necessary children to view this object.
    canvas_object = __clean_object(canvas.to_mongo()) # Build the required Canvas
    canvas_object["images"] = [item for item in required_objects["Annotation"] if canvas["ATid"] in item["belongsTo"]]
    sub_annotation_lists = [item for item in required_objects["AnnotationList"] if canvas["ATid"] in item["belongsTo"]]
    canvas_object["otherContent"] = [{} for i in range(len(sub_annotation_lists))]
    for annotation_list_index, annotation_list in enumerate(sub_annotation_lists):
        canvas_object["otherContent"][annotation_list_index] = annotation_list
    canvas_object["ATcontext"] = settings.IIIF_CONTEXT
    return canvas_object


def view_annotation(annotation):
    annotation_object = __clean_object(annotation.to_mongo()) # Build the required Annotation
    annotation_object['ATcontext'] = settings.IIIF_CONTEXT
    return annotation_object


def view_annotation_list(annotation_list):
    required_objects = __get_annotation_list_children(annotation_list.to_mongo()) # Grab only the necessary children to view this object.
    annotation_list_object = __clean_object(annotation_list.to_mongo()) # Build the required AnnotationList
    annotation_list_object['resources'] = []
    for annotation_index, sub_annotation in enumerate(required_objects["Annotation"]):
        annotation_list_object['resources'].append(__get_embedded_object(sub_annotation))
    annotation_list_object['ATcontext'] = settings.IIIF_CONTEXT
    return annotation_list_object


def view_layer(layer):
    required_objects = __get_layer_children(layer.to_mongo()) # Grab only the necessary children to view this object.
    layer_object = __clean_object(layer.to_mongo()) # Build the required Layer
    layer_object['otherContent'] = []
    for sub_annotation_list in required_objects["AnnotationList"]:
        layer_object['otherContent'].append(__get_embedded_object(sub_annotation_list))
    layer_object['ATcontext'] = settings.IIIF_CONTEXT
    return layer_object


# --------------------------------- End GET Methods ----------------------------------------------- #





# --------------------------------- Begin POST Methods ----------------------------------------------- #
@task(name="create_collection")
def create_collection(user, collection_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in collection_data: # {scheme}://{host}/{prefix}/collections/{name}
            collection_data["name"] = collection_data.pop("@id").split("/")[-1].strip()
        else: # Generate a unique random UUID for the name
            collection_data["name"] = 'collection_'+str(uuid.uuid4())
        if collection_data["name"]==settings.TOP_LEVEL_COLLECTION_NAME:
            error_message = "Collection name cannot be: {0}.".format(settings.TOP_LEVEL_COLLECTION_NAME)
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': error_message, "object": collection_data}}
            return process_result(response, queue_activity)
        collection_data["ATid"] = "{0}/collections/{1}".format(settings.IIIF_BASE_URL, collection_data["name"])
        if not user["is_superuser"]: collection_data["ownedBy"] = [user["username"]] # Add the current user as an owner for this object
        # check for any nested structures
        children = []
        sub_collections = sub_manifests = sub_members = False
        if 'collections' in collection_data: sub_collections = collection_data["collections"]
        if 'manifests' in collection_data: sub_manifests = collection_data["manifests"]
        if 'members' in collection_data: sub_members = collection_data["members"]
        collection_serializer = CollectionSerializer(data=collection_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and the object with name already exists,
            # ignore creating the object. Instead, update with given data.
            try:
                Collection.objects.get(name=collection_data["name"])
                item_exists = True
            except Collection.DoesNotExist: pass
        if not item_exists:
            if collection_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_collections:
                    result = __create_or_update_sub_children(user, sub_collections, collection_data["ATid"], queue_activity, bulk_create_actions, create_collection, "sub_collections_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_collections_ids"]
                if sub_manifests:
                    result = __create_or_update_sub_children(user, sub_manifests, collection_data["ATid"], queue_activity, bulk_create_actions, create_manifest, "sub_manifests_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_manifests_ids"]
                if sub_members:
                    result = __collection_create_or_update_sub_members(user, sub_members, collection_data["ATid"], queue_activity, bulk_create_actions, create_collection, create_manifest)
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_collections_ids"]
                        children += result["sub_manifests_ids"]
                response_data = collection_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Collection"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": collection_serializer.errors, "object": collection_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: collection_data.pop("ownedBy")
            return update_collection(user, collection_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_manifest")
def create_manifest(user, manifest_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in manifest_data: # {scheme}://{host}/{prefix}/{identifier}/manifest
            manifest_data["identifier"] = manifest_data.pop("@id").split("/")[-2].strip()
        manifest_data["ATid"] = settings.IIIF_BASE_URL+'/'+manifest_data["identifier"]+'/manifest'
        if not user["is_superuser"]: manifest_data["ownedBy"] = [user["username"]] # Add the current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_sequences = sub_ranges = False
        if 'sequences' in manifest_data: sub_sequences = manifest_data["sequences"]
        if 'structures' in manifest_data: sub_ranges = manifest_data["structures"]
        manifest_serializer = ManifestSerializer(data=manifest_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Manifest.objects.get(identifier=manifest_data["identifier"])
                item_exists = True
            except Manifest.DoesNotExist: pass
        if not item_exists:
            if manifest_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_sequences:
                    result = __create_or_update_sub_children(user, sub_sequences, manifest_data["ATid"], queue_activity, bulk_create_actions, create_sequence, "sub_sequences_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_sequences_ids"]
                if sub_ranges:
                    result = __create_or_update_sub_children(user, sub_ranges, manifest_data["ATid"], queue_activity, bulk_create_actions, create_range, "sub_ranges_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_ranges_ids"]
                response_data = manifest_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Manifest"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": manifest_serializer.errors, "object": manifest_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: manifest_data.pop("ownedBy")
            return update_manifest(user, manifest_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_sequence")
def create_sequence(user, sequence_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in sequence_data: # {scheme}://{host}/{prefix}/{identifier}/sequence/{name}
            sequence_data["ATid"] = sequence_data.pop("@id")
        else: # Generate a unique random UUID for the name
            sequence_data["ATid"] = "{0}/identifier/sequence/sequence_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        sequence_data["name"] = sequence_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in sequence_data: # belongsTo = {scheme}://{host}/{prefix}/{identifier}/manifest
            sequence_data["identifier"] = sequence_data["belongsTo"][0].split("/")[-2].strip()
        else:
            sequence_data["identifier"] = sequence_data["ATid"].split("/")[-3].strip()
        sequence_data["ATid"] = "{0}/{1}/sequence/{2}".format(settings.IIIF_BASE_URL, sequence_data["identifier"], sequence_data["name"])
        if not user["is_superuser"]: sequence_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_canvases = False
        if 'canvases' in sequence_data: sub_canvases = sequence_data["canvases"]
        sequence_serializer = SequenceSerializer(data=sequence_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Sequence.objects.get(identifier=sequence_data["identifier"], name=sequence_data["name"])
                item_exists = True
            except Sequence.DoesNotExist: pass
        if not item_exists:
            if sequence_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_canvases:
                    result = __create_or_update_sub_children(user, sub_canvases, sequence_data["ATid"], queue_activity, bulk_create_actions, create_canvas, "sub_canvases_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_canvases_ids"]
                response_data = sequence_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Sequence"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}   
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": sequence_serializer.errors, "object": sequence_data}}
                return process_result(response, queue_activity)
        else:  # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: sequence_data.pop("ownedBy")
            return update_sequence(user, sequence_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_range")
def create_range(user, range_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in range_data: # {scheme}://{host}/{prefix}/{identifier}/range/{name}
            range_data["ATid"] = range_data.pop("@id")  
        else: # Generate a unique random UUID for the name
            range_data["ATid"] = "{0}/identifier/range/range_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        range_data["name"] = range_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in range_data: # Might belong to either Manifest or Range
            if 'manifest' in range_data["belongsTo"][0]: # belongsTo = {scheme}://{host}/{prefix}/{identifier}/manifest
                range_data["identifier"] = range_data["belongsTo"][0].split("/")[-2].strip()  
            else: # belongsTo = {scheme}://{host}/{prefix}/{identifier}/range/{name}
                range_data["identifier"] = range_data["belongsTo"][0].split("/")[-3].strip()
        else:
            range_data["identifier"] = range_data["ATid"].split("/")[-3].strip()
        range_data["ATid"] = "{0}/{1}/range/{2}".format(settings.IIIF_BASE_URL, range_data["identifier"], range_data["name"])
        if not user["is_superuser"]: range_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_canvases = sub_ranges = sub_members = False
        if 'canvases' in range_data: sub_canvases = range_data["canvases"]
        if 'ranges' in range_data: sub_ranges = range_data["ranges"]
        if 'members' in range_data: sub_members = range_data["members"]
        range_serializer = RangeSerializer(data=range_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Range.objects.get(identifier=range_data["identifier"], name=range_data["name"])
                item_exists = True
            except Range.DoesNotExist:
                pass
        if not item_exists:
            if range_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_canvases:
                    result = __create_or_update_sub_children(user, sub_canvases, range_data["ATid"], queue_activity, bulk_create_actions, create_canvas, "sub_canvases_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_canvases_ids"]
                if sub_ranges:
                    result = __create_or_update_sub_children(user, sub_ranges, range_data["ATid"], queue_activity, bulk_create_actions, create_range, "sub_ranges_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_ranges_ids"]
                if sub_members:
                    result = __range_create_or_update_sub_members(user, sub_members, range_data["ATid"], queue_activity, bulk_create_actions, create_range, create_canvas)
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_canvases_ids"]
                        children += result["sub_ranges_ids"]
                response_data = range_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Range"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": range_serializer.errors, "object": range_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: range_data.pop("ownedBy")
            return update_range(user, range_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_canvas")
def create_canvas(user, canvas_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in canvas_data: # {scheme}://{host}/{prefix}/{identifier}/canvas/{name}
            canvas_data["ATid"] = canvas_data.pop("@id") 
        else: # Generate a unique random UUID for the name
            canvas_data["ATid"] = "{0}/identifier/canvas/canvas_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        canvas_data["name"] = canvas_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in canvas_data: # {scheme}://{host}/{prefix}/{identifier}/sequence_or_range/{name}
            canvas_data["identifier"] = canvas_data["belongsTo"][0].split("/")[-3].strip()  
        else:
            canvas_data["identifier"] = canvas_data["ATid"].split("/")[-3].strip()
        canvas_data["ATid"] = "{0}/{1}/canvas/{2}".format(settings.IIIF_BASE_URL, canvas_data["identifier"], canvas_data["name"])
        if not user["is_superuser"]: canvas_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_annotations = sub_annotation_lists = False
        if 'images' in canvas_data: sub_annotations = canvas_data["images"]
        if 'otherContent' in canvas_data: sub_annotation_lists = canvas_data["otherContent"]
        canvas_serializer = CanvasSerializer(data=canvas_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Canvas.objects.get(identifier=canvas_data["identifier"], name=canvas_data["name"])
                item_exists = True
            except Canvas.DoesNotExist:
                pass
        if not item_exists:
            if canvas_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_annotations:
                    result = __create_or_update_sub_children(user, sub_annotations, canvas_data["ATid"], queue_activity, bulk_create_actions, create_annotation, "sub_annotations_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_annotations_ids"]
                if sub_annotation_lists:
                    result = __create_or_update_sub_children(user, sub_annotation_lists, canvas_data["ATid"], queue_activity, bulk_create_actions, create_annotation_list, "sub_annotation_lists_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_annotation_lists_ids"]
                response_data = canvas_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Canvas"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": canvas_serializer.errors, "object": canvas_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: canvas_data.pop("ownedBy")
            return update_canvas(user, canvas_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_annotation")
def create_annotation(user, annotation_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in annotation_data: # {scheme}://{host}/{prefix}/{identifier}/annotation/{name}
            annotation_data["ATid"] = annotation_data.pop("@id")  
        else: # Generate a unique random UUID for the name
            annotation_data["ATid"] = "{0}/identifier/annotation/annotation_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        annotation_data["name"] = annotation_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in annotation_data:
            annotation_data["identifier"] = annotation_data["belongsTo"][0].split("/")[-3].strip()  
        else:
            annotation_data["identifier"] = annotation_data["ATid"].split("/")[-3].strip()
        annotation_data["ATid"] = "{0}/{1}/annotation/{2}".format(settings.IIIF_BASE_URL, annotation_data["identifier"], annotation_data["name"])
        if not user["is_superuser"]: annotation_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        annotation_serializer = AnnotationSerializer(data=annotation_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Annotation.objects.get(identifier=annotation_data["identifier"], name=annotation_data["name"])
                item_exists = True
            except Annotation.DoesNotExist: pass
        if not item_exists:
            if annotation_serializer.is_valid(): # Validations for object passed.
                response_data = annotation_serializer.validated_data
                bulk_create_actions["Annotation"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotation_serializer.errors, "object": annotation_data}}
                return process_result(response, queue_activity)
        else:  # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: annotation_data.pop("ownedBy")
            return update_annotation(user, annotation_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_annotation_list")
def create_annotation_list(user, annotation_list_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in annotation_list_data: # {scheme}://{host}/{prefix}/{identifier}/list/{name}
            annotation_list_data["ATid"] = annotation_list_data.pop("@id")  
        else: # Generate a unique random UUID for the name
            annotation_list_data["ATid"] = "{0}/identifier/list/list_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        annotation_list_data["name"] = annotation_list_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in annotation_list_data:
            annotation_list_data["identifier"] = annotation_list_data["belongsTo"][0].split("/")[-3].strip()  
        else:
            annotation_list_data["identifier"] = annotation_list_data["ATid"].split("/")[-3].strip()
        annotation_list_data["ATid"] = "{0}/{1}/list/{2}".format(settings.IIIF_BASE_URL, annotation_list_data["identifier"], annotation_list_data["name"])
        if not user["is_superuser"]: annotation_list_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_annotations = False
        if 'resources' in annotation_list_data: sub_annotations = annotation_list_data["resources"]
        annotation_list_serializer = AnnotationListSerializer(data=annotation_list_data)
        item_exists = False
        if embedded_creation:
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                AnnotationList.objects.get(identifier=annotation_list_data["identifier"], name=annotation_list_data["name"])
                item_exists = True
            except AnnotationList.DoesNotExist: pass
        if not item_exists:
            if annotation_list_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_annotations:
                    result = __create_or_update_sub_children(user, sub_annotations, annotation_list_data["ATid"], queue_activity, bulk_create_actions, create_annotation, "sub_annotations_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_annotations_ids"]
                response_data = annotation_list_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["AnnotationList"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else:
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotation_list_serializer.errors, "object": annotation_list_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: annotation_list_data.pop("ownedBy")
            return update_annotation_list(user, annotation_list_data, True, queue_activity, bulk_create_actions)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="create_layer")
def create_layer(user, layer_data, embedded_creation, queue_activity, bulk_create_actions):
    try:
        if "@id" in layer_data: # {scheme}://{host}/{prefix}/{identifier}/layer/{name}
            layer_data["ATid"] = layer_data.pop("@id")
        else: # Generate a unique random UUID for the name
            layer_data["ATid"] = "{0}/identifier/layer/layer_{1}".format(settings.IIIF_BASE_URL, uuid.uuid4())
        layer_data["name"] = layer_data["ATid"].split("/")[-1].strip()
        if 'belongsTo' in layer_data: # pragma: no cover
            layer_data["identifier"] = layer_data["belongsTo"][0].split("/")[-3].strip()
        else:
            layer_data["identifier"] = layer_data["ATid"].split("/")[-3].strip()
        layer_data["ATid"] = "{0}/{1}/layer/{2}".format(settings.IIIF_BASE_URL, layer_data["identifier"], layer_data["name"])
        if not user["is_superuser"]: layer_data["ownedBy"] = [user["username"]] # Add current user as an owner for this object
        # Check for any nested structures
        children = []
        sub_annotation_lists = False
        if 'otherContent' in layer_data: sub_annotation_lists = layer_data["otherContent"]
        layer_serializer = LayerSerializer(data=layer_data)
        item_exists = False
        if embedded_creation: # pragma: no cover
            # If this object is being created from a parent object and this object already exists,
            # ignore creating this object. Instead, update with given data.
            try:
                Layer.objects.get(identifier=layer_data["identifier"], name=layer_data["name"])
                item_exists = True
            except Layer.DoesNotExist: pass
        if not item_exists:
            if layer_serializer.is_valid(): # Validations for object passed. Nested validations pending.
                if sub_annotation_lists:
                    result = __create_or_update_sub_children(user, sub_annotation_lists, layer_data["ATid"], queue_activity, bulk_create_actions, create_annotation_list, "sub_annotation_lists_ids")
                    if result["status"]=="fail": # Validation error occurred on children creation.
                        response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                        return process_result(response, queue_activity)
                    else:
                        children += result["sub_annotation_lists_ids"]
                response_data = layer_serializer.validated_data
                response_data["children"] = list(set(children))
                bulk_create_actions["Layer"].append(response_data) # Add this object to the bulk operations list.
                response = {"status": status.HTTP_201_CREATED, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
                if not embedded_creation:
                    post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                    return process_result(response, queue_activity) # Process the queue_activity and return final response.
                else: # pragma: no cover
                    return response # Return response for parent Object
            else: # Validation error occurred for this object. Process the queue_activity and return final response.
                response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": layer_serializer.errors, "object": layer_data}}
                return process_result(response, queue_activity)
        else: # Ignore creating this object if it already exists. Instead update the existing object.
            if not user["is_superuser"]: layer_data.pop("ownedBy") # pragma: no cover
            return update_layer(user, layer_data, True, queue_activity, bulk_create_actions) # pragma: no cover
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)

# --------------------------------- End POST Methods ----------------------------------------------- #



# --------------------------------- Begin PUT Methods ----------------------------------------------- #

@task(name="update_collection")
def update_collection(user, collection_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "name" not in collection_data: collection_data["name"] = "Unknown"
        name = collection_data["name"]
        if name==settings.TOP_LEVEL_COLLECTION_NAME:
            response = {"status": status.HTTP_412_PRECONDITION_FAILED, "data": {'error': "Top level Collection cannot be edited.", "object": collection_data}}
            return process_result(response, queue_activity)
        sub_collections = sub_manifests = sub_members = False
        collection = Collection.objects.get(name=name)          
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, collection)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Check for any nested structures
        if 'collections' in collection_data: sub_collections = collection_data["collections"]
        if 'manifests' in collection_data: sub_manifests = collection_data["manifests"]
        if 'members' in collection_data: sub_members = collection_data["members"]
        if "@id" in collection_data: # {scheme}://{host}/{prefix}/collections/{name}
            collection_data["name"] = collection_data.pop("@id").split("/")[-1].strip()
        collection_data["ATid"] = "{0}/collections/{1}".format(settings.IIIF_BASE_URL, collection_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(collection_data, collection)
        collection_serializer = CollectionSerializer(collection, data=collection_data, partial=True)
        if collection_serializer.is_valid():
            # Update all Collections & Manifests that 'belongsTo' this Collection if @id(name) has been changed
            if collection_data["name"]!=name:
                for belongs_to_collection in Collection.objects(belongsTo__contains=collection.ATid):
                    belongs_to_collection.belongsTo.remove(collection.ATid)
                    belongs_to_collection.belongsTo.append(collection_data["ATid"])
                    belongs_to_collection.save()
                for belongs_to_manifest in Manifest.objects(belongsTo__contains=collection.ATid):
                    belongs_to_manifest.belongsTo.remove(collection.ATid)
                    belongs_to_manifest.belongsTo.append(collection_data["ATid"])
                    belongs_to_manifest.save()
                for parent_collection in Collection.objects(children__contains=collection.ATid):
                    parent_collection.children.remove(collection.ATid)
                    parent_collection.children.append(collection_data["ATid"])
                    parent_collection.save()
            # Update all sub_collections, submanifests and sub_members
            children = []
            if sub_collections:
                result = __create_or_update_sub_children(user, sub_collections, collection_data["ATid"], queue_activity, bulk_create_actions, update_collection, "sub_collections_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_collections_ids"] # Update the children list
            if sub_manifests:
                result = __create_or_update_sub_children(user, sub_manifests, collection_data["ATid"], queue_activity, bulk_create_actions, update_manifest, "sub_manifests_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_manifests_ids"] # Update the children list
            if sub_members:
                result = __collection_create_or_update_sub_members(user, sub_members, collection_data["ATid"], queue_activity, bulk_create_actions, update_collection, update_manifest)
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_collections_ids"] # Update the children list
                    children += result["sub_manifests_ids"] # Update the children list
            collection_serializer.save(children=list(set(collection.children+children))) 
            response_data = collection_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity) # Process bulk operations
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": collection_serializer.errors, "object": collection_data}}
            return process_result(response, queue_activity)
    except Collection.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_collection(user, collection_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Collection with name '{0}' does not exist.".format(name)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_manifest")
def update_manifest(user, manifest_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in manifest_data: manifest_data["identifier"] = "Unknown"
        identifier = manifest_data["identifier"]
        manifest = Manifest.objects.get(identifier=identifier)
        sub_sequences = sub_ranges = False
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, manifest)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Check for any nested structures
        if 'sequences' in manifest_data: sub_sequences = manifest_data["sequences"]
        if 'structures' in manifest_data: sub_ranges = manifest_data["structures"]
        if "@id" in manifest_data:
            manifest_data["identifier"] = manifest_data.pop("@id").split("/")[-2].strip()
        manifest_data["ATid"] = "{0}/{1}/manifest".format(settings.IIIF_BASE_URL, manifest_data["identifier"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(manifest_data, manifest)
        manifest_serializer = ManifestSerializer(manifest, data=manifest_data, partial=True)
        if manifest_serializer.is_valid():
            # Update all Sequences & Ranges that 'belongsTo' this Manifest if @id(identifier) has been changed
            if manifest_data["identifier"]!=identifier:
                for belongs_to_sequence in Sequence.objects(belongsTo__contains=manifest.ATid):
                    belongs_to_sequence.belongsTo.remove(manifest.ATid)
                    belongs_to_sequence.belongsTo.append(manifest_data["ATid"])
                    belongs_to_sequence.save()
                for belongs_to_range in Range.objects(belongsTo__contains=manifest.ATid):
                    belongs_to_range.belongsTo.remove(manifest.ATid)
                    belongs_to_range.belongsTo.append(manifest_data["ATid"])
                    belongs_to_range.save()
                for parent_collection in Collection.objects(children__contains=manifest.ATid):
                    parent_collection.children.remove(manifest.ATid)
                    parent_collection.children.append(manifest_data["ATid"])
                    parent_collection.save()
            # Update all sub_sequences and sub_ranges
            children = []
            if sub_sequences:
                result = __create_or_update_sub_children(user, sub_sequences, manifest_data["ATid"], queue_activity, bulk_create_actions, update_sequence, "sub_sequences_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_sequences_ids"] # Update the children list
            if sub_ranges:
                result = __create_or_update_sub_children(user, sub_ranges, manifest_data["ATid"], queue_activity, bulk_create_actions, update_range, "sub_ranges_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_ranges_ids"] # Update the children list
            manifest_serializer.save(children=list(set(manifest.children+children)))
            response_data = manifest_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": manifest_serializer.errors, "object": manifest_data}}
            return process_result(response, queue_activity)
    except Manifest.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_manifest(user, manifest_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "'{0}' does not have a Manifest.".format(identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_sequence")
def update_sequence(user, sequence_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in sequence_data: sequence_data['identifier'] = "Unknown"
        if "name" not in sequence_data: sequence_data['name'] = "Unknown"
        identifier, name = sequence_data['identifier'], sequence_data['name']
        sequence = Sequence.objects.get(identifier=identifier, name=name)
        sub_canvases = False
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, sequence)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        if 'canvases' in sequence_data: sub_canvases = sequence_data["canvases"]
        if "@id" in sequence_data:
            sequence_data["ATid"] = sequence_data.pop("@id")
            sequence_data["name"] = sequence_data["ATid"].split("/")[-1].strip()
            sequence_data["identifier"] = sequence_data["ATid"].split("/")[-3].strip()
        sequence_data["ATid"] = "{0}/{1}/sequence/{2}".format(settings.IIIF_BASE_URL, sequence_data["identifier"], sequence_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(sequence_data, sequence)
        sequence_serializer = SequenceSerializer(sequence, data=sequence_data, partial=True)
        if sequence_serializer.is_valid():
            # Update all Canvaes that 'belongsTo' Sequence if @id(identifier or name) has been changed
            if sequence_data["identifier"]!=identifier or sequence_data["name"]!=name:
                for belongs_to_canvas in Canvas.objects(belongsTo__contains=sequence.ATid):
                    belongs_to_canvas.belongsTo.remove(sequence.ATid)
                    belongs_to_canvas.belongsTo.append(sequence_data["ATid"])
                    belongs_to_canvas.save()
                for parent_manifest in Manifest.objects(children__contains=sequence.ATid):
                    parent_manifest.children.remove(sequence.ATid)
                    parent_manifest.children.append(sequence_data["ATid"])
                    parent_manifest.save()
            children = []
            if sub_canvases:
                result = __create_or_update_sub_children(user, sub_canvases, sequence_data["ATid"], queue_activity, bulk_create_actions, update_canvas, "sub_canvases_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_canvases_ids"] # Update the children list
            sequence_serializer.save(children=list(set(sequence.children+children)))
            response_data = sequence_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": sequence_serializer.errors, "object": sequence_data}}
            return process_result(response, queue_activity)
    except Sequence.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_sequence(user, sequence_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Sequence with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_range")
def update_range(user, range_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in range_data: range_data['identifier'] = "Unknown"
        if "name" not in range_data: range_data['name'] = "Unknown"
        identifier, name = range_data['identifier'], range_data['name']
        range = Range.objects.get(identifier=identifier, name=name)
        sub_canvases = sub_ranges = sub_members = False
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, range)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Check for nested objects
        if 'canvases' in range_data: sub_canvases = range_data["canvases"]
        if 'ranges' in range_data: sub_ranges = range_data["ranges"]
        if 'members' in range_data: sub_members = range_data["members"]
        if "@id" in range_data:
            range_data["ATid"] = range_data.pop("@id")
            range_data["name"] = range_data["ATid"].split("/")[-1].strip()
            range_data["identifier"] = range_data["ATid"].split("/")[-3].strip()
        range_data["ATid"] = "{0}/{1}/range/{2}".format(settings.IIIF_BASE_URL, range_data["identifier"], range_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(range_data, range)
        range_serializer = RangeSerializer(range, data=range_data, partial=True)
        if range_serializer.is_valid():
            # Update all Canvaes & Ranges that 'belongsTo' this Range if @id(identifier or name) has been changed
            if range_data["identifier"]!=identifier or range_data["name"]!=name:
                for belongs_to_canvas in Canvas.objects(belongsTo__contains=range.ATid):
                    belongs_to_canvas.belongsTo.remove(range.ATid)
                    belongs_to_canvas.belongsTo.append(range_data["ATid"])
                    belongs_to_canvas.save()
                for belongs_to_range in Range.objects(belongsTo__contains=range.ATid):
                    belongs_to_range.belongsTo.remove(range.ATid)
                    belongs_to_range.belongsTo.append(range_data["ATid"])
                    belongs_to_range.save()
                for parent_manifest in Manifest.objects(children__contains=range.ATid):
                    parent_manifest.children.remove(range.ATid)
                    parent_manifest.children.append(range_data["ATid"])
                    parent_manifest.save()
                for parent_range in Range.objects(children__contains=range.ATid):
                    parent_range.children.remove(range.ATid)
                    parent_range.children.append(range_data["ATid"])
                    parent_range.save()
            children = []
            if sub_canvases:
                result = __create_or_update_sub_children(user, sub_canvases, range_data["ATid"], queue_activity, bulk_create_actions, update_canvas, "sub_canvases_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_canvases_ids"] # Update the children list
            if sub_ranges:
                result = __create_or_update_sub_children(user, sub_ranges, range_data["ATid"], queue_activity, bulk_create_actions, update_range, "sub_ranges_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_ranges_ids"] # Update the children list
            if sub_members:
                result = __range_create_or_update_sub_members(user, sub_members, range_data["ATid"], queue_activity, bulk_create_actions, update_range, update_canvas)
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_canvases_ids"] # Update the children list
                    children += result["sub_ranges_ids"] # Update the children list
            range_serializer.save(children=list(set(range.children+children)))
            response_data = range_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": range_serializer.errors, "object": range_data}}
            return process_result(response, queue_activity)
    except Range.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_range(user, range_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Range with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_canvas")
def update_canvas(user, canvas_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in canvas_data: canvas_data['identifier'] = "Unknown"
        if "name" not in canvas_data: canvas_data['name'] = "Unknown"
        identifier, name = canvas_data['identifier'], canvas_data['name']
        sub_annotations = sub_annotation_lists = False
        canvas = Canvas.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, canvas)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Check for nested objects
        if 'images' in canvas_data: sub_annotations = canvas_data["images"]
        if 'otherContent' in canvas_data: sub_annotation_lists = canvas_data["otherContent"]
        if "@id" in canvas_data:
            canvas_data["ATid"] = canvas_data.pop("@id")
            canvas_data["name"] = canvas_data["ATid"].split("/")[-1].strip()
            canvas_data["identifier"] = canvas_data["ATid"].split("/")[-3].strip()
        canvas_data["ATid"] = "{0}/{1}/canvas/{2}".format(settings.IIIF_BASE_URL, canvas_data["identifier"], canvas_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(canvas_data, canvas)
        canvas_serializer = CanvasSerializer(canvas, data=canvas_data, partial=True)
        if canvas_serializer.is_valid():
            # Update all Annotations & AnnotationLists that 'belongsTo' this Canvas if @id(identifier or name) has been changed
            if canvas_data["identifier"]!=identifier or canvas_data["name"]!=name:
                for belongs_to_annotation in Annotation.objects(belongsTo__contains=canvas.ATid):
                    belongs_to_annotation.belongsTo.remove(canvas.ATid)
                    belongs_to_annotation.belongsTo.append(canvas_data["ATid"])
                    belongs_to_annotation.save()
                for belongs_to_annotation_list in AnnotationList.objects(belongsTo__contains=canvas.ATid):
                    belongs_to_annotation_list.belongsTo.remove(canvas.ATid)
                    belongs_to_annotation_list.belongsTo.append(canvas_data["ATid"])
                    belongs_to_annotation_list.save()
                for parent_sequence in Sequence.objects(children__contains=canvas.ATid):
                    parent_sequence.children.remove(canvas.ATid)
                    parent_sequence.children.append(canvas_data["ATid"])
                    parent_sequence.save()
                for parent_range in Range.objects(children__contains=canvas.ATid):
                    parent_range.children.remove(canvas.ATid)
                    parent_range.children.append(canvas_data["ATid"])
                    parent_range.save()
            children = []
            if sub_annotations:
                result = __create_or_update_sub_children(user, sub_annotations, canvas_data["ATid"], queue_activity, bulk_create_actions, update_annotation, "sub_annotations_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_annotations_ids"] # Update the children list
            if sub_annotation_lists:
                result = __create_or_update_sub_children(user, sub_annotation_lists, canvas_data["ATid"], queue_activity, bulk_create_actions, update_annotation_list, "sub_annotation_lists_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_annotation_lists_ids"] # Update the children list
            canvas_serializer.save(children=list(set(canvas.children+children)))
            response_data = canvas_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": canvas_serializer.errors, "object": canvas_data}}
            return process_result(response, queue_activity)
    except Canvas.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_canvas(user, canvas_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Canvas with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_annotation")
def update_annotation(user, annotation_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in annotation_data: annotation_data['identifier'] = "Unknown"
        if "name" not in annotation_data: annotation_data['name'] = "Unknown"
        identifier, name = annotation_data['identifier'], annotation_data['name']
        annotation = Annotation.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, annotation)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        if "@id" in annotation_data:
            annotation_data["ATid"] = annotation_data.pop("@id")
            annotation_data["name"] = annotation_data["ATid"].split("/")[-1].strip()
            annotation_data["identifier"] = annotation_data["ATid"].split("/")[-3].strip()
        annotation_data["ATid"] = "{0}/{1}/annotation/{2}".format(settings.IIIF_BASE_URL, annotation_data["identifier"], annotation_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(annotation_data, annotation)
        annotation_serializer = AnnotationSerializer(annotation, data=annotation_data, partial=True)
        if annotation_serializer.is_valid():
            # Update all Resources that 'belongsTo' this Annotation if @id(identifier or name) has been changed
            if annotation_data["identifier"]!=identifier or annotation_data["name"]!=name:
                for parent_canvas in Canvas.objects(children__contains=annotation.ATid):
                    parent_canvas.children.remove(annotation.ATid)
                    parent_canvas.children.append(annotation_data["ATid"])
                    parent_canvas.save()
                for parent_annotation_list in AnnotationList.objects(children__contains=annotation.ATid):
                    parent_annotation_list.children.remove(annotation.ATid)
                    parent_annotation_list.children.append(annotation_data["ATid"])
                    parent_annotation_list.save()
            annotation_serializer.save()
            response_data = annotation_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotation_serializer.errors, "object": annotation_data}}
            return process_result(response, queue_activity)
    except Annotation.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_annotation(user, annotation_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Annotation with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_annotation_list")
def update_annotation_list(user, annotation_list_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in annotation_list_data: annotation_list_data['identifier'] = "Unknown"
        if "name" not in annotation_list_data: annotation_list_data['name'] = "Unknown"
        identifier, name = annotation_list_data['identifier'], annotation_list_data['name']
        annotation_list = AnnotationList.objects.get(identifier=identifier, name=name)
        sub_annotations = False
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, annotation_list)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        if 'resources' in annotation_list_data: sub_annotations = annotation_list_data["resources"]
        if "@id" in annotation_list_data:
            annotation_list_data["ATid"] = annotation_list_data.pop("@id")
            annotation_list_data["name"] = annotation_list_data["ATid"].split("/")[-1].strip()
            annotation_list_data["identifier"] = annotation_list_data["ATid"].split("/")[-3].strip()
        annotation_list_data["ATid"] = "{0}/{1}/list/{2}".format(settings.IIIF_BASE_URL, annotation_list_data["identifier"], annotation_list_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(annotation_list_data, annotation_list)
        annotation_list_serializer = AnnotationListSerializer(annotation_list, data=annotation_list_data, partial=True)
        if annotation_list_serializer.is_valid():
            # Update all Annotations that 'belongsTo' this AnnotationList if @id(identifier or name) has been changed
            if annotation_list_data["identifier"]!=identifier or annotation_list_data["name"]!=name:
                for belongs_to_annotation in Annotation.objects(belongsTo=annotation_list.ATid):
                    belongs_to_annotation.belongsTo.remove(annotation_list.ATid)
                    belongs_to_annotation.belongsTo.append(annotation_list_data["ATid"])
                    belongs_to_annotation.save()
                for parent_canvas in Canvas.objects(children__contains=annotation_list.ATid):
                    parent_canvas.children.remove(annotation_list.ATid)
                    parent_canvas.children.append(annotation_list_data["ATid"])
                    parent_canvas.save()
                for parent_layer in Layer.objects(children__contains=annotation_list.ATid):
                    parent_layer.children.remove(annotation_list.ATid)
                    parent_layer.children.append(annotation_list_data["ATid"])
                    parent_layer.save()
            children = []
            if sub_annotations:
                result = __create_or_update_sub_children(user, sub_annotations, annotation_list_data["ATid"], queue_activity, bulk_create_actions, update_annotation, "sub_annotations_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_annotations_ids"] # Update the children list
            annotation_list_serializer.save(children=list(set(annotation_list.children+children)))
            response_data = annotation_list_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": annotation_list_serializer.errors, "object": annotation_list_data}}
            return process_result(response, queue_activity)
    except AnnotationList.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_annotation_list(user, annotation_list_data, True, queue_activity, bulk_create_actions)
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "AnnotationList with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="update_layer")
def update_layer(user, layer_data, embedded_update, queue_activity, bulk_create_actions):
    try:
        if "identifier" not in layer_data: layer_data['identifier'] = "Unknown"
        if "name" not in layer_data: layer_data['name'] = "Unknown"
        identifier, name = layer_data['identifier'], layer_data['name']
        layer = Layer.objects.get(identifier=identifier, name=name)
        sub_annotation_lists = False
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, layer)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        if 'otherContent' in layer_data: sub_annotation_lists = layer_data["otherContent"]
        if "@id" in layer_data:
            layer_data["ATid"] = layer_data.pop("@id")
            layer_data["name"] = layer_data["ATid"].split("/")[-1].strip()
            layer_data["identifier"] = layer_data["ATid"].split("/")[-3].strip()
        layer_data["ATid"] = "{0}/{1}/layer/{2}".format(settings.IIIF_BASE_URL, layer_data["identifier"], layer_data["name"])
        # If this is an embedded_update, append belongsTo if this object already has other belongsTo
        if embedded_update: __update_belongs_to_list(layer_data, layer)
        layer_serializer = LayerSerializer(layer, data=layer_data, partial=True)
        if layer_serializer.is_valid():
            # Update all Canvaes & Layers that 'belongsTo' this Layer if @id(identifier or name) has been changed
            if layer_data["identifier"]!=identifier or layer_data["name"]!=name:
                for belongs_to_annotation_list in AnnotationList.objects(belongsTo__contains=layer.ATid):
                    belongs_to_annotation_list.belongsTo.remove(layer.ATid)
                    belongs_to_annotation_list.belongsTo.append(layer_data["ATid"])
                    belongs_to_annotation_list.save()
                for parent_range in Range.objects(children__contains=layer.ATid):
                    parent_range.children.remove(layer.ATid)
                    parent_range.children.append(layer_data["ATid"])
                    parent_range.save()
            children = []
            if sub_annotation_lists:
                result = __create_or_update_sub_children(user, sub_annotation_lists, layer_data["ATid"], queue_activity, bulk_create_actions, update_annotation_list, "sub_annotation_lists_ids")
                if result["status"]=="fail": # Validation error occurred on children creation.
                    response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": result["errors"]}
                    return process_result(response, queue_activity)
                else:
                    children += result["sub_annotation_lists_ids"] # Update the children list
            layer_serializer.save(children=list(set(layer.children+children)))
            response_data = layer_serializer.data
            response = {"status": status.HTTP_200_OK, "data": {"@id": response_data["ATid"], "@type": response_data["ATtype"]}}
            if not embedded_update: # Process the queue_activity and return final response.
                post_bulk_insert_update(bulk_create(bulk_create_actions), user, queue_activity)
                return process_result(response, queue_activity)
            else:  # pragma: no cover
                return response # Return response for parent Object
        else: # Validation error occurred for this object. Process the queue_activity and return final response.
            response = {"status": status.HTTP_422_UNPROCESSABLE_ENTITY, "data": {"error": layer_serializer.errors, "object": layer_data}}
            return process_result(response, queue_activity)
    except Layer.DoesNotExist:
        if embedded_update: # If this is an embedded update, create this object if it doesn't exist.
            return create_layer(user, layer_data, True, queue_activity, bulk_create_actions) # pragma: no cover
        else:
            response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Layer with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
            return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


# --------------------------------- End PUT Methods ----------------------------------------------- #



# --------------------------------- Begin DELETE Methods ----------------------------------------------- #

@task(name="destroy_collection")
def destroy_collection(user, identifier__name, queue_activity):
    try:
        name = identifier__name.split("__")[1]
        collection = Collection.objects.get(name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, collection, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(collection, __get_collection_children)
        bulk_delete_actions["Collection"].append(collection.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = collection
        message = "Successfully deleted Collection '{0}'.".format(name)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        return process_result(response, queue_activity)
    except Collection.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Collection with name '{0}' does not exist.".format(name)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_manifest")
def destroy_manifest(user, identifier__name, queue_activity):
    try:
        identifier = identifier__name.split("__")[0]
        manifest = Manifest.objects.get(identifier=identifier)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, manifest, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(manifest, __get_manifest_children)
        bulk_delete_actions["Manifest"].append(manifest.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = manifest
        message = "Successfully deleted the Manifest of '{0}'.".format(identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        return process_result(response, queue_activity)
    except Manifest.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "'{0}' does not have a Manifest.".format(identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_sequence")
def destroy_sequence(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        sequence = Sequence.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, sequence, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(sequence, __get_sequence_children)
        bulk_delete_actions["Sequence"].append(sequence.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = sequence
        message = "Successfully deleted Sequence '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        bulk_delete(bulk_delete_actions)
        return process_result(response, queue_activity)
    except Sequence.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Sequence with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_range")
def destroy_range(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        range_object = Range.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, range_object, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(range_object, __get_range_children)
        bulk_delete_actions["Range"].append(range_object.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = range_object
        message = "Successfully deleted Range '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        bulk_delete(bulk_delete_actions)
        return process_result(response, queue_activity)
    except Range.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Range with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_canvas")
def destroy_canvas(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        canvas = Canvas.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, canvas, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(canvas, __get_canvas_children)
        bulk_delete_actions["Canvas"].append(canvas.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = canvas
        message = "Successfully deleted Canvas '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        bulk_delete(bulk_delete_actions)
        return process_result(response, queue_activity)
    except Canvas.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Canvas with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_annotation")
def destroy_annotation(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        annotation = Annotation.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, annotation, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        annotation.delete()
        response_data = annotation
        message = "Successfully deleted Annotation '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        return process_result(response, queue_activity)
    except Annotation.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Annotation with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_annotation_list")
def destroy_annotation_list(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        annotation_list = AnnotationList.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, annotation_list, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(annotation_list, __get_annotation_list_children)
        bulk_delete_actions["AnnotationList"].append(annotation_list.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = annotation_list
        message = "Successfully deleted AnnotationList '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        bulk_delete(bulk_delete_actions)
        return process_result(response, queue_activity)
    except AnnotationList.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "AnnotationList with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


@task(name="destroy_layer")
def destroy_layer(user, identifier__name, queue_activity):
    try:
        identifier, name = identifier__name.split("__")
        layer = Layer.objects.get(identifier=identifier, name=name)
        # Check if current user has permission for this object
        not_have_permission = __check_user_permission(user, layer, True)
        if not_have_permission: return process_result(not_have_permission, queue_activity)
        # Delete all children objects recursively.
        bulk_delete_actions = __get_children_ids_for_bulk_action(layer, __get_layer_children)
        bulk_delete_actions["Layer"].append(layer.ATid)
        bulk_delete(bulk_delete_actions)
        response_data = layer
        message = "Successfully deleted Layer '{0}' from identifier '{1}'.".format(name, identifier)
        response = {"status": status.HTTP_204_NO_CONTENT, "data": {'message': message, "@id": response_data["ATid"], "@type": response_data["ATtype"]}}
        bulk_delete(bulk_delete_actions)
        return process_result(response, queue_activity)
    except Layer.DoesNotExist:
        response = {"status": status.HTTP_404_NOT_FOUND, "data": {'error': "Layer with name '{0}' does not exist in identifier '{1}'.".format(name, identifier)}}
        return process_result(response, queue_activity)
    except Exception as e: # pragma: no cover
        response = {"status": status.HTTP_400_BAD_REQUEST, "data": {'error': e.message}}
        return process_result(response, queue_activity)


# --------------------------------- End DELETE Methods ----------------------------------------------- #




# --------------------------------- Begin Helper Functions ----------------------------------------------- #


def __check_user_permission(user, obj, delete=False):
    # Check if current user has permission for this object
    if not user["is_superuser"] and user["username"] not in obj.ownedBy:
        return {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "You don't have the necessary permission to perform this action. Please contact your admin."}}
     # Check if this object belongs to another User if the request is DELETE
    if delete and not user["is_superuser"] and len(obj.ownedBy) > 1:
        return {"status": status.HTTP_401_UNAUTHORIZED, "data": {'error': "This object is owned by many users. Please contact your admin to perform this action."}}


def __update_belongs_to_list(object_data, obj):
    # If this is an embedded_update, append belongsTo if this object already has other belongsTo
    if 'belongsTo' in object_data and obj.belongsTo != []:
        object_data['belongsTo'] += obj.belongsTo
        object_data['belongsTo'] = set(object_data['belongsTo'])


def __collection_sub_members_pre_validation(members, belongs_to):
    sub_collections, sub_manifests = [], []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongs_to]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}, "FAIL"
        else:
            if member["@type"] not in ["sc:Collection", "sc:Manifest"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Collection or sc:Manifest.'}}, "FAIL"
        if member["@type"]=="sc:Collection":
            sub_collections.append(member)
        else:
            sub_manifests.append(member)
    return sub_collections, sub_manifests


def __collection_create_or_update_sub_members(user, members, belongs_to, queue_activity, bulk_create_actions, create_or_update_collection_function, create_or_update_manifest_function):
    sub_collections, sub_manifests = __collection_sub_members_pre_validation(members, belongs_to)
    if sub_manifests=="FAIL": return sub_collections
    sub_collections_ids, sub_manifests_ids = [], []
    result = __create_or_update_sub_children(user, sub_collections, belongs_to, queue_activity, bulk_create_actions, create_or_update_collection_function, "sub_collections_ids")
    if result["status"]=="fail":
        return result
    else:
        sub_collections_ids = result["sub_collections_ids"]
    result = __create_or_update_sub_children(user, sub_manifests, belongs_to, queue_activity, bulk_create_actions, create_or_update_manifest_function, "sub_manifests_ids")
    if result["status"]=="fail":
        return result
    else:
        sub_manifests_ids = result["sub_manifests_ids"] 
    return {"status": "success", "sub_collections_ids": sub_collections_ids, "sub_manifests_ids": sub_manifests_ids}


def _range_sub_members_pre_validation(members, belongs_to):
    sub_canvases, sub_ranges = [], []
    for index, member in enumerate(members):
        member["belongsTo"] = [belongs_to]
        member["order"] = index+1
        if "@type" not in member:
            return {"status": "fail", "errors": {'error': 'Field @type is required for member object.'}}, "FAIL"
        else:
            if member["@type"] not in ["sc:Canvas", "sc:Range"]:
                return {"status": "fail", "errors": {'error': 'Field @type must be sc:Canvas or sc:Range.'}}, "FAIL"
        if member["@type"]=="sc:Canvas":
            sub_canvases.append(member)
        else:
            sub_ranges.append(member)
    return sub_canvases, sub_ranges


def __range_create_or_update_sub_members(user, members, belongs_to, queue_activity, bulk_create_actions, create_or_update_range_function, create_or_update_canvas_function):
    sub_canvases, sub_ranges = _range_sub_members_pre_validation(members, belongs_to)
    if sub_ranges=="FAIL": return sub_canvases
    sub_canvases_ids, sub_ranges_ids = [], []
    result = __create_or_update_sub_children(user, sub_canvases, belongs_to, queue_activity, bulk_create_actions, create_or_update_canvas_function, "sub_canvases_ids")
    if result["status"] == "fail":  
        return result 
    else:
        sub_canvases_ids = result["sub_canvases_ids"]
    result = __create_or_update_sub_children(user, sub_ranges, belongs_to, queue_activity, bulk_create_actions, create_or_update_range_function, "sub_ranges_ids")
    if result["status"] == "fail":  
        return result
    else:
        sub_ranges_ids = result["sub_ranges_ids"]
    return {"status": "success", "sub_canvases_ids": sub_canvases_ids, "sub_ranges_ids": sub_ranges_ids}


def __create_or_update_sub_children(user, children, belongs_to, queue_activity, bulk_create_actions, create_or_update_function, child_type):
    children_ids = []
    for index, child in enumerate(children):
        if isinstance(child, basestring): child = {"@id": child}
        if "@id" in child:
            if child_type=="sub_collections_ids": # Special case for Collection
                child['name'] = child["@id"].split("/")[-1].strip()
            elif  child_type=="sub_manifests_ids": # Special case for Manifest
                child['identifier'] = child["@id"].split("/")[-2].strip()
            else: # All other generic objects
                child['name'] = child["@id"].split("/")[-1].strip()
                child['identifier'] = child["@id"].split("/")[-3].strip()
        child["belongsTo"] = [belongs_to]
        child["order"] = index+1
        # If creating/updating an Annotation, populate the 'on' field automatically.
        if child_type=="sub_annotations_ids" and "canvas" in belongs_to: child["on"] = belongs_to
        sub_child = create_or_update_function(user, child, True, queue_activity, bulk_create_actions)
        if sub_child["status"] >= 400:  
            return {"status": "fail", "errors": sub_child} 
        else:
            children_ids.append(sub_child["data"]["@id"])
    return {"status": "success", child_type: children_ids}


# Update duplicate entries after Bulk insert
def post_bulk_insert_update(to_update, user, queue_activity):
    map_model_to_update_function = {
        "Collection": update_collection,
        "Manifest": update_manifest,
        "Sequence": update_sequence,
        "Range": update_range,
        "Canvas": update_canvas,
        "Annotation": update_annotation,
        "AnnotationList": update_annotation_list,
        "Layer": update_layer
    }
    for model, update_function in map_model_to_update_function.iteritems():
        if to_update[model]:
            for obj in to_update[model]:
                update_function(user, obj, True, queue_activity, None)


def __get_children_ids_for_bulk_action(obj, function_to_get_children):
    required_children = function_to_get_children(obj, False)
    bulk_actions = {}
    for model in ["Collection", "Manifest", "Sequence", "Range", "Canvas", "Annotation", "AnnotationList", "Layer"]:
        bulk_actions[model] = [item["ATid"] for item in required_children[model]]
    return bulk_actions


# Remove all internal properties from the GET response
def __clean_object(object):
    if "_id" in object: del object["_id"]
    if "id" in object: del object["id"]
    if "identifier" in object: del object["identifier"]
    if "name" in object: del object["name"]
    if "order" in object: del object["order"]
    if "embeddedEntirely" in object: del object["embeddedEntirely"]
    if "hidden" in object: del object["hidden"]
    if "ownedBy" in object: del object["ownedBy"]
    return object


# Return the shortened embedded object
def __get_embedded_object(object):
    return {
        "@id": object["ATid"],
        "@type": object["ATtype"],
        "label": object["label"] if "label" in object else None
    }


# Merge the key,values of dict_2 into dict_1
def __merge_two_dictionaries(dict_1, dict_2):
    for model in ["Collection", "Manifest", "Sequence", "Range", "Canvas", "Annotation", "AnnotationList", "Layer"]:
        dict_1[model] += dict_2[model]


def __get_collection_children(collection, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Collection
        children["Collection"] = [__clean_object(item.to_mongo()) for item in Collection.objects(ATid__in=collection['children'], hidden=False).order_by('order')]
        children["Manifest"] = [__clean_object(item.to_mongo()) for item in Manifest.objects(ATid__in=collection['children'], hidden=False).order_by('order')]
    else: # DELETE request for a Collection
        children["Collection"] = [__clean_object(item.to_mongo()) for item in Collection.objects(ATid__in=collection['children']).order_by('order')]
        children["Manifest"] = [__clean_object(item.to_mongo()) for item in Manifest.objects(ATid__in=collection['children']).order_by('order')]
        for sub_collection in children["Collection"]:
            sub_children = __get_collection_children(sub_collection, False)
            __merge_two_dictionaries(children, sub_children)
        for sub_manifest in children["Manifest"]:
            sub_children = __get_manifest_children(sub_manifest, False)
            __merge_two_dictionaries(children, sub_children)
    return children


def __get_manifest_children(manifest, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Manifest
        children["Sequence"] = [__clean_object(item.to_mongo()) for item in Sequence.objects(ATid__in=manifest['children'], hidden=False).order_by('order')]
        children["Range"] = [__clean_object(item.to_mongo()) for item in Range.objects(ATid__in=manifest['children'], hidden=False).order_by('order')]
        required_range_ids = []
        for range_object in children["Range"]:
            required_range_ids += [child for child in range_object["children"] if "range" in child]
        children["Range"] += [__clean_object(item.to_mongo()) for item in Range.objects(ATid__in=required_range_ids, hidden=False).order_by('order')]
        required_canvas_ids = []
        for sequence in children["Sequence"]:
            required_canvas_ids += [child for child in sequence["children"] if "canvas" in child]
        for range_object in children["Range"]:
            required_canvas_ids += [child for child in range_object["children"] if "canvas" in child]
        required_canvas_ids = list(set(required_canvas_ids))
        children["Canvas"] = [__clean_object(item.to_mongo()) for item in Canvas.objects(ATid__in=required_canvas_ids, hidden=False).order_by('order')]
        required_annotation_ids = []
        required_annotation_list_ids = []
        for canvas in children["Canvas"]:
            required_annotation_ids += [child for child in canvas["children"] if "annotation" in child]
            required_annotation_list_ids += [child for child in canvas["children"] if "list" in child]
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=required_annotation_ids, hidden=False).order_by('order')]
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=required_annotation_list_ids, hidden=False).order_by('order')]
    else: # DELETE request for a Manifest
        children["Sequence"] = [__clean_object(item.to_mongo()) for item in Sequence.objects(ATid__in=manifest['children']).order_by('order')]
        children["Range"] = [__clean_object(item.to_mongo()) for item in Range.objects(ATid__in=manifest['children']).order_by('order')]
        for sub_sequence in children["Sequence"]:
            sub_children = __get_sequence_children(sub_sequence, False)
            __merge_two_dictionaries(children, sub_children)
        for sub_range in children["Range"]:
            sub_children = __get_range_children(sub_range, False)
            __merge_two_dictionaries(children, sub_children)
    return children


def __get_sequence_children(sequence, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Sequence
        children["Canvas"] = [__clean_object(item.to_mongo()) for item in Canvas.objects(ATid__in=sequence['children'], hidden=False).order_by('order')]
        required_annotation_ids = []
        required_annotation_list_ids = []
        for canvas in children["Canvas"]:
            required_annotation_ids += [child for child in canvas["children"] if "annotation" in child]
            required_annotation_list_ids += [child for child in canvas["children"] if "list" in child]
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=required_annotation_ids, hidden=False).order_by('order')]
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=required_annotation_list_ids, hidden=False).order_by('order')]
    else: # DELETE request for a Sequence
        children["Canvas"] = [__clean_object(item.to_mongo()) for item in Canvas.objects(ATid__in=sequence['children']).order_by('order')]
        for sub_canvas in children["Canvas"]:
            sub_children = __get_canvas_children(sub_canvas, False)
            __merge_two_dictionaries(children, sub_children)
    return children


def __get_canvas_children(canvas, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Canvas
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=canvas['children'], hidden=False).order_by('order')]
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=canvas['children'], hidden=False).order_by('order')]
    else: # DELETE request for a Canvas
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=canvas['children']).order_by('order')]
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=canvas['children']).order_by('order')]
        for sub_annotation_list in children["AnnotationList"]:
            sub_children = __get_annotation_list_children(sub_annotation_list, False)
            __merge_two_dictionaries(children, sub_children)
    return children


def __get_range_children(range, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Range
        children["Canvas"] = [__clean_object(item.to_mongo()) for item in Canvas.objects(ATid__in=range['children'], hidden=False).order_by('order')]
        children["Range"] = [__clean_object(item.to_mongo()) for item in Range.objects(ATid__in=range['children'], hidden=False).order_by('order')]
    else: # DELETE request for a Range
        children["Canvas"] = [__clean_object(item.to_mongo()) for item in Canvas.objects(ATid__in=range['children']).order_by('order')]
        children["Range"] = [__clean_object(item.to_mongo()) for item in Range.objects(ATid__in=range['children']).order_by('order')]
        for sub_range in children["Range"]:
            sub_children = __get_range_children(sub_range, False)
            __merge_two_dictionaries(children, sub_children)
        for sub_canvas in children["Canvas"]:
            sub_children = __get_canvas_children(sub_canvas, False)
            __merge_two_dictionaries(children, sub_children)
    return children


def __get_annotation_list_children(annotation_list, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a AnnotationList
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=annotation_list['children'], hidden=False).order_by('order')]
    else: # DELETE request for a AnnotationList
        children["Annotation"] = [__clean_object(item.to_mongo()) for item in Annotation.objects(ATid__in=annotation_list['children']).order_by('order')]
    return children


def __get_layer_children(layer, view_mode=True):
    children = {"Collection": [], "Manifest": [], "Sequence": [], "Range": [], "Canvas": [], "Annotation": [], "AnnotationList": [], "Layer": []}
    if view_mode: # GET request for a Layer
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=layer['children'], hidden=False).order_by('order')]
    else: # DELETE request for a Layer
        children["AnnotationList"] = [__clean_object(item.to_mongo()) for item in AnnotationList.objects(ATid__in=layer['children']).order_by('order')]
        for sub_annotation_list in children["AnnotationList"]:
            sub_children = __get_annotation_list_children(sub_annotation_list, False)
            __merge_two_dictionaries(children, sub_children)
    return children


# --------------------------------- End Helper Functions ----------------------------------------------- #
