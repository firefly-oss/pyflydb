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
Basic pyFlyDb usage example.

This example connects to a running FlyDB instance and demonstrates
basic operations including:
- Connection establishment
- Authentication
- Table creation
- Data insertion
- Querying
- Transaction management
"""

import sys
import os

# Add parent directory to path to import pyflydb
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyflydb


def main():
    """Main example function."""
    
    print("=" * 60)
    print("pyFlyDb - Basic Usage Example")
    print("=" * 60)
    print()
    
    # Connection parameters - use environment variables for credentials
    host = os.environ.get("FLYDB_HOST", "localhost")
    port = int(os.environ.get("FLYDB_PORT", "8889"))
    user = os.environ.get("FLYDB_USER", "admin")
    password = os.environ.get("FLYDB_PASSWORD")
    
    if not password:
        print("Error: FLYDB_PASSWORD environment variable is required.")
        print("Set it with: export FLYDB_PASSWORD='your_password'")
        sys.exit(1)
    
    try:
        # Step 1: Connect to FlyDB
        print(f"Connecting to FlyDB at {host}:{port}...")
        conn = pyflydb.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        print("Connected successfully.")
        print()
        
        # Step 2: Get server information
        print("Getting server information...")
        try:
            info = conn.get_server_info()
            print(f"  Server version: {info.get('server_version', 'N/A')}")
            print(f"  Protocol version: {info.get('protocol_version', 'N/A')}")
            print(f"  Capabilities: {', '.join(info.get('capabilities', []))}")
        except Exception as e:
            print(f"  Note: Could not get server info: {e}")
        print()
        
        # Step 3: Check connection health
        print("Checking connection health...")
        if conn.ping():
            print("  Connection is active.")
        else:
            print("  Connection check failed.")
        print()
        
        # Step 4: Create a cursor
        print("Creating cursor...")
        cursor = conn.cursor()
        print("  Cursor created.")
        print()
        
        # Step 5: Create a test table
        print("Creating test table 'users'...")
        try:
            cursor.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
            print("  Table created successfully.")
        except pyflydb.DatabaseError as e:
            print(f"  Note: Table might already exist: {e}")
        print()
        
        # Step 6: Insert some data
        print("Inserting test data...")
        users_data = [
            (1, "Alice", 30),
            (2, "Bob", 25),
            (3, "Charlie", 35),
            (4, "Diana", 28),
            (5, "Eve", 32)
        ]
        
        for user_id, name, age in users_data:
            cursor.execute(
                "INSERT INTO users VALUES (%s, %s, %s)",
                (user_id, name, age)
            )
        print(f"  Inserted {len(users_data)} users.")
        print()
        
        # Step 7: Query the data
        print("Querying all users...")
        cursor.execute("SELECT * FROM users")
        
        if cursor.description:
            print(f"  Columns: {[col[0] for col in cursor.description]}")
        print(f"  Row count: {cursor.rowcount}")
        print()
        
        print("  Results:")
        for row in cursor:
            print(f"    ID: {row[0]}, Name: {row[1]}, Age: {row[2]}")
        print()
        
        # Step 8: Query with parameters
        print("Querying users older than 28...")
        cursor.execute("SELECT name, age FROM users WHERE age > %s", (28,))
        
        results = cursor.fetchall()
        print(f"  Found {len(results)} users:")
        for row in results:
            print(f"    {row[0]} - Age {row[1]}")
        print()
        
        # Step 9: Named parameters
        print("Querying specific user by name...")
        cursor.execute(
            "SELECT * FROM users WHERE name = %(name)s",
            {"name": "Alice"}
        )
        
        row = cursor.fetchone()
        if row:
            print(f"  Found: {row}")
        else:
            print("  Not found")
        print()
        
        # Step 10: Update data
        print("Updating Alice's age...")
        cursor.execute("UPDATE users SET age = %s WHERE name = %s", (31, "Alice"))
        print("  Updated.")
        print()
        
        # Step 11: Verify update
        print("Verifying update...")
        cursor.execute("SELECT age FROM users WHERE name = %s", ("Alice",))
        row = cursor.fetchone()
        if row:
            print(f"  Alice's new age: {row[0]}")
        print()
        
        # Step 12: Commit transaction (if not autocommit)
        if not conn.autocommit:
            print("Committing transaction...")
            conn.commit()
            print("  Transaction committed.")
            print()
        
        # Step 13: Cleanup
        print("Cleaning up...")
        cursor.close()
        conn.close()
        print("  Connection closed.")
        print()
        
        print("=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    except pyflydb.AuthenticationError as e:
        print(f"Error: Authentication failed: {e}")
        sys.exit(1)
    except pyflydb.ConnectionError as e:
        print(f"Error: Connection failed: {e}")
        print("  Make sure FlyDB is running on localhost:8889")
        sys.exit(1)
    except pyflydb.DatabaseError as e:
        print(f"Error: Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
