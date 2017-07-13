import json
import http.client
from random import randint

from controller import settings
from . import kubernetes_tmpl


def deploy_platform(**data):
    # deploy config first
    deploy_configmap(resource_type='platform', is_item=True, is_config=True, **data)
    #
    namespace = data.get('namespace', 'fog-kube-system')
    platform_name = data['resource_id']
    deploy_api = '/api/v1/namespaces/{namespace}/replicationcontrollers'.format(namespace=namespace)
    con = http.client.HTTPConnection(settings.KUBE_API_DOMAIN)
    header = {"Content-type": "application/json"}
    body = {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": platform_name,
            "namespace": "kube-system"
        },
        "spec": {
            "replicas": 1,
            "selector": {"app": platform_name},
            "template": {
                "metadata": {
                    "name": platform_name,
                    "labels": {
                        "resource_type": "platform",
                        "app": platform_name,
                        "description": data['description'],
                        "namespace": namespace,
                        "label": data['label'],
                        # "regex": data['regex'],
                        "version": data['version']
                    },
                },
                "spec": {
                    "containers": [{
                        "name": platform_name,
                        "image": settings.IOT_PLATFORM[data['platform_type']]['image'],
                        "ports": [
                             {
                                 "containerPort": 8080
                             }
                         ],
                        "volumeMounts": [
                            {
                                "name": settings.IOT_PLATFORM[data['platform_type']]['config']['name'],
                                "mountPath": settings.IOT_PLATFORM[data['platform_type']]['config']['mountPath'],
                                "subPath": settings.IOT_PLATFORM[data['platform_type']]['config']['subPath']
                            },
                            {
                                "name": settings.IOT_PLATFORM[data['platform_type']]['item']['name'],
                                "mountPath": settings.IOT_PLATFORM[data['platform_type']]['item']['mountPath'],
                                "subPath": settings.IOT_PLATFORM[data['platform_type']]['item']['subPath']
                            }
                        ]
                    }],
                    "volumes": [{
                        "name": settings.IOT_PLATFORM[data['platform_type']]['config']['name'],
                        "configMap": {
                            "name": settings.IOT_PLATFORM[data['platform_type']]['config_configmap']['name']+'-'+data['resource_id'],
                            "items": [
                            {
                                "key": settings.IOT_PLATFORM[data['platform_type']]['config_configmap']['key'],
                                "path": settings.IOT_PLATFORM[data['platform_type']]['config_configmap']['path']
                            }]
                        }
                    }, {
                        "name": settings.IOT_PLATFORM[data['platform_type']]['item']['name'],
                        "configMap": {
                            "name": settings.IOT_PLATFORM[data['platform_type']]['item_configmap']['name']+'-'+data['resource_id'],
                            "items": [
                            {
                                "key": settings.IOT_PLATFORM[data['platform_type']]['item_configmap']['key'],
                                "path": settings.IOT_PLATFORM[data['platform_type']]['item_configmap']['path']
                            }]
                        }
                    }],
                    "restartPolicy": "Always"
                }
            }
        }
    }
    # print(json.dumps(body))
    con.request('POST', deploy_api, json.dumps(body).encode('utf-8'), header)
    response = con.getresponse()
    print(response.getcode())
    raw = response.read().decode()
    return raw


