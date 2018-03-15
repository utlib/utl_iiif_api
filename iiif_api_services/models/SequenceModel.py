from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:Sequence)$'


class Sequence(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this Sequence belongs to.")
    )
    name = fields.StringField(
        required=True,
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF Sequence.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Sequence',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Sequence.")
    )
    viewingDirection = fields.StringField(
        null=True,
        help_text=("The direction that a sequence of canvases should be displayed to the user. A manifest may have exactly one viewing direction, and if so, it applies to all of its sequences unless the sequence specifies its own viewing direction.")
    )

    # LINKING PROPERTIES
    startCanvas = fields.URLField(
        null=True,
        help_text=(
            "A link from a sequence or range to a canvas that is contained within the sequence.")
    )
