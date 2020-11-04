import os

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

print("Testing env variables...")
print("DB_USER=", DB_USER)
print("DB_PASS=", DB_PASS)
print("DB_NAME=", DB_NAME)