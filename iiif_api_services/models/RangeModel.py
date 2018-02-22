from mongoengine import Document, EmbeddedDocument, DynamicDocument, DynamicField, fields


class Range(DynamicDocument):
    item = fields.StringField(required=True)
    name = fields.StringField(required=True) # must be unique within the same item
    context = fields.URLField(required=True, default='http://iiif.io/api/presentation/2/context.json')
    type = fields.StringField(required=True, default='sc:Range')
    label = fields.StringField(required=True)
    metadata = fields.DynamicField(null=True)
    description = fields.DynamicField(null=True)
    thumbnail = fields.DynamicField(null=True)
    viewingDirection = fields.DynamicField(null=True)
    viewingHint = fields.DynamicField(null=True)
    license = fields.DynamicField(null=True)
    attribution = fields.DynamicField(null=True)
    logo = fields.DynamicField(null=True)
    related = fields.DynamicField(null=True)
    rendering = fields.DynamicField(null=True)
    seeAlso = fields.DynamicField(null=True)
    service = fields.DynamicField(null=True)
    within = fields.DynamicField(null=True)
    startCanvas = fields.DynamicField(null=True)
    canvases = fields.ListField(fields.DynamicField(null=True))
    contentLayer = fields.DynamicField(null=True)
    ranges = fields.ListField(fields.DynamicField(null=True))
    members = fields.ListField(fields.DynamicField(null=True))