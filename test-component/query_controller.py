from influxdb import InfluxDBClient

client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')


def build_query(_time_min, _time_max):
    return 'SELECT * FROM "data_collect_rate" WHERE time >\'' + \
           _time_min + '\' AND time < \'' + _time_max + '\' ;'

def execute_query():
    _result = client.query(build_query('2017-04-15 02:00:00', '2017-04-15 06:00:00'))
    return list(_result.get_points())

def translate_result_to_model():
    """

    :return:
    """

    for item in execute_query():
        pretty_view = dict()
        data_dict = dict(item)
        for k, v in data_dict.items():
            if str(v) != 'None':
                pretty_view[k] = v
        temp = dict()
        for k, v in pretty_view.items():
            if k == 'num_of_message':
                k = 'NumOfMessage'
            build_level_dict(k, v, temp)
        print(temp)


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


# translate_result_to_model()
# client.query("DROP MEASUREMENT \"data_collect_rate\"")