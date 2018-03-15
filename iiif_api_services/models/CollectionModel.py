from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:Collection)$'


class Collection(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    name = fields.StringField(
        required=True,
        unique=True,
        regex=valid_name,
        help_text=("The name of this IIIF Collection.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:Collection',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:Collection.")
    )
    navDate = fields.StringField(
        null=True,
        help_text=("A date that the client can use for navigation purposes when presenting the resource to the user in a time-based user interface, such as a calendar or timeline. The value must be an xsd:dateTime literal in UTC, expressed in the form YYYY-MM-DDThh:mm:ssZ.")
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
    next = fields.StringField(
        null=True,
        help_text=("A link from a page resource to the next page resource that follows it in order. The resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    prev = fields.StringField(
        null=True,
        help_text=("A link from a page resource to the previous page resource that precedes it in order. The resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    total = fields.IntField(
        null=True,
        help_text=("The total number of leaf resources, such as annotations within a layer, within a list of pages. The value must be a non-negative integer.")
    )
    startIndex = fields.IntField(
        null=True,
        help_text=("The 0 based index of the first included resource in the current page, relative to the parent paged resource. The value must be a non-negative integer.")
    )
