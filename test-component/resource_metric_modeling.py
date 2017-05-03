from influxdb import InfluxDBClient

client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')


"""
{
	"('memory / usage', None)":
	[{
		'time': '2017-04-03T07:00:00Z',
		'host_id': '128.199.91.17',
		'namespace_id': '1a480b89-10a1-11e7-8989-7eb92be1eeb0',
		'container_base_image': 'huanphan/onem2m:1.0',
		'labels': 'app:onem2m-1',
		'pod_name': 'onem2m-1-z8zn2',
		'type': 'pod_container',
		'value': 8368128,
		'nodename': '128.199.91.17',
		'pod_namespace': 'kube-system',
		'container_name': 'onem2m-1',
		'pod_id': 'eff777e6-10a7-11e7-8989-7eb92be1eeb0',
		'hostname': '128.199.91.17',
		'namespace_name': 'kube-system'
	}, {
		'time': '2017-04-03T07:00:00Z',
		'host_id': '128.199.91.17',
		'namespace_id': '1a480b89-10a1-11e7-8989-7eb92be1eeb0',
		'container_base_image': 'huanphan/onem2m:1.0',
		'labels': 'app:onem2m-1',
		'pod_name': 'onem2m-1-dm6mk',
		'type': 'pod_container',
		'value': 235900928,
		'nodename': '128.199.91.17',
		'pod_namespace': 'kube-system',
		'container_name': 'onem2m-1',
		'pod_id': '8cac43ee-1819-11e7-8989-7eb92be1eeb0',
		'hostname': '128.199.91.17',
		'namespace_name': 'kube-system'
	}]
}
"""
"""
<DataModel>
	<Id>32534534534</Id>
	<Timestamp>149342332</Timestamp>
	<Metric>
		<MetricName>Memory usage</MetricName>
		<Units>
			<Data>Bytes</Data>
		</Units>
		<MetricType>Gauge</MetricType>
		<DataPoint>
			<DataType>Integer</DataType>
			<DataFrequency>10</DataFrequency>
			<Value>102400</Value>
		</DataPoint>
	</Metric>
	<Resource>
		<ResourceId>openhab_542425</ResourceId>
		<Endpoint>http://192.168.30.44:8300/metrics/ram_usage</Endpoint>
		<State>active</State>
		<Description>IoT Platform memory usage</Description>
		<PlatformName>OpenHAB_IoT_LAB_1</PlatformName>
		<PlatformType>OpenHAB</PlatformType>
		<Version>0.8</Version>
		<Regex>mem_usage: ([0-9]+)%</Regex>
	</Resource>
</DataModel>
"""


def _cpu_query(_namespace, _time_min, _time_max):
    return 'SELECT * FROM "cpu/usage_rate" WHERE "type" = \'pod_container\' AND "namespace_name" = \''+_namespace+'\' AND time >' + \
           _time_min + ' AND time < ' + _time_max + ' ;'

def _mem_query(_namespace, _time_min, _time_max):
    return 'SELECT * FROM "memory/usage" WHERE "type" = \'pod_container\' AND "namespace_name" = \''+_namespace+'\' AND time >\'' + \
           _time_min + '\' AND time < \'' + _time_max + '\' ;'

def _net_query(_namespace, _time_min, _time_max):
    return 'SELECT * FROM "network/tx_rate" WHERE "type" = \'pod\' AND "namespace_name" = \''+_namespace+'\' AND time >' + \
           _time_min + ' AND time < ' + _time_max + ' ;'

def query(_query):
    _list_output = []
    _result = client.query(_query)
    for item in list(_result.get_points()):
        # get label dict
        labels_dict = dict()
        if not item.get('labels'):
            continue
        if str(item['labels']).find(',') > -1:
            labels = str(item['labels']).split(',')
            for label in labels:
                if label.find(':') > -1:
                    labels_dict[label.split(':')[0]] = label.split(':')[1]
        else:

            if str(item['labels']).find(':') > -1:
                labels_dict[item['labels'].split(':')[0]] = item['labels'].split(':')[1]
        output = dict(item)
        output['labels'] = labels_dict
        _list_output.append(output)
    return _list_output

def transform_to_model(_metric_name, _metric_units, _data_type, data_input=dict()):
    try:
        model = {
            "measurement": "data_collect_rate",
            "tags": {
                'Metric_MetricName': _metric_name,
                'Metric_Units': _metric_units,
                'Metric_DataPoint_DataType': _data_type,
                'Metric_DataPoint_DataFrequency': '10',
                'Resource_ResourceId': data_input['pod_name'],
                'Resource_Namespace': data_input['namespace_name'],
                'Resource_Endpoint': 'http://{hostname}/{pod_name}/{metric_name}'.format(
                    hostname=data_input['hostname'],
                    pod_name=data_input['pod_name'],
                    metric_name=_metric_name),
                'Resource_State': 'activate',
                'Resource_Description': '{container_base_image}, '
                                        '{container_name}'.format(
                    container_base_image=data_input.get('container_base_image', 'Null'),
                    container_name=data_input.get('container_name', 'Null')),
                'Resource_Tag': data_input['labels'].get('k8s-app', 'k8s-cluster'),
                'Resource_Version': data_input['labels'].get('version', 'v1'),
                'Resource_Regex': '{metric}: ([0-9]+)%'.format(metric=_metric_name)
            },
            "fields": {
                "num_of_message": 1,
                "value": float(data_input['value']),
            }
        }
        if data_input['labels'].get('type', '') == 'platform':
            model['tags'].update({
                'Resource_Description': data_input['labels']['description'],
                'Resource_Version': data_input['labels']['version'],
                'Resource_PlatformName': data_input['labels']['name'],
                'Resource_PlatformType': data_input['labels']['name']})
    except Exception as e:
        print(e)
        model = {}
    return [model]

def write_point(point):
    client.write_points(point)
    print('Publish message')

def run():
    time_min = '2017-04-30 18:50:00'
    time_max = '2017-04-30 18:56:00'
    name_space = 'kube-system'
    items = query(_mem_query(name_space, time_min, time_max))
    for item in items:
        if item['container_name'] == 'onem2m-4':
            print(item)
            print(transform_to_model('memory_usage', 'Data_Byte', 'Long', item))
    # for item in query(_mem_query(name_space, time_min, time_max)):
    #     print(transform_to_model('memory_usage', 'Data_Byte', 'Long', item))
    # while True:
    #     print('Time: {}'.format(time_min))
    #     # memory usage
    #     [write_point(transform_to_model('memory_usage', 'Data_Byte', 'Long', item)) for item in
    #             query(_mem_query(name_space, time_min, time_max))]
    #     # cpu usage
    #     [write_point(transform_to_model('cpu_usage_rate', 'Statistic_Percentile', 'Float', item)) for item in
    #             query(_cpu_query(name_space, time_min, time_max))]
    #     # loop transform to model
    #     # network usage
    #     [write_point(transform_to_model('network_send_usage', 'Data Rate_bpm', 'Float', item)) for item in
    #             query(_net_query(name_space, time_min, time_max))]
    #     # loop transform to model
    #     # write_to_db
    #     time_min = str(int(time_min[:len(time_min) - 1]) + 60) + 's'
    #     time_max = str(int(time_min[:len(time_max) - 1]) + 60) + 's'

run()