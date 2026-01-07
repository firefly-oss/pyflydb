# pyFlyDb

**A professional Python driver for FlyDB - Inspired by psycopg3**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

pyFlyDb is a high-performance, DB-API 2.0 compliant Python driver for FlyDB. It uses FlyDB's native binary protocol for efficient communication and provides a familiar, Pythonic interface inspired by psycopg3.

## Features

- **Full Binary Protocol Support** - Efficient communication using FlyDB's native protocol
- **DB-API 2.0 Compliant** - Standard Python database interface
- **Type Safety** - Built with Pydantic for robust type handling
- **Context Managers** - Automatic resource cleanup
- **Transaction Management** - Full transaction support with commit and rollback
- **Thread-Safe** - Safe for concurrent use
- **DSN Connection Strings** - Support for URI and key-value connection strings
- **Enhanced Result Parsing** - Intelligent parsing of FlyDB query results
- **Comprehensive Error Handling** - Full exception hierarchy following DB-API 2.0

## Installation

```bash
# Install from source
cd pyFlyDb
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
import pyflydb

# Connect to FlyDB
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    user="admin",
    password="your_password"
)

# Create a cursor and execute queries
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
cursor.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
cursor.execute("INSERT INTO users VALUES (2, 'Bob', 25)")

# Fetch results
cursor.execute("SELECT * FROM users")
for row in cursor:
    print(row)  # (1, 'Alice', 30)

# Commit and close
conn.commit()
cursor.close()
conn.close()
```

## Using Context Managers (Recommended)

```python
import pyflydb

# Automatic connection and transaction management
with pyflydb.connect(host="localhost", port=8889, user="admin", password="secret") as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE age > %s", (25,))
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"User: {row[1]}, Age: {row[2]}")
    # Cursor automatically closed
    # Transaction automatically committed (or rolled back on error)
# Connection automatically closed
```

## Parameterized Queries

### Positional Parameters

```python
cursor.execute(
    "INSERT INTO users VALUES (%s, %s, %s)",
    (3, "Charlie", 35)
)

cursor.execute(
    "SELECT * FROM users WHERE age > %s AND name LIKE %s",
    (25, "A%")
)
```

### Named Parameters

```python
cursor.execute(
    "INSERT INTO users VALUES (%(id)s, %(name)s, %(age)s)",
    {"id": 4, "name": "Diana", "age": 28}
)

cursor.execute(
    "SELECT * FROM users WHERE name = %(name)s",
    {"name": "Alice"}
)
```

## Transaction Management

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)

try:
    cursor = conn.cursor()
    
    # Execute multiple operations
    cursor.execute("INSERT INTO users VALUES (5, 'Eve', 32)")
    cursor.execute("UPDATE users SET age = 33 WHERE id = 5")
    
    # Commit the transaction
    conn.commit()
except Exception as e:
    # Rollback on error
    conn.rollback()
    print(f"Transaction failed: {e}")
finally:
    conn.close()
```

### Autocommit Mode

```python
# Disable transaction management for simple queries
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    autocommit=True
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
# No need to call commit()
```

## Fetching Results

### fetchone() - Get next row

```python
cursor.execute("SELECT * FROM users")
row = cursor.fetchone()
while row:
    print(row)
    row = cursor.fetchone()
```

### fetchmany() - Get multiple rows

```python
cursor.execute("SELECT * FROM users")
while True:
    rows = cursor.fetchmany(100)  # Fetch 100 rows at a time
    if not rows:
        break
    for row in rows:
        print(row)
```

### fetchall() - Get all rows

```python
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row)
```

### Iterator Interface

```python
cursor.execute("SELECT * FROM users")
for row in cursor:
    print(row)
```

## Batch Operations

```python
# Execute the same query with different parameters
data = [
    (6, "Frank", 29),
    (7, "Grace", 31),
    (8, "Henry", 27)
]

cursor.executemany(
    "INSERT INTO users VALUES (%s, %s, %s)",
    data
)
conn.commit()
```

## Connection Information

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)

# Check if connection is alive
if conn.ping():
    print("Connection is active")

# Get server information
info = conn.get_server_info()
print(f"Server version: {info.get('server_version')}")
print(f"Protocol version: {info.get('protocol_version')}")
print(f"Capabilities: {info.get('capabilities')}")

conn.close()
```

