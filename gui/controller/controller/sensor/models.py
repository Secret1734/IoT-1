from django.db import models
from iot_platform.models import PlatformModel
import uuid
from django.dispatch import receiver
from utils import kubernetes_client, kubernetes_tmpl
from controller import settings


class SensorModel(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    resource_id = models.TextField(unique=True, max_length=32, auto_created=True, null=False)
    choices = (
        ('Diode', 'Diode'),
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
    platform_listener = models.ForeignKey(PlatformModel, to_field='resource_id', null=True)

    class Meta:
        db_table = "sensor"

    def __str__(self):
        return str(self.resource_id)

    def clean(self):
        # temp = '-'.join([str(self.platform_type), str(self.namespace), str(self.version), str(self.id)])
        # self.resource_id = temp.lower()
        super().clean()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        _id = SensorModel.objects.count()+1
        temp = '-'.join([str(self.description), str(self.namespace), str(self.version), str(_id)])
        self.resource_id = temp.lower()
        super().save(force_insert, force_update, using, update_fields)



@receiver(models.signals.post_save, sender=SensorModel)
def deploy_sensor(sender, instance, **kwargs):
    """
    Callback function for signal
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    print('----- Deploy sensor')
    print(kubernetes_client.deploy_sensor(**dict(instance.__dict__)))
    print('----- Assign sensor')
    print(kubernetes_client.assign_sensor_to_platform(sensor_id=str(instance.resource_id), platform_id=str(instance.platform_listener.resource_id),
                                                      platform_type=str(instance.platform_listener.platform_type),
                                                      namespace=str(instance.platform_listener.namespace)))

@receiver(models.signals.post_delete, sender=SensorModel)
def delete_sensor(sender, instance, **kwargs):
    print('--- Delete sensor')
    print(kubernetes_client.delete_resource(instance.resource_id, namespace='kube-system', resource_type=kubernetes_tmpl.REPLICATION_RESOURCE))
    print('--- Delete configmap')
    config_uid = settings.SENSOR['config_configmap']['name']+'-'+instance.resource_id
    print(kubernetes_client.delete_resource(config_uid, namespace=instance.namespace, resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE))

    item_uid = settings.SENSOR['item_configmap']['name']+'-'+instance.resource_id
    print(kubernetes_client.delete_resource(item_uid, namespace=instance.namespace,
                                            resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE))