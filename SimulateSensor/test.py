import http.client
from random import randint
import json

def write_sitemap_file(i):
    try:
        f = open('test.config/config_' + str(int(i / 10)) + '.cfg', 'w')
        f.writelines('128.199.242.5\n')
        f.writelines('31382\n')
        f.writelines('sensor_\n')
        f.writelines('sensor_\n')
        f.writelines(str(i) + '\n')
        f.writelines('60\n')
    except IOError:
        print('Can not open file sitemap\n')
    else:
        f.close()


def write_item_openhab_file(index, index_2):
    try:
        f = open('test.config/openhab.items/demo_{}.items'.format(index), 'w')
        for k in range(index_2, index_2 + 5):
            f.write('Number openhab_pf_{}'.format(str(k)) +
                    ' "Value [%.1f]" {mqtt="<[mqttIn:'+'openhab_pf_{}/temperature'.format(str(k))+':state:default], '+
                    '>[mqttOut:'+'openhab_pf_{}/temperature'.format(str(k))+':state:*:default]"}\n')
    except IOError:
        print('Can not open file item\n')
    else:
        f.close()


def write_file(file_name, data):
    with open(file_name, "w") as myfile:
        myfile.write(data)

def gen_sensor_item(start, end, sensor_index, freq=20, is_onem2m=True):
    """
    name=Weather Temperature Sensor,topic=/in0,frequent=10,type=Diode,unit=Temperature:Celsius,label=task:collect_temperature,namespace=IOT_LAB_1,version=v1.06,resoure_type=sensor
    name=Body Temperature Sensor,topic=/in1,frequent=10,type=IC,unit=Temperature:Fahrenheit,label=task:collect_temperature,namespace=IOT_LAB_2,version=v1.6,resoure_type=sensor
    name=SONY Light Sensor V1,topic=/in2,frequent=10,type=IC,unit=LightMeter:ISO,label=task:light_meter,namespace=IOT_LAB_1,version=v2.05,resoure_type=sensor
    name=ATA Light Sensor V2,topic=/in3,frequent=10,type=Semiconductor,unit=LightMeter:ISO,label=task:light_meter,namespace=IOT_LAB_2,version=v4.0,resoure_type=sensor
    name=SENSYS Atmosphere Sensor,topic=/in4,frequent=10,type=IC,unit=Pressure:PSI,label=task:pressure_warning,namespace=IOT_LAB_2,version=v1.3,resoure_type=sensor
    :param start:
    :param end:
    :param type:
    :param freq:
    :param prefix:
    :return:
    """
    tmpl = [
        'name=Weather Temperature Sensor - {id},topic=sensor_{id},frequent={freq},type=Diode,unit=Temperature:Celsius,label=task:collect_temperature,namespace=IOT_LAB_1,version=v1.06,resoure_type=sensor',
        'name=Body Temperature Sensor - {id},topic=sensor_{id},frequent={freq},type=IC,unit=Temperature:Fahrenheit,label=task:collect_temperature,namespace=IOT_LAB_2,version=v1.6,resoure_type=sensor',
        'name=SONY Light Sensor V1 - {id},topic=sensor_{id},frequent={freq},type=IC,unit=LightMeter:ISO,label=task:light_meter,namespace=IOT_LAB_1,version=v2.05,resoure_type=sensor',
        'name=ATA Light Sensor V2 - {id},topic=sensor_{id},frequent={freq},type=Semiconductor,unit=LightMeter:ISO,label=task:light_meter,namespace=IOT_LAB_2,version=v4.0,resoure_type=sensor',
        'name=SENSYS Atmosphere Sensor - {id},topic=sensor_{id},frequent={freq},type=IC,unit=Pressure:PSI,label=task:pressure_warning,namespace=IOT_LAB_2,version=v1.3,resoure_type=sensor'
    ]
    sensor_item = ''
    if is_onem2m:
        platform_item = list()
    else:
        platform_item = ''
    measure_item = ''

    for i in range(start, end+1):
        arr_index = randint(0, 4)
        id = str(sensor_index) + '_' + str(i)
        sensor_item += str(tmpl[arr_index].format(id=id, freq=freq)+'\n')
        if is_onem2m:
            item = dict()
            item['item_name'] = 'sensor_{id}'.format(id=id)
            item['topic'] = 'sensor_{id}'.format(id=id)
            item['item_type'] = '1'
            platform_item.append(item)
        else:
            platform_item += str('String sensor_'+id+' "sensor_'+id+': [%s]" {mqtt="<[mqttIn:sensor_'+id+':state:default], >[mqttOut:sensor_'+id+':state:*:EXEC(/openhab/configurations/get_timestamp.sh ${state} ${itemName})]"}'+'\n')
        measure_item += str('sensor_{id}'.format(id=id)+'\n')
    if is_onem2m:
        return [sensor_item, json.dumps(platform_item), measure_item]
    else:
        return [sensor_item, platform_item, measure_item]

