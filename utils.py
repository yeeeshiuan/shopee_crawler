import csv

def get_hant_2_hans_map_from_csv_file(file_path):
    data = {}
    with open(file_path, 'r') as file_path:
        reader = csv.reader(file_path, delimiter=',')
        for row in reader:
            sub_row = row[1:]
            sub_dict = {}
            sub_key = ''
            for index, item in enumerate(sub_row):
                if (index % 2) == 0:
                    sub_key = item
                else:
                    sub_dict[sub_key] = item
            data[row[0]] = sub_dict
    return data

def sort_hant_to_hans_map(hant2Hans_map):
    fined_hant2Hans_map = {}
    for k, v in hant2Hans_map.items():
        if len(v) > 1:
            sorted_tuple_list = sorted(v.items(), key=lambda x: len(x[0]), reverse=True)
            sorted_sub_dict = {i[0]:i[1] for i in sorted_tuple_list}
            fined_hant2Hans_map[k] = sorted_sub_dict
        else:
            fined_hant2Hans_map[k] = v
    return fined_hant2Hans_map

def get_sorted_hant2hans_map(file_path):
    # '../resources/hant2hans.csv'
    hant2Hans_map = get_hant_2_hans_map_from_csv_file(file_path)
    return sort_hant_to_hans_map(hant2Hans_map)
