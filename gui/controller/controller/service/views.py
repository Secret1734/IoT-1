from rest_framework import viewsets
from django.shortcuts import render

# Create your views here.
class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows platforms to be viewed or edited.
    """
    queryset = PlatformModel.objects.all()
    serializer_class = PlatformSerializer
