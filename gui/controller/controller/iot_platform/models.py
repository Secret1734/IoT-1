from django.db import models
import uuid
from django.dispatch import receiver
from utils import kubernetes_client, kubernetes_tmpl
from controller import settings


class PlatformModel(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    resource_id = models.TextField(unique=True, max_length=32, auto_created=True, null=False)
    choices = (
        ('onem2m', 'OneM2M'),
        ('openhab', 'OpenHAB'),
    )
    platform_type = models.CharField(max_length=32, null=False, default='onem2m', choices=choices)
    description = models.TextField(max_length=32, null=True)
    choices = (
        ('kube-system', 'Kube System'),
    )
    namespace = models.CharField(max_length=32, null=False, default='kube-system', choices=choices)
    label = models.TextField(max_length=32, null=True)
    # regex = models.TextField(max_length=32, null=True, default='(*.)')
    version = models.TextField(max_length=32, null=False, default='v1')

    class Meta:
        db_table = "platform"

    def __str__(self):
        return str(self.resource_id)

    def clean(self):
        super().clean()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        _id = PlatformModel.objects.count()+1
        self.resource_id = '-'.join([str(self.platform_type), str(self.namespace), str(self.version), str(_id)])
        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        return super().delete(using, keep_parents)


@receiver(models.signals.post_save, sender=PlatformModel)
def deploy_platform(sender, instance, **kwargs):
    """
    Callback function for signal
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    print(kubernetes_client.deploy_platform(**dict(instance.__dict__)))


@receiver(models.signals.post_delete, sender=PlatformModel)
def delete_platform(sender, instance, **kwargs):
    print('--- Delete platform')
    print(kubernetes_client.delete_resource(instance.resource_id, namespace=instance.namespace, resource_type=kubernetes_tmpl.REPLICATION_RESOURCE))
    print('--- Delete configmap')
    config_uid = settings.IOT_PLATFORM[instance.platform_type]['config_configmap']['name']+'-'+instance.resource_id
    print(kubernetes_client.delete_resource(config_uid, namespace=instance.namespace, resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE))

    item_uid = settings.IOT_PLATFORM[instance.platform_type]['item_configmap']['name']+'-'+instance.resource_id
    print(kubernetes_client.delete_resource(item_uid, namespace=instance.namespace,
                                            resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE))