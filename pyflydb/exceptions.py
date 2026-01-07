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
Exception hierarchy for pyFlyDb.

This module defines all exceptions that can be raised by the pyFlyDb driver,
following the Python DB-API 2.0 exception hierarchy with FlyDB-specific extensions.
"""

from typing import Optional


class Warning(Exception):
    """
    Base class for warning categories.
    
    Important for non-error notifications like data truncations.
    """
    pass


class Error(Exception):
    """
    Base class for all database errors.
    
    This is the root of the exception hierarchy for database-related errors.
    """
    
    def __init__(self, message: str, code: Optional[int] = None, sqlstate: Optional[str] = None):
        """
        Initialize the error with message and optional error metadata.
        
        Args:
            message: Human-readable error message
            code: FlyDB error code
            sqlstate: SQL standard SQLSTATE code
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.sqlstate = sqlstate


class InterfaceError(Error):
    """
    Exception raised for errors related to the database interface.
    
    These are errors in the driver itself, not the database.
    Examples: connection errors, protocol errors.
    """
    pass


class DatabaseError(Error):
    """
    Exception raised for errors related to the database.
    
    These are errors that come from the database server.
    """
    pass


class DataError(DatabaseError):
    """
    Exception raised for errors due to problems with the processed data.
    
    Examples: division by zero, numeric value out of range, invalid data type.
    """
    pass


class OperationalError(DatabaseError):
    """
    Exception raised for errors related to database operations.
    
    These errors are not necessarily under the control of the programmer.
    Examples: connection lost, database shutdown, transaction failed.
    """
    pass


class IntegrityError(DatabaseError):
    """
    Exception raised when the relational integrity is affected.
    
    Examples: foreign key constraint violation, duplicate key.
    """
    pass


class InternalError(DatabaseError):
    """
    Exception raised when the database encounters an internal error.
    
    Examples: cursor not valid anymore, transaction out of sync.
    """
    pass


class ProgrammingError(DatabaseError):
    """
    Exception raised for programming errors.
    
    Examples: table not found, syntax error in SQL, wrong number of parameters.
    """
    pass


class NotSupportedError(DatabaseError):
    """
    Exception raised when a method or database API is not supported.
    
    Example: requesting a feature that FlyDB doesn't implement.
    """
    pass


# FlyDB-specific exceptions

class ConnectionError(InterfaceError):
    """
    Exception raised when connection to FlyDB fails.
    
    This includes initial connection failures and connection loss during operation.
    """
    pass


class ProtocolError(InterfaceError):
    """
    Exception raised when there's an error in the binary protocol.
    
    Examples: invalid message format, unsupported protocol version, corrupted data.
    """
    pass


class AuthenticationError(OperationalError):
    """
    Exception raised when authentication fails.
    
    This occurs when provided credentials are invalid or insufficient.
    """
    pass


class QueryError(DatabaseError):
    """
    Exception raised when query execution fails.
    
    This is a general query error that doesn't fit other categories.
    """
    pass


class TransactionError(OperationalError):
    """
    Exception raised for transaction-related errors.
    
    Examples: cannot start transaction, transaction already active, rollback failed.
    """
    pass


class CursorError(InterfaceError):
    """
    Exception raised for cursor-related errors.
    
    Examples: cursor closed, invalid cursor state, fetch on non-SELECT.
    """
    pass


class PoolError(InterfaceError):
    """
    Exception raised for connection pool errors.
    
    Examples: pool exhausted, pool closed, invalid pool configuration.
    """
    pass


class TimeoutError(OperationalError):
    """
    Exception raised when an operation times out.
    
    Examples: connection timeout, query timeout, lock timeout.
    """
    pass
