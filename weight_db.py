import pandas as pd
from connector import connection
from convert import convert_date
from get_data import get_weight_data
import json

cursor = connection.cursor()

create_weight_table = """
create table if not exists weight(
    id int auto_increment primary key,
    value_fp_val int,
    value_map_val json,
    date varchar(15)
);
"""

cursor.execute(create_weight_table)

weight_data = get_weight_data()
weight_json = json.loads(weight_data)

points_data = weight_json['raw_response']['bucket'][0]['dataset'][0]['point']

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
 INSERT INTO weight (value_fp_val, value_map_val, date)
 VALUES (%s, %s, %s);
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (row['value_fpVal'], row['value_mapVal'], row['date']))

print('Weight data inserted successfully')
connection.commit()

cursor.close()
connection.close()
