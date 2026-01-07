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
DSN (Data Source Name) Parsing for pyFlyDb.

Supports connection strings in various formats:
- flydb://user:password@host:port/database
- flydb://host:port?user=admin&password=secret
- host=localhost port=8889 user=admin password=secret
"""

import re
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse


def parse_dsn(dsn: str) -> Dict[str, any]:
    """
    Parse a DSN string into connection parameters.
    
    Supported formats:
        - URI: flydb://user:password@host:port/database?param=value
        - Key-value: host=localhost port=8889 user=admin password=secret
    
    Args:
        dsn: Connection string
        
    Returns:
        Dictionary of connection parameters
        
    Example:
        params = parse_dsn("flydb://admin:secret@localhost:8889/mydb")
        conn = pyflydb.connect(**params)
    """
    # Try URL format first
    if '://' in dsn:
        return _parse_uri(dsn)
    else:
        return _parse_key_value(dsn)


def _parse_uri(uri: str) -> Dict[str, any]:
    """Parse URI-style DSN."""
    parsed = urlparse(uri)
    
    params = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 8889,
    }
    
    if parsed.username:
        params["user"] = parsed.username
    
    if parsed.password:
        params["password"] = parsed.password
    
    if parsed.path and parsed.path != '/':
        params["database"] = parsed.path.lstrip('/')
    
    # Parse query parameters
    if parsed.query:
        query_params = parse_qs(parsed.query)
        for key, value in query_params.items():
            # Use first value if list
            params[key] = value[0] if isinstance(value, list) else value
    
    # Convert string port to int
    if isinstance(params.get("port"), str):
        params["port"] = int(params["port"])
    
    # Convert string booleans
    if "autocommit" in params:
        params["autocommit"] = params["autocommit"].lower() in ("true", "1", "yes")
    
    return params


def _parse_key_value(dsn: str) -> Dict[str, any]:
    """Parse key=value style DSN."""
    params = {}
    
    # Simple key=value parsing
    for part in dsn.split():
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            # Convert known integer fields
            if key == "port":
                value = int(value)
            elif key == "autocommit":
                value = value.lower() in ("true", "1", "yes")
            
            params[key] = value
    
    return params


def make_dsn(**params) -> str:
    """
    Create a DSN string from connection parameters.
    
    Args:
        **params: Connection parameters (host, port, user, password, etc.)
        
    Returns:
        DSN string in URI format
        
    Example:
        dsn = make_dsn(host="localhost", port=8889, user="admin", password="secret")
        # Returns: flydb://admin:secret@localhost:8889
    """
    user = params.get("user", "")
    password = params.get("password", "")
    host = params.get("host", "localhost")
    port = params.get("port", 8889)
    database = params.get("database", "")
    
    # Build userinfo
    userinfo = ""
    if user:
        userinfo = user
        if password:
            userinfo += f":{password}"
        userinfo += "@"
    
    # Build path
    path = f"/{database}" if database else ""
    
    # Build query string for extra params
    extra_params = []
    for key, value in params.items():
        if key not in ("user", "password", "host", "port", "database"):
            extra_params.append(f"{key}={value}")
    
    query = "?" + "&".join(extra_params) if extra_params else ""
    
    return f"flydb://{userinfo}{host}:{port}{path}{query}"
