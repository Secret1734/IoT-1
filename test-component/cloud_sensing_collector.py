#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import re
import xml.etree.ElementTree as ET
import time
import json
import subprocess

# db_client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')
db_client = InfluxDBClient('monitoring-influxdb', 8086, 'root', 'root', 'k8s')
CONFIG_PATH = ''
ITEM_PATH = 'items.cfg'


def adaptor_convert_message(message):
    """
    Convert message (xml, json) to one-type message
    :param message:
    :return:
    """
    adapted_message = dict()
    try:
        # xml message type
        """
        <DataModel>
            <Timestamp>149342354</Timestamp>
            <Sensor>
                <num_of_sensor>4</num_of_sensor>
                <Timestamp>149342354</Timestamp>
                <Metric>
                    <MetricName>CPU usage rate</MetricName>
                    <Units>
                        <Statistic>Percentage</Statistic>
                    </Units>
                    <MetricType>Gauge</MetricType>
                    <DataPoint>
                        <DataType>Float</DataType>
                        <DataFrequency>10</DataFrequency>
                        <Value>0.8</Value>
                    </DataPoint>
                </Metric>
                <ResourceId>sensor_air_mesurement_3243</ResourceId>
                <SensorType>Air Humidiry</SensorType>
                <Manufacturer>Panasonic</Manufacturer>
                <Description>Air humidity mesurement</Description>
                "Label": "task:light_meter",
                        "ResourceType": "sensor",
                        "Version": "v2.05",
                        "Namespace": "IOT_LAB_1",
            </Sensor>
            <Resource>
                <Endpoint>http://192.168.55.43:8300/device/values</Endpoint>
                <State>active</State>
                <PlatformListener>onem2m_34234</PlatformListener>
                <Regex>value: ([0-9]+)%</Regex>
            </Resource>
        </DataModel>
        """
        root = ET.fromstring(message)
        adapted_message['timestamp_platform'] = float(root.find('./Timestamp').text)
        adapted_message['timestamp_platform_process'] = float(root.find('./Timestamp_2').text)
        adapted_message['timestamp_sensor'] = float(root.find('./Sensor/Timestamp').text)
        metric_node = root.find('./Sensor/Metric')
        adapted_message['num_of_sensor'] = int(root.find('./Sensor/num_of_sensor').text)
        adapted_message['Metric'] = {
            'MetricName': metric_node.find('./MetricName').text,
            'Units': {item.tag: item.text for item in metric_node.find('./Units')},
            'MetricType': metric_node.find('./MetricType').text,
            'DataPoint': {'DataType': metric_node.find('./DataPoint/DataType').text,
                          'DataFrequency': float(metric_node.find('./DataPoint/DataFrequency').text),
                          'Value': float(metric_node.find('./DataPoint/Value').text)}
        }
        adapted_message['Resource'] = {
               'Description': root.find('./Sensor/Description').text,
               'SensorType': root.find('./Sensor/SensorType').text,
               'Manufacturer': root.find('./Sensor/Manufacturer').text,
               'ResourceId': root.find('./Sensor/ResourceId').text,
               'Label': root.find('./Sensor/Label').text,
               'ResourceType': root.find('./Sensor/ResourceType').text,
               'Version': root.find('./Sensor/Version').text,
               'Namespace': root.find('./Sensor/Namespace').text,
        }
        adapted_message['Resource'].update({item.tag: item.text for item in root.find('./Resource')})
    except :
        """
        {   "Timestamp": 3432432,
                    "Sensor": {
                        "num_of_sensor": 4,
                        "Timestamp": 234234234,
                        "Metric": {
                            "MetricName": "[sensor]", "Units": {"Statistic": "Percentage"}
                            , "MetricType": "Gauge"
                            , "DataPoint": {
                                "DataType": "Float",
                                "DataFrequency": "2",
                                "Value": "143"
                            }
                        },
                        "Description": "[sensor]",
                        "SensorType": "[sensor]",
                        "Manufacturer": "Panasonic",
                        "ResourceId": "[sensor_id]",
                        "Label": "task:light_meter",
                        "ResourceType": "sensor",
                        "Version": "v2.05",
                        "Namespace": "IOT_LAB_1",
                    }
                    ,
                    "Resource": {
                        "Endpoint": "[host]/demo/[item_name]",
                        "State": "active",
                        "PlatformListener": "[plafform_host]",
                        "Regex": "(.*)"
                    }
                }
        """
        print('------------------')
        json_data = dict(json.loads(message))
        adapted_message['timestamp_platform'] = json_data['Timestamp']
        adapted_message['timestamp_sensor'] = json_data['Sensor']['Timestamp']
        adapted_message['Metric'] = json_data['Sensor']['Metric']
        adapted_message['num_of_sensor'] = int(json_data['Sensor']['num_of_sensor'])
        adapted_message['Resource'] = {'Endpoint': json_data['Resource']['Endpoint'],
                                       'State': json_data['Resource']['State'],
                                       'PlatformListener': json_data['Resource']['PlatformListener'],
                                       'Regex': json_data['Resource']['Regex'],
                                       'Description': json_data['Sensor']['Description'],
                                       'SensorType': json_data['Sensor']['SensorType'],
                                       'Manufacturer': json_data['Sensor']['Manufacturer'],
                                       'ResourceId': json_data['Sensor']['ResourceId'],
                                       'Namespace': json_data['Sensor']['Namespace'],
                                       'Version': json_data['Sensor']['Version'],
                                       'ResourceType': json_data['Sensor']['ResourceType'],
                                       'Label': json_data['Sensor']['Label'],
                                       }

    return adapted_message


