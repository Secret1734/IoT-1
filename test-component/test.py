import csv
import os
# list_uri = dict()
# with open('/home/huanpc/linkchecker-out.csv') as csvfile:
#     csvreader = csv.DictReader(csvfile, delimiter=';')
#     for index, row in enumerate(csvreader):
#         if row['result'] != '404 Not Found':
#             continue
#         if str(row['urlname']).find('https://test.onfta.com/ow_userfiles/plugins') < 0:
#             continue
#         if not list_uri.get(row['urlname']):
#             list_uri[row['urlname']] = row['parentname'] + ';'+ row['result']
#
# with open('/home/huanpc/filter_link.csv', 'w') as f:
#     for k, v in list_uri.items():
#         f.write('{};{}\n\n'.format(k, v))
from influxdb import InfluxDBClient
client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')

time_min = '2017-04-10 18:35:00'
time_max = '2017-04-11 00:35:00'

def _mem_query(_namespace, _container_name):
    return 'SELECT * FROM "memory/usage" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + \
           _namespace+'\' AND "container_name"=\''+_container_name+'\' ;'

def _cpu_query(_namespace, _container_name):
    return 'SELECT * FROM "cpu/usage_rate" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + \
           _namespace+'\' AND "container_name"=\''+_container_name+'\' ;'

def _net_query(_namespace, _container_name):
    return 'SELECT * FROM "network/rx_rate" WHERE "type" = \'pod\' AND "namespace_name" = \''+\
           _namespace+'\' AND "labels"=\'app:'+_container_name+'\';'

def query_and_write_file(platform='onem2m-1'):
    result = client.query(_net_query('kube-system', platform))
    for k, v in result.items():
        file_path = 'lynq/{}/{}'.format(platform, 'network_receive.csv')
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, 'w') as csvfile:
            _list = list(v)
            field_names = dict(_list[0]).keys()
            writer = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=',', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for item in _list:
                writer.writerow(item)

for item in ['onem2m-1', 'onem2m-2', 'onem2m-3', 'openhab-2', 'openhab-3', 'openhab-1', 'onem2m-4', 'onem2m-5']:
    query_and_write_file(item)