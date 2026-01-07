#!/usr/bin/env python3
# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Debug script to inspect FlyDB protocol responses.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyflydb
from pyflydb.protocol import create_query_message, MessageType


def main():
    print("=" * 60)
    print("pyFlyDb - Protocol Debug")
    print("=" * 60)
    print()
    
    host = "localhost"
    port = 8889
    user = "admin"
    password = "QPQUwwwC%%x#f2!8"
    
    try:
        # Connect
        print("Connecting...")
        conn = pyflydb.connect(host=host, port=port, user=user, password=password)
        print("✓ Connected\n")
        
        # Test 1: Simple SELECT to see response format
        print("Test 1: Executing simple query...")
        query_msg = create_query_message("SELECT 1 as test_col")
        conn._send_message(query_msg)
        response = conn._receive_message()
        
        print(f"Response type: {response.msg_type}")
        print(f"Response payload:")
        print(json.dumps(response.payload, indent=2))
        print()
        
        # Test 2: CREATE TABLE
        print("Test 2: CREATE TABLE response...")
        query_msg = create_query_message("CREATE TABLE test_debug (id INT, value TEXT)")
        conn._send_message(query_msg)
        response = conn._receive_message()
        
        print(f"Response type: {response.msg_type}")
        print(f"Response payload:")
        print(json.dumps(response.payload, indent=2))
        print()
        
        # Test 3: INSERT
        print("Test 3: INSERT response...")
        query_msg = create_query_message("INSERT INTO test_debug VALUES (1, 'hello')")
        conn._send_message(query_msg)
        response = conn._receive_message()
        
        print(f"Response type: {response.msg_type}")
        print(f"Response payload:")
        print(json.dumps(response.payload, indent=2))
        print()
        
        # Test 4: SELECT
        print("Test 4: SELECT response...")
        query_msg = create_query_message("SELECT * FROM test_debug")
        conn._send_message(query_msg)
        response = conn._receive_message()
        
        print(f"Response type: {response.msg_type}")
        print(f"Response payload:")
        print(json.dumps(response.payload, indent=2))
        print()
        
        conn.close()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
