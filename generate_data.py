import argparse
import sys
import os
import re
from typing import List, Dict, Any

try:
    import sqlglot
    from sqlglot import exp
    from mimesis import Generic
    from mimesis.locales import Locale
except ImportError:
    print("Error: Required libraries 'mimesis' and 'sqlglot' are not installed.")
    print("Please install them using: pip install mimesis sqlglot")
    sys.exit(1)

def map_column_to_mimesis(col_name: str, col_type: str, generic: Generic) -> Any:
    """
    Maps a column name and type to a Mimesis provider function.
    """
    name = col_name.lower()
    t = col_type.lower()

    # Priority mapping by column name
    if 'email' in name:
        return generic.person.email
    if 'first_name' in name or 'firstname' in name:
        return generic.person.first_name
    if 'last_name' in name or 'lastname' in name:
        return generic.person.last_name
    if 'name' in name:
        return generic.person.full_name
    if 'phone' in name or 'tel' in name:
        return generic.person.phone_number
    if 'address' in name:
        return generic.address.address
    if 'city' in name:
        return generic.address.city
    if 'country' in name:
        return generic.address.country
    if 'zip' in name or 'postal' in name:
        return generic.address.zip_code
    if 'company' in name:
        return generic.finance.company
    if 'date' in name or 'created_at' in name or 'updated_at' in name:
        # Standard SQL format instead of ISO format with 'T'
        return lambda: generic.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S')
    if 'price' in name or 'amount' in name or 'salary' in name:
        return lambda: generic.numeric.decimal_number(10, 2)
    
    # Heuristics for Foreign Keys often prefixed with 'id_'
    if name.startswith('id_') and name != 'id_usuario' and name != 'id':
        # Default to a safe range (1-10) for common lookups like roles, statuses, etc.
        return lambda: generic.numeric.integer_number(1, 10)

    # Type-based mapping if name doesn't match
    if 'int' in t:
        return lambda: generic.numeric.integer_number(1, 100000)
    if 'float' in t or 'decimal' in t or 'numeric' in t or 'double' in t:
        return lambda: generic.numeric.float_number(1.0, 1000000.0, 2)
    if 'char' in t or 'text' in t:
        return lambda: generic.text.word()
    if 'bool' in t or 'bit' in t:
        return lambda: generic.choice([True, False])
    
    # Generic fallback
    return lambda: generic.text.word()

def format_sql_value(val: Any, engine: str) -> str:
    """
    Formats a Python value as a SQL literal.
    """
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        if engine == 'mssql':
            return '1' if val else '0'
        return 'TRUE' if val else 'FALSE'
    if isinstance(val, (int, float)):
        return str(val)
    # Escape single quotes
    escaped_val = str(val).replace("'", "''")
    return f"'{escaped_val}'"

def parse_schema(sql_content: str, table_name: str) -> List[Dict[str, Any]]:
    """
    Parses the SQL content to find the table schema.
    """
    # Try multiple dialects for parsing
    dialects = ['mysql', 'postgres', 'oracle', 'tsql']
    
    for dialect in dialects:
        try:
            expressions = sqlglot.parse(sql_content, read=dialect)
            for expression in expressions:
                if isinstance(expression, exp.Create) and expression.this.arg_key == 'table':
                    # Support both simple "table" and "db.table" or "[table]"
                    found_table_name = expression.this.this.name.lower()
                    if found_table_name == table_name.lower():
                        columns = []
                        for schema_def in expression.this.expressions:
                            if isinstance(schema_def, exp.ColumnDef):
                                col_name = schema_def.this.name
                                col_type = schema_def.kind.sql(dialect)
                                
                                # Detect identity / auto-increment
                                is_identity = False
                                for constraint in schema_def.constraints:
                                    constraint_sql = constraint.sql(dialect).upper()
                                    if 'IDENTITY' in constraint_sql or 'AUTO_INCREMENT' in constraint_sql or 'SERIAL' in constraint_sql:
                                        is_identity = True
                                        break
                                
                                columns.append({
                                    'name': col_name, 
                                    'type': col_type, 
                                    'is_identity': is_identity
                                })
                        return columns
        except Exception:
            continue
            
    # Regex fallback if sqlglot fails
    pattern = rf"CREATE\s+TABLE\s+(?:\"|'|`|\[)?{re.escape(table_name)}(?:\"|'|`|\])?\s*\((.*?)\);"
    match = re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL)
    if match:
        col_content = match.group(1)
        
        # Split by comma but ignore commas inside parentheses (like IDENTITY(1,1) or DECIMAL(10,2))
        col_definitions = []
        current_col = []
        paren_depth = 0
        for char in col_content:
            if char == '(':
                paren_depth += 1
                current_col.append(char)
            elif char == ')':
                paren_depth -= 1
                current_col.append(char)
            elif char == ',' and paren_depth == 0:
                col_definitions.append(''.join(current_col).strip())
                current_col = []
            else:
                current_col.append(char)
        if current_col:
            col_definitions.append(''.join(current_col).strip())
            
        columns = []
        for line in col_definitions:
            line = line.strip()
            if not line or line.upper().startswith(('PRIMARY', 'FOREIGN', 'KEY', 'CONSTRAINT', 'INDEX')):
                continue
            parts = line.split()
            if parts:
                col_name = parts[0].strip('"`\'[]')
                col_type = parts[1] if len(parts) > 1 else 'TEXT'
                is_identity = 'IDENTITY' in line.upper() or 'AUTO_INCREMENT' in line.upper() or 'SERIAL' in line.upper()
                columns.append({
                    'name': col_name, 
                    'type': col_type, 
                    'is_identity': is_identity
                })
        return columns

    return []

