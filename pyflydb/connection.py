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
FlyDB Connection Management.

This module provides the Connection class for managing connections to FlyDB servers
using the binary protocol. It handles connection lifecycle, authentication, and
provides a factory for creating cursors.

The design is inspired by psycopg3's connection interface.
"""

import socket
import threading
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager

from . import exceptions
from .protocol import (
    HEADER_SIZE,
    Message,
    MessageHeader,
    MessageType,
    create_auth_message,
    create_ping_message,
    create_begin_tx_message,
    create_commit_tx_message,
    create_rollback_tx_message,
    create_get_server_info_message,
)


# DB-API 2.0 module-level attributes
apilevel = "2.0"
threadsafety = 2  # Threads may share the module and connections
paramstyle = "pyformat"  # Python extended format codes, e.g. ...WHERE name=%(name)s


class Connection:
    """
    Connection to a FlyDB server using the binary protocol.
    
    This class manages the lifecycle of a database connection, including:
    - Establishing TCP connection to the server
    - Authenticating with username/password
    - Managing transaction state
    - Creating cursors for query execution
    - Proper cleanup on close
    
    Connections can be used as context managers for automatic cleanup:
        
        with pyflydb.connect(host="localhost", port=8889) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    
    Thread Safety:
        Connections are thread-safe for concurrent use, but it's recommended
        to use one connection per thread or use connection pooling.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8889,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        autocommit: bool = False,
    ):
        """
        Initialize a connection to FlyDB.
        
        Args:
            host: Hostname or IP address of the FlyDB server
            port: Port number for the binary protocol (default: 8889)
            user: Username for authentication (optional for public access)
            password: Password for authentication
            database: Database name (for future multi-database support)
            connect_timeout: Timeout in seconds for connection establishment
            autocommit: Whether to automatically commit transactions
            
        Raises:
            exceptions.ConnectionError: If connection fails
            exceptions.AuthenticationError: If authentication fails
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.autocommit = autocommit
        self.connect_timeout = connect_timeout
        
        # Connection state
        self._socket: Optional[socket.socket] = None
        self._closed = False
        self._authenticated = False
        self._in_transaction = False
        self._server_info: Optional[Dict[str, Any]] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Establish connection
        self._connect()
        
        # Authenticate if credentials provided
        if user and password:
            self._authenticate()
    
    def _connect(self) -> None:
        """
        Establish TCP connection to the FlyDB server.
        
        Raises:
            exceptions.ConnectionError: If connection fails
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.connect_timeout:
                self._socket.settimeout(self.connect_timeout)
            
            self._socket.connect((self.host, self.port))
            
            # Set socket to blocking mode after connection
            self._socket.settimeout(None)
            
        except socket.timeout as e:
            raise exceptions.TimeoutError(
                f"Connection to {self.host}:{self.port} timed out"
            ) from e
        except socket.error as e:
            raise exceptions.ConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {e}"
            ) from e
    
    def _authenticate(self) -> None:
        """
        Authenticate with the FlyDB server.
        
        Raises:
            exceptions.AuthenticationError: If authentication fails
        """
        if not self.user or not self.password:
            return
        
        # Create and send authentication message
        auth_msg = create_auth_message(self.user, self.password)
        self._send_message(auth_msg)
        
        # Receive authentication response
        response = self._receive_message()
        
        if response.msg_type == MessageType.AUTH_RESULT:
            payload = response.payload
            if payload.get("success"):
                self._authenticated = True
            else:
                raise exceptions.AuthenticationError(
                    payload.get("message", "Authentication failed")
                )
        elif response.msg_type == MessageType.ERROR:
            raise exceptions.AuthenticationError(
                response.payload.get("message", "Authentication error")
            )
        else:
            raise exceptions.ProtocolError(
                f"Unexpected response to AUTH: {response.msg_type}"
            )
    
    def _send_message(self, message: Message) -> None:
        """
        Send a message to the server.
        
        Args:
            message: Message to send
            
        Raises:
            exceptions.ConnectionError: If sending fails
            exceptions.InterfaceError: If connection is closed
        """
        with self._lock:
            if self._closed:
                raise exceptions.InterfaceError("Connection is closed")
            
            if not self._socket:
                raise exceptions.InterfaceError("Not connected")
            
            try:
                data = message.to_bytes()
                self._socket.sendall(data)
            except socket.error as e:
                self._closed = True
                raise exceptions.ConnectionError(f"Failed to send message: {e}") from e
    
    def _receive_message(self) -> Message:
        """
        Receive a message from the server.
        
        Returns:
            Received message
            
        Raises:
            exceptions.ConnectionError: If receiving fails
            exceptions.ProtocolError: If message format is invalid
        """
        with self._lock:
            if self._closed:
                raise exceptions.InterfaceError("Connection is closed")
            
            if not self._socket:
                raise exceptions.InterfaceError("Not connected")
            
            try:
                # Read header
                header_data = self._recv_exactly(HEADER_SIZE)
                header = MessageHeader.from_bytes(header_data)
                
                # Read payload
                payload_data = b""
                if header.length > 0:
                    payload_data = self._recv_exactly(header.length)
                
                # Decode message
                message = Message.from_bytes(header, payload_data)
                return message
                
            except socket.error as e:
                self._closed = True
                raise exceptions.ConnectionError(f"Failed to receive message: {e}") from e
    
    def _recv_exactly(self, n: int) -> bytes:
        """
        Receive exactly n bytes from the socket.
        
        Args:
            n: Number of bytes to receive
            
        Returns:
            Received bytes
            
        Raises:
            exceptions.ConnectionError: If connection is lost
        """
        data = b""
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                raise exceptions.ConnectionError("Connection lost while reading data")
            data += chunk
        return data
    
    def cursor(self) -> "Cursor":
        """
        Create a new cursor for executing queries.
        
        Returns:
            A new Cursor instance
            
        Raises:
            exceptions.InterfaceError: If connection is closed
            
        Example:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
        """
        if self._closed:
            raise exceptions.InterfaceError("Connection is closed")
        
        # Import here to avoid circular dependency
        from .cursor import Cursor
        return Cursor(self)
    
    def commit(self) -> None:
        """
        Commit the current transaction.
        
        If autocommit is enabled, this is a no-op.
        
        Raises:
            exceptions.TransactionError: If commit fails
            exceptions.InterfaceError: If connection is closed
        """
        if self._closed:
            raise exceptions.InterfaceError("Connection is closed")
        
        if self.autocommit:
            return
        
        if not self._in_transaction:
            return
        
        # Send commit message
        commit_msg = create_commit_tx_message()
        self._send_message(commit_msg)
        
        # Receive response
        response = self._receive_message()
        
        if response.msg_type == MessageType.TX_RESULT:
            if response.payload.get("success"):
                self._in_transaction = False
            else:
                raise exceptions.TransactionError(
                    response.payload.get("message", "Commit failed")
                )
        elif response.msg_type == MessageType.ERROR:
            raise exceptions.TransactionError(
                response.payload.get("message", "Commit error")
            )
        else:
            raise exceptions.ProtocolError(
                f"Unexpected response to COMMIT: {response.msg_type}"
            )
    
    def rollback(self) -> None:
        """
        Rollback the current transaction.
        
        If autocommit is enabled, this is a no-op.
        
        Raises:
            exceptions.TransactionError: If rollback fails
            exceptions.InterfaceError: If connection is closed
        """
        if self._closed:
            raise exceptions.InterfaceError("Connection is closed")
        
        if self.autocommit:
            return
        
        if not self._in_transaction:
            return
        
        # Send rollback message
        rollback_msg = create_rollback_tx_message()
        self._send_message(rollback_msg)
        
        # Receive response
        response = self._receive_message()
        
        if response.msg_type == MessageType.TX_RESULT:
            if response.payload.get("success"):
                self._in_transaction = False
            else:
                raise exceptions.TransactionError(
                    response.payload.get("message", "Rollback failed")
                )
        elif response.msg_type == MessageType.ERROR:
            raise exceptions.TransactionError(
                response.payload.get("message", "Rollback error")
            )
        else:
            raise exceptions.ProtocolError(
                f"Unexpected response to ROLLBACK: {response.msg_type}"
            )
    
    def ping(self) -> bool:
        """
        Send a ping to check if the connection is alive.
        
        Returns:
            True if server responds, False otherwise
        """
        if self._closed:
            return False
        
        try:
            ping_msg = create_ping_message()
            self._send_message(ping_msg)
            response = self._receive_message()
            return response.msg_type == MessageType.PONG
        except Exception:
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the FlyDB server.
        
        Returns:
            Dictionary with server information including version, capabilities, etc.
            
        Raises:
            exceptions.InterfaceError: If connection is closed
        """
        if self._closed:
            raise exceptions.InterfaceError("Connection is closed")
        
        # Return cached info if available
        if self._server_info:
            return self._server_info
        
        # Request server info
        info_msg = create_get_server_info_message()
        self._send_message(info_msg)
        
        response = self._receive_message()
        
        if response.msg_type == MessageType.SESSION_RESULT:
            self._server_info = response.payload
            return self._server_info
        elif response.msg_type == MessageType.ERROR:
            raise exceptions.DatabaseError(
                response.payload.get("message", "Failed to get server info")
            )
        else:
            raise exceptions.ProtocolError(
                f"Unexpected response to GET_SERVER_INFO: {response.msg_type}"
            )
    
    def close(self) -> None:
        """
        Close the connection to the server.
        
        This releases all resources associated with the connection.
        After closing, the connection cannot be used again.
        
        It's safe to call close() multiple times.
        """
        with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            # Rollback any active transaction
            if self._in_transaction:
                try:
                    self.rollback()
                except Exception:
                    pass  # Ignore errors during cleanup
            
            # Close the socket
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass  # Ignore errors during cleanup
                finally:
                    self._socket = None
    
    @property
    def closed(self) -> bool:
        """Check if the connection is closed."""
        return self._closed
    
    def __enter__(self) -> "Connection":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes connection."""
        if exc_type is not None:
            # Rollback on exception
            try:
                self.rollback()
            except Exception:
                pass
        else:
            # Commit on success (if not autocommit)
            if not self.autocommit and self._in_transaction:
                try:
                    self.commit()
                except Exception:
                    pass
        
        self.close()
    
    def __del__(self) -> None:
        """Destructor - ensure connection is closed."""
        try:
            self.close()
        except Exception:
            pass


