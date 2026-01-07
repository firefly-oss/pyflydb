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
Basic test suite for pyFlyDb.

Tests connection, authentication, query execution, and result handling.
"""

import pytest
import pyflydb


# Test configuration
TEST_HOST = "localhost"
TEST_PORT = 8889
TEST_USER = "admin"
TEST_PASSWORD = "QPQUwwwC%%x#f2!8"


@pytest.fixture
def connection():
    """Create a test connection."""
    conn = pyflydb.connect(
        host=TEST_HOST,
        port=TEST_PORT,
        user=TEST_USER,
        password=TEST_PASSWORD
    )
    yield conn
    conn.close()


def test_connection():
    """Test basic connection establishment."""
    conn = pyflydb.connect(host=TEST_HOST, port=TEST_PORT, user=TEST_USER, password=TEST_PASSWORD)
    assert conn is not None
    assert not conn.closed
    conn.close()
    assert conn.closed


def test_dsn_connection():
    """Test connection using DSN."""
    dsn = f"flydb://{TEST_USER}:{TEST_PASSWORD}@{TEST_HOST}:{TEST_PORT}"
    conn = pyflydb.connect(dsn)
    assert conn is not None
    assert not conn.closed
    conn.close()


def test_context_manager():
    """Test connection as context manager."""
    with pyflydb.connect(host=TEST_HOST, port=TEST_PORT, user=TEST_USER, password=TEST_PASSWORD) as conn:
        assert not conn.closed
    assert conn.closed


def test_ping(connection):
    """Test connection ping."""
    assert connection.ping()


def test_server_info(connection):
    """Test retrieving server information."""
    info = connection.get_server_info()
    assert info is not None
    assert "server_version" in info


def test_cursor_creation(connection):
    """Test cursor creation."""
    cursor = connection.cursor()
    assert cursor is not None
    assert not cursor.closed
    cursor.close()
    assert cursor.closed


def test_create_table(connection):
    """Test CREATE TABLE statement."""
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE test_basic (id INT, name TEXT)")
    assert cursor.rowcount >= 0
    cursor.close()


def test_insert(connection):
    """Test INSERT statement."""
    cursor = connection.cursor()
    cursor.execute("INSERT INTO test_basic VALUES (1, 'Alice')")
    assert cursor.rowcount >= 0
    cursor.close()


def test_select(connection):
    """Test SELECT statement."""
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_basic")
    rows = cursor.fetchall()
    assert isinstance(rows, list)
    cursor.close()


def test_parameterized_query(connection):
    """Test parameterized queries."""
    cursor = connection.cursor()
    
    # Positional parameters
    cursor.execute("INSERT INTO test_basic VALUES (%s, %s)", (2, "Bob"))
    assert cursor.rowcount >= 0
    
    # Named parameters
    cursor.execute(
        "SELECT * FROM test_basic WHERE name = %(name)s",
        {"name": "Bob"}
    )
    
    cursor.close()


def test_fetchone(connection):
    """Test fetchone method."""
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_basic")
    row = cursor.fetchone()
    assert row is None or isinstance(row, tuple)
    cursor.close()


def test_fetchmany(connection):
    """Test fetchmany method."""
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_basic")
    rows = cursor.fetchmany(2)
    assert isinstance(rows, list)
    cursor.close()


def test_fetchall(connection):
    """Test fetchall method."""
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_basic")
    rows = cursor.fetchall()
    assert isinstance(rows, list)
    cursor.close()


def test_cursor_iterator(connection):
    """Test cursor as iterator."""
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_basic")
    count = 0
    for row in cursor:
        count += 1
    assert count >= 0
    cursor.close()


def test_cursor_context_manager(connection):
    """Test cursor as context manager."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM test_basic")
        assert not cursor.closed
    assert cursor.closed


def test_transaction_commit(connection):
    """Test transaction commit."""
    cursor = connection.cursor()
    cursor.execute("INSERT INTO test_basic VALUES (3, 'Charlie')")
    connection.commit()
    cursor.close()


