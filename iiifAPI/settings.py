"""
Django settings for iiifAPI.
"""
import os
import datetime
import mongoengine
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_mongoengine',
    'mongoengine.django.mongo_auth',
    'iiif_api_services',
    'django_nose',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'iiifAPI.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

WSGI_APPLICATION = 'iiifAPI.wsgi.application'

# This will be replaced by mongoDB, but must be present to make django happy :)
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = { 
    'default': {
        'ENGINE': 'django.db.backends.sqlite3' 
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'EST'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = ( os.path.join(BASE_DIR, "static"), )


# Don't confuse Django's AUTHENTICATION_BACKENDS with DRF's AUTHENTICATION_CLASSES!
AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)
# This is a dummy django model. It's just a crutch to keep django content,
# while all the real functionality is associated with MONGOENGINE_USER_DOCUMENT
AUTH_USER_MODEL = 'mongo_auth.MongoUser'
# Custom User model to support Auth with MongoDB 
MONGOENGINE_USER_DOCUMENT = 'iiif_api_services.models.User.User'
# REST FRAMEWORK SETTINGS
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'iiif_api_services.helpers.JSONLDrenderer.JSONLDRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    )
}
# JWT AUTHENTICATION SETTINGS
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=99999),
}

# The following settings should be configured depending on server environment.
QUEUE_POST_ENABLED = False # If enabled, all POST requests will be served by a Queueing system with 202 Immediate Response.
QUEUE_PUT_ENABLED = False # If enabled, all PUT requests will be served by a Queueing system with 202 Immediate Response.
QUEUE_DELETE_ENABLED = False # If enabled, all DELETE requests will be served by a Queueing system with 202 Immediate Response.
QUEUE_RUNNER = 'THREAD' # The method for processing background taks in Queue system. Choices are: "PROCESS" or "THREAD" or "CELERY"
BROKER_URL = 'redis://localhost:6379' # Config only if QUEUE_RUNNER is set to "CELERY". RabbitMQ, Redis or any compatible other broker.
SECRET_KEY = '9*zibp0m7#7e#rz#j)(6=-v99cxcd3(85@d)rxcmy54nqq*%qj' # Use a different secret key in production.
DEBUG = True # SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = ['*'] # A list of strings representing the host/domain names that this site can serve.
MONGO_DATABASE_URI = "mongodb://localhost:27017/iiifAPI" # MongoDB URI. Overide this vale in production.
LORIS_DIRECTORY = "/home/rajakumaj/IIIFAPI/Images/" # The base path of the system directory where LORIS stores all images. Overide this vale in production.
LORIS_URL = 'https://iiif.library.utoronto.ca/image/v2/' # The base url for images being served from Loris. Overide this vale in production.
REGISTER_SECRET_KEY = "BATMAN" # Secret key which allows an Admin user to register. Overide this vale in production.
IIIF_BASE_URL = "http://localhost:8000" # Base url to generate the @id field in IIIF objects. Overide this vale in production.
IIIF_CONTEXT = "http://iiif.io/api/presentation/2/context.json" # Default IIIF @context to use for this API.
TOP_LEVEL_COLLECTION_NAME = "UofT" # The {name} of the Organization to display in top level Collection. {scheme}://{host}/{prefix}/collection/{name}.
TOP_LEVEL_COLLECTION_LABEL = "University of Toronto Libraries" # The label of the Organization top level Collection.

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
if TESTING:
    # Overide the Loris config for test environment
    LORIS_DIRECTORY = '/tmp/IIIFAPI/Testing/Test_Images/'
    LORIS_URL = 'http://localhost/loris/iiifAPI/'
    # Run background tasks synchronously for CELERY if enabled
    CELERY_ALWAYS_EAGER = True
    # MongoDB settings for testing
    TEST_MONGO_DATABASE = {
        'db': 'iiifAPI_Testing',
        'host': ['localhost'],
        'port': 27017,
    }
    # Django Nose Config
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_ARGS = [
        '--cover-erase',
        '--with-coverage',
        '--cover-html',
        '--cover-xml',
        '--cover-package=iiif_api_services',
        '--with-xunit',
        '--xunit-file=testsXMLResults.xml',
        '--verbosity=1'
    ]

# Overide dev settings with PRODUCTION SETTINGS in Production
try:
  from local_settings import *
except ImportError:
  pass

mongoengine.connect(host=MONGO_DATABASE_URI)
