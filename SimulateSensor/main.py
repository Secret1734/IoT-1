# -*- coding: utf-8 -*-
import os
import sys, getopt
import paho.mqtt.client as mqtt
import random
import _thread
import time
import json
import socket
import http.client
import subprocess
import threading
HOST = '0.0.0.0'
PORT = 9090
# gb_freq = 0
CONFIG_PATH = 'config/config.cfg'
ITEMS_PATH = 'config/items.cfg'
MILISECOND = 0.001
TIME_FOR_GC = 5
INCREASE_STEP = 10
global gl_num_of_sensor
gl_num_of_sensor = INCREASE_STEP
# global pause_lock
# pause_lock = False

class Item(object):
    def __init__(self, init_data):
        self.mapping_dict_to_item(input_dict=init_data)

    def convert_string_to_item(self, string):
        # sensor_name, topic_in,topic_out,frequent
        tokens = str(string).split(',')
        self._sensor_name = tokens[1]
        self._topic = tokens[2]
        self._frequent = int(tokens[3])

    def mapping_dict_to_item(self, input_dict):
        # name = SENSYS
        # Atmosphere
        # Sensor, topic = onem2m_pf_7 / temperature, frequent = 10, type = IC, unit = Pressure:PSI, label = task:pressure_warning, namespace = IOT_LAB_2, version = v1
        # .3, resoure_type = sensor
        self._sensor_name = input_dict['name']
        self._topic = input_dict['topic']
        self._frequent = float(input_dict['frequent'])
        self._type = input_dict['type']
        self._unit = {str(input_dict['unit']).split(':')[0]: str(input_dict['unit']).split(':')[1]}
        self._label = input_dict['label']
        self._namespace = input_dict['namespace']
        self._version = input_dict['version']
        self._resoure_type = input_dict['resoure_type']

    def get_sensor_name(self):
        return self._sensor_name

    def get_topic(self):
        return self._topic

    def get_frequent(self):
        return self._frequent

    def get_unit(self):
        return self._unit

    def get_type(self):
        return self._type

    def increase_frequent(self):
        self._frequent += 10
        print(self._frequent)
        return self._frequent

    def get_label(self):
        return self._label

    def get_version(self):
        return self._version

    def get_namespace(self):
        return self._namespace

    def get_resource_type(self):
        return self._resoure_type

def on_disconnect(client, userdata, rc):
    client.reconnect()


class SensorThread (threading.Thread):
    def __init__(self, item, ip_broker, port_broker, is_increase_freq, test_time, host_ip, qos):
        threading.Thread.__init__(self)
        self._item = item
        self._mqtt_client = mqtt.Client(item._topic)
        self._mqtt_client.connect(ip_broker, int(port_broker), keepalive=900)
        self._mqtt_client.on_disconnect = on_disconnect
        self._is_increase_freq = is_increase_freq
        self._test_time = test_time
        self._host_ip = host_ip
        self._qos = qos

    def send_data(self):
        start_time = time.time()
        time_data_change_period = random.randint(60, 3600)
        time_data_change = time.time()
        data_value = random.randint(0, 100)
        print('Change data value. Period {} Value {}'.format(time_data_change_period, data_value))
        while 1:
            next_time = time.time()
            if next_time - time_data_change >= time_data_change_period:
                time_data_change = next_time
                time_data_change_period = random.randint(60, 3600)
                data_value = random.randint(0, 100)
                print('Change data value. Period {} Value {}'.format(time_data_change_period, data_value))

            """
            "Sensor": {
                        "num_of_sensor": 4,
                        "Timestamp": 234234234,
                        "Metric": {
                            "MetricName": "[sensor]",
                            "Units": {"Statistic": "Percentage"}
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
                        self._label = input_dict['label']
                self._namespace = input_dict['namespace']
                self._version = input_dict['version']
                self._resoure_type
                            }
            """
            data = dict()
            data['Metric'] = {
                "MetricName": self._item.get_sensor_name(),
                "Units": self._item.get_unit(),
                "MetricType": "Gauge",
                "DataPoint": {
                    "DataType": "Float",
                    "DataFrequency": self._item.get_frequent(),
                    "Value": data_value}
            }
            data['Description'] = self._item.get_sensor_name()
            # Temperature Sensor Diode, Transistor, IC
            data['SensorType'] = self._item.get_type()
            data['Manufacturer'] = "Panasonic"
            data['ResourceId'] = '{sensor_name}:{host_ip}'.format(sensor_name=self._item.get_sensor_name(), host_ip=self._host_ip)

            # proc = subprocess.Popen(['curl "http://www.just-the-time.appspot.com/?f=%s.%f"'], stdout=subprocess.PIPE,
            #                         shell=True)
            # (out, err) = proc.communicate()
            # delay = time.time() - tmp
            # data['Timestamp'] = str(float(out.decode())-float(delay))
            data['Timestamp'] = "{0:.6f}".format(time.time())
            global gl_num_of_sensor
            data['num_of_sensor'] = str(gl_num_of_sensor)
            data['Label'] = self._item.get_label()
            data['Version'] = self._item.get_version()
            data['Namespace'] = self._item.get_namespace()
            data['ResourceType'] = self._item.get_resource_type()
            message = json.dumps(data)
            self._mqtt_client.publish(topic=self._item.get_topic(), payload=message, qos=int(self._qos))
            print('Publish message to topic: {}'.format(self._item.get_topic()))
            time.sleep(60 / self._item.get_frequent())
            if self._is_increase_freq:
                if next_time - start_time >= self._test_time:
                    start_time = next_time
                    self._item.increase_frequent()

    def run(self):
        self.send_data()

