from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:Range)$'


class Range(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this Range belongs to.")
    )
    name = fields.StringField(
        required=True,
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF Range.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Range',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Range.")
    )
    viewingDirection = fields.StringField(
        null=True,
        help_text=("The direction that a range of canvases should be displayed to the user. A manifest may have exactly one viewing direction, and if so, it applies to all of its ranges unless the range specifies its own viewing direction.")
    )

    # LINKING PROPERTIES
    startCanvas = fields.URLField(
        null=True,
        help_text=(
            "A link from a range or range to a canvas that is contained within the range.")
    )
    contentLayer = fields.URLField(
        null=True,
        help_text=("Ranges may also link to a layer, that has the content of the range using the contentLayer linking property. This allows, for example, the range representing a newspaper article that is split across multiple pages to be linked with the text of the article.")
    )
