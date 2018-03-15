from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:Manifest)$'


class Manifest(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique=True,
        regex=valid_name,
        help_text=("The identifier of this IIIF Manifest.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Manifest',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Manifest.")
    )
    viewingDirection = fields.StringField(
        null=True,
        help_text=("The direction that a sequence of canvases should be displayed to the user. A manifest may have exactly one viewing direction, and if so, it applies to all of its sequences unless the sequence specifies its own viewing direction.")
    )
    navDate = fields.StringField(
        null=True,
        help_text=("A date that the client can use for navigation purposes when presenting the resource to the user in a time-based user interface, such as a calendar or timeline. The value must be an xsd:dateTime literal in UTC, expressed in the form YYYY-MM-DDThh:mm:ssZ.")
    )
