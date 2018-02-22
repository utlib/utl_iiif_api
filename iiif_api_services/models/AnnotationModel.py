from mongoengine import Document, fields
from django.conf import settings # import the settings file to get IIIF_BASE_URL

# Regex Validation Helpers
valid_name =  r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(oa\:Annotation)$'

class Annotation(Document):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this Annotation belongs to.")
    )
    name = fields.StringField(
        required=True, 
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF Annotation.")
    )
    order = fields.IntField(
        default=0, 
        help_text=("The order in which this (sub)Annotation was given when created from a main Canvas.")
    )
    embeddedEntirely = fields.BooleanField(
        default=False, 
        help_text=("Whether this Annotation should embedded in its entirety in the response.")
    )
    belongsTo = fields.ListField(
        default=[],
        help_text=("List of resources this resource belongs to.")
    )
    children = fields.ListField(
        default=[],
        help_text=("List of child objects for this resource.")
    )
    hidden = fields.BooleanField(
        default=False,
        help_text=("Whether to show this reource in the respnse.")
    )
    ownedBy = fields.ListField(
        default=[],
        help_text=("List of users who have PUT, DELETE access to this object.")
    )
        
    # DESCRIPTIVE AND RIGHTS PROPERTIES
    # label can be a String or a Key-Value pair. {"label": {"@value": "Bla", "@language": "en"}}
    label = fields.DynamicField(
        null=True, 
        help_text=("A human readable label, name or title for the resource.")
    )
    metadata = fields.ListField(
        null=True, 
        help_text=("A list of short descriptive entries, given as pairs of human readable label and value to be displayed to the user.")
    )
    # description can be a String or a Key-Value pair. {"description": {"@value": "Bla", "@language": "en"}}
    description = fields.DynamicField(
        null=True, 
        help_text=("A longer-form prose description of the object or resource that the property is attached to, intended to be conveyed to the user as a full text description, rather than a simple label and value.")
    )
    thumbnail = fields.DictField(
        null=True, 
        help_text=("A small image that depicts or pictorially represents the resource that the property is attached to, such as the title page, a significant image or rendering of a canvas with multiple content resources associated with it.")
    )
    # attribution can be a String or a Key-Value pair. {"attribution": {"@value": "Bla", "@language": "en"}}
    attribution = fields.DynamicField(
        null=True, 
        help_text=("Text that must be shown when the resource it is associated with is displayed or used. For example, this could be used to present copyright or ownership statements, or simply an acknowledgement of the owning and/or publishing institution.")
    )
    license = fields.StringField(
        null=True,
        help_text=("A link to an external resource that describes the license or rights statement under which the resource may be used.")
    )
    # Logo could be a url or a hash representing an IIIF image @id and service
    logo = fields.DynamicField(
        null=True, 
        help_text=("A small image that represents an individual or organization associated with the resource it is attached to. This could be the logo of the owning or hosting institution.")
    )

    # TECHNICAL PROPERTIES
    ATid = fields.StringField(
        unique=True,
        required=True, 
        help_text=("The URI that identifies the resource. It is recommended that an HTTP URI be used for all resources.")
    )
    ATtype = fields.StringField(
        required=True, 
        default='oa:Annotation',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: oa:Annotation.")
    )
    viewingHint = fields.StringField(
        null=True, 
        help_text=("A hint to the client as to the most appropriate method of displaying the resource.")
    )
    motivation = fields.DynamicField(
        null=True,
        help_text=("Each association of an image must have the motivation field and the value must be 'sc:painting'. This is in order to distinguish it from comment annotations about the canvas. Note that all resources which are to be displayed as part of the representation are given the motivation of 'sc:painting', regardless of whether they are images or not. For example, a transcription of the text in a page is considered 'painting' as it is a representation of the object, whereas a comment about the page is not.")
    )

    # LINKING PROPERTIES
    # Any resource type may have one or more of thw following external linking resources. Either a single value or a list of values
    seeAlso = fields.DynamicField(
        null=True, 
        help_text=("A link to a machine readable document that semantically describes the resource with the seeAlso property, such as an XML or RDF description. This document could be used for search and discovery or inferencing purposes, or just to provide a longer description of the resource.")
    )
    service = fields.DynamicField(
        null=True, 
        help_text=("A link to a service that makes more functionality available for the resource, such as from an image to the base URI of an associated IIIF Image API service. The service resource should have additional information associated with it in order to allow the client to determine how to make appropriate use of it, such as a profile link to a service description.")
    )
    related = fields.DynamicField(
        null=True, 
        help_text=("A link to an external resource intended to be displayed directly to the user, and is related to the resource that has the related property. Examples might include a video or academic paper about the resource, a website, an HTML description, and so forth.")
    )
    rendering = fields.DynamicField(
        null=True, 
        help_text=("A link to an external resource intended for display or download by a human user. This property can be used to link from a manifest, collection or other resource to the preferred viewing environment for that resource, such as a viewer page on the publisher's web site.")
    )
    within = fields.DynamicField(
        null=True, 
        help_text=("A link to a resource that contains the current resource, such as annotation lists within a layer. This also allows linking upwards to collections that allow browsing of the digitized objects available.")
    )
    on = fields.DynamicField(
        required=True, 
        default=settings.IIIF_BASE_URL+'/UofT/canvas/default',
        help_text=("The URI of the canvas. This is to ensure consistency with annotations that target only part of the resource.")
    )

    # Image or Other CONTENT
    resource = fields.DynamicField(
        null=True, 
        help_text=("The image itself is linked in the resource property of the annotation.")
    )

    # OTHER PROPERTIES
    stylesheet = fields.DynamicField(
        null=True,
        help_text=("The Cascading Style Sheets standard (CSS) is used to describe how the client should render a given resource to the user. The CSS information is embedded within the annotation using the same ContentAsText approach")
    )
    selector = fields.DynamicField(
        null=True,
        help_text=(" if the image is available via the IIIF Image API, it may be more convenient to have the server do the rotation of the image. This uses a custom Selector for the Image API, further described in the Open Annotation extensions annex.")
    )