def create_message(data_payload, topic, time_received):
    # proc = subprocess.Popen(['curl "http://www.just-the-time.appspot.com/?f=%s.%f"'], stdout=subprocess.PIPE,
    #                         shell=True)
    # (out, err) = proc.communicate()
    # timenow = float(out.decode())
    timenow = float(time.time())
    round_trip_1 = float(data_payload['timestamp_platform']) - float(data_payload['timestamp_sensor'])
    round_trip_2 = timenow - float(data_payload['timestamp_platform'])
    round_trip_3 = round_trip_1 + round_trip_2
    metric_unit_key = list(dict(data_payload['Metric']['Units']).keys())[0]
    metric_unit_val = dict(data_payload['Metric']['Units'])[metric_unit_key]
    json_body = [
        {
            "measurement": "data_collect_rate",
            "tags": {
                "topic_id": str(topic),
                "num_of_sensor": data_payload['num_of_sensor'],
                "Metric_MetricName": data_payload['Metric']['MetricName'],
                "Metric_Units": '{}_{}'.format(metric_unit_key, metric_unit_val),
                "Metric_MetricType": data_payload['Metric']['MetricType'],
                "Metric_DataPoint_DataType": data_payload['Metric']['DataPoint']['DataType'],
                "Metric_DataPoint_DataFrequency": data_payload['Metric']['DataPoint']['DataFrequency'],
                "Resource_ResourceId": data_payload['Resource']['ResourceId'],
                "Resource_Endpoint": data_payload['Resource']['Endpoint'],
                "Resource_State": data_payload['Resource']['State'],
                "Resource_Description": data_payload['Resource']['Description'],
                "Resource_SensorType": data_payload['Resource']['SensorType'],
                "Resource_Manufacturer": data_payload['Resource']['Manufacturer'],
                "Resource_PlatformListener": data_payload['Resource']['PlatformListener'],
                "Resource_Regex": data_payload['Resource']['Regex'],
                "Resource_Type": data_payload['Resource']['ResourceType'],
                "Namespace": data_payload['Resource']['Namespace'],
                "Version": data_payload['Resource']['Version'],
                "Label": data_payload['Resource']['Label'],
            },
            "fields": {
                "num_of_message": 1,
                "value": float(data_payload['Metric']['DataPoint']['Value']),
                "round_trip_1": round_trip_1,
                "round_trip_2": round_trip_2,
                "round_trip_3": round_trip_3,
                "timestamp_platform": float(data_payload['timestamp_platform']),
                "timestamp_sensor": float(data_payload['timestamp_sensor']),
                "timestamp_platform_process": float(data_payload['timestamp_platform_process']),
                "timestamp_cloud_process": (timenow - time_received),
            }
        }
    ]
    return json_body


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    items = [(line.rstrip('\n'), 1) for line in open(ITEM_PATH)]
    client.subscribe(items)
    # client.subscribe([('onem2m_pf_1/temperature', 0), ('onem2m_pf_2/temperature', 0), ('onem2m_pf_3/temperature', 0), ('onem2m_pf_4/temperature', 0), ('onem2m_pf_5/temperature', 0)])


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = re.sub('\s+', ' ', str(msg.payload.decode("utf-8")).strip())
    # print(payload)
    print('Public message from topic {}'.format(msg.topic))

    message = create_message(adaptor_convert_message(payload), str(msg.topic), time.time())
    db_client.write_points(message)
    # print(message)



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# client.connect("188.166.238.158", 30146, 60)
client.connect("mqtt-service", 1883, 60)
# client.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

# db_client.write_points(create_message(adaptor_convert_message(''), 'topic_1'))
# print(adaptor_convert_message(''))
