import os
import json
import random
import pandas as pd

import data

""" ONLY RUN THIS FILE WHEN YOU WANT TO GENERATE A NEW PROBLEM INSTANCE """

# Do not change
variation_multipliers = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
standard_order_sizes = [0.0, 15.0, 20.0, 15.0, 20.0, 20.0, 20.0, 20.0, 15.0, 15.0, 15.0, 15.0, 7.5, 15.0, 20.0, 10.0,
                        15.0, 15.0, 15.0, 15.0, 10.0, 17.5, 17.5, 17.5, 17.5, 17.5, 17.5, 15.0]
# Changed due avoid variation in order sizes

weather_forecasts = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2,
     2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
     1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
     3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 3,
     3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
     3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
]


def generate_test_instances():
    weather_scenario = 0
    number_of_vessels = 1
    return_time = 80
    planning_period_hours = 80
    time_units_per_hour = 4
    generate_test_instance(orders_file_path=f'{data.PROJECT_DIR_PATH}/input/data/speed_optimization_case.xlsx',
                           template_path=f'{data.PROJECT_DIR_PATH}/input/templates/mongstad_template.json',
                           number_of_vessels=number_of_vessels,
                           return_time=return_time,
                           weather_scenario=weather_scenario,
                           planning_period_hours=planning_period_hours,
                           time_units_per_hour=time_units_per_hour,
                           outdir_path=f'{data.PROJECT_DIR_PATH}/input/mongstad/insight/speed_opt')


def generate_test_instance(orders_file_path,
                           template_path,
                           number_of_vessels, return_time,
                           weather_scenario,
                           planning_period_hours, time_units_per_hour,
                           outdir_path):
    df = pd.read_excel(orders_file_path, None)

    for sheet_name in df.keys():
        sheet_df = df[sheet_name]

        with open(template_path) as template:
            json_file = json.load(template)

        number_of_orders, number_of_insts, inst_ordering = extract_instance_info(sheet_name)

        add_orders_to_json(json_file, sheet_df)
        add_vessels_to_json(json_file, number_of_vessels, return_time)
        add_time_info_to_json(json_file, planning_period_hours, time_units_per_hour)
        add_instance_info_to_json(json_file, number_of_orders, number_of_insts, inst_ordering, weather_scenario,
                                  number_of_vessels)
        add_weather_forecast_to_json(json_file, weather_forecasts[weather_scenario])

        filename = get_filename(base=str(sheet_name),
                                vessels=number_of_vessels,
                                weather_scenario=weather_scenario)

        for entry in os.listdir(outdir_path):
            if os.path.isfile(os.path.join(outdir_path, entry)):
                assert entry != filename, 'File already generated, check if we really want to overwrite!'

        output_file_path = f'{outdir_path}/{filename}'

        with open(output_file_path, 'w') as ofp:
            json.dump(json_file, ofp)


def extract_instance_info(sheet_name):
    sheet_info = sheet_name.split('-')
    number_of_orders = int(''.join(list(sheet_info[0])[1:]))
    number_of_insts = int(number_of_orders / 2)
    inst_ordering = 'Random'
    return number_of_orders, number_of_insts, inst_ordering


def add_orders_to_json(json_file, df):
    json_file.update({'orders': {}})

    for order_idx, row in df.iterrows():
        inst_idx = row['Installation ID']
        order_type = row['Order type']
        p = random.random()
        order_size = draw_order_size(p, inst_idx)
        add_order_to_json(json_file, order_idx, order_type, order_size, inst_idx)


def draw_order_size(p, idx, l1=0.1, l2=0.3, l3=0.7, l4=0.9, l5=1):
    if 0 <= p < l1:
        return standard_order_sizes[idx] * variation_multipliers[1]
    elif l1 <= p < l2:
        return standard_order_sizes[idx] * variation_multipliers[2]
    elif l2 <= p < l3:
        return standard_order_sizes[idx] * variation_multipliers[3]
    elif l3 <= p < l4:
        return standard_order_sizes[idx] * variation_multipliers[4]
    elif l4 <= p < l5:
        return standard_order_sizes[idx] * variation_multipliers[5]


def add_order_to_json(json_file, order_idx, order_type, order_size, inst_idx):
    mandatory = True if list(order_type)[0] == 'M' else False
    delivery = True if list(order_type)[1] == 'D' else False
    json_file['orders'].update({str(order_idx): {'transport_type': 'delivery' if delivery else 'pickup',
                                                 'mandatory': 'True' if mandatory else 'False',
                                                 'size': order_size,
                                                 'installation': inst_idx}})


def add_vessels_to_json(json_file, number_of_vessels, return_time, total_vessels_in_fleet=5):
    return_times = [return_time if number_of_vessels >= i else 0 for i in range(1, total_vessels_in_fleet + 1)]
    return_times.append(return_time)  # Spot vessel

    for vessel_idx, vessel in enumerate(json_file['vessels']):
        json_file['vessels'][vessel].update({'return_time': return_times[vessel_idx]})


def add_time_info_to_json(json_file, planning_period_in_hours, time_units_per_hour):
    json_file.update({'planning_period_in_hours': planning_period_in_hours,
                      'time_units_per_hour': time_units_per_hour})


def add_instance_info_to_json(json_file, number_of_orders, number_of_insts, inst_ordering, weather_scenario,
                              number_of_vessels):
    json_file.update({'number_of_orders': number_of_orders,
                      'number_of_installations': number_of_insts,
                      'installation_ordering': inst_ordering,
                      'weather_scenario': weather_scenario,
                      'fleet_size': number_of_vessels})


def add_weather_forecast_to_json(json_file, weather_forecast):
    json_file.update({'weather_forecast': weather_forecast})


def get_filename(base, vessels, weather_scenario):
    return f'{base}-V{vessels}-WS{weather_scenario}.json'


if __name__ == '__main__':
    generate_test_instances()
