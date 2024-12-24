import pandas as pd
from convert import convert_date
from connector import connection
from get_data import get_bpm_data
import json

cursor = connection.cursor()

create_heart_rate_table = """
create table if not exists heart_rate(
    id int auto_increment primary key,
    value_fp_val float,
    value_map_val json,
    date varchar(15)
);
"""

cursor.execute(create_heart_rate_table)

bpm_data = get_bpm_data()
bpm_json = json.loads(bpm_data)

points_data = bpm_json['raw_response']['bucket'][0]['dataset'][0]['point']

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
INSERT INTO heart_rate (value_fp_val, value_map_val, date)
VALUES (%s, %s, %s);
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (row['value_fpVal'], row['value_mapVal'], row['date']))

print('Heart data inserted successfully')

connection.commit()

cursor.close()
connection.close()