import os
import json

""" ONLY RUN THIS FILE WHEN YOU WANT TO GENERATE A NEW PROBLEM INSTANCE """

# Do not change
variation_multipliers = [0, 0.5, 0.75, 1.0, 1.25, 1.5]
standard_order_sizes = [0.0, 15.0, 20.0, 15.0, 20.0, 20.0, 20.0, 20.0, 15.0, 15.0, 15.0, 15.0, 7.5, 15.0, 20.0, 10.0,
                        15.0, 15.0, 15.0, 15.0, 10.0, 17.5, 17.5, 17.5, 17.5, 17.5, 17.5, 15.0]

# Change for different scenarios
order_size_variations_md = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
order_size_variations_od = [0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
order_size_variations_op = [0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

vessel_return_days = [4, 0, 0, 0, 0, 4]

weather_forecast = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

dirpath = 'mongstad'
file_path = 'templates/mongstad_template.json'

with open(file_path) as file:
    json_file = json.load(file)

json_file.update({'orders': {}})

order_id = 1
for inst_idx, osv_md in enumerate(order_size_variations_md):
    order_size = standard_order_sizes[inst_idx] * variation_multipliers[osv_md]
    if order_size == 0:
        continue
    json_file['orders'].update({str(order_id): {'transport_type': 'delivery',
                                                'mandatory': 'True',
                                                'size': order_size,
                                                'installation': inst_idx}})
    order_id += 1

for inst_idx, osv_od in enumerate(order_size_variations_od):
    order_size = standard_order_sizes[inst_idx] * variation_multipliers[osv_od]
    if order_size == 0:
        continue
    json_file['orders'].update({str(order_id): {'transport_type': 'delivery',
                                                'mandatory': 'False',
                                                'size': order_size,
                                                'installation': inst_idx}})
    order_id += 1

for inst_idx, osv_op in enumerate(order_size_variations_op):
    order_size = standard_order_sizes[inst_idx] * variation_multipliers[osv_op]
    if order_size == 0:
        continue
    json_file['orders'].update({str(order_id): {'transport_type': 'pickup',
                                                'mandatory': 'False',
                                                'size': order_size,
                                                'installation': inst_idx}})
    order_id += 1

for vessel_idx, vessel in enumerate(json_file['vessels']):
    json_file['vessels'][vessel].update({'return_day': vessel_return_days[vessel_idx]})

json_file.update({'weather_forecast': weather_forecast})

filenames = os.listdir(dirpath)
file_numbers = []
for filename in filenames:
    file_numbers.append(int(filename.split('.')[0]))

new_file_number = str(max(file_numbers) + 1)
new_file_name = new_file_number + '.json'
out_file_path = dirpath + '/' + new_file_name

with open(out_file_path, 'w') as fp:
    json.dump(json_file, fp)



