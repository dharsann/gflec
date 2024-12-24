import pandas as pd
from convert import convert_date
from connector import connection
from get_data import get_distance_data
import json

cursor = connection.cursor()

create_distance_table = """
create table if not exists distance(
    id int auto_increment primary key,
    value_fp_val float,
    value_map_val json,
    date varchar(15)
);
"""

cursor.execute(create_distance_table)

distance_data = get_distance_data()
distance_json = json.loads(distance_data)

points_data = distance_json['bucket'][0]['dataset'][0]['point']

records = []

for point in points_data:
    start_time_nanos = point['startTimeNanos']
    date = convert_date(int(start_time_nanos))

    record = {
        'date': date,
        'value_fpVal': point['value'][0]['fpVal'], 
        'value_mapVal': json.dumps(point['value'][0]['mapVal']) if point['value'][0]['mapVal'] else None
    }
    records.append(record)

df = pd.DataFrame(records)

insert_query = """
INSERT INTO distance (value_fp_val, value_map_val, date)
VALUES (%s, %s, %s);
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (row['value_fpVal'], row['value_mapVal'], row['date']))

print('Distance data inserted successfully')

connection.commit()

cursor.close()
connection.close()