def connect(
    dsn: Optional[str] = None,
    host: str = "localhost",
    port: int = 8889,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    connect_timeout: Optional[float] = None,
    autocommit: bool = False,
    **kwargs
) -> Connection:
    """
    Create a connection to a FlyDB server.
    
    This is the primary way to connect to FlyDB from Python.
    
    Args:
        dsn: Connection string (flydb://user:pass@host:port/db or key=value format)
        host: Hostname or IP address of the FlyDB server
        port: Port number for the binary protocol (default: 8889)
        user: Username for authentication
        password: Password for authentication
        database: Database name (reserved for future use)
        connect_timeout: Timeout in seconds for connection establishment
        autocommit: Whether to automatically commit transactions
        **kwargs: Additional connection parameters
        
    Returns:
        A connected Connection instance
        
    Raises:
        exceptions.ConnectionError: If connection fails
        exceptions.AuthenticationError: If authentication fails
        
    Example:
        # Connect with DSN
        conn = pyflydb.connect("flydb://admin:secret@localhost:8889")
        
        # Connect with parameters
        conn = pyflydb.connect(
            host="localhost",
            port=8889,
            user="admin",
            password="secret"
        )
        
        # Use as context manager
        with pyflydb.connect(host="localhost", port=8889) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    # Parse DSN if provided
    if dsn:
        from .dsn import parse_dsn
        params = parse_dsn(dsn)
        # Override with explicit parameters
        if host != "localhost":
            params["host"] = host
        if port != 8889:
            params["port"] = port
        if user is not None:
            params["user"] = user
        if password is not None:
            params["password"] = password
        if database is not None:
            params["database"] = database
        if connect_timeout is not None:
            params["connect_timeout"] = connect_timeout
        params["autocommit"] = autocommit
        params.update(kwargs)
        return Connection(**params)
    
    return Connection(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=connect_timeout,
        autocommit=autocommit,
    )
