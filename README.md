# IIIF API

## Digital Manuscripts - University of Toronto Libraries

* A Python-Django Restful API service that implements the IIIF Image API, Presentation API, Search API and Authentication API. 

* The purpose of this API is to enable communication between defined IIIF-compliant image stores and standard tools and will therefore support portability of information among applications. 

* Within our institution, the API will be primarily used to store IIIF manifests and collections generated from various library collections sites. It will also be used by an OA and IIIF-compliant Omeka image viewer and annotator plugin as well as support an OA import/export Omeka plugin. In addition to that, it will also support a series of experiments with a collation application(Viscoll) that will support manuscript scholars’ needs to visualize the physical construction of codices. 

## Dependencies
### 1. Python 2
* Install and Setup [Python 2](https://www.python.org/download/releases/2.7.2)

### 2. Loris Image Server
* Install and Setup [Loris Image Server](https://github.com/loris-imageserver/loris/blob/development/doc/dependencies.md)
* Loris is an implementation of the [IIIF Image API 2.0](http://iiif.io/api/image/2.0)

### 3. MongoDB Server
* Install and Setup [MongoDB Server](https://www.mongodb.com)
* MongoDB is a document database with the extensive scalability and flexibility.

### 4. Pipenv
* Install and Setup [Pipenv](https://robots.thoughtbot.com/how-to-manage-your-python-projects-with-pipenv)
* It brings together Pip, Pipfile and Virtualenv to provide a straightforward and powerful command line tool.

## Installation
### 1. Requirements
* The following packages are required.

    ```
    djangorestframework = "==3.6.4"
    "django-rest-framework-mongoengine" = "==3.3.1"
    mongoengine = "==0.9"
    pymongo = "==2.8"
    "django-test-addons" = "*"
    "djangorestframework-jwt" = "*"
    "django-nose" = "*"
    coverage = "*"
    "django-extensions" = "*"
    Django = "==1.9"
    "nose-watch" = "*"
    celery = "*"
    ```

### 2. Download and Setup Virtual Environment
* Clone the repository and install required packages.

    ```
    git clone https://git.library.utoronto.ca/digitaltoolsmss/iiifAPI.git
    cd iiifAPI
    pipenv install
    pipenv shell
    ```
* Pipenv will install all the packages listed in `Pipfile` file.
* (Optional) Some packages are used only for development purposes, and can be installed with `pipenv install --dev`
*  Finally, activate the virtual environment with  `pipenv shell`

### 2. Setup File
* The app settings can be found at `iiifAPI/settings.py`.
* Things to note:
    * `SECRET_KEY`: [Create your  new secret key](http://www.miniwebtool.com/django-secret-key-generator/) and replace the existing value.
    * `DEBUG`: Set to `True` in development and `False` in production.
    * `ALLOWED_HOSTS`: Modify to suite your domain specific settings.
    * `MONGO_DATABASE_URI`: The full URI of the mongoDB server.
    * `REGISTER_SECRET_KEY`: Secret key which allows an Admin user to register. Overide this vale in production.
    * `IIIF_BASE_URL`: Base url to generate the @id field in IIIF objects. Overide this vale in production.
    * `IIIF_CONTEXT`: Default IIIF @context to use for this API. Currently version 2.0.  
    * `LORIS_DIRECTORY`: The file system directory where LORIS stores all images. Change as needed.
    * `LORIS_URL`: The fully resolved URL for images served from Loris. Change as needed.
    * `QUEUE_POST_ENABLED`: If enabled, all POST requests will be served by a Queueing system with 202 Immediate Response.
    * `QUEUE_PUT_ENABLED`: If enabled, all PUT requests will be served by a Queueing system with 202 Immediate Response.
    * `QUEUE_DELETE_ENABLED`: If enabled, all DELETE requests will be served by a Queueing system with 202 Immediate Response.
    * `QUEUE_RUNNER`: The method for processing background taks in Queue system. Choices are: "PROCESS" or "THREAD" or "CELERY"
    * `BROKER_URL`: Config only if QUEUE_RUNNER is set to "CELERY". RabbitMQ, Redis or any compatible other broker.
    * `TOP_LEVEL_COLLECTION_NAME`: The {name} of the Organization to display in top level Collection url. {scheme}://{host}/{prefix}/collection/{name}.
    * `TOP_LEVEL_COLLECTION_LABEL`: The label of the Organization top level Collection.

## Development
* There is no need to run any migrations or syncdb commands. 
* Simply run `python manage.py runsever` to start the development server.

## Testing
* All test suites are located in `iiif_api_services/tests` and can be executed with `python manage.py test`
* To run a specific test, execute `python manage.py test iiif_api_services/tests/{filename.py}`

## Endpoints Documentation
* All endpoints with an interactive documentation can be accessed from the application `root url`. 
* Endpoints are documented with Open-API spec as a JSON config file located at `static/swagger.json`
* In production, make sure the change the default `host` from `localhost:8000` to your actual domain.
* Documentation generated by Postman API client can be found [here](https://documenter.getpostman.com/view/2715671/iiifapi/7EDAuAF#b9700f39-e609-d0ce-9fe3-0a089e19eacb).

## Deployment
### 1. Download and Configure App
* Download the latest version from `git clone https://git.library.utoronto.ca/digitaltoolsmss/iiifAPI.git`
* Modify `ALLOWED_HOSTS = ["server_domain_or_IP"]` in `iiifAPI/settings.py`
* Django uses the `STATIC_ROOT` and `STATICFILES_DIRS` setting to determine the directory where these files should go. 
  Run `python manage.py collectstatic` from the root directory. 
* Modify `MONGO_DATABASE_NAME` and `MONGO_DATABASE_HOST` to match the production environment settings.

### 2. Configure with Apache or NGINX Web Server
* [Djano with Apache] (https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04)
* [Django with NGINX] (https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-16-04)
* NOTE: In either of these setup, there is no need to run the following commands because we use MongoDB.
    * `manage.py makemigrations`, `manage.py migrate` and `manage.py createsuperuser`


## Copyright and License

Copyright 2018 University of Toronto Libraries

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

