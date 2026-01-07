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
Type Adapters and Row Objects with Pydantic.

This module provides type conversion and validation using Pydantic models,
allowing for strongly-typed database results and better IDE support.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, date, time
from decimal import Decimal

try:
    from pydantic import BaseModel, Field, ConfigDict, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # Fallback


class Row(dict):
    """
    Enhanced row object with both dict and attribute access.
    
    Allows accessing columns by name or index:
        row['name'] or row.name
        row[0]
    """
    
    def __init__(self, columns: List[str], values: Tuple[Any, ...]):
        """
        Initialize a row with column names and values.
        
        Args:
            columns: List of column names
            values: Tuple of column values
        """
        super().__init__(zip(columns, values))
        self._columns = columns
        self._values = values
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access."""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Row has no column '{name}'")
    
    def __getitem__(self, key: Union[str, int]) -> Any:
        """Allow both name and index access."""
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)
    
    def __repr__(self) -> str:
        """String representation."""
        items = ', '.join(f"{k}={v!r}" for k, v in self.items())
        return f"Row({items})"
    
    @property
    def columns(self) -> List[str]:
        """Get column names."""
        return self._columns
    
    @property
    def values(self) -> Tuple[Any, ...]:
        """Get values as tuple."""
        return self._values
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dictionary."""
        return dict(self)
    
    def to_tuple(self) -> Tuple[Any, ...]:
        """Convert to tuple."""
        return self._values


class TypeAdapter:
    """
    Type conversion and validation for database values.
    
    Provides methods to convert Python types to SQL and vice versa.
    """
    
    @staticmethod
    def to_sql(value: Any) -> str:
        """
        Convert Python value to SQL string representation.
        
        Args:
            value: Python value
            
        Returns:
            SQL string representation
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float, Decimal)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        elif isinstance(value, date):
            return f"'{value.isoformat()}'"
        elif isinstance(value, time):
            return f"'{value.isoformat()}'"
        elif isinstance(value, (list, tuple)):
            # Array type
            items = ', '.join(TypeAdapter.to_sql(v) for v in value)
            return f"ARRAY[{items}]"
        elif isinstance(value, dict):
            # JSON type
            import json
            return f"'{json.dumps(value)}'"
        else:
            # Fallback to string
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    @staticmethod
    def from_sql(value: Any, target_type: Optional[type] = None) -> Any:
        """
        Convert SQL value to Python type.
        
        Args:
            value: SQL value
            target_type: Optional target Python type
            
        Returns:
            Converted Python value
        """
        if value is None:
            return None
        
        if target_type is None:
            return value
        
        try:
            if target_type == bool:
                if isinstance(value, str):
                    return value.upper() in ('TRUE', 'T', '1', 'YES', 'Y')
                return bool(value)
            elif target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == Decimal:
                return Decimal(str(value))
            elif target_type == str:
                return str(value)
            elif target_type == datetime:
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            elif target_type == date:
                if isinstance(value, str):
                    return date.fromisoformat(value)
                return value
            elif target_type == time:
                if isinstance(value, str):
                    return time.fromisoformat(value)
                return value
            else:
                return value
        except (ValueError, TypeError):
            return value


if PYDANTIC_AVAILABLE:
    class DatabaseModel(BaseModel):
        """
        Base model for database rows with Pydantic validation.
        
        Example:
            class User(DatabaseModel):
                id: int
                name: str
                age: int
                email: Optional[str] = None
            
            # Create from database row
            user = User.from_row(row)
        """
        
        model_config = ConfigDict(
            from_attributes=True,
            arbitrary_types_allowed=True,
            str_strip_whitespace=True
        )
        
        @classmethod
        def from_row(cls, row: Union[Dict, Row, Tuple], columns: Optional[List[str]] = None):
            """
            Create model instance from database row.
            
            Args:
                row: Database row (dict, Row object, or tuple)
                columns: Column names (required if row is tuple)
                
            Returns:
                Model instance
            """
            if isinstance(row, dict):
                return cls(**row)
            elif isinstance(row, Row):
                return cls(**row.to_dict())
            elif isinstance(row, tuple) and columns:
                return cls(**dict(zip(columns, row)))
            else:
                raise ValueError("Invalid row format")
        
        def to_row(self) -> Dict[str, Any]:
            """Convert model to dictionary suitable for database insert."""
            return self.model_dump()

else:
    # Fallback when Pydantic is not available
    class DatabaseModel:
        """Fallback DatabaseModel when Pydantic is not installed."""
        
        @classmethod
        def from_row(cls, row, columns=None):
            raise ImportError("Pydantic is required for DatabaseModel. Install with: pip install pydantic")
        
        def to_row(self):
            raise ImportError("Pydantic is required for DatabaseModel. Install with: pip install pydantic")
