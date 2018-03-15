from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(oa\:Annotation)$'


class Annotation(IIIFModel):
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

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='oa:Annotation',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: oa:Annotation.")
    )
    motivation = fields.DynamicField(
        null=True,
        help_text=("Each association of an image must have the motivation field and the value must be 'sc:painting'. This is in order to distinguish it from comment annotations about the canvas. Note that all resources which are to be displayed as part of the representation are given the motivation of 'sc:painting', regardless of whether they are images or not. For example, a transcription of the text in a page is considered 'painting' as it is a representation of the object, whereas a comment about the page is not.")
    )

    # LINKING PROPERTIES
    on = fields.DynamicField(
        null=True,
        help_text=(
            "The URI of the canvas. This is to ensure consistency with annotations that target only part of the resource.")
    )

    # Image or Other CONTENT
    resource = fields.DynamicField(
        null=True,
        help_text=(
            "The image itself is linked in the resource property of the annotation.")
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