def deploy_sensor(**data):
    # deploy config first
    deploy_configmap(resource_type='sensor', is_item=True, is_config=True, **data)
    #
    namespace = data.get('namespace', 'fog-kube-system')
    sensor_name = data['resource_id']
    deploy_api = '/api/v1/namespaces/{namespace}/replicationcontrollers'.format(namespace=namespace)
    con = http.client.HTTPConnection(settings.KUBE_API_DOMAIN)
    header = {"Content-type": "application/json"}
    body = {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": sensor_name,
            "namespace": "kube-system"
        },
        "spec": {
            "replicas": 1,
            "selector": {"app": sensor_name},
            "template": {
                "metadata": {
                    "name": sensor_name,
                    "labels": {
                        "app": sensor_name,
                        "description": data['description'],
                        "namespace": namespace,
                        "label": data['label'],
                        # "regex": data['regex'],
                        "version": data['version'],
                        "sensor_type": data['sensor_type'],
                        "manufacturer": data['manufacturer'],
                        "resource_type": "sensor",
                    },
                },
                "spec": {
                    "containers": [{
                        "name": sensor_name,
                        "image": settings.SENSOR['image'],
                        "volumeMounts": [
                            {
                                "name": settings.SENSOR['config']['name'],
                                "mountPath": settings.SENSOR['config']['mountPath'],
                                "subPath": settings.SENSOR['config']['subPath']
                            },
                            {
                                "name": settings.SENSOR['item']['name'],
                                "mountPath": settings.SENSOR['item']['mountPath'],
                                "subPath": settings.SENSOR['item']['subPath']
                            }
                        ]
                    }],
                    "volumes": [{
                        "name": settings.SENSOR['config']['name'],
                        "configMap": {
                            "name": settings.SENSOR['config_configmap']['name']+'-'+data['resource_id'],
                            "items": [
                                {
                                    "key": settings.SENSOR['config_configmap']['key'],
                                    "path": settings.SENSOR['config_configmap']['path']
                                }]
                        }
                    }, {
                        "name": settings.SENSOR['item']['name'],
                        "configMap": {
                            "name": settings.SENSOR['item_configmap']['name']+'-'+data['resource_id'],
                            "items": [
                                {
                                    "key": settings.SENSOR['item_configmap']['key'],
                                    "path": settings.SENSOR['item_configmap']['path']
                                }]
                        }
                    }],
                    "restartPolicy": "Always"
                }
            }
        }
    }
    con.request('POST', deploy_api, json.dumps(body).encode('utf-8'), header)
    response = con.getresponse()
    raw = response.read().decode()
    return raw


def delete_resource(resource_id, namespace='kube-system', resource_type=kubernetes_tmpl.REPLICATION_RESOURCE, kube_api=settings.KUBE_API_DOMAIN):
    # /api/v1/namespaces/kube-system/replicationcontrollers/openhab-platform
    uri_api = '/api/v1/namespaces/{namespace}/{resource_type}/{resource_id}'.format(namespace=namespace,
                                                                                    resource_id=resource_id,
                                                                                    resource_type=resource_type)
    con = http.client.HTTPConnection(kube_api)
    header = {"Content-type": "application/json"}
    con.request('DELETE', uri_api, '', header)
    response = con.getresponse()
    raw = response.read().decode()
    return raw


def delete_resource_by_label(label_key, label_val, namespace='kube-system', resource_type=kubernetes_tmpl.REPLICATION_RESOURCE, kube_api=settings.KUBE_API_DOMAIN):
    uri_api = '/api/v1/namespaces/{namespace}/{resource_type}/?labelSelector={label}'.format(namespace=namespace,
                                                                                    resource_type=resource_type,
                                                                                    label='{}%3D{}'.format(label_key, label_val))
    con = http.client.HTTPConnection(kube_api)
    header = {"Content-type": "application/json"}
    con.request('DELETE', uri_api, '', header)
    response = con.getresponse()
    raw = response.read().decode()
    return raw

def deploy_configmap(resource_type, is_item=True, is_config=True, **resource):
    gen = gen_configmap(resource_type=resource_type, **resource)
    if is_item:
        print('--------------- Deploy item')
        if resource_type == 'sensor':
            data = {'key': gen['item_key'], 'value': gen['item'], 'namespace': resource['namespace'],
                    'config_name': settings.SENSOR['item_configmap']['name'] + '-' +
                                   resource['resource_id']}
        elif resource_type == 'platform':
            data = {'key': gen['item_key'], 'value': gen['item'], 'namespace': resource['namespace'],
                    'config_name': settings.IOT_PLATFORM[resource['platform_type']]['item_configmap']['name'] + '-' + resource['resource_id']}
        print(deploy_configmap_item(**data))
    if is_config:
        print('--------------- Deploy config')
        if resource_type == 'sensor':
            data = {'key': gen['config_key'], 'value': gen['config'], 'namespace': resource['namespace'],
                    'config_name': settings.SENSOR['config_configmap']['name'] + '-' +
                                   resource['resource_id']}
        elif resource_type == 'platform':
            data = {'key': gen['config_key'], 'value': gen['config'], 'namespace': resource['namespace'],
                    'config_name': settings.IOT_PLATFORM[resource['platform_type']]['config_configmap']['name'] + '-' +
                                   resource['resource_id']}
        print(deploy_configmap_item(**data))


