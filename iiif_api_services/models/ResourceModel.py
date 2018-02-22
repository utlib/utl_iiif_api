from mongoengine import Document, EmbeddedDocument, DynamicDocument, DynamicField, fields


class Resource(DynamicDocument):
    item = fields.StringField(required=True)
    name = fields.StringField(required=True) # must be unique within the same item
    context = fields.URLField(required=True, default='http://iiif.io/api/presentation/2/context.json')
    type = fields.StringField(required=True)
    format = fields.StringField(null=True)
    res_url = fields.DynamicField(null=True, default="")
    label = fields.StringField(null=True)
    height = fields.IntField(null=True)
    width = fields.IntField(null=True)
    metadata = fields.DynamicField(null=True)
    description = fields.DynamicField(null=True)
    thumbnail = fields.DynamicField(null=True)
    viewingHint = fields.DynamicField(null=True)
    license = fields.DynamicField(null=True)
    attribution = fields.DynamicField(null=True)
    logo = fields.DynamicField(null=True)
    related = fields.DynamicField(null=True)
    rendering = fields.DynamicField(null=True)
    seeAlso = fields.DynamicField(null=True)
    service = fields.DynamicField(null=True)
    within = fields.DynamicField(null=True)

