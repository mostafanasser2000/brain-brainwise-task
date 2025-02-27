from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta:
        model = User
        fields = UserDetailsSerializer.Meta.fields + ("role",)
        read_only_fields = UserDetailsSerializer.Meta.read_only_fields + ("role",)