## Error Handling

```python
import pyflydb

try:
    conn = pyflydb.connect(
        host="localhost",
        port=8889,
        user="admin",
        password="wrong_password"
    )
except pyflydb.AuthenticationError as e:
    print(f"Authentication failed: {e}")
except pyflydb.ConnectionError as e:
    print(f"Connection failed: {e}")
except pyflydb.Error as e:
    print(f"Database error: {e}")
```

### Exception Hierarchy

```
Exception
└── Warning
└── Error
    ├── InterfaceError
    │   ├── ConnectionError
    │   ├── ProtocolError
    │   ├── CursorError
    │   └── PoolError
    └── DatabaseError
        ├── DataError
        ├── OperationalError
        │   ├── AuthenticationError
        │   ├── TransactionError
        │   └── TimeoutError
        ├── IntegrityError
        ├── InternalError
        ├── ProgrammingError
        ├── NotSupportedError
        └── QueryError
```

## DB-API 2.0 Compliance

pyFlyDb implements the [Python Database API Specification v2.0](https://peps.python.org/pep-0249/):

```python
import pyflydb

# Module-level attributes
print(pyflydb.apilevel)      # "2.0"
print(pyflydb.threadsafety)  # 2 (Threads may share module and connections)
print(pyflydb.paramstyle)    # "pyformat" (e.g., %(name)s)

# Cursor attributes
cursor.description  # Column metadata (name, type, etc.)
cursor.rowcount     # Number of rows affected/returned
cursor.arraysize    # Default number of rows for fetchmany()
```

## Connection String Format

```python
# Basic connection
conn = pyflydb.connect(host="localhost", port=8889)

# With authentication
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    user="admin",
    password="secret"
)

# With timeout
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    connect_timeout=10.0  # 10 seconds
)

# With autocommit
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    autocommit=True
)
```

## Advanced Usage

### Connection Attributes

```python
conn = pyflydb.connect(host="localhost", port=8889)

print(conn.closed)       # Check if connection is closed
print(conn.autocommit)   # Check autocommit status
print(conn.host)         # Server host
print(conn.port)         # Server port
```

### Cursor Attributes

```python
cursor = conn.cursor()
cursor.execute("SELECT id, name, age FROM users")

# Column descriptions (DB-API 2.0)
for column in cursor.description:
    print(f"Column: {column[0]}")

# Row count
print(f"Rows returned: {cursor.rowcount}")
```

## Architecture

pyFlyDb uses FlyDB's binary protocol for efficient communication:

```
┌─────────────────────────────────────────────────┐
│            Python Application                   │
└─────────────────┬───────────────────────────────┘
                  │
                  │ pyFlyDb (this driver)
                  │
┌─────────────────▼───────────────────────────────┐
│          Binary Protocol Layer                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Message Format:                         │   │
│  │  [Magic|Version|Type|Flags|Length|Data]  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
                  │ TCP Socket (port 8889)
                  │
┌─────────────────▼───────────────────────────────┐
│            FlyDB Server                         │
│  ┌──────────────────────────────────────────┐   │
│  │ • SQL Parser & Executor                  │   │
│  │ • Transaction Manager                    │   │
│  │ • Storage Engine (KVStore + WAL)        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Performance Tips

1. **Use Context Managers** - Ensures proper resource cleanup
2. **Batch Operations** - Use `executemany()` for bulk inserts
3. **Fetchmany** - For large result sets, use `fetchmany()` instead of `fetchall()`
4. **Autocommit** - Enable for read-only workloads to reduce overhead
5. **Connection Pooling** - Reuse connections across requests (coming soon)

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=pyflydb tests/
```

### Code Quality

```bash
# Format code
black pyflydb/

# Lint code
ruff pyflydb/

# Type checking
mypy pyflydb/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Copyright 2026 Firefly Software Solutions Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Acknowledgments

- Inspired by [psycopg3](https://www.psycopg.org/psycopg3/) - the excellent PostgreSQL adapter
- Built for [FlyDB](https://github.com/firefly/flydb) - a lightweight SQL database

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/firefly/pyflydb).
