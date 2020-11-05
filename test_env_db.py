import os
import pymysql

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

print("Testing env variables...")
print("DB_USER=", DB_USER)
print("DB_PASS=", DB_PASS)
print("DB_NAME=", DB_NAME)

db = pymysql.connect("localhost", DB_USER, DB_PASS, DB_NAME)
cursor = db.cursor()

cursor.execute("show tables")
table_name = cursor.fetchone()
print("Database table: %s" % table_name)
print("Type:", type(table_name))

sql_string = "select * from "+str(table_name[0])
print("SQL:", sql_string)

cursor.execute(sql_string)
table_row = cursor.fetchone()
print("Table row:", table_row)