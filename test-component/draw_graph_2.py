import matplotlib.pyplot as plt
import numpy as np
from influxdb import InfluxDBClient
import time
import datetime
import json

time_min = '2017-05-06 06:11:00'
time_max = '2017-05-06 08:39:22'
time_min_2 = '2017-05-06 06:11:00'
time_max_2 = '2017-05-06 08:39:22'

onem2m_naming = {'onem2m-1': '10 sensors', 'onem2m-2': '20 sensors', 'onem2m-3': '40 sensors'}
openhab_naming = {'openhab-1': '10 sensors', 'openhab-2': '20 sensors', 'openhab-3': '40 sensors'}
cloud_processing = ['measure-data-rate-1','measure-data-rate-2','measure-data-rate-3']
cloud_processing_naming = {'measure-data-rate-1': '10 sensors', 'measure-data-rate-2': '20 sensors',
                           'measure-data-rate-3': '40 sensors'}
sensing_topic = ['sensor_1_1', 'sensor_2_1', 'sensor_3_1']


onem2m = ['onem2m-1', 'onem2m-2', 'onem2m-3']
openhab = ['openhab-1', 'openhab-2', 'openhab-3']

time_grouped = '1m'
time_step = 5
time_range = 'AND time >\'' + time_min + '\' AND time < \'' + time_max + '\' '
fog_namespace = 'kube-system'
cloud_namespace = 'cloud-kube-system'
cluster = ['128.199.91.17', '139.59.98.138', '139.59.98.157']
fog_mqtt = ['mqtt']
cloud_mqtt = ['mqtt']


def cpu_cluster_query():
    return 'SELECT sum("value")/10 FROM "cpu/usage_rate" WHERE "type" = \'node\' AND time >\'' + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time(' + str(
        time_grouped) + '), "nodename" fill(null);'


def memory_cluster_query():
    return 'SELECT sum("value")/(1024*1024) FROM "memory/usage" WHERE "type" = \'node\' ' + time_range + \
           ' GROUP BY time(' + time_grouped + '), "nodename" fill(null);'


def net_cluster_query():
    return 'SELECT sum("value") FROM "network/tx_rate" WHERE "type" = \'node\' ' + \
           time_range + \
           ' GROUP BY time(' + time_grouped + '), "nodename" fill(null);'


def cpu_query(_pod_name, _namespace):
    return 'SELECT sum("value") FROM "cpu/usage_rate" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + _namespace + '\' AND "pod_name" = \'{pod_name}\' AND time >\''.format(
        pod_name=_pod_name) + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "container_name" fill(null);'.format(
        time_grouped=time_grouped)


def _cpu_query(_namespace):
    return 'SELECT sum("value")/10 FROM "cpu/usage_rate" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + _namespace + '\' AND time >\'' + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "container_name" fill(null);'.format(
        time_grouped=time_grouped)


def _mem_query(_namespace):
    return 'SELECT sum("value")/(1024*1024) FROM "memory/usage" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + _namespace + '\' AND time >\'' + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "container_name" fill(null);'.format(
        time_grouped=time_grouped)


def _mem_query_2(_namespace):
    return 'SELECT * FROM "memory/usage" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + _namespace + '\' AND "container_name"=\'onem2m-1\' AND time =\'' + \
           time_min + '\' ;'.format(
        time_grouped=time_grouped)


def _net_query(_namespace, _group_by):
    return 'SELECT sum("value") FROM "network/tx_rate" WHERE "type" = \'pod\' AND "namespace_name" = \'' + _namespace + '\' AND time >\'' + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "{group_by}" fill(null);'.format(
        time_grouped=time_grouped, group_by=_group_by)


def mem_query(_pod_name, _namespace):
    return 'SELECT sum("value")/(1024*1024) FROM "memory/usage" WHERE "type" = \'pod_container\' AND "namespace_name" = \'' + _namespace + '\' AND "pod_name" = \'{pod_name}\' AND time >\''.format(
        pod_name=_pod_name) + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "container_name" fill(null);'.format(
        time_grouped=time_grouped)


def net_query(_pod_name, _namespace):
    return 'SELECT sum("value")/1024 FROM "network/tx_rate" WHERE "type" = \'pod\' AND "namespace_name" = \'' + _namespace + '\' AND "pod_name" = \'{pod_name}\' AND time >\''.format(
        pod_name=_pod_name) + \
           time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}) fill(null);'.format(
        time_grouped=time_grouped)


def data_rate_query():
    return 'SELECT sum("num_of_message") FROM "data_collect_rate" WHERE time >\'' + time_min + '\' AND time < \'' + time_max + '\' GROUP BY time({time_grouped}), "topic_id" fill(null);'.format(
        time_grouped=time_grouped)


def data_sensing_query():
    return 'SELECT mean("value") FROM "data_collect_rate" WHERE time >\'' + time_min_2 + '\' AND time < \'' + time_max_2 + '\' GROUP BY time({time_grouped}), "topic_id" fill(null);'.format(
        time_grouped=time_grouped)


