from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:Layer)$'


class Layer(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this Layer belongs to.")
    )
    name = fields.StringField(
        required=True,
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF Layer.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Layer',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Layer.")
    )
    viewingDirection = fields.StringField(
        null=True,
        help_text=("The direction that a range of canvases should be displayed to the user. A manifest may have exactly one viewing direction, and if so, it applies to all of its ranges unless the range specifies its own viewing direction.")
    )

    # PAGING PROPERTIES
    first = fields.StringField(
        null=True,
        help_text=("A link from a resource with pages, such as a collection or layer, to its first page resource, another collection or an annotation list respectively. The page resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    last = fields.StringField(
        null=True,
        help_text=("A link from a resource with pages to its last page resource. The page resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    total = fields.IntField(
        null=True,
        help_text=("The total number of leaf resources, such as annotations within a layer, within a list of pages. The value must be a non-negative integer.")
    )
