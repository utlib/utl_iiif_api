from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from iiif_api_services.serializers.UserSerializer import *
from rest_framework import permissions
from iiif_api_services.models.User import User
from django.conf import settings # import the settings file to get REGISTER_SECRET_KEY
from iiif_api_services.views.BackgroundProcessing import updatePermission
import json

class CustomRegisterStaffPermission(permissions.BasePermission):
    message ="You don't have the necessary permission to perform this action. Please contact your admin."

    def has_permission(self, request, view):
        if request.method=="POST" and request.get_full_path()=="/auth/staff":
            return (request.user and request.user.is_superuser)
        elif request.method in ["GET", "PUT", "DELETE"] and "/auth/staff" in request.get_full_path():
            return (request.user and request.user.is_superuser)
        elif request.method == "PUT" and "/auth/admin/updatePermission" in request.get_full_path():
            return (request.user and request.user.is_superuser)
        else:
            return True



class AdminView(ModelViewSet):

    permission_classes = (permissions.AllowAny, CustomRegisterStaffPermission)

    # POST /auth/admin
    def createAdmin(self, request, identifier=None, format=None):
        try:
            request.data['username'] = request.data['username'].replace(" ", "")
            user = User.objects.get(username=request.data['username'])
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with username already exists."})
        except:
            try:
                request.data['email'] = request.data['email'].replace(" ", "")
                user = User.objects.get(email=request.data['email'])
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with email already exists."})
            except:
                data = request.data
                if "secretKey" not in data:
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "Param secretKey is required."})
                if (data["secretKey"] != settings.REGISTER_SECRET_KEY):
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "Invalid secretKey provided."})
                serializer = UserAdminSerializer(data=data)
                if serializer.is_valid():
                    user = serializer.save()
                    if user:
                        viewSerializer = UserViewSerializer(user)
                        return Response(viewSerializer.data)
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    # POST /auth/staff
    def createStaff(self, request, identifier=None, format=None):
        try:
            request.data['username'] = request.data['username'].replace(" ", "")
            user = User.objects.get(username=request.data['username'])
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with username already exists."})
        except:
            try:
                request.data['email'] = request.data['email'].replace(" ", "")
                user = User.objects.get(email=request.data['email'])
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with email already exists."})
            except:
                serializer = UserStaffSerializer(data=request.data)
                if serializer.is_valid():
                    user = serializer.save()
                    if user:
                        viewSerializer = UserViewSerializer(user)
                        return Response(viewSerializer.data)
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    # PUT /auth/staff/:id
    def updateStaff(self, request, id=None, format=None):
        try:
            user = User.objects.get(id=id)
            userSerializer = UserViewSerializer(user, data=request.data, context={'request': request}, partial=True)
            if userSerializer.is_valid():
                userSerializer.save()
                viewSerializer = UserViewSerializer(user)
                return Response(viewSerializer.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "User with id '" + id + "' does not exist."}) 
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    # DELETE /auth/staff/:id
    def deleteStaff(self, request, id=None, format=None):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted user with id '" + id + "'."})
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "User with id '" + id + "' does not exist."}) 
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})


    # GET /auth/staff
    def viewStaffs(self, request, format=None):
        try:
            users = User.objects(is_superuser=False)
            if users:
                usersSerializer = UserViewSerializer(users, context={'request': request}, many=True)
                return Response(usersSerializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No staff users found."})           
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message}) 


    # PUT /auth/admin/updatePermission
    def updatePermission(self, request, format=None):
        try:
            requestBody = json.loads(request.body)
            if "username" not in requestBody:
                return Response(data={"error": "username field is required"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif not isinstance(requestBody["username"], basestring):
                return Response(data={"error": "username must be a string."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            if "action" not in requestBody:
                return Response(data={"error": "action field is required. Possible values are 'ADD' and 'REMOVE'."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif requestBody["action"] not in ['ADD', 'REMOVE']:
                return Response(data={"error": "Allowed values for action are 'ADD' and 'REMOVE'."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            updatePermission(requestBody)
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully updated user permissions for given objects."})
        except Exception as e: # pragma: no cover
            print e.message
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Something went wrong while performing the action. Make sure the request body is valid."}) 