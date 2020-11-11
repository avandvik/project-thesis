import os
import json
import random
import pandas as pd
import pathlib

""" ONLY RUN THIS FILE WHEN YOU WANT TO GENERATE A NEW PROBLEM INSTANCE """

# Do not change
variation_multipliers = [0, 0.5, 0.75, 1.0, 1.25, 1.5]
standard_order_sizes = [0.0, 15.0, 20.0, 15.0, 20.0, 20.0, 20.0, 20.0, 15.0, 15.0, 15.0, 15.0, 7.5, 15.0, 20.0, 10.0,
                        15.0, 15.0, 15.0, 15.0, 10.0, 17.5, 17.5, 17.5, 17.5, 17.5, 17.5, 15.0]

weather_forecasts = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                      1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                      2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2,
                      2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]]


def generate_test_instance(orders_file_path,
                           template_path,
                           number_of_vessels, return_day,
                           weather_scenario,
                           outdir_path):
    df = pd.read_excel(orders_file_path, None)

    for sheet_name in df.keys():
        sheet_df = df[sheet_name]

        with open(template_path) as template:
            json_file = json.load(template)

        add_orders_to_json(json_file, sheet_df)
        add_vessels_to_json(json_file, number_of_vessels, return_day)
        add_weather_forecast_to_json(json_file, weather_forecasts[weather_scenario])

        filename = get_filename(base=str(sheet_name), vessels=number_of_vessels, weather_scenario=weather_scenario)
        for entry in os.listdir(outdir_path):
            if os.path.isfile(os.path.join(outdir_path, entry)):
                assert entry != filename, 'File already generated, check if we really want to overwrite!'

        output_file_path = f'{outdir_path}/{filename}'

        with open(output_file_path, 'w') as ofp:
            json.dump(json_file, ofp)


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


def add_orders_to_json(json_file, df):
    json_file.update({'orders': {}})

    for order_idx, row in df.iterrows():
        inst_idx = row['Installation idx']
        order_type = row['Order type']
        p = random.random()
        order_size = draw_order_size(p, inst_idx)
        add_order_to_json(json_file, order_idx, order_type, order_size, inst_idx)


def add_order_to_json(json_file, order_idx, order_type, order_size, inst_idx):
    mandatory = True if list(order_type)[0] == 'M' else False
    delivery = True if list(order_type)[1] == 'D' else False
    json_file['orders'].update({str(order_idx): {'transport_type': 'delivery' if delivery else 'pickup',
                                                 'mandatory': 'True' if mandatory else 'False',
                                                 'size': order_size,
                                                 'installation': inst_idx}})


def add_vessels_to_json(json_file, number_of_vessels, return_day, total_vessels_in_fleet=5):
    return_days = [return_day if number_of_vessels >= i else 0 for i in range(1, total_vessels_in_fleet + 1)]
    return_days.append(return_day)  # Spot vessel

    for vessel_idx, vessel in enumerate(json_file['vessels']):
        json_file['vessels'][vessel].update({'return_day': return_days[vessel_idx]})


def add_weather_forecast_to_json(json_file, weather_forecast):
    json_file.update({'weather_forecast': weather_forecast})


def get_filename(base, vessels, weather_scenario):
    return f'{base}-V{vessels}-WS{weather_scenario}.json'


if __name__ == '__main__':
    base_path = pathlib.Path(__file__).parent.absolute()

    generate_test_instance(orders_file_path=f'{base_path}/orders.xlsx',
                           template_path=f'{base_path}/templates/mongstad_template.json',
                           number_of_vessels=1,
                           return_day=3,
                           weather_scenario=0,
                           outdir_path=f'{base_path}/mongstad')
