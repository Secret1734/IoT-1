from rest_framework import viewsets
from iot_platform.models import PlatformModel
from iot_platform.serializers import PlatformSerializer
from django.http import HttpResponse
import json
import dicttoxml
from influxdb import InfluxDBClient
import xml.dom.minidom

class PlatformViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows platforms to be viewed or edited.
    """
    queryset = PlatformModel.objects.all()
    serializer_class = PlatformSerializer

def ajax_get_xml(request, time_stamp):
    result = translate_result_to_model(time_stamp, str(int(time_stamp)+3600*12))
    # message = [{'content': xml_content}, {'content': xml_content}]
    content = json.dumps(result)
    return HttpResponse(content, content_type="application/json")

def translate_result_to_model(time_min, time_max):
    list_data = execute_query(time_min=time_min, time_max=time_max)
    list_result = []
    for item in list_data:
        data_dict = dict(item)
        xml_doc = xml.dom.minidom.parseString(build_xml(data_dict=data_dict))
        list_result.append({'content': xml_doc.toprettyxml()})
    return list_result

def build_xml(data_dict):
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
    return str(dicttoxml.dicttoxml(pretty_view, attr_type=False, custom_root='DataModel').decode())

def build_query(_time_min, _time_max):
    return 'SELECT * FROM "data_collect_rate" WHERE time >' + \
           _time_min + 's AND time < ' + _time_max + 's ;'

def execute_query(time_min, time_max):
    client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')
    _result = client.query(build_query(time_min, time_max), epoch='s')
    return list(_result.get_points())