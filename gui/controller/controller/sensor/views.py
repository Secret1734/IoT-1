from rest_framework import viewsets
from .models import SensorModel
from .serializers import SensorSerializer


class SensorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows platforms to be viewed or edited.
    """
    queryset = SensorModel.objects.all()
    serializer_class = SensorSerializer
