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
FlyDB Binary Protocol Implementation.

This module implements the FlyDB binary wire protocol for efficient
communication with the FlyDB server. The protocol uses a type-length-value
encoding with a fixed-size header.

Protocol Format:
    +--------+--------+--------+--------+--------+--------+...
    | Magic  | Version| MsgType| Flags  |    Length (4B)   | Payload...
    +--------+--------+--------+--------+--------+--------+...

Header Fields:
    - Magic (1 byte): Protocol magic number (0xFD for FlyDB)
    - Version (1 byte): Protocol version (currently 0x01)
    - MsgType (1 byte): Message type identifier
    - Flags (1 byte): Message flags (compression, encryption, etc.)
    - Length (4 bytes): Payload length in big-endian format
    - Payload: Variable-length JSON-encoded message data
"""

import json
import struct
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple
from io import BytesIO

from .exceptions import ProtocolError


# Protocol constants
MAGIC_BYTE = 0xFD  # FlyDB magic byte
PROTOCOL_VERSION = 0x01  # Current protocol version
HEADER_SIZE = 8  # Size of the message header in bytes
MAX_MESSAGE_SIZE = 16 * 1024 * 1024  # Maximum message size (16 MB)


class MessageType(IntEnum):
    """
    Message type identifiers for the FlyDB binary protocol.
    
    These match the message types defined in FlyDB's internal/protocol/protocol.go
    """
    # Core messages (0x01-0x0F)
    QUERY = 0x01
    QUERY_RESULT = 0x02
    ERROR = 0x03
    PREPARE = 0x04
    PREPARE_RESULT = 0x05
    EXECUTE = 0x06
    DEALLOCATE = 0x07
    AUTH = 0x08
    AUTH_RESULT = 0x09
    PING = 0x0A
    PONG = 0x0B
    
    # Cursor operations (0x10-0x1F)
    CURSOR_OPEN = 0x10
    CURSOR_FETCH = 0x11
    CURSOR_CLOSE = 0x12
    CURSOR_SCROLL = 0x13
    CURSOR_RESULT = 0x14
    
    # Metadata operations (0x20-0x2F)
    GET_TABLES = 0x20
    GET_COLUMNS = 0x21
    GET_PRIMARY_KEYS = 0x22
    GET_FOREIGN_KEYS = 0x23
    GET_INDEXES = 0x24
    GET_TYPE_INFO = 0x25
    METADATA_RESULT = 0x26
    
    # Transaction operations (0x30-0x3F)
    BEGIN_TX = 0x30
    COMMIT_TX = 0x31
    ROLLBACK_TX = 0x32
    SAVEPOINT = 0x33
    TX_RESULT = 0x34
    
    # Session operations (0x40-0x4F)
    SET_OPTION = 0x40
    GET_OPTION = 0x41
    GET_SERVER_INFO = 0x42
    SESSION_RESULT = 0x43


class MessageFlag(IntEnum):
    """Message flags for optional features."""
    NONE = 0x00
    COMPRESSED = 0x01
    ENCRYPTED = 0x02


class MessageHeader:
    """
    Represents a FlyDB protocol message header.
    
    The header contains metadata about the message including type, size, and flags.
    """
    
    def __init__(
        self,
        msg_type: MessageType,
        length: int,
        magic: int = MAGIC_BYTE,
        version: int = PROTOCOL_VERSION,
        flags: MessageFlag = MessageFlag.NONE,
    ):
        """
        Initialize a message header.
        
        Args:
            msg_type: The type of message
            length: Length of the payload in bytes
            magic: Protocol magic byte (default: MAGIC_BYTE)
            version: Protocol version (default: PROTOCOL_VERSION)
            flags: Message flags (default: MessageFlag.NONE)
        """
        self.magic = magic
        self.version = version
        self.msg_type = msg_type
        self.flags = flags
        self.length = length
    
    def to_bytes(self) -> bytes:
        """
        Encode the header to bytes.
        
        Returns:
            8-byte header in wire format
            
        Raises:
            ProtocolError: If header values are invalid
        """
        if self.length > MAX_MESSAGE_SIZE:
            raise ProtocolError(f"Message size {self.length} exceeds maximum {MAX_MESSAGE_SIZE}")
        
        # Pack header: 4 bytes + 4-byte length (big-endian)
        return struct.pack(
            ">BBBBI",
            self.magic,
            self.version,
            self.msg_type,
            self.flags,
            self.length,
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageHeader":
        """
        Decode a header from bytes.
        
        Args:
            data: 8-byte header data
            
        Returns:
            Decoded MessageHeader instance
            
        Raises:
            ProtocolError: If header is invalid or unsupported
        """
        if len(data) < HEADER_SIZE:
            raise ProtocolError(f"Invalid header size: {len(data)} bytes, expected {HEADER_SIZE}")
        
        magic, version, msg_type, flags, length = struct.unpack(">BBBBI", data[:HEADER_SIZE])
        
        # Validate magic byte
        if magic != MAGIC_BYTE:
            raise ProtocolError(f"Invalid magic byte: 0x{magic:02X}, expected 0x{MAGIC_BYTE:02X}")
        
        # Validate protocol version
        if version != PROTOCOL_VERSION:
            raise ProtocolError(
                f"Unsupported protocol version: 0x{version:02X}, expected 0x{PROTOCOL_VERSION:02X}"
            )
        
        # Validate message size
        if length > MAX_MESSAGE_SIZE:
            raise ProtocolError(f"Message size {length} exceeds maximum {MAX_MESSAGE_SIZE}")
        
        return cls(
            msg_type=MessageType(msg_type),
            length=length,
            magic=magic,
            version=version,
            flags=MessageFlag(flags),
        )


class Message:
    """
    Represents a complete FlyDB protocol message.
    
    A message consists of a header and an optional JSON payload.
    """
    
    def __init__(self, msg_type: MessageType, payload: Optional[Dict[str, Any]] = None):
        """
        Initialize a message.
        
        Args:
            msg_type: The type of message
            payload: Optional dictionary payload (will be JSON-encoded)
        """
        self.msg_type = msg_type
        self.payload = payload or {}
    
    def to_bytes(self) -> bytes:
        """
        Encode the complete message to bytes.
        
        Returns:
            Message in wire format (header + payload)
            
        Raises:
            ProtocolError: If encoding fails
        """
        try:
            # Encode payload as JSON
            payload_bytes = json.dumps(self.payload).encode("utf-8") if self.payload else b""
            
            # Create and encode header
            header = MessageHeader(msg_type=self.msg_type, length=len(payload_bytes))
            header_bytes = header.to_bytes()
            
            return header_bytes + payload_bytes
        except Exception as e:
            raise ProtocolError(f"Failed to encode message: {e}") from e
    
    @classmethod
    def from_bytes(cls, header: MessageHeader, payload_data: bytes) -> "Message":
        """
        Decode a message from header and payload data.
        
        Args:
            header: Already-decoded message header
            payload_data: Raw payload bytes
            
        Returns:
            Decoded Message instance
            
        Raises:
            ProtocolError: If decoding fails
        """
        try:
            # Decode JSON payload if present
            payload = json.loads(payload_data.decode("utf-8")) if payload_data else {}
            
            msg = cls(msg_type=header.msg_type, payload=payload)
            return msg
        except Exception as e:
            raise ProtocolError(f"Failed to decode message: {e}") from e


# Message creation helpers for common message types

def create_auth_message(username: str, password: str) -> Message:
    """Create an authentication message."""
    return Message(MessageType.AUTH, {"username": username, "password": password})


def create_query_message(query: str) -> Message:
    """Create a query execution message."""
    return Message(MessageType.QUERY, {"query": query})


def create_prepare_message(name: str, query: str) -> Message:
    """Create a prepared statement message."""
    return Message(MessageType.PREPARE, {"name": name, "query": query})


def create_execute_message(name: str, params: List[Any]) -> Message:
    """Create an execute prepared statement message."""
    return Message(MessageType.EXECUTE, {"name": name, "params": params})


def create_deallocate_message(name: str) -> Message:
    """Create a deallocate prepared statement message."""
    return Message(MessageType.DEALLOCATE, {"name": name})


def create_ping_message() -> Message:
    """Create a ping message."""
    return Message(MessageType.PING)


def create_begin_tx_message(
    isolation_level: int = 1, read_only: bool = False, deferrable: bool = False
) -> Message:
    """Create a begin transaction message."""
    return Message(
        MessageType.BEGIN_TX,
        {"isolation_level": isolation_level, "read_only": read_only, "deferrable": deferrable},
    )


def create_commit_tx_message() -> Message:
    """Create a commit transaction message."""
    return Message(MessageType.COMMIT_TX)


def create_rollback_tx_message() -> Message:
    """Create a rollback transaction message."""
    return Message(MessageType.ROLLBACK_TX)


def create_get_tables_message(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    table_name: Optional[str] = None,
    table_types: Optional[List[str]] = None,
) -> Message:
    """Create a get tables metadata message."""
    payload = {}
    if catalog is not None:
        payload["catalog"] = catalog
    if schema is not None:
        payload["schema"] = schema
    if table_name is not None:
        payload["table_name"] = table_name
    if table_types is not None:
        payload["table_types"] = table_types
    return Message(MessageType.GET_TABLES, payload)


def create_get_columns_message(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    table_name: Optional[str] = None,
    column_name: Optional[str] = None,
) -> Message:
    """Create a get columns metadata message."""
    payload = {}
    if catalog is not None:
        payload["catalog"] = catalog
    if schema is not None:
        payload["schema"] = schema
    if table_name is not None:
        payload["table_name"] = table_name
    if column_name is not None:
        payload["column_name"] = column_name
    return Message(MessageType.GET_COLUMNS, payload)


def create_set_option_message(option: str, value: Any) -> Message:
    """Create a set session option message."""
    return Message(MessageType.SET_OPTION, {"option": option, "value": value})


def create_get_option_message(option: str) -> Message:
    """Create a get session option message."""
    return Message(MessageType.GET_OPTION, {"option": option})


def create_get_server_info_message() -> Message:
    """Create a get server info message."""
    return Message(MessageType.GET_SERVER_INFO)
