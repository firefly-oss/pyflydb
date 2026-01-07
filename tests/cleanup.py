#!/usr/bin/env python3
import sys
sys.path.insert(0, '..')
import pyflydb

conn = pyflydb.connect(host='localhost', port=8889, user='admin', password='QPQUwwwC%%x#f2!8')
cursor = conn.cursor()
try:
    cursor.execute('DROP TABLE integration_test')
    print("Table dropped successfully")
except Exception as e:
    print(f"Table drop failed or doesn't exist: {e}")
cursor.close()
conn.close()