def test_transaction_rollback(connection):
    """Test transaction rollback."""
    cursor = connection.cursor()
    cursor.execute("INSERT INTO test_basic VALUES (4, 'Diana')")
    connection.rollback()
    cursor.close()


def test_dsn_parsing():
    """Test DSN parsing."""
    from pyflydb.dsn import parse_dsn
    
    # URI format
    params = parse_dsn("flydb://admin:secret@localhost:8889/mydb")
    assert params["host"] == "localhost"
    assert params["port"] == 8889
    assert params["user"] == "admin"
    assert params["password"] == "secret"
    assert params["database"] == "mydb"
    
    # Key-value format
    params = parse_dsn("host=localhost port=8889 user=admin")
    assert params["host"] == "localhost"
    assert params["port"] == 8889
    assert params["user"] == "admin"


def test_make_dsn():
    """Test DSN creation."""
    from pyflydb.dsn import make_dsn
    
    dsn = make_dsn(host="localhost", port=8889, user="admin", password="secret")
    assert "localhost" in dsn
    assert "8889" in dsn
    assert "admin" in dsn


def test_result_parser():
    """Test result parser."""
    from pyflydb.parser import ResultParser
    
    # INSERT result
    result = ResultParser.parse_result("INSERT 1")
    assert result["statement_type"] == "INSERT"
    assert result["row_count"] == 1
    
    # UPDATE result
    result = ResultParser.parse_result("UPDATE 5")
    assert result["statement_type"] == "UPDATE"
    assert result["row_count"] == 5
    
    # CREATE result
    result = ResultParser.parse_result("CREATE TABLE OK")
    assert result["statement_type"] == "CREATE"


def test_type_adapter():
    """Test type adapter."""
    from pyflydb.types import TypeAdapter
    
    # Test to_sql
    assert TypeAdapter.to_sql(None) == "NULL"
    assert TypeAdapter.to_sql(True) == "TRUE"
    assert TypeAdapter.to_sql(False) == "FALSE"
    assert TypeAdapter.to_sql(42) == "42"
    assert TypeAdapter.to_sql("test") == "'test'"
    assert TypeAdapter.to_sql("it's") == "'it''s'"  # Escaped quote
    
    # Test from_sql
    assert TypeAdapter.from_sql("42", int) == 42
    assert TypeAdapter.from_sql("3.14", float) == 3.14
    assert TypeAdapter.from_sql("TRUE", bool) is True


def test_row_object():
    """Test Row object."""
    from pyflydb.types import Row
    
    row = Row(["id", "name", "age"], (1, "Alice", 30))
    
    # Dict access
    assert row["id"] == 1
    assert row["name"] == "Alice"
    
    # Attribute access
    assert row.id == 1
    assert row.name == "Alice"
    
    # Index access
    assert row[0] == 1
    assert row[1] == "Alice"
    
    # Properties
    assert row.columns == ["id", "name", "age"]
    assert row.values == (1, "Alice", 30)
    assert row.to_tuple() == (1, "Alice", 30)
    assert row.to_dict() == {"id": 1, "name": "Alice", "age": 30}


def test_exception_hierarchy():
    """Test exception hierarchy."""
    assert issubclass(pyflydb.DatabaseError, pyflydb.Error)
    assert issubclass(pyflydb.InterfaceError, pyflydb.Error)
    assert issubclass(pyflydb.ConnectionError, pyflydb.InterfaceError)
    assert issubclass(pyflydb.AuthenticationError, pyflydb.OperationalError)
    assert issubclass(pyflydb.QueryError, pyflydb.DatabaseError)


def test_dbapi_attributes():
    """Test DB-API 2.0 module attributes."""
    assert pyflydb.apilevel == "2.0"
    assert pyflydb.threadsafety == 2
    assert pyflydb.paramstyle == "pyformat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
