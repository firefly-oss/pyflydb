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
pyFlyDb - Python Driver for FlyDB

A professional, high-performance Python database driver for FlyDB, inspired by psycopg3.
Implements the Python DB-API 2.0 specification for database access.

Basic Usage:
    import pyflydb
    
    # Connect to FlyDB
    conn = pyflydb.connect(
        host="localhost",
        port=8889,
        user="admin",
        password="secret"
    )
    
    # Execute queries
    with conn.cursor() as cursor:
        cursor.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
        cursor.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
        cursor.execute("SELECT * FROM users")
        
        for row in cursor:
            print(row)
    
    # Commit and close
    conn.commit()
    conn.close()

Context Manager Usage:
    with pyflydb.connect(host="localhost", port=8889) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()

Features:
    - Full binary protocol support for efficient communication
    - DB-API 2.0 compliant
    - Connection pooling support
    - Transaction management
    - Prepared statements
    - Type conversion with Pydantic
    - Context managers for automatic resource cleanup
    - Thread-safe connections
"""

__version__ = "1.0.0"
__author__ = "Firefly Software Solutions Inc."
__license__ = "Apache-2.0"

# Core connection and cursor classes
from .connection import Connection, connect, apilevel, threadsafety, paramstyle
from .cursor import Cursor

# Exception hierarchy
from .exceptions import (
    # Base exceptions
    Warning,
    Error,
    
    # DB-API 2.0 exceptions
    InterfaceError,
    DatabaseError,
    DataError,
    OperationalError,
    IntegrityError,
    InternalError,
    ProgrammingError,
    NotSupportedError,
    
    # FlyDB-specific exceptions
    ConnectionError,
    ProtocolError,
    AuthenticationError,
    QueryError,
    TransactionError,
    CursorError,
    PoolError,
    TimeoutError,
)

# Protocol types (for advanced usage)
from .protocol import MessageType, MessageFlag

# Type adapters and row objects
from .types import Row, TypeAdapter, DatabaseModel

# Parser
from .parser import ResultParser

# DSN utilities
from .dsn import parse_dsn, make_dsn

# Public API
__all__ = [
    # Version
    "__version__",
    
    # Core classes
    "Connection",
    "Cursor",
    "connect",
    
    # DB-API 2.0 attributes
    "apilevel",
    "threadsafety",
    "paramstyle",
    
    # Base exceptions
    "Warning",
    "Error",
    
    # DB-API 2.0 exceptions
    "InterfaceError",
    "DatabaseError",
    "DataError",
    "OperationalError",
    "IntegrityError",
    "InternalError",
    "ProgrammingError",
    "NotSupportedError",
    
    # FlyDB-specific exceptions
    "ConnectionError",
    "ProtocolError",
    "AuthenticationError",
    "QueryError",
    "TransactionError",
    "CursorError",
    "PoolError",
    "TimeoutError",
    
    # Protocol types
    "MessageType",
    "MessageFlag",
    
    # Type adapters
    "Row",
    "TypeAdapter",
    "DatabaseModel",
    
    # Parser
    "ResultParser",
    
    # DSN utilities
    "parse_dsn",
    "make_dsn",
]
