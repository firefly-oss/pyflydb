# Getting Started with pyFlyDb

Welcome to pyFlyDb! This guide will help you get up and running quickly.

## Prerequisites

- Python 3.8 or higher
- FlyDB server running (with binary protocol enabled on port 8889)
- pip (Python package installer)

## Installation

### From Source (Development)

```bash
# Clone or navigate to the pyFlyDb directory
cd pyFlyDb

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```python
import pyflydb
print(pyflydb.__version__)  # Should print: 0.1.0
```

## Quick Start

### 1. Start FlyDB Server

Make sure your FlyDB server is running with the binary protocol enabled:

```bash
./flydb --text-port 8888 --binary-port 8889
```

You should see output indicating both protocols are listening.

### 2. Your First Connection

Create a file called `my_first_connection.py`:

```python
import pyflydb

# Connect to FlyDB
conn = pyflydb.connect(
    host="localhost",
    port=8889,
    user="admin",
    password="your_password"
)

# Test the connection
if conn.ping():
    print("Connected successfully!")

# Get server info
info = conn.get_server_info()
print(f"Server version: {info.get('server_version')}")

# Close
conn.close()
```

Run it:

```bash
python my_first_connection.py
```

### 3. Execute Your First Query

```python
import pyflydb

with pyflydb.connect(host="localhost", port=8889, user="admin", password="secret") as conn:
    cursor = conn.cursor()
    
    # Create a table
    cursor.execute("CREATE TABLE products (id INT, name TEXT, price INT)")
    
    # Insert data
    cursor.execute("INSERT INTO products VALUES (1, 'Laptop', 999)")
    cursor.execute("INSERT INTO products VALUES (2, 'Mouse', 25)")
    
    # Query data
    cursor.execute("SELECT * FROM products")
    
    print("Products:")
    for row in cursor:
        print(f"  ID: {row[0]}, Name: {row[1]}, Price: ${row[2]}")
    
    # Connection automatically commits and closes
```

### 4. Using Parameters

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)
cursor = conn.cursor()

# Positional parameters
product_id = 3
name = "Keyboard"
price = 75

cursor.execute(
    "INSERT INTO products VALUES (%s, %s, %s)",
    (product_id, name, price)
)

# Named parameters
cursor.execute(
    "SELECT * FROM products WHERE price > %(min_price)s",
    {"min_price": 50}
)

results = cursor.fetchall()
for row in results:
    print(row)

conn.commit()
conn.close()
```

## Common Patterns

### Pattern 1: Context Managers (Recommended)

Always use context managers for automatic resource cleanup:

```python
import pyflydb

with pyflydb.connect(host="localhost", port=8889) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        # Process rows...
    # Cursor automatically closed here
    # Transaction automatically committed (or rolled back on error)
# Connection automatically closed here
```

### Pattern 2: Transaction Management

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)

try:
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO accounts VALUES (1, 'Alice', 1000)")
    cursor.execute("INSERT INTO accounts VALUES (2, 'Bob', 500)")
    
    # Transfer money
    cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    
    # Commit if everything succeeds
    conn.commit()
    print("Transaction successful!")
    
except Exception as e:
    # Rollback on any error
    conn.rollback()
    print(f"Transaction failed: {e}")
    
finally:
    conn.close()
```

### Pattern 3: Batch Operations

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)
cursor = conn.cursor()

# Insert multiple rows efficiently
data = [
    (10, "Product A", 100),
    (11, "Product B", 200),
    (12, "Product C", 300),
]

cursor.executemany(
    "INSERT INTO products VALUES (%s, %s, %s)",
    data
)

conn.commit()
cursor.close()
conn.close()
```

### Pattern 4: Fetching Results

```python
import pyflydb

conn = pyflydb.connect(host="localhost", port=8889)
cursor = conn.cursor()

cursor.execute("SELECT * FROM products")

# Method 1: Fetch one at a time
row = cursor.fetchone()
while row:
    print(row)
    row = cursor.fetchone()

# Method 2: Fetch in batches
cursor.execute("SELECT * FROM products")
while True:
    rows = cursor.fetchmany(100)  # Fetch 100 rows
    if not rows:
        break
    for row in rows:
        print(row)

# Method 3: Fetch all (for small result sets)
cursor.execute("SELECT * FROM products")
all_rows = cursor.fetchall()
for row in all_rows:
    print(row)

# Method 4: Iterator (most Pythonic)
cursor.execute("SELECT * FROM products")
for row in cursor:
    print(row)

cursor.close()
conn.close()
```

## Error Handling

Always handle exceptions appropriately:

```python
import pyflydb

try:
    conn = pyflydb.connect(
        host="localhost",
        port=8889,
        user="admin",
        password="wrong_password"
    )
except pyflydb.AuthenticationError:
    print("Invalid credentials")
except pyflydb.ConnectionError:
    print("Could not connect to server")
except pyflydb.TimeoutError:
    print("Connection timed out")
except pyflydb.Error as e:
    print(f"Database error: {e}")
```

## Configuration Options

### Connection Parameters

```python
conn = pyflydb.connect(
    host="localhost",          # Server hostname
    port=8889,                 # Binary protocol port
    user="admin",              # Username (optional)
    password="secret",         # Password (optional)
    database=None,             # Database name (reserved for future)
    connect_timeout=10.0,      # Connection timeout in seconds
    autocommit=False           # Auto-commit mode
)
```

### Cursor Configuration

```python
cursor = conn.cursor()
cursor.arraysize = 100  # Default rows for fetchmany()
```

## Next Steps

1. **Read the README**: Check out [README.md](README.md) for comprehensive documentation
2. **Try Examples**: Run the examples in the `examples/` directory
3. **Check the Code**: Browse the well-documented source code in `pyflydb/`
4. **Report Issues**: Found a bug? Report it on GitHub

## Troubleshooting

### Connection Refused

**Problem**: `ConnectionError: Failed to connect to localhost:8889`

**Solution**:
- Verify FlyDB is running
- Check that binary protocol is enabled on port 8889
- Verify firewall settings

### Authentication Failed

**Problem**: `AuthenticationError: Authentication failed`

**Solution**:
- Verify username and password
- Check FlyDB user configuration
- Ensure user has appropriate permissions

### Import Error

**Problem**: `ModuleNotFoundError: No module named 'pyflydb'`

**Solution**:
```bash
# Install the package
cd pyFlyDb
pip install -e .
```

## Support

- **Documentation**: See README.md
- **Examples**: Check examples/ directory
- **Issues**: GitHub Issues (coming soon)
- **Source Code**: Browse pyflydb/ directory

## License

Copyright 2026 Firefly Software Solutions Inc.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

Happy coding with pyFlyDb!