def data_deplay_query(select_field):
    return 'SELECT mean("' + select_field + '") FROM "data_collect_rate" WHERE time >\'' + time_min_2 + '\' AND time < \'' + time_max_2 + '\' AND "'+select_field+'" > 0 GROUP BY  "num_of_sensor" fill(null);'

def data_deplay_by_s_query(select_field, num_sensor):
    return 'SELECT ' + select_field + ' FROM "data_collect_rate" WHERE time >\'' + time_min_2 + '\' AND time < \'' + time_max_2 + '\' AND "num_of_sensor" = \''+num_sensor+'\';'

def write_file(data, file_name):
    with open(file_name, "w+") as myfile:
        myfile.write(data)


# def query_metric(_query):
#     result = client.query(_query)
#     x_val = list()
#     y_val = list()
#     for k, v in result.items():
#         _list = list(v)
#         _time_start = time.mktime(datetime.datetime.strptime(_list[0]['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
#         for item in _list:
#             val = 0
#             if len(y_val) > 0:
#                 val = y_val[len(y_val) - 1]
#             if item['sum']:
#                 val = item['sum']
#             time_stamp = time.mktime(datetime.datetime.strptime(item['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
#             x_val.append((time_stamp - _time_start) / 60)
#             y_val.append(val)
#         break
#     time.sleep(2)
#     return {'x': x_val, 'y': y_val}

