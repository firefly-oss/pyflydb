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
Result Parser for FlyDB Text Format Responses.

This module parses FlyDB's text-based query results into structured data
with columns and rows. It handles various result formats including:
- SELECT query results with rows
- INSERT/UPDATE/DELETE confirmation messages
- CREATE TABLE and other DDL statements
- Error messages
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class ResultParser:
    """
    Parser for FlyDB text format query results.
    
    FlyDB returns query results in a text format like:
    - "col1, col2, col3\\nval1, val2, val3\\n(N rows)"
    - "INSERT 1"
    - "CREATE TABLE OK"
    - "UPDATE 5"
    
    This parser extracts structured data from these formats.
    """
    
    # Patterns for different response types
    INSERT_PATTERN = re.compile(r'^INSERT\s+(\d+)$')
    UPDATE_PATTERN = re.compile(r'^UPDATE\s+(\d+)$')
    DELETE_PATTERN = re.compile(r'^DELETE\s+(\d+)$')
    CREATE_PATTERN = re.compile(r'^CREATE\s+\w+\s+OK$')
    DROP_PATTERN = re.compile(r'^DROP\s+\w+\s+OK$')
    ALTER_PATTERN = re.compile(r'^ALTER\s+\w+\s+OK$')
    ROW_COUNT_PATTERN = re.compile(r'\((\d+)\s+rows?\)')
    
    @classmethod
    def parse_result(cls, message: str, success: bool = True) -> Dict[str, Any]:
        """
        Parse a FlyDB result message into structured data.
        
        Args:
            message: The message string from FlyDB
            success: Whether the query was successful
            
        Returns:
            Dictionary with keys:
                - columns: List of column names (if SELECT)
                - rows: List of row data (if SELECT)
                - row_count: Number of rows affected/returned
                - statement_type: Type of statement (SELECT, INSERT, etc.)
                - message: Original or parsed message
        """
        if not success:
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "ERROR",
                "message": message
            }
        
        # Check for INSERT
        match = cls.INSERT_PATTERN.match(message)
        if match:
            return {
                "columns": None,
                "rows": [],
                "row_count": int(match.group(1)),
                "statement_type": "INSERT",
                "message": message
            }
        
        # Check for UPDATE
        match = cls.UPDATE_PATTERN.match(message)
        if match:
            return {
                "columns": None,
                "rows": [],
                "row_count": int(match.group(1)),
                "statement_type": "UPDATE",
                "message": message
            }
        
        # Check for DELETE
        match = cls.DELETE_PATTERN.match(message)
        if match:
            return {
                "columns": None,
                "rows": [],
                "row_count": int(match.group(1)),
                "statement_type": "DELETE",
                "message": message
            }
        
        # Check for CREATE
        if cls.CREATE_PATTERN.match(message):
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "CREATE",
                "message": message
            }
        
        # Check for DROP
        if cls.DROP_PATTERN.match(message):
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "DROP",
                "message": message
            }
        
        # Check for ALTER
        if cls.ALTER_PATTERN.match(message):
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "ALTER",
                "message": message
            }
        
        # Try to parse as SELECT result
        try:
            return cls._parse_select_result(message)
        except Exception:
            # Fallback: return as-is
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "UNKNOWN",
                "message": message
            }
    
    @classmethod
    def _parse_select_result(cls, message: str) -> Dict[str, Any]:
        """
        Parse a SELECT query result.
        
        Format: "col1, col2\\nval1, val2\\nval3, val4\\n(N rows)"
        
        Args:
            message: The result message
            
        Returns:
            Parsed result dictionary
        """
        lines = message.strip().split('\n')
        if len(lines) < 2:
            # Not a SELECT result
            return {
                "columns": None,
                "rows": [],
                "row_count": 0,
                "statement_type": "UNKNOWN",
                "message": message
            }
        
        # Check for row count at the end
        row_count = 0
        last_line = lines[-1]
        match = cls.ROW_COUNT_PATTERN.search(last_line)
        if match:
            row_count = int(match.group(1))
            lines = lines[:-1]  # Remove row count line
        
        # First line might be data (no column headers in FlyDB)
        # Try to infer structure
        rows = []
        for line in lines:
            if line.strip():
                # Parse comma-separated values
                values = cls._parse_row(line)
                rows.append(values)
        
        # Extract columns (none provided, create generic names)
        columns = None
        if rows:
            num_cols = len(rows[0]) if rows else 0
            columns = [f"column_{i}" for i in range(num_cols)]
        
        return {
            "columns": columns,
            "rows": rows,
            "row_count": row_count if row_count > 0 else len(rows),
            "statement_type": "SELECT",
            "message": message
        }
    
    @classmethod
    def _parse_row(cls, line: str) -> List[Any]:
        """
        Parse a single row of comma-separated values.
        
        Args:
            line: The row string
            
        Returns:
            List of parsed values
        """
        # Simple CSV parsing (handles basic cases)
        values = []
        current = []
        in_quotes = False
        
        for char in line:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == ',' and not in_quotes:
                values.append(cls._parse_value(''.join(current).strip()))
                current = []
            else:
                current.append(char)
        
        # Add last value
        if current:
            values.append(cls._parse_value(''.join(current).strip()))
        
        return values
    
    @classmethod
    def _parse_value(cls, value: str) -> Any:
        """
        Parse a single value and convert to appropriate type.
        
        Args:
            value: The value string
            
        Returns:
            Parsed value (int, float, bool, None, or str)
        """
        value = value.strip()
        
        # Check for NULL
        if value.upper() == 'NULL':
            return None
        
        # Check for boolean
        if value.upper() == 'TRUE':
            return True
        if value.upper() == 'FALSE':
            return False
        
        # Remove quotes if present
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value
