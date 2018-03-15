from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-=,\#]+$'
valid_type = r'^(sc\:Canvas)$'


class Canvas(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this Canvas belongs to.")
    )
    name = fields.StringField(
        required=True,
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF Canvas.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Canvas',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Canvas.")
    )
    height = fields.IntField(
        null=True,
        help_text=(
            "The height of a canvas or image resource. For images, the value is in pixels. For canvases, the value does not have a unit.")
    )
    width = fields.IntField(
        null=True,
        help_text=(
            "The width of a canvas or image resource. For images, the value is in pixels. For canvases, the value does not have a unit.")
    )
