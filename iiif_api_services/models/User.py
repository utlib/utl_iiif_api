import datetime
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from mongoengine import fields, Document
from bson import ObjectId


class User(Document):
    id = fields.StringField(primary_key=True, default=str(ObjectId()))
    username = fields.StringField(required=True)
    email = fields.EmailField(required=True, unique=True) 
    password = fields.StringField(
        required=True,
        max_length=128,
        verbose_name='password',
    )
    is_staff = fields.BooleanField(default=True)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    last_login = fields.DateTimeField(default=timezone.now, verbose_name='last login')
    date_joined = fields.DateTimeField(default=timezone.now, verbose_name='date joined')
    user_permissions = fields.ListField(
        default=[],
        help_text='objects allowed to be modified by this user',
    )

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.username

    def __unicode__(self):
        return self.username

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def set_password(self, raw_password):
        """
        Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.
        """
        self.password = make_password(raw_password)
        self.save()
        return self

    def check_password(self, raw_password):
        """
        Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """
        return check_password(raw_password, self.password)

    @classmethod
    def create_user(cls, username, email, password, is_superuser=False):
        """
        Create (and save) a new user with the given username and password
        """
        now = datetime.datetime.now()
        user = cls(id=str(ObjectId()), username=username, email=email, date_joined=now, is_superuser=is_superuser)
        user.set_password(password)
        user.save()
        return user



