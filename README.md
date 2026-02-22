# Synthetic Data Generator

This script generates a SQL dump file with synthetic data for a specific database table based on a provided creation script.

## Installation

Creation of a python virtual environment is recommended:

```bash
python -m venv venv
source venv/bin/activate
```

The script requires `mimesis` and `sqlglot`. You can install them using:

```bash
pip install mimesis sqlglot
```

## Usage

Run the script with the following parameters:

```bash
python generate_data.py --script <PATH_TO_SQL_SCRIPT> --engine <ENGINE_TYPE> --table <TABLE_NAME> --rows <NUMBER_OF_ROWS>
```

### Parameters:
- `--script`: Path to the SQL file containing the `CREATE TABLE` statement.
- `--engine`: Target database engine (`oracle`, `mssql`, `postgresql`, `mysql`).
- `--table`: The name of the table to generate data for.
- `--rows`: The number of rows to generate.
- `--output`: (Optional) Path to the output dump file. Defaults to `<TABLE_NAME>_dump.sql`.

### Example:

```bash
python generate_data.py --script schema.sql --engine postgresql --table users --rows 100
```

### Example 2:
```bash
python generate_data.py --script seed.sql --engine mssql --table usuarios --rows 100 --output seed100.sql
```

## Features:
- **Intelligent Mapping**: Automatically maps column names like `email`, `first_name`, `address`, etc., to relevant `mimesis` data providers.
- **Type Fallback**: If a column name isn't recognized, it uses the SQL data type to generate appropriate junk data.
- **Engine Specifics**: Handles basic engine-level formatting (e.g., `COMMIT` for Oracle, boolean handling for MS SQL).
- **Sturdy Parsing**: Uses `sqlglot` to reliably parse SQL schemas across different dialects.
