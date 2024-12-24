import mysql.connector

connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='lec',
    auth_plugin='mysql_native_password'
)