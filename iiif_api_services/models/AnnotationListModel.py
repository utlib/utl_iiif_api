from mongoengine import fields
from iiif_api_services.models.IIIFAbstractClass import IIIFModel

# Regex Validation Helpers
valid_name = r'^[a-zA-Z0-9_:\-]+$'
valid_type = r'^(sc\:AnnotationList)$'


class AnnotationList(IIIFModel):
    # PROPERTIES FOR INTERNAL USE
    identifier = fields.StringField(
        required=True,
        unique_with='name',
        regex=valid_name,
        help_text=("The identifier this AnnotationList belongs to.")
    )
    name = fields.StringField(
        required=True,
        unique_with='identifier',
        regex=valid_name,
        help_text=("The name of this IIIF AnnotationList.")
    )

    # TECHNICAL PROPERTIES
    ATtype = fields.StringField(
        required=True,
        default='sc:AnnotationList',
        regex=valid_type,
        help_text=("The type of this IIIF resource. Must be: sc:AnnotationList.")
    )

    # PAGING PROPERTIES
    next = fields.StringField(
        null=True,
        help_text=("A link from a page resource to the next page resource that follows it in order. The resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    prev = fields.StringField(
        null=True,
        help_text=("A link from a page resource to the previous page resource that precedes it in order. The resource should be referenced by just its URI (from @id) but may also have more information associated with it as an object.")
    )
    startIndex = fields.IntField(
        null=True,
        help_text=("The 0 based index of the first included resource in the current page, relative to the parent paged resource. The value must be a non-negative integer.")
    )