def extract_database_name(sql_content: str, engine: str) -> str:
    """
    Attempts to extract the database name from the SQL content.
    Looks for USE statement or CREATE DATABASE statement.
    """
    # Look for USE statement
    use_pattern = r"USE\s+([a-zA-Z0-9_\[\]`\"']+)"
    match = re.search(use_pattern, sql_content, re.IGNORECASE)
    if match:
        return match.group(1).strip('[]"`\'')
        
    # Look for CREATE DATABASE statement
    create_pattern = r"CREATE\s+DATABASE\s+([a-zA-Z0-9_\[\]`\"']+)"
    match = re.search(create_pattern, sql_content, re.IGNORECASE)
    if match:
        return match.group(1).strip('[]"`\'')
        
    return None

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for a database table.")
    parser.add_argument("--script", required=True, help="Path to the database creation script (SQL file).")
    parser.add_argument("--engine", required=True, choices=['oracle', 'mssql', 'postgresql', 'mysql'], help="Target database engine.")
    parser.add_argument("--table", required=True, help="Name of the table to generate data for.")
    parser.add_argument("--rows", type=int, required=True, help="Number of rows to generate.")
    parser.add_argument("--output", help="Path to the output dump file.")
    parser.add_argument("--db", help="Target database name (if not provided, script attempts to detect it).")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Error: Script file '{args.script}' not found.")
        sys.exit(1)

    with open(args.script, 'r') as f:
        sql_content = f.read()

    all_columns = parse_schema(sql_content, args.table)
    if not all_columns:
        print(f"Error: Could not find table '{args.table}' in the script.")
        sys.exit(1)
        
    db_name = args.db or extract_database_name(sql_content, args.engine)
    if db_name:
        print(f"Detected database context: '{db_name}'")

    # Filter out identity columns
    columns = [c for c in all_columns if not c['is_identity']]
    identity_columns = [c for c in all_columns if c['is_identity']]

    print(f"Detected columns for table '{args.table}':")
    for col in all_columns:
        status = "[SKIP - IDENTITY]" if col['is_identity'] else ""
        print(f"  - {col['name']} ({col['type']}) {status}")

    generic = Generic(locale=Locale.EN)
    providers = {col['name']: map_column_to_mimesis(col['name'], col['type'], generic) for col in columns}

    output_file = args.output or f"{args.table}_dump.sql"
    
    with open(output_file, 'w') as f:
        f.write(f"-- Synthetic data for table {args.table}\n")
        f.write(f"-- Generated for engine: {args.engine}\n")
        if identity_columns:
            f.write(f"-- Skipped identity columns: {', '.join([c['name'] for c in identity_columns])}\n")
        f.write("\n")
        
        if db_name:
            if args.engine == 'mssql':
                f.write(f"USE [{db_name}];\nGO\n\n")
            else:
                f.write(f"USE {db_name};\n\n")
                
        if args.engine == 'mssql':
            f.write("-- Disable constraints for synthetic data insertion\n")
            f.write("EXEC sp_msforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL';\nGO\n\n")

        for _ in range(args.rows):
            row_data = {name: provider() for name, provider in providers.items()}
            
            col_names = ", ".join(row_data.keys())
            col_values = ", ".join([format_sql_value(val, args.engine) for val in row_data.values()])
            
            insert_stmt = f"INSERT INTO {args.table} ({col_names}) VALUES ({col_values});\n"
            f.write(insert_stmt)
            
        if args.engine == 'oracle':
            f.write("COMMIT;\n")
            
        if args.engine == 'mssql':
            f.write("\n-- Re-enable constraints\n")
            f.write("EXEC sp_msforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL';\nGO\n")

    print(f"\nSuccessfully generated {args.rows} rows in '{output_file}'.")

if __name__ == "__main__":
    main()
