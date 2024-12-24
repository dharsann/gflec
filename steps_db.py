import pandas as pd
from convert import convert_date
from connector import connection
from get_data import get_steps_data
import json

cursor = connection.cursor()

create_steps_table = """
create table if not exists steps(
    id int auto_increment primary key,
    value_int_val int,
    value_map_val json,
    date varchar(15)
);
"""

cursor.execute(create_steps_table)

steps_data = get_steps_data()
steps_json = json.loads(steps_data)

points_data = steps_json['bucket'][0]['dataset'][0]['point']

records = []

for point in points_data:
    start_time_nanos = point['startTimeNanos']
    date = convert_date(int(start_time_nanos))

    record = {
        'date': date,
        'value_intVal': point['value'][0]['intVal'], 
        'value_mapVal': json.dumps(point['value'][0]['mapVal']) if point['value'][0]['mapVal'] else None
    }
    records.append(record)

df = pd.DataFrame(records)

insert_query = """
INSERT INTO steps (value_int_val, value_map_val, date)
VALUES (%s, %s, %s);
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (row['value_intVal'], row['value_mapVal'], row['date']))

print('Steps data inserted successfully')

connection.commit()

cursor.close()
connection.close()