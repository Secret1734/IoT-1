from rest_framework import viewsets
from iot_platform.models import PlatformModel
from iot_platform.serializers import PlatformSerializer


class PlatformViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows platforms to be viewed or edited.
    """
    queryset = PlatformModel.objects.all()
    serializer_class = PlatformSerializer
