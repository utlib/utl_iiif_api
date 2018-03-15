from mongoengine import Document, fields


class Queue(Document):
    status = fields.StringField(
        required=True,
        default="Pending",
        help_text=(
            "The current status of the request. Either Pending or Complete.")
    )

    activity = fields.DictField(
        null=True,
        default={},
        help_text=("The corresponding activity for this Queue")
    )
