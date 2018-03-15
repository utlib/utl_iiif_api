import json
from django.conf import settings
from rest_framework import status
from rest_framework import permissions
from rest_framework.response import Response
from iiif_api_services.models.User import User
from rest_framework.viewsets import ModelViewSet
from iiif_api_services.serializers.UserSerializer import *
from iiif_api_services.helpers.ProcessRequest import update_permission


class CustomRegisterStaffPermission(permissions.BasePermission):
    message = "You don't have the necessary permission to perform this action. Please contact your admin."

    def has_permission(self, request, view):
        staff_create = request.method == "POST" and request.get_full_path() == "/auth/staff"
        staff_update_delete_view = request.method in [
            "GET", "PUT", "DELETE"] and "/auth/staff" in request.get_full_path()
        staff_update_permission = request.method == "PUT" and "/auth/admin/updatePermission" in request.get_full_path()
        if staff_create or staff_update_delete_view or staff_update_permission:
            return (request.user and request.user.is_superuser)
        else:
            return True


class AdminView(ModelViewSet):

    permission_classes = (permissions.AllowAny, CustomRegisterStaffPermission)

    # POST /auth/admin
    def create_user(self, request, identifier=None, format=None):
        try:
            request.data['username'] = request.data['username'].replace(
                " ", "")
            user = User.objects.get(username=request.data['username'])
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with username already exists."})
        except:
            try:
                request.data['email'] = request.data['email'].replace(" ", "")
                user = User.objects.get(email=request.data['email'])
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "User with email already exists."})
            except:
                data = request.data
                if request.get_full_path() == "/auth/admin" and "secretKey" not in data:
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "Param secretKey is required."})
                if request.get_full_path() == "/auth/admin" and (data["secretKey"] != settings.REGISTER_SECRET_KEY):
                    return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data={'error': "Invalid secretKey provided."})
                if request.get_full_path() == "/auth/admin":
                    serializer = UserAdminSerializer(data=data)
                else:
                    serializer = UserStaffSerializer(data=request.data)
                if serializer.is_valid():
                    user = serializer.save()
                    view_serializer = UserViewSerializer(user)
                    return Response(view_serializer.data)
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # PUT /auth/staff/:id
    def update_staff(self, request, id=None, format=None):
        try:
            user = User.objects.get(id=id)
            user_serializer = UserViewSerializer(user, data=request.data, context={
                                                 'request': request}, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
                view_serializer = UserViewSerializer(user)
                return Response(view_serializer.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "User with id '" + id + "' does not exist."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # DELETE /auth/staff/:id
    def delete_staff(self, request, id=None, format=None):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return Response(status=status.HTTP_200_OK, data={'message': "Successfully deleted user with id '" + id + "'."})
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "User with id '" + id + "' does not exist."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # GET /auth/staff
    def view_staffs(self, request, format=None):
        try:
            users = User.objects(is_superuser=False)
            if users:
                users_serializer = UserViewSerializer(
                    users, context={'request': request}, many=True)
                return Response(users_serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': "No staff users found."})
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': e.message})

    # PUT /auth/admin/updatePermission
    def update_permission(self, request, format=None):
        try:
            request_body = json.loads(request.body)
            if "username" not in request_body:
                return Response(data={"error": "username field is required"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif not isinstance(request_body["username"], basestring):
                return Response(data={"error": "username must be a string."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            if "action" not in request_body:
                return Response(data={"error": "action field is required. Possible values are 'ADD' and 'REMOVE'."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif request_body["action"] not in ['ADD', 'REMOVE']:
                return Response(data={"error": "Allowed values for action are 'ADD' and 'REMOVE'."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            result = update_permission(request_body)
            return Response(status=result['status'], data=result['data'])
        except Exception as e:  # pragma: no cover
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': "Something went wrong while performing the action. Make sure the request body is valid.", 'message': e.message})
