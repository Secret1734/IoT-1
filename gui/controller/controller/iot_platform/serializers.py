from rest_framework import serializers
from iot_platform.models import PlatformModel


class PlatformSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlatformModel
        fields = ('id', 'platform_type', 'description', 'namespace', 'label', 'version')