class SimulatorEngine(object):
    _bStop = 1

    def __init__(self):
        # read config
        config = self.read_config_file(CONFIG_PATH)
        self._ip_broker = config['ip_broker']
        self._port_broker = config['port_broker']
        self._client_name = config['broker_client_name']
        self._qos = config['qos']
        self._num_of_sensor = 0
        if config['increase_freq'] and config['increase_freq'] == 'True':
            self._is_increase_freq = True
        else:
            self._is_increase_freq = False
        if config['increase_instance'] and config['increase_instance'] == 'True':
            self._is_increase_instance = True
        else:
            self._is_increase_instance = False
        self.test_time = float(config['test_time'])
        self._items = self.read_item_file(ITEMS_PATH)
        self._mqttc = mqtt.Client(self._client_name)
        self._mqttc.connect(self._ip_broker, int(self._port_broker), keepalive=900)
        self._host_ip = socket.gethostbyname(socket.gethostname())
        self._threads = []

    def read_config_file(self, file_path):
        _config = dict()
        for line in open(file_path):
            _line = line.rstrip('\n')
            tmp = _line.split('=')
            _config[tmp[0]] = tmp[1]
        return _config

    def read_item_file(self, file_path):
        _items = list()
        for line in open(file_path):
            _item = dict()
            _line = line.rstrip('\n')
            fields = _line.split(',')
            for field in fields:
                tmp = field.split('=')
                _item[tmp[0]] = tmp[1]
            _items.append(Item(_item))
        return _items

    # def send_data(self, item):
    #     start_time = time.time()
    #     time_data_change_period = random.randint(60, 3600)
    #     time_data_change = time.time()
    #     data_value = random.randint(0, 100)
    #     print('Change data value. Period {} Value {}'.format(time_data_change_period, data_value))
    #     while 1:
    #         next_time = time.time()
    #         if next_time - time_data_change >= time_data_change_period:
    #             time_data_change = next_time
    #             time_data_change_period = random.randint(60, 3600)
    #             data_value = random.randint(0, 100)
    #             print('Change data value. Period {} Value {}'.format(time_data_change_period, data_value))
    #
    #         """
    #         "Sensor": {
    #                     "num_of_sensor": 4,
    #                     "Timestamp": 234234234,
    #                     "Metric": {
    #                         "MetricName": "[sensor]",
    #                         "Units": {"Statistic": "Percentage"}
    #                         , "MetricType": "Gauge"
    #                         , "DataPoint": {
    #                             "DataType": "Float",
    #                             "DataFrequency": "2",
    #                             "Value": "143"
    #                         }
    #                     },
    #                     "Description": "[sensor]",
    #                     "SensorType": "[sensor]",
    #                     "Manufacturer": "Panasonic",
    #                     "ResourceId": "[sensor_id]",
    #                     self._label = input_dict['label']
    #             self._namespace = input_dict['namespace']
    #             self._version = input_dict['version']
    #             self._resoure_type
    #                         }
    #         """
    #         data = dict()
    #         data['Metric'] = {
    #             "MetricName": item.get_sensor_name(),
    #             "Units": item.get_unit(),
    #             "MetricType": "Gauge",
    #             "DataPoint": {
    #                 "DataType": "Float",
    #                 "DataFrequency": item.get_frequent(),
    #                 "Value": data_value}
    #         }
    #         data['Description'] = item.get_sensor_name()
    #         # Temperature Sensor Diode, Transistor, IC
    #         data['SensorType'] = item.get_type()
    #         data['Manufacturer'] = "Panasonic"
    #         data['ResourceId'] = '{sensor_name}:{host_ip}'.format(sensor_name=item.get_sensor_name(), host_ip=self._host_ip)
    #         tmp = time.time()
    #
    #         # proc = subprocess.Popen(['curl "http://www.just-the-time.appspot.com/?f=%s.%f"'], stdout=subprocess.PIPE,
    #         #                         shell=True)
    #         # (out, err) = proc.communicate()
    #         # delay = time.time() - tmp
    #         # data['Timestamp'] = str(float(out.decode())-float(delay))
    #         data['Timestamp'] = "{0:.3f}".format(time.time())
    #         data['num_of_sensor'] = str(self._num_of_sensor)
    #         data['Label'] = item.get_label()
    #         data['Version'] = item.get_version()
    #         data['Namespace'] = item.get_namespace()
    #         data['ResourceType'] = item.get_resource_type()
    #         message = json.dumps(data)
    #         self._mqttc.publish(topic=item.get_topic(), payload=message)
    #         print('Publish message to topic: {}'.format(item.get_topic()))
    #         time.sleep(60 / item.get_frequent())
    #         if self._is_increase_freq:
    #             if next_time - start_time >= self.test_time:
    #                 start_time = next_time
    #                 item.increase_frequent()

    # def register_sensor_with_ordinator(self):
    #     os.system(
    #         'sensor_detail="$(/bin/hostname -i),$(hostname)" && curl -F "sensor_detail=${sensor_detail}" -F "defined_file=@openhab/demo.items"  ${CO_ORDINATOR_DOMAIN}/sensor/define')

    def execute(self, num_of_item_start):
        try:
            for item in self._items[num_of_item_start:num_of_item_start+INCREASE_STEP]:
                # _thread.start_new_thread(self.send_data, (item,))
                time.sleep(1)
                sensor_thread = SensorThread(item=item, ip_broker=self._ip_broker, port_broker=self._port_broker,
                                             is_increase_freq=self._is_increase_freq,
                                             test_time=self.test_time, host_ip=self._host_ip, qos=self._qos)
                sensor_thread.start()
                self._threads.append(sensor_thread)
        except Exception as e:
            print(e)

    @property
    def is_increase_instance(self):
        return self._is_increase_instance

    @property
    def items(self):
        return self._items

    @property
    def mqttc(self):
        return self._mqttc

    @property
    def ip_broker(self):
        return self._ip_broker

    @property
    def port_broker(self):
        return self._port_broker


def main(argv):
    engine = SimulatorEngine()
    start_time = time.time()
    item_start = 0
    engine._num_of_sensor = INCREASE_STEP
    global gl_num_of_sensor
    global pause_lock
    gl_num_of_sensor = INCREASE_STEP
    engine.execute(item_start)
    while 1:
        if item_start+INCREASE_STEP*2 <= len(engine.items):
            next_time = time.time()
            if engine.is_increase_instance:
                if next_time - start_time >= engine.test_time:
                    # pause_lock = True
                    # print('Time for increase')
                    # time.sleep(TIME_FOR_GC)
                    start_time = next_time
                    item_start += INCREASE_STEP
                    # engine._num_of_sensor = item_start + INCREASE_STEP
                    gl_num_of_sensor = item_start + INCREASE_STEP
                    engine.execute(item_start)
                    # pause_lock = False



if __name__ == '__main__':
    main(sys.argv[1:])