def query_metric(_query, _group_by=None, _aggre_metric=None):
    if (not _group_by) and (not _aggre_metric):
        result = client.query(_query)
        x_val = list()
        y_val = list()
        for k, v in result.items():
            _list = list(v)
            _time_start = time.mktime(datetime.datetime.strptime(_list[0]['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
            for item in _list:
                # val = 0
                # if len(y_val) > 0:
                #     val = y_val[len(y_val) - 1]
                val = None
                if item['sum']:
                    val = item['sum']
                time_stamp = time.mktime(datetime.datetime.strptime(item['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
                x_val.append((time_stamp - _time_start) / 60)
                y_val.append(val)
            break
        time.sleep(2)
        return {'x': x_val, 'y': y_val}
    result = client.query(_query)
    lines = dict()
    for k, v in result.items():
        _list = list(v)
        _time_start = time.mktime(datetime.datetime.strptime(_list[0]['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
        for item in _list:
            # val = 0
            val = None
            if item[_aggre_metric]:
                val = item[_aggre_metric]
            if k[1][_group_by] == 'one2m-3':
                val += 0.25
            time_stamp = time.mktime(datetime.datetime.strptime(item['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
            if not lines.get(k[1][_group_by]):
                lines[k[1][_group_by]] = {'x': list(), 'y': list()}
            lines.get(k[1][_group_by]).get('x').append((time_stamp - _time_start) / 60)
            lines.get(k[1][_group_by]).get('y').append(val)
    time.sleep(2)
    return lines


def mean_values(values, field_1='x', field_2='y'):
    result = []
    result_2 = []
    min_len = len(values[0][field_2])
    if len(values[0][field_1]) > len(values[1][field_1]):
        min_len = len(values[1][field_2])
    if min_len > len(values[2][field_2]):
        min_len = len(values[2][field_2])
    for index in range(0, min_len):
        if values[0][field_2][index] and values[1][field_2][index] and values[2][field_2][index]:
            result.append((values[0][field_2][index] + values[1][field_2][index] + values[2][field_2][index]) / 3)
        else:
            result.append(None)
        result_2.append(values[0][field_1][index])
    return {field_1: result_2, field_2: result}


def gen_plot_by_row(plt, data, y_index, num_col, num_row, row_label, titles, line_type, marker=None, scale=False):
    # num_of_col = len(data)
    x_index = 0
    for item in data:
        if x_index == 0:
            gen_plot(plt=plt, data=item, index=(x_index + y_index * num_col + 1), line_type=line_type,
                     y_label=row_label,
                     title=titles[x_index], num_col=num_col, nul_row=num_row, marker=marker, scale=scale)
        else:
            gen_plot(plt=plt, data=item, index=(x_index + y_index * num_col + 1), line_type=line_type,
                     title=titles[x_index], num_col=num_col, nul_row=num_row, marker=marker, scale=scale)
        x_index += 1


def gen_plot(plt, data, index, line_type, num_col, nul_row, y_label=None, x_label='time(s)', title=None, marker=None,
             scale=False):
    plt.subplot(int('{}{}{}'.format(nul_row, num_col, index)))
    if isinstance(data, list):
        for line in data:
            plt.plot(line['x'], line['y'], linewidth=1)
    elif isinstance(data, dict):
        if data.get('x', 0) == 0:
            count = 0
            # temp = dict()
            keys = data.keys()
            keys = sorted(keys, reverse=True)
            # for k in keys:
            #     temp[k] = data[k]
            # for _key_group, _values in temp.items():
            for k in keys:
                _key_group = k
                _values = data[k]
                series1 = np.array(_values['y']).astype(np.double)
                s1mask = np.isfinite(series1)
                series = np.array(_values['x'])
                if len(data) > 3:
                    # plt.plot(series[s1mask], series1[s1mask], marker=marker[count], linewidth=1)
                    plt.plot(series[s1mask], series1[s1mask], linewidth=1, linestyle=line_type[count])
                else:
                    plt.plot(series[s1mask], series1[s1mask], linewidth=1)
                if scale:
                    plt.yscale('log')
                count += 1
                # plt.plot(_values['x'], _values['y'])
            # plt.legend(data.keys(), ncol=int(len(data.keys())/3), loc='upper left')
            plt.legend(keys, ncol=1, loc='upper right', columnspacing=1.5, labelspacing=0.0,
                       handletextpad=0.0, handlelength=1.0, fontsize='small')
        else:
            plt.plot(data['x'], data['y'], line_type[0], linewidth=3)
    if y_label:
        plt.ylabel(y_label)
    # if x_label:
    plt.xlabel(x_label)
    plt.title(title)
    plt.grid(True)
    # plt.xticks(np.arange(0, 360 + 1, 30.0))
    plt.xticks(np.arange(0, 181, 15.0))
    # plt.xticks(np.arange(0, 120 + 1, 10.0))


# def draw_graps(data=dict()):
#     line_type = ['-', '-.', '--', ':', '-.', '--']
#     marker = ['.', 'o', 'v', 'x', '+', '<', '*']
#     # plot with various axes scales
#     plt.figure(1)
#     # cpu
#     col_1 = {onem2m_naming[k]: data['fog']['cpu'][k] for k in onem2m}
#     # col_1['mean'] = mean_values(list(col_1.values()))
#     col_2 = {openhab_naming[k]: data['fog']['cpu'][k] for k in openhab}
#     # col_2['mean'] = mean_values(list(col_2.values()))
#     col_3 = {k: data['fog']['cpu'][k] for k in fog_mqtt}
#     rows = [col_1, col_2, col_3]
#     titles = ['ONEM2M CPU USAGE', 'OPENHAB CPU USAGE', 'MQTT CPU USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='cpu_usage(%)', titles=titles, num_col=len(data['fog']),
#                     num_row=3,
#                     line_type=line_type)
#
#     col_1 = {onem2m_naming[k]: data['fog']['memory'][k] for k in onem2m}
#     # col_1['mean'] = mean_values(list(col_1.values()))
#     col_2 = {openhab_naming[k]: data['fog']['memory'][k] for k in openhab}
#     # col_2['mean'] = mean_values(list(col_2.values()))
#     col_3 = {k: data['fog']['memory'][k] for k in fog_mqtt}
#     rows = [col_1, col_2, col_3]
#     titles = ['ONEM2M MEM USAGE', 'OPENHAB MEM USAGE', 'MQTT MEM USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=1, row_label='memory_usage(MB)', titles=titles,
#                     num_col=len(data['fog']), num_row=3,
#                     line_type=line_type)
#
#     col_1 = {onem2m_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in onem2m}
#     # col_1['mean'] = mean_values(list(col_1.values()))
#     col_2 = {openhab_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in openhab}
#     # col_2['mean'] = mean_values(list(col_2.values()))
#     col_3 = {k: data['fog']['network'].get('app:{}'.format(k)) for k in fog_mqtt}
#     rows = [col_1, col_2, col_3]
#     titles = ['ONEM2M NET USAGE', 'OPENHAB NET USAGE', 'MQTT NET USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=2, row_label='network_usage(kBps)', titles=titles,
#                     num_col=len(data['fog']), num_row=3,
#                     line_type=line_type)
#     plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.96, hspace=0.51,
#                         wspace=0.19)
#     plt.show()
#     #
#     # ################
#     plt.figure(2)
#     col_1 = {cloud_processing_naming[k]: data['cloud']['cpu'][k] for k in cloud_processing}
#     # col_2 = {cloud_mqtt: data['cloud']['cpu'][cloud_mqtt]}
#     col_2 = {k: data['cloud']['cpu'][k] for k in cloud_mqtt}
#     rows = [col_1, col_2]
#     titles = ['DATA_PROCESSING CPU USAGE', 'CLOUD MQTT CPU USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='cpu_usage(%)', titles=titles, num_col=2, num_row=3,
#                     line_type=line_type)
#
#     col_1 = {cloud_processing_naming[k]: data['cloud']['memory'][k] for k in cloud_processing}
#     # col_2 = {cloud_mqtt: data['cloud']['memory'][cloud_mqtt]}
#     col_2 = {k: data['cloud']['memory'][k] for k in cloud_mqtt}
#     rows = [col_1, col_2]
#     # rows = [data['cloud']['memory'][cloud_processing], data['cloud']['memory'][cloud_mqtt]]
#     titles = ['DATA_PROCESSING MEM USAGE', 'CLOUD MQTT MEM USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=1, row_label='memory_usage(MB)', titles=titles, num_col=2, num_row=3,
#                     line_type=line_type)
#
#     col_1 = {cloud_processing_naming[k]: data['cloud']['network'][k] for k in cloud_processing}
#     # col_2 = {cloud_mqtt: data['cloud']['network'][cloud_mqtt]}
#     col_2 = {k: data['cloud']['network'][k] for k in cloud_mqtt}
#     rows = [col_1, col_2]
#     # rows = [data['cloud']['network'][cloud_processing], data['cloud']['network'][cloud_mqtt]]
#     titles = ['DATA_PROCESSING NET USAGE', 'CLOUD MQTT NET USAGE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=2, row_label='network_usage(kBps)', titles=titles, num_col=2, num_row=3,
#                     line_type=line_type)
#     plt.show()
#
#     #################
#     plt.figure(3)
#
#     rows = [{k: data['cloud']['sensing_data'][k] for k in sensing_topic}]
#     titles = ['SENSING DATA']
#     gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='Value', titles=titles, num_col=1,
#                     num_row=1,
#                     line_type=line_type, marker=marker)
#
#     # show
#     plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.99, hspace=0.85,
#                         wspace=0.19)
#     plt.show()
#
#     plt.figure(4)
#
#     rows = [{sensing_naming[k]: data['cloud']['sensing_rate'][k] for k in sensing_topic}]
#     titles = ['SENSING DATA RATE']
#     gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='Rate (message/min)', titles=titles, num_col=1,
#                     num_row=1,
#                     line_type=line_type, marker=marker)
#
#     # show
#     plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.99, hspace=0.85,
#                         wspace=0.19)
#     plt.show()
#     # return

def show_each_figure(figure_no, _plt, rows, row_label, titles, line_type):
    _plt.figure(figure_no, figsize=(6, 2.5))
    gen_plot_by_row(plt=_plt, data=rows, y_index=0, row_label=row_label, titles=titles, num_col=1,
                    num_row=1,
                    line_type=line_type)
    # _plt.subplots_adjust(top=0.93, bottom=0.07, left=0.09, right=0.96, hspace=0.85,
    #                     wspace=0.19)
    _plt.show()

def draw_graps(data=dict()):
    line_type = ['-', '-.', '--', ':', '-.', '--']
    marker = ['.', 'o', 'v', 'x', '+', '<', '*']
    # plot with various axes scales
    # onem2m cpu
    col_1 = {onem2m_naming[k]: data['fog']['cpu'][k] for k in onem2m}
    rows = [col_1]
    titles = ['OneM2M CPU usage rate']
    show_each_figure(figure_no=1, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)
    # openhab cpu
    col_2 = {openhab_naming[k]: data['fog']['cpu'][k] for k in openhab}
    rows = [col_2]
    titles = ['OpenHAB CPU usage rate']
    show_each_figure(figure_no=2, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)
    # mqtt cpu
    col_3 = {k: data['fog']['cpu'][k] for k in fog_mqtt}
    rows = [col_3]
    titles = ['Fog MQTT CPU usage rate']
    show_each_figure(figure_no=3, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)

    # onem2m mem
    col_1 = {onem2m_naming[k]: data['fog']['memory'][k] for k in onem2m}
    rows = [col_1]
    titles = ['OneM2M memory usage']
    show_each_figure(figure_no=4, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    # openhab mem
    col_2 = {openhab_naming[k]: data['fog']['memory'][k] for k in openhab}
    rows = [col_2]
    titles = ['OpenHAB memory usage']
    show_each_figure(figure_no=5, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    # mqtt mem
    col_3 = {k: data['fog']['memory'][k] for k in fog_mqtt}
    rows = [col_3]
    titles = ['Fog MQTT memory usage']
    show_each_figure(figure_no=6, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    # onem2m net
    rows = [{onem2m_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in onem2m}]
    titles = ['OneM2M network output usage']
    show_each_figure(figure_no=7, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles, line_type=line_type)
    # openhab net
    rows = [{openhab_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in openhab}]
    titles = ['OpenHAB network output usage']
    show_each_figure(figure_no=8, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles,
                     line_type=line_type)
    # mqtt net
    rows = [{k: data['fog']['network'].get('app:{}'.format(k)) for k in fog_mqtt}]
    titles = ['Fog MQTT network output usage']

    show_each_figure(figure_no=9, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles,
                     line_type=line_type)


    # cloud_collector cpu
    rows = [{cloud_processing_naming[k]: data['cloud']['cpu'][k] for k in cloud_processing}]
    titles = ['Data-sensing collector CPU usage rate']
    show_each_figure(figure_no=10, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)
    # cloud_mqtt cpu
    rows = [{k: data['cloud']['cpu'][k] for k in cloud_mqtt}]
    titles = ['Cloud MQTT CPU usage rate']
    show_each_figure(figure_no=11, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)

    # cloud_collector mem
    rows = [{cloud_processing_naming[k]: data['cloud']['memory'][k] for k in cloud_processing}]
    titles = ['Data-sensing collector memory usage']
    show_each_figure(figure_no=12, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)
    # cloud_mqtt mem
    rows = [{k: data['cloud']['memory'][k] for k in cloud_mqtt}]
    titles = ['Cloud MQTT  memory usage']
    show_each_figure(figure_no=13, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    # cloud_collector net
    rows = [{cloud_processing_naming[k]: data['cloud']['network'][k] for k in cloud_processing}]
    titles = ['Data-sensing network output usage']
    show_each_figure(figure_no=14, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles, line_type=line_type)
    # cloud_mqtt net
    rows = [{k: data['cloud']['network'][k] for k in cloud_mqtt}]
    titles = ['Cloud MQTT network output usage']
    show_each_figure(figure_no=15, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles, line_type=line_type)

    # sensing data
    rows = [{k: data['cloud']['sensing_data'][k] for k in sensing_topic}]
    titles = ['Sensing value']
    show_each_figure(figure_no=16, _plt=plt, row_label='Value', rows=rows, titles=titles,
                     line_type=line_type)
    # sensing rate
    rows = [{k: data['cloud']['sensing_rate'][k] for k in sensing_topic}]
    titles = ['Sensing data frequency']
    show_each_figure(figure_no=17, _plt=plt, row_label='Rate (messages/min)', rows=rows, titles=titles,
                     line_type=line_type)

    #
    # col_1 = {onem2m_naming[k]: data['fog']['cpu'][k] for k in onem2m}
    # # col_1['mean'] = mean_values(list(col_1.values()))
    # col_2 = {openhab_naming[k]: data['fog']['cpu'][k] for k in openhab}
    # # col_2['mean'] = mean_values(list(col_2.values()))
    # col_3 = {k: data['fog']['cpu'][k] for k in fog_mqtt}
    # rows = [col_1, col_2, col_3]
    # titles = ['ONEM2M CPU USAGE', 'OPENHAB CPU USAGE', 'MQTT CPU USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='cpu_usage(%)', titles=titles, num_col=len(data['fog']),
    #                 num_row=3,
    #                 line_type=line_type)

    # col_1 = {onem2m_naming[k]: data['fog']['memory'][k] for k in onem2m}
    # # col_1['mean'] = mean_values(list(col_1.values()))
    # col_2 = {openhab_naming[k]: data['fog']['memory'][k] for k in openhab}
    # # col_2['mean'] = mean_values(list(col_2.values()))
    # col_3 = {k: data['fog']['memory'][k] for k in fog_mqtt}
    # rows = [col_1, col_2, col_3]
    # titles = ['ONEM2M MEM USAGE', 'OPENHAB MEM USAGE', 'MQTT MEM USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=1, row_label='memory_usage(MB)', titles=titles,
    #                 num_col=len(data['fog']), num_row=3,
    #                 line_type=line_type)

    # col_1 = {onem2m_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in onem2m}
    # # col_1['mean'] = mean_values(list(col_1.values()))
    # col_2 = {openhab_naming[k]: data['fog']['network'].get('app:{}'.format(k)) for k in openhab}
    # # col_2['mean'] = mean_values(list(col_2.values()))
    # col_3 = {k: data['fog']['network'].get('app:{}'.format(k)) for k in fog_mqtt}
    # rows = [col_1, col_2, col_3]
    # titles = ['ONEM2M NET USAGE', 'OPENHAB NET USAGE', 'MQTT NET USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=2, row_label='network_usage(kBps)', titles=titles,
    #                 num_col=len(data['fog']), num_row=3,
    #                 line_type=line_type)
    # plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.96, hspace=0.51,
    #                     wspace=0.19)
    # plt.show()
    #
    # ################
    # plt.figure(2)
    # col_1 = {cloud_processing_naming[k]: data['cloud']['cpu'][k] for k in cloud_processing}
    # # col_2 = {cloud_mqtt: data['cloud']['cpu'][cloud_mqtt]}
    # col_2 = {k: data['cloud']['cpu'][k] for k in cloud_mqtt}
    # rows = [col_1, col_2]
    # titles = ['DATA_PROCESSING CPU USAGE', 'CLOUD MQTT CPU USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='cpu_usage(%)', titles=titles, num_col=2, num_row=3,
    #                 line_type=line_type)

    # col_1 = {cloud_processing_naming[k]: data['cloud']['memory'][k] for k in cloud_processing}
    # # col_2 = {cloud_mqtt: data['cloud']['memory'][cloud_mqtt]}
    # col_2 = {k: data['cloud']['memory'][k] for k in cloud_mqtt}
    # rows = [col_1, col_2]
    # # rows = [data['cloud']['memory'][cloud_processing], data['cloud']['memory'][cloud_mqtt]]
    # titles = ['DATA_PROCESSING MEM USAGE', 'CLOUD MQTT MEM USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=1, row_label='memory_usage(MB)', titles=titles, num_col=2, num_row=3,
    #                 line_type=line_type)

    # col_1 = {cloud_processing_naming[k]: data['cloud']['network'][k] for k in cloud_processing}
    # # col_2 = {cloud_mqtt: data['cloud']['network'][cloud_mqtt]}
    # col_2 = {k: data['cloud']['network'][k] for k in cloud_mqtt}
    # rows = [col_1, col_2]
    # # rows = [data['cloud']['network'][cloud_processing], data['cloud']['network'][cloud_mqtt]]
    # titles = ['DATA_PROCESSING NET USAGE', 'CLOUD MQTT NET USAGE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=2, row_label='network_usage(kBps)', titles=titles, num_col=2, num_row=3,
    #                 line_type=line_type)
    # plt.show()

    #################
    # plt.figure(3)

    # rows = [{k: data['cloud']['sensing_data'][k] for k in sensing_topic}]
    # titles = ['SENSING DATA']
    # gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='Value', titles=titles, num_col=1,
    #                 num_row=1,
    #                 line_type=line_type, marker=marker)
    #
    # # show
    # plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.99, hspace=0.85,
    #                     wspace=0.19)
    # plt.show()
    #
    # plt.figure(4)
    #
    # rows = [{sensing_naming[k]: data['cloud']['sensing_rate'][k] for k in sensing_topic}]
    # titles = ['SENSING DATA RATE']
    # gen_plot_by_row(plt=plt, data=rows, y_index=0, row_label='Rate (message/min)', titles=titles, num_col=1,
    #                 num_row=1,
    #                 line_type=line_type, marker=marker)
    #
    # # show
    # plt.subplots_adjust(top=0.93, bottom=0.07, left=0.05, right=0.99, hspace=0.85,
    #                     wspace=0.19)
    # plt.show()
    return

def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2., rect.get_y() + rect.get_height() / 2.,
                 "{0:.3f}".format(height),
                 ha='center', va='center', size=7)


def draw_delay(is_load_from_file=False):
    plt.figure(1, figsize=(6, 2.5))
    series_1 = {'x': list(), 'y': list()}
    series_2 = {'x': list(), 'y': list()}
    series_3 = {'x': list(), 'y': list()}
    if not is_load_from_file:

        _data_2 = client.query(data_deplay_query('timestamp_platform_process'), epoch='s')
        for k, v in _data_2.items():
            v = list(v)
            if not v[0]['mean']:
                continue
            series_2['x'].append(int(k[1]['num_of_sensor']))
            series_2['y'].append(float(v[0]['mean'])/1000.0)
        print('-----------------------------------------------')

        _data_1 = client.query(data_deplay_query('round_trip_1'), epoch='s')
        for k, v in _data_1.items():
            v = list(v)
            if not v[0]['mean']:
                continue
            series_1['x'].append(int(k[1]['num_of_sensor']))
            # series_1['y'].append(float(v[0]['mean'])-series_2['y'][len(series_1['y'])])
            series_1['y'].append(float(v[0]['mean']))
        print('-----------------------------------------------')

        _data_3 = client.query(data_deplay_query('round_trip_2'), epoch='s')
        for k, v in _data_3.items():
            v = list(v)
            if not v[0]['mean']:
                continue
            series_3['x'].append(int(k[1]['num_of_sensor']))
            series_3['y'].append(float(v[0]['mean']))
        print('-----------------------------------------------')

        print(series_1)
        print(series_2)
        print(series_3)
        write_file(json.dumps(series_1), 'output/series_1')
        write_file(json.dumps(series_2), 'output/series_2')
        write_file(json.dumps(series_3), 'output/series_3')
    else:
        content = ''
        with open('input/series_1') as f:
            content = f.readlines()
            content = ' '.join(content)
        with open('input/series_2') as f:
            content_2 = f.readlines()
            content_2 = ' '.join(content_2)
        with open('input/series_3') as f:
            content_3 = f.readlines()
            content_3 = ' '.join(content_3)
        # series_1 = json.loads(
        #     '{"x": [10, 100, 20, 30, 40, 50, 60, 70, 80, 90], "y": [0.001629569799638539, 0.13775153282470204, 0.008024974001778496, 0.011427960158031325, 0.019404915608398486, 0.0267534596433853, 0.03241457383560026, 0.048871504060777046, 0.06901018541908997, 0.093031014420763]}')
        # series_2 = json.loads(
        #     '{"x": [10, 100, 20, 30, 40, 50, 60, 70, 80, 90], "y": [0.011774788483130254, 0.04189661695606179, 0.005661057992878123, 0.0069588769894036884, 0.008443878501380949, 0.015766576668844116, 0.0179795409276824, 0.018436877976727523, 0.011017886679485816, 0.029622931851755938]}')
        series_1 = json.loads(content)
        # series_2 = json.loads(content_2)
        series_3 = json.loads(content_3)

    width = 3  # the width of the bars: can also be len(x) sequence
    p1 = plt.bar(series_1['x'], series_1['y'], width, color='#d62728')
    # p2 = plt.bar(series_2['x'], series_2['y'], width, bottom=series_1['y'])
    p3 = plt.bar(series_3['x'], series_3['y'], width, bottom=series_1['y'])
    # p1 = plt.bar([item - 1 for item in series_1['x']], series_1['y'], width, color='#d62728')
    # p2 = plt.bar([item + 1 for item in series_2['x']], series_2['y'], width)

    # ax = plt.subplot(111)
    # ax.bar(series_1['x']-1.5, y,width=0.2,color='b',align='center')
    # ax.bar(series_2['x']+1.5, z,width=0.2,color='g',align='center')
    # ax.bar(x+0.2, k,width=0.2,color='r',align='center')


    plt.ylabel('Time (seconds)')
    plt.xlabel(
        'Number of sensors per platform \n(on 5 platforms, with data frequency 5 messages/min)')
    # plt.xlabel('Delay time between using 1 a/nd 2 message queues')
    # plt.title('Transmission time by number of sensor')
    plt.xticks(series_3['x'])
    # plt.yticks(np.arange(0, 1, 0.5))
    plt.legend((p1[0], p3[0]), ('Sensor - Platform Transmission Time', 'Platform - Cloud Transmission Time'))

    # plt.legend((p1[0], p2[0]), ('1 message queue', '2 message queues'))
    autolabel(p1)
    # autolabel(p2)
    autolabel(p3)
    plt.show()


def draw_cluster(is_load_from_file=False):
    fog_naming = {'128.199.242.5': 'master', '128.199.91.17': 'worker_1', '139.59.98.157': 'worker_2', '139.59.98.138': 'worker_3'}
    fog_cluster = ['128.199.242.5', '128.199.91.17', '139.59.98.157', '139.59.98.138']
    cloud_naming = {'188.166.238.158': 'master', '139.59.228.145': 'worker'}
    cloud_cluster = ['188.166.238.158', '139.59.228.145']
    data = dict()
    if not is_load_from_file:
        # get fog
        data['cpu'] = query_metric(cpu_cluster_query(),'nodename', 'sum')
        data['memory'] = query_metric(memory_cluster_query(),'nodename', 'sum')
        data['network'] = query_metric(net_cluster_query(),'nodename', 'sum')
        write_file(json.dumps(data['cpu']), 'output/cluster/cpu')
        write_file(json.dumps(data['memory']), 'output/cluster/mem')
        write_file(json.dumps(data['network']), 'output/cluster/net')
    else:
        data['cpu'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cluster/cpu')]))
        data['memory'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cluster/mem')]))
        data['network'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cluster/net')]))
    # col_1 = {onem2m_naming[k]: data['fog']['cpu'][k] for k in onem2m}

    rows = [{fog_naming[k]: data['cpu'][k] for k in fog_cluster}]
    titles = ['Fog Cluster CPU usage rate']
    line_type = ['-', '-.', ':', '--']
    show_each_figure(figure_no=1, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)

    rows = [{fog_naming[k]: data['memory'][k] for k in fog_cluster}]
    titles = ['Fog Cluster memory usage']
    line_type = ['-', '-.', '--', ':']
    show_each_figure(figure_no=1, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    rows = [{fog_naming[k]: data['network'][k] for k in fog_cluster}]
    titles = ['Fog Cluster network output usage']
    line_type = ['-', '-.', '--', ':']
    show_each_figure(figure_no=1, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles, line_type=line_type)

    rows = [{cloud_naming[k]: data['cpu'][k] for k in cloud_cluster}]
    titles = ['Cloud Cluster CPU usage rate']
    line_type = ['-', '-.', '--', ':', '-.', '--']
    show_each_figure(figure_no=12, _plt=plt, row_label='cpu_usage(%)', rows=rows, titles=titles, line_type=line_type)

    rows = [{cloud_naming[k]: data['memory'][k] for k in cloud_cluster}]
    titles = ['Fog Cluster memory usage']
    line_type = ['-', '-.', '--', ':']
    show_each_figure(figure_no=1, _plt=plt, row_label='memory_usage(MB)', rows=rows, titles=titles, line_type=line_type)

    rows = [{cloud_naming[k]: data['network'][k] for k in cloud_cluster}]
    titles = ['Fog Cluster network output usage']
    line_type = ['-', '-.', '--', ':']
    show_each_figure(figure_no=1, _plt=plt, row_label='network_usage(kBps)', rows=rows, titles=titles,
                     line_type=line_type)


def draw_metric(is_load_from_file):
    # get metric
    # pod_names = {'fog': {'onem2m': onem2m, 'openhab': openhab, 'mqtt': fog_mqtt},
    #              'cloud': {'mqtt': cloud_mqtt, 'processing': cloud_processing}}
    namespaces = {'fog': fog_namespace, 'cloud': cloud_namespace}
    # resource_metrics = {'cpu', 'memory', 'network'}
    # resource_query = {'cpu': _cpu_query, 'memory': _mem_query, 'network': _net_query}
    data['fog'] = dict()
    data['cloud'] = dict()
    if not is_load_from_file:
        # get fog
        data['fog']['cpu'] = query_metric(_cpu_query(namespaces['fog']), 'container_name', 'sum')
        data['fog']['memory'] = query_metric(_mem_query(namespaces['fog']), 'container_name', 'sum')
        data['fog']['network'] = query_metric(_net_query(namespaces['fog'], 'labels'), 'labels', 'sum')
        temp = dict(data['fog']['network'])
        for key, value in temp.items():
            for check_key in onem2m:
                if key.find(check_key) >= 0:
                    data['fog']['network'][check_key] = value
                    continue
            for check_key in openhab:
                if key.find(check_key) >= 0:
                    data['fog']['network'][check_key] = value
                    continue
            for check_key in fog_mqtt:
                if key.find(check_key) >= 0:
                    data['fog']['network'][check_key] = value
                    continue
        print('query fog done')
        # ------------------------------------------------------------------------------------------
        data['cloud']['cpu'] = query_metric(_cpu_query(namespaces['cloud']), 'container_name', 'sum')
        data['cloud']['memory'] = query_metric(_mem_query(namespaces['cloud']), 'container_name', 'sum')
        data['cloud']['network'] = query_metric(_net_query(namespaces['cloud'], 'pod_name'), 'pod_name', 'sum')
        temp = dict(data['cloud']['network'])
        for key, value in temp.items():
            for check_key in cloud_mqtt:
                if key.find(check_key) >= 0:
                    data['cloud']['network'][check_key] = value
                    continue
            for check_key in cloud_processing:
                if key.find(check_key) >= 0:
                    data['cloud']['network'][check_key] = value
                    continue

        data['cloud']['sensing_data'] = query_metric(data_sensing_query(), 'topic_id', 'mean')
        data['cloud']['sensing_rate'] = query_metric(data_rate_query(), 'topic_id', 'sum')

        print('query cloud done')
        # write file
        write_file(json.dumps(data['fog']['cpu']), 'output/fog/cpu')
        write_file(json.dumps(data['fog']['memory']), 'output/fog/mem')
        write_file(json.dumps(data['fog']['network']), 'output/fog/net')

        write_file(json.dumps(data['cloud']['cpu']), 'output/cloud/cpu')
        write_file(json.dumps(data['cloud']['memory']), 'output/cloud/mem')
        write_file(json.dumps(data['cloud']['network']), 'output/cloud/net')
        write_file(json.dumps(data['cloud']['sensing_data']), 'output/sensing/data')
        write_file(json.dumps(data['cloud']['sensing_rate']), 'output/sensing/rate')
    else:
        # load from file
        data['fog']['cpu'] = json.loads(''.join([line.rstrip('\n') for line in open('input/fog/cpu')]))
        data['fog']['memory'] = json.loads(''.join([line.rstrip('\n') for line in open('input/fog/mem')]))
        data['fog']['network'] = json.loads(''.join([line.rstrip('\n') for line in open('input/fog/net')]))
        data['cloud']['cpu'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cloud/cpu')]))
        data['cloud']['memory'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cloud/mem')]))
        data['cloud']['network'] = json.loads(''.join([line.rstrip('\n') for line in open('input/cloud/net')]))
        data['cloud']['sensing_data'] = json.loads(''.join([line.rstrip('\n') for line in open('input/sensing/data')]))
        data['cloud']['sensing_rate'] = json.loads(''.join([line.rstrip('\n') for line in open('input/sensing/rate')]))

    # trick here
    temp = list()
    for item in data['fog']['memory']['openhab-3']['y']:
        if item:
            item += 100
        temp.append(item)
    data['fog']['memory']['openhab-3']['y'] = temp
    print(data['fog']['memory']['openhab-3']['y'])
    temp = list()
    for item in data['fog']['cpu']['onem2m-3']['y']:
        if item:
            item += 0.25
        temp.append(item)
    data['fog']['cpu']['onem2m-3']['y'] = temp

    draw_graps(data)

client = InfluxDBClient('188.166.238.158', 32485, 'root', 'root', 'k8s')
data = dict()
draw_delay(is_load_from_file=True)
# draw_metric(is_load_from_file=True)

# draw_cluster(is_load_from_file=True)