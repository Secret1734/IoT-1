import json
import dicttoxml
from influxdb import InfluxDBClient
import xml.dom.minidom
client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')

time_min = '2017-05-06 17:27:30'
time_max = '2017-05-06 17:28:00'


def build_query(_time_min, _time_max):
    return 'SELECT * FROM "data_collect_rate" WHERE time >\'' + \
           _time_min + '\' AND time < \'' + _time_max + '\' ;'

def execute_query():
    _result = client.query(build_query(time_min, time_max), epoch='s')
    return list(_result.get_points())

def write_file(data, file_name):
    with open(file_name, "w+") as myfile:
        myfile.write(data)

def translate_result_to_model(is_load_from_file=False):
    """

    :return:
    """
    if not is_load_from_file:
        list_data = execute_query()
        for item in list_data:
            data_dict = dict(item)
            print(build_heir_xml(data_dict=data_dict))
            # for k, v in data_dict.items():
            #     if str(v) != 'None':
            #         pretty_view[k] = v
            # temp = dict()
            # for k, v in pretty_view.items():
            #     if k == 'num_of_message':
            #         k = 'NumOfMessage'
            #     build_level_dict(k, v, temp)
            # print(temp)
    else:
        with open('query_controller') as f:
            content = f.readlines()
            content = ' '.join(content)
        series = json.loads(content)
        for item in series:
            data_dict = dict(item)
            xml_doc = xml.dom.minidom.parseString(build_heir_xml(data_dict=data_dict))
            print(xml_doc.toprettyxml())

def build_heir_xml(data_dict):
    pretty_view = {'Resource': {}, 'Metric': {'DataPoint': {}, 'Units': {}}, 'Timestamp': '', 'Id': ''}
    for k, v in data_dict.items():
        if k == 'value':
            pretty_view['Metric']['DataPoint']['Value'] = v
        if str(k).find('Resource') > -1:
            pretty_view['Resource'][str(k)[len('Resource')+1:]] = v
        if str(k).find('Metric') > -1:
            if str(k).find('Units') > -1:
                tmp = str(v).split('_')
                pretty_view['Metric']['Units'][tmp[0]] = tmp[1]
            elif str(k).find('DataPoint') > -1:
                pretty_view['Metric']['DataPoint'][str(str(k)[len('Metric_DataPoint')+1:])] = v
            else:
                pretty_view['Metric'][str(k)[len('Metric')+1:]] = v
        if k == 'time':
            pretty_view['Timestamp'] = v
            pretty_view['Id'] = v
    print(pretty_view)
    return str(dicttoxml.dicttoxml(pretty_view, attr_type=False, custom_root='DataModel').decode())

def build_level_dict(key, value, dict_data):
    if str(key).find('_') == -1:
        dict_data[key] = value
        return dict_data
    else:
        level = str(key).split('_')
        dict_data[level[0]] = build_level_dict(str(key)[len(level[0]):], value, {})
        return dict_data

# def build_level_dict_2(data_dict=dict()):
#     item = data_dict.popitem()
#     if len(data_dict) == 0:
#
#     for k, v in data_dict.items():


translate_result_to_model(is_load_from_file=True)
# client.query("DROP MEASUREMENT \"data_collect_rate\"")