def deploy_configmap_item(**data):
    print('--------------------------')
    key = data['key']
    value = data['value']
    namespace = data['namespace']
    config_name = data['config_name']
    body = {
        "kind": "ConfigMap",
        "apiVersion": "v1",
        "metadata": {
            "name": config_name,
            "namespace": namespace
        },
        "data": {
            key: value
        }
    }
    deploy_api = '/api/v1/namespaces/{namespace}/configmaps'.format(namespace=namespace)
    kube_api = settings.KUBE_API_DOMAIN
    if data.get('kube_api'):
        kube_api = data.get('kube_api')
    con = http.client.HTTPConnection(kube_api)
    header = {"Content-type": "application/json"}
    con.request('POST', deploy_api, json.dumps(body).encode('utf-8'), header)
    response = con.getresponse()
    raw = response.read().decode()
    return raw


def gen_configmap(resource_type, platform_type='onem2m', **resource_data):
    if resource_type == 'sensor':
        key_config = kubernetes_tmpl.SENSOR_CONFIG_KEY
        key_item = kubernetes_tmpl.SENSOR_ITEM_KEY
        config = kubernetes_tmpl.SENSOR_CONFIG.replace('/broker_client_name/', resource_data['resource_id'])
        item = str(kubernetes_tmpl.SENSOR_ITEM[resource_data['description']])
        item = item.format(id=resource_data['resource_id'], freq='10', namespace=resource_data['namespace'], version='v01')
    elif resource_type == 'platform':
        if platform_type == "onem2m":
            key_config = kubernetes_tmpl.ONEM2M_CONFIG_KEY
            key_item = kubernetes_tmpl.ONEM2M_ITEM_KEY
            config = kubernetes_tmpl.ONEM2M_CONFIG
            config['clientId'] = resource_data['resource_id']
            item = kubernetes_tmpl.ONEM2M_ITEM
        else:
            key_config = kubernetes_tmpl.OPENHAB_CONFIG_KEY
            key_item = kubernetes_tmpl.OPENHAB_ITEM_KEY
            config = kubernetes_tmpl.OPENHAB_CONFIG.replace("/mqttIn.clientId/", resource_data['resource_id'])
            item = kubernetes_tmpl.OPENHAB_ITEM.replace("/sensor_id/", "demo")
    return {'config': str(config), 'item': str(item), 'config_key': key_config, 'item_key': key_item}


def assign_sensor_to_platform(sensor_id, platform_id, namespace='kube-system', platform_type='onem2m'):
    # delete old item
    item_uid = settings.IOT_PLATFORM[platform_type]['item_configmap']['name'] + '-' + platform_id
    print('Delete old item')
    print(delete_resource(item_uid, namespace=namespace,
                                            resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE))
    print('Delete old item for cloud sensing')
    print(delete_resource(kubernetes_tmpl.CLOUD_SENSING_ITEM_CONFIG, namespace=kubernetes_tmpl.CLOUD_NAMESPACE,
                          resource_type=kubernetes_tmpl.CONFIG_MAP_RESOURCE, kube_api=settings.CLOUD_KUBE_API_DOMAIN))

    # create new item
    key = ''
    if platform_type == 'openhab':
        item = kubernetes_tmpl.OPENHAB_ITEM.replace("/sensor_id/", sensor_id)
        key = 'demo.items'
    else:
        item = kubernetes_tmpl.ONEM2M_ITEM.replace("test", sensor_id)
        key = 'items.cfg'
    data = {'key': key, 'value': item, 'namespace': namespace, 'config_name': item_uid, 'kube_api': settings.KUBE_API_DOMAIN}
    print('Create new item')
    print(deploy_configmap_item(**data))

    print('Create new item for cloud sensing')
    item = kubernetes_tmpl.CLOUD_SENSING_ITEM.replace("/sensor_id/", sensor_id)
    data = {'key': kubernetes_tmpl.CLOUD_SENSING_ITEM_KEY, 'value': item, 'namespace': kubernetes_tmpl.CLOUD_NAMESPACE, 'config_name': kubernetes_tmpl.CLOUD_SENSING_ITEM_CONFIG, 'kube_api': settings.CLOUD_KUBE_API_DOMAIN}
    print(deploy_configmap_item(**data))

    # reset pod
    print('Reset platform pod')
    print(delete_resource_by_label(label_key='app', label_val=platform_id, namespace=namespace, resource_type=kubernetes_tmpl.POD_RESOURCE, kube_api=settings.CLOUD_KUBE_API_DOMAIN))

    print('Reset cloud sensing pod')
    print(delete_resource_by_label(label_key='app', label_val=kubernetes_tmpl.CLOUD_SENSING_ID, namespace=kubernetes_tmpl.CLOUD_NAMESPACE,
                                   resource_type=kubernetes_tmpl.POD_RESOURCE, kube_api=settings.CLOUD_KUBE_API_DOMAIN))