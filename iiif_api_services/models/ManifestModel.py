from mongoengine import Document, EmbeddedDocument, DynamicDocument, DynamicField, fields


class Manifest(DynamicDocument):
    item = fields.StringField(required=True, unique=True)
    context = fields.URLField(required=True, default='http://iiif.io/api/presentation/2/context.json')
    type = fields.StringField(required=True, default='sc:Manifest')
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
    sequences = fields.ListField(fields.DynamicField(null=True))
    structures = fields.ListField(fields.DynamicField(null=True))