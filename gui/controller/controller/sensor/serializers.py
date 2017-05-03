from rest_framework import serializers
from .models import SensorModel


class SensorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SensorModel
        fields = ('sensor_type', 'description', 'namespace', 'label', 'version', 'manufacturer',
                  'platform_listener')
