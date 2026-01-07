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
Comprehensive integration test for pyFlyDb.

Tests all features against a running FlyDB instance.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyflydb


class TestRunner:
    """Test runner with proper error handling and reporting."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name, func):
        """Run a single test."""
        try:
            print(f"\n[TEST] {name}...", end=" ")
            func()
            print("PASSED")
            self.passed += 1
            return True
        except Exception as e:
            print(f"FAILED: {e}")
            self.failed += 1
            self.errors.append((name, str(e)))
            return False
    
    def summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("="*70)
        
        if self.errors:
            print("\nFailed Tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        return self.failed == 0


def main():
    print("="*70)
    print("pyFlyDb Integration Test Suite")
    print("="*70)
    
    # Test configuration - use environment variables for credentials
    HOST = os.environ.get("FLYDB_HOST", "localhost")
    PORT = int(os.environ.get("FLYDB_PORT", "8889"))
    USER = os.environ.get("FLYDB_USER", "admin")
    PASSWORD = os.environ.get("FLYDB_PASSWORD")
    
    if not PASSWORD:
        print("\nError: FLYDB_PASSWORD environment variable is required.")
        print("Set it with: export FLYDB_PASSWORD='your_password'")
        sys.exit(1)
    
    # Use unique table name to avoid conflicts
    import time
    TABLE_NAME = f"test_{int(time.time())}"
    
    runner = TestRunner()
    conn = None
    
    # Test 1: Basic Connection
    def test_connection():
        nonlocal conn
        conn = pyflydb.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD
        )
        assert conn is not None
        assert not conn.closed
    
    if not runner.test("Basic Connection", test_connection):
        print("\nCannot proceed without connection. Exiting.")
        sys.exit(1)
    
    # Test 2: Connection Ping
    def test_ping():
        assert conn.ping() == True
    
    runner.test("Connection Ping", test_ping)
    
    # Test 3: Server Info
    def test_server_info():
        info = conn.get_server_info()
        assert info is not None
        assert "server_version" in info
        print(f"\n      Server version: {info.get('server_version')}")
        print(f"      Protocol version: {info.get('protocol_version')}")
        print(f"      Capabilities: {info.get('capabilities')}")
    
    runner.test("Server Information", test_server_info)
    
    # Test 4: Cursor Creation
    def test_cursor():
        cursor = conn.cursor()
        assert cursor is not None
        assert not cursor.closed
        cursor.close()
        assert cursor.closed
    
    runner.test("Cursor Creation", test_cursor)
    
    # Test 5: Create Table
    def test_create_table():
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE {TABLE_NAME} (id INT, name TEXT, value INT)")
        cursor.close()
    
    runner.test("CREATE TABLE", test_create_table)
    
    # Test 6: Insert Data
    def test_insert():
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {TABLE_NAME} VALUES (1, 'Alice', 100)")
        cursor.execute(f"INSERT INTO {TABLE_NAME} VALUES (2, 'Bob', 200)")
        cursor.execute(f"INSERT INTO {TABLE_NAME} VALUES (3, 'Charlie', 300)")
        cursor.close()
    
    runner.test("INSERT", test_insert)
    
    # Test 7: Parameterized Insert
    def test_parameterized_insert():
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {TABLE_NAME} VALUES (%s, %s, %s)", (4, "Diana", 400))
        cursor.close()
    
    runner.test("Parameterized INSERT", test_parameterized_insert)
    
    # Test 8: Named Parameters
    def test_named_parameters():
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} VALUES (%(id)s, %(name)s, %(value)s)",
            {"id": 5, "name": "Eve", "value": 500}
        )
        cursor.close()
    
    runner.test("Named Parameters", test_named_parameters)
    
    # Test 9: SELECT and fetchall
    def test_select_fetchall():
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        print(f"\n      Fetched {len(rows)} rows")
        assert isinstance(rows, list)
        cursor.close()
    
    runner.test("SELECT with fetchall()", test_select_fetchall)
    
    # Test 10: SELECT and fetchone
    def test_select_fetchone():
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        row = cursor.fetchone()
        if row:
            print(f"\n      First row: {row}")
        assert row is None or isinstance(row, tuple)
        cursor.close()
    
    runner.test("SELECT with fetchone()", test_select_fetchone)
    
    # Test 11: SELECT and iteration
    def test_select_iterate():
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        count = 0
        for row in cursor:
            count += 1
        print(f"\n      Iterated {count} rows")
        cursor.close()
    
    runner.test("SELECT with iteration", test_select_iterate)
    
    # Test 12: UPDATE
    def test_update():
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {TABLE_NAME} SET value = 999 WHERE name = 'Alice'")
        cursor.close()
    
    runner.test("UPDATE", test_update)
    
    # Test 13: DELETE
    def test_delete():
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE name = 'Eve'")
        cursor.close()
    
    runner.test("DELETE", test_delete)
    
    # Test 14: Transaction Commit
    def test_commit():
        conn.commit()
    
    runner.test("Transaction COMMIT", test_commit)
    
    # Test 15: Context Manager - Cursor
    def test_cursor_context():
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {TABLE_NAME}")
            assert not cursor.closed
        assert cursor.closed
    
    runner.test("Cursor Context Manager", test_cursor_context)
    
    # Test 16: DSN Parsing
    def test_dsn_parsing():
        from pyflydb.dsn import parse_dsn
        params = parse_dsn("flydb://admin:secret@localhost:8889/testdb")
        assert params["host"] == "localhost"
        assert params["port"] == 8889
        assert params["user"] == "admin"
        assert params["password"] == "secret"
        assert params["database"] == "testdb"
        print(f"\n      Parsed: {params}")
    
    runner.test("DSN Parsing", test_dsn_parsing)
    
    # Test 17: Result Parser
    def test_result_parser():
        from pyflydb.parser import ResultParser
        
        result = ResultParser.parse_result("INSERT 1")
        assert result["statement_type"] == "INSERT"
        assert result["row_count"] == 1
        
        result = ResultParser.parse_result("UPDATE 5")
        assert result["statement_type"] == "UPDATE"
        assert result["row_count"] == 5
        
        print(f"\n      Parser working correctly")
    
    runner.test("Result Parser", test_result_parser)
    
    # Test 18: Type Adapter
    def test_type_adapter():
        from pyflydb.types import TypeAdapter
        
        assert TypeAdapter.to_sql(None) == "NULL"
        assert TypeAdapter.to_sql(True) == "TRUE"
        assert TypeAdapter.to_sql(42) == "42"
        assert TypeAdapter.to_sql("test") == "'test'"
        
        assert TypeAdapter.from_sql("42", int) == 42
        assert TypeAdapter.from_sql("TRUE", bool) is True
        
        print(f"\n      Type conversions working")
    
    runner.test("Type Adapter", test_type_adapter)
    
    # Test 19: Row Object
    def test_row_object():
        from pyflydb.types import Row
        
        row = Row(["id", "name", "value"], (1, "Test", 100))
        
        # Test different access methods
        assert row["id"] == 1
        assert row.name == "Test"
        assert row[2] == 100
        assert row.to_tuple() == (1, "Test", 100)
        
        print(f"\n      Row object: {row}")
    
    runner.test("Row Object", test_row_object)
    
    # Test 20: Cleanup
    def test_cleanup():
        cursor = conn.cursor()
        try:
            cursor.execute("DROP TABLE {TABLE_NAME}")
        except:
            pass  # Table may not exist
        cursor.close()
        conn.close()
        assert conn.closed
    
    runner.test("Cleanup and Close", test_cleanup)
    
    # Final summary
    success = runner.summary()
    
    if success:
        print("\nAll tests passed successfully!")
        print("pyFlyDb is working correctly with your FlyDB instance.")
    else:
        print("\nSome tests failed. Please review the errors above.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
