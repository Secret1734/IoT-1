from django.db import models

class SensorModel(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    resource_id = models.TextField(unique=True, max_length=32, auto_created=True, null=False)
    choices = (
        ('mqtt', 'Mqtt'),
        ('Semiconductor', 'Semiconductor'),
        ('IC', 'IC'),
    )
    sensor_type = models.CharField(max_length=32, null=False, default='Diode', choices=choices)
    choices = (
        ('Weather-Temperature-Sensor', 'Weather Temperature'),
        ('Body-Temperature-Sensor', 'Body Temperature'),
        ('SONY-Light-Sensor-V1', 'SONY Light V1'),
        ('ATA-Light-Sensor-V2', 'ATA Light V2'),
        ('SENSYS-Atmosphere-Sensor', 'SENSYS Atmosphere'),
    )
    description = models.CharField(max_length=32, null=False, default='Weather-Temperature-Sensor', choices=choices)
    namespace = models.TextField(max_length=32, null=True)
    label = models.TextField(max_length=32, null=True)
    # regex = models.TextField(max_length=32, null=True)
    version = models.TextField(max_length=32, null=True)
    manufacturer = models.TextField(max_length=32, null=False, default='SONY')
