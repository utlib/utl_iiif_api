from datetime import datetime
from mongoengine import Document, fields
from iiif_api_services.models.User import User


class Activity(Document):
    username = fields.StringField(
        null=True,
        help_text=(
            "The authenticated username who made the request or AnonymousUser.")
    )

    requestPath = fields.StringField(
        null=True,
        help_text=("Request path.")
    )

    requestMethod = fields.StringField(
        null=True,
        help_text=("HTTP method (POST, PUT, etc).")
    )

    remoteAddress = fields.StringField(
        null=True,
        help_text=("Remote IP address of request.")
    )

    requestBody = fields.DictField(
        null=True,
        help_text=("Request data.")
    )

    responseBody = fields.DictField(
        null=True,
        help_text=("Response for the request made.")
    )

    responseCode = fields.IntField(
        null=True,
        help_text=("Status code of the response.")
    )

    startTime = fields.DateTimeField(
        null=True,
        default=datetime.now(),
        help_text=("Timestamp of request.")
    )

    endTime = fields.DateTimeField(
        null=True,
        help_text=("Timestamp of request end.")
    )

    error = fields.StringField(
        null=True,
        help_text=("Error traceback incase of 500 internal error.")
    )

    queueID = fields.StringField(
        null=True,
        default="PENDING",
        help_text=("ID of the corresponding Queue")
    )
