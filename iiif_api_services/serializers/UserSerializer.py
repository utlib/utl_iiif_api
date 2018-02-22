from rest_framework_mongoengine import serializers as rest_mongo_serializers
from iiif_api_services.models.User import User


class UserAdminSerializer(rest_mongo_serializers.DocumentSerializer):
    def create(self, validated_data): # pragma: no cover
        return User.create_user(validated_data['username'], validated_data['email'], validated_data['password'], is_superuser=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', )



class UserStaffSerializer(rest_mongo_serializers.DocumentSerializer):
    def create(self, validated_data): # pragma: no cover
        return User.create_user(validated_data['username'], validated_data['email'], validated_data['password'])

    class Meta:
        model = User
        fields = ('username', 'email', 'password', )


class UserViewSerializer(rest_mongo_serializers.DocumentSerializer):

    class Meta:
        model = User
        exclude = ('password',)