def gen_onem2m_item(start, end, prefix=None):
    print('[')
    for i in range(start, end+1):
        item = dict()
        if prefix:
            item['item_name'] = 'onem2m_pf_{prefix}_{index}'.format(index=i, prefix=prefix)
        else:
            item['item_name'] = 'onem2m_pf_{index}'.format(index=i)
        item['item_type'] = '1'
        if prefix:
            item['topic'] = 'onem2m_pf_{prefix}_{index}/temperature'.format(index=i, prefix=prefix)
        else:
            item['topic'] = 'onem2m_pf_{index}/temperature'.format(index=i)
        if i == end:
            print('{}'.format(item))
        else:
            print('{},'.format(item))
    print(']')

def gen_openhab_item(start, end):
    for i in range(start, end + 1):
        print('String openhab_pf_'+str(i)+' "[%s]" {mqtt="<[mqttIn:openhab_pf_'+str(i)+'/temperature:state:default], >[mqttOut:openhab_pf_'+str(i)+'/temperature:state:*:default]"}')

def gen_topic(start, end, type, prefix=None):
    if prefix:
        for i in range(start, end+1):
            print('{type}_pf_{prefix}_{index}/temperature'.format(
                type=type, index=i, prefix=prefix
            ))
    else:
        for i in range(start, end+1):
            print('{type}_pf_{index}/temperature'.format(
                type=type, index=i
            ))

# for i in range(16, 31):
    # item = dict()
    # item['item_name'] = 'onem2m_pf_{}'.format(i)
    # item['item_type'] = '1'
    # item['topic'] = 'onem2m_pf_{}/temperature'.format(i)
    # print('{},'.format(item))
    # print('String openhab_pf_'+str(i)+' "[%s]" {mqtt="<[mqttIn:openhab_pf_'+str(i)+'/temperature:state:default], >[mqttOut:openhab_pf_'+str(i)+'/temperature:state:*:default]"}')
# gen_sensor_item(16, 30, 'openhab', 20)
# gen_onem2m_item(16, 30)
# gen_openhab_item()
# gen_topic(16,30,'openhab')
# Gen instance
# num = 5
# for i in range(1, 4):
#     data = gen_sensor_item(start=1, end=num, is_onem2m=True, sensor_index=i, freq=5)
#     write_file('output/sensor/items.{index}.cfg'.format(index=i), data[0])
#     write_file('output/platform/onem2m/items.{index}.cfg'.format(index=i), data[1])
#     write_file('output/measure/items.{index}.cfg'.format(index=i), data[2])
#     num += 5
# #
# num = 5
# for i in range(4, 7):
#     data = gen_sensor_item(start=1, end=num, is_onem2m=False, sensor_index=i, freq=5)
#     write_file('output/sensor/items.{index}.cfg'.format(index=i), data[0])
#     write_file('output/platform/openhab/demo.{index}.items'.format(index=i-3), data[1])
#     write_file('output/measure/items.{index}.cfg'.format(index=i), data[2])
#     num += 5

# Gen freq
# freq = 10
# for i in range(1, 4):
#     data = gen_sensor_item(start=1, end=10, is_onem2m=True, sensor_index=i, freq=freq)
#     write_file('output/sensor/items.{index}.cfg'.format(index=i), data[0])
#     write_file('output/platform/onem2m/items.{index}.cfg'.format(index=i), data[1])
#     write_file('output/measure/items.{index}.cfg'.format(index=i), data[2])
#     freq *= 2
#
# freq = 10
# for i in range(4, 7):
#     data = gen_sensor_item(start=1, end=10, is_onem2m=False, sensor_index=i, freq=freq)
#     write_file('output/sensor/items.{index}.cfg'.format(index=i), data[0])
#     write_file('output/platform/openhab/demo.{index}.items'.format(index=i-3), data[1])
#     write_file('output/measure/items.{index}.cfg'.format(index=i), data[2])
#     freq *= 2

# Gen delay
for i in range(1, 7):
    data = gen_sensor_item(start=1, end=100, is_onem2m=False, sensor_index=i, freq=5)
    write_file('output/sensor/items.{index}.cfg'.format(index=i), data[0])
    # write_file('output/platform/onem2m/items.{index}.cfg'.format(index=i), data[1])
    write_file('output/platform/openhab/demo.{index}.items'.format(index=i), data[1])
    write_file('output/measure/items.{index}.cfg'.format(index=i), data[2])

# con = http.client.HTTPConnection(host='172.217.25.20', port=80)
# header = {"Content-type": "text/plain"}
# con.request('GET', '/?f=%s.%f', '', header)
# response = con.getresponse()
# print(response.read())
# import urllib.request
# print(urllib.request.urlopen("http://www.just-the-time.appspot.com/?f=%s.%f").read())
# import os
# print(os.popen('curl "http://www.just-the-time.appspot.com/?f=%s.%f"').read())

# import subprocess
#
# proc = subprocess.Popen(['curl "http://www.just-the-time.appspot.com/?f=%s.%f"'], stdout=subprocess.PIPE, shell=True)
# (out, err) = proc.communicate()
# print("program output:", str(out.decode()))