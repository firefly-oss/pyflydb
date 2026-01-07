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
FlyDB Cursor Implementation.

This module provides the Cursor class for executing SQL queries and fetching results.
The design follows the Python DB-API 2.0 specification and is inspired by psycopg3.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from . import exceptions
from .protocol import (
    MessageType,
    create_query_message,
    create_prepare_message,
    create_execute_message,
    create_deallocate_message,
)
from .parser import ResultParser


class Cursor:
    """
    Database cursor for executing queries and fetching results.
    
    Cursors are created by calling Connection.cursor() and should be closed
    after use. They can be used as context managers for automatic cleanup.
    
    Example:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            row = cursor.fetchone()
            print(row)
    
    DB-API 2.0 Attributes:
        description: Column metadata (name, type, etc.)
        rowcount: Number of rows affected/returned
        arraysize: Default number of rows for fetchmany()
    """
    
    def __init__(self, connection: "Connection"):
        """
        Initialize a cursor.
        
        Args:
            connection: The Connection instance that owns this cursor
        """
        self._connection = connection
        self._closed = False
        
        # DB-API 2.0 attributes
        self.description: Optional[List[Tuple]] = None
        self.rowcount: int = -1
        self.arraysize: int = 1
        
        # Query results
        self._rows: List[List[Any]] = []
        self._row_index: int = 0
        
        # Last query information
        self._last_query: Optional[str] = None
        self._columns: List[str] = []
    
    def execute(
        self,
        query: str,
        parameters: Optional[Union[Sequence, Dict[str, Any]]] = None
    ) -> "Cursor":
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            parameters: Optional parameters for query substitution
                       Can be a sequence for positional parameters (%s)
                       or dict for named parameters (%(name)s)
        
        Returns:
            Self for method chaining
            
        Raises:
            exceptions.ProgrammingError: If query syntax is invalid
            exceptions.DatabaseError: If query execution fails
            exceptions.InterfaceError: If cursor or connection is closed
            
        Example:
            # Positional parameters
            cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
            
            # Named parameters
            cursor.execute(
                "SELECT * FROM users WHERE name = %(name)s",
                {"name": "alice"}
            )
        """
        if self._closed:
            raise exceptions.InterfaceError("Cursor is closed")
        
        if self._connection.closed:
            raise exceptions.InterfaceError("Connection is closed")
        
        # Handle parameter substitution
        if parameters:
            query = self._substitute_parameters(query, parameters)
        
        self._last_query = query
        self._reset_results()
        
        # Send query message
        query_msg = create_query_message(query)
        self._connection._send_message(query_msg)
        
        # Receive response
        response = self._connection._receive_message()
        
        # Handle response
        if response.msg_type == MessageType.QUERY_RESULT:
            self._handle_query_result(response.payload)
        elif response.msg_type == MessageType.ERROR:
            error_msg = response.payload.get("message", "Query execution failed")
            error_code = response.payload.get("code", 0)
            raise exceptions.DatabaseError(error_msg, code=error_code)
        else:
            raise exceptions.ProtocolError(
                f"Unexpected response to QUERY: {response.msg_type}"
            )
        
        return self
    
    def executemany(
        self,
        query: str,
        parameters_list: Sequence[Union[Sequence, Dict[str, Any]]]
    ) -> "Cursor":
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            parameters_list: Sequence of parameter sets
            
        Returns:
            Self for method chaining
            
        Raises:
            exceptions.DatabaseError: If any query execution fails
            
        Example:
            cursor.executemany(
                "INSERT INTO users (name, age) VALUES (%s, %s)",
                [("alice", 30), ("bob", 25), ("charlie", 35)]
            )
        """
        if self._closed:
            raise exceptions.InterfaceError("Cursor is closed")
        
        total_rowcount = 0
        
        for parameters in parameters_list:
            self.execute(query, parameters)
            if self.rowcount >= 0:
                total_rowcount += self.rowcount
        
        self.rowcount = total_rowcount
        return self
    
    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """
        Fetch the next row from the result set.
        
        Returns:
            A tuple representing the row, or None if no more rows
            
        Raises:
            exceptions.InterfaceError: If cursor is closed
            
        Example:
            cursor.execute("SELECT * FROM users")
            row = cursor.fetchone()
            while row:
                print(row)
                row = cursor.fetchone()
        """
        if self._closed:
            raise exceptions.InterfaceError("Cursor is closed")
        
        if self._row_index >= len(self._rows):
            return None
        
        row = self._rows[self._row_index]
        self._row_index += 1
        return tuple(row)
    
    def fetchmany(self, size: Optional[int] = None) -> List[Tuple[Any, ...]]:
        """
        Fetch multiple rows from the result set.
        
        Args:
            size: Number of rows to fetch (default: self.arraysize)
            
        Returns:
            List of tuples representing rows
            
        Raises:
            exceptions.InterfaceError: If cursor is closed
            
        Example:
            cursor.execute("SELECT * FROM users")
            while True:
                rows = cursor.fetchmany(100)
                if not rows:
                    break
                for row in rows:
                    print(row)
        """
        if self._closed:
            raise exceptions.InterfaceError("Cursor is closed")
        
        if size is None:
            size = self.arraysize
        
        rows = []
        for _ in range(size):
            row = self.fetchone()
            if row is None:
                break
            rows.append(row)
        
        return rows
    
    def fetchall(self) -> List[Tuple[Any, ...]]:
        """
        Fetch all remaining rows from the result set.
        
        Returns:
            List of tuples representing all remaining rows
            
        Raises:
            exceptions.InterfaceError: If cursor is closed
            
        Example:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        """
        if self._closed:
            raise exceptions.InterfaceError("Cursor is closed")
        
        rows = []
        while True:
            row = self.fetchone()
            if row is None:
                break
            rows.append(row)
        
        return rows
    
    def close(self) -> None:
        """
        Close the cursor and release resources.
        
        It's safe to call close() multiple times.
        After closing, the cursor cannot be used again.
        """
        if self._closed:
            return
        
        self._closed = True
        self._reset_results()
    
    def _reset_results(self) -> None:
        """Reset result state for a new query."""
        self._rows = []
        self._row_index = 0
        self._columns = []
        self.description = None
        self.rowcount = -1
    
    def _handle_query_result(self, payload: Dict[str, Any]) -> None:
        """
        Handle a query result payload.
        
        Args:
            payload: The query result payload from the server
        """
        success = payload.get("success", False)
        
        if not success:
            error_msg = payload.get("message", "Query failed")
            raise exceptions.QueryError(error_msg)
        
        # Parse the result message using enhanced parser
        message = payload.get("message", "")
        parsed = ResultParser.parse_result(message, success)
        
        # Extract columns from parsed result or original payload
        self._columns = parsed.get("columns") or payload.get("columns") or []
        
        # Build description tuple (DB-API 2.0)
        # Set to None for non-SELECT queries (no columns)
        if self._columns:
            self.description = [
                (name, None, None, None, None, None, None)
                for name in self._columns
            ]
        else:
            self.description = None
        
        # Extract rows from parsed result or original payload
        rows = parsed.get("rows") or payload.get("rows")
        self._rows = rows if rows else []
        
        # Set rowcount from parsed result or original payload
        self.rowcount = parsed.get("row_count") or payload.get("row_count", len(self._rows))
        
        # Reset row index
        self._row_index = 0
    
    def _substitute_parameters(
        self,
        query: str,
        parameters: Union[Sequence, Dict[str, Any]]
    ) -> str:
        """
        Substitute parameters into the query string.
        
        Args:
            query: SQL query with placeholders
            parameters: Parameters to substitute
            
        Returns:
            Query with parameters substituted
            
        Note:
            This is a simple implementation. In production, you'd want
            proper SQL escaping and parameterized queries.
        """
        if isinstance(parameters, dict):
            # Named parameters: %(name)s
            return query % {k: self._escape_value(v) for k, v in parameters.items()}
        else:
            # Positional parameters: %s
            # Convert to tuple if it's a list
            if isinstance(parameters, list):
                parameters = tuple(parameters)
            
            # Simple substitution - replace %s with values
            parts = query.split("%s")
            if len(parts) - 1 != len(parameters):
                raise exceptions.ProgrammingError(
                    f"Query requires {len(parts) - 1} parameters, but {len(parameters)} provided"
                )
            
            result = []
            for i, part in enumerate(parts[:-1]):
                result.append(part)
                result.append(self._escape_value(parameters[i]))
            result.append(parts[-1])
            
            return "".join(result)
    
    def _escape_value(self, value: Any) -> str:
        """
        Escape a value for SQL.
        
        Args:
            value: Value to escape
            
        Returns:
            Escaped string representation
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes by doubling them
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            # For other types, convert to string and escape
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    @property
    def closed(self) -> bool:
        """Check if the cursor is closed."""
        return self._closed
    
    def __enter__(self) -> "Cursor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes cursor."""
        self.close()
    
    def __iter__(self) -> "Cursor":
        """Make cursor iterable."""
        return self
    
    def __next__(self) -> Tuple[Any, ...]:
        """Iterator next - fetch next row."""
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row
