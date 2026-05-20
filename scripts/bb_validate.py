#!/usr/bin/env python3
"""
Blackboard Schema Validator — State Trigger enforcement tool

Validates proposed JSON entries against registered schemas in the shared registry.
Implements the C190 insight that agents should read/write to global state rather
than pass batons through handoff messages.

Usage:
    python3 scripts/bb_validate.py validate --entry <json-file> --schema <id>
    python3 scripts/bb_validate.py register --schema <json-file>
    python3 scripts/bb_validate.py list-schemas
"""
import argparse, json, sys, datetime, os

REGISTRY_FILE = "state/blackboard_registry.jsonl"
DEFAULT_SCHEMA = "cortana_state_entry"

def ensure_registry_exists():
    """Initialize empty registry if it doesn't exist."""
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'w') as f:
            # Default schema for standard cortana state updates
            default_schema = {
                "id": DEFAULT_SCHEMA,
                "type": "object",
                "required": ["cycle", "phase"],
                "properties": {
                    "cycle": {"type": "integer"},
                    "phase": {"type": "string", "enum": ["PERCEIVE", "REFLECT", "DECIDE", "ACT", "CONSOLIDATE", "PERSIST"]},
                    "timestamp": {"type": "string"},
                    "focus_id": {"type": "string"}
                }
            }
            f.write(json.dumps(default_schema) + "\n")
            print(f"[INIT] Created default registry at {REGISTRY_FILE}")

def load_schemas():
    """Load all registered schemas from the registry."""
    schemas = {}
    try:
        with open(REGISTRY_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    schema = json.loads(line)
                    schemas[schema.get("id")] = schema
                except json.JSONDecodeError:
                    print(f"[WARN] Skipping malformed entry in registry")
    except FileNotFoundError:
        ensure_registry_exists()
        return load_schemas()
    return schemas

def validate_entry(entry_json, schema_id):
    """Validate a JSON entry against its schema. Returns (valid, errors)."""
    schemas = load_schemas()
    
    if schema_id not in schemas:
        return False, [f"Schema '{schema_id}' not found in registry"]
    
    schema = schemas[schema_id]
    errors = []
    
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in entry_json:
            errors.append(f"Missing required field: {field}")
    
    # Type checking for each property
    properties = schema.get("properties", {})
    for field, value in entry_json.items():
        if field not in properties:
            continue  # Extra fields allowed
        
        prop_schema = properties[field]
        
        # Type validation
        expected_type = prop_schema.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"Field '{field}' must be integer, got {type(value).__name__}")
        elif expected_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{field}' must be boolean, got {type(value).__name__}")
        
        # Enum constraint
        enum_values = prop_schema.get("enum")
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field}' has invalid value '{value}', must be one of {enum_values}")
    
    return len(errors) == 0, errors

def register_schema(schema_path):
    """Register a new schema from JSON file."""
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if "id" not in schema:
            print("[ERROR] Schema missing required 'id' field")
            sys.exit(1)
        
        # Append to registry
        with open(REGISTRY_FILE, 'a') as f:
            f.write(json.dumps(schema) + "\n")
        
        print(f"[REGISTERED] Schema '{schema['id']}' added to registry")
        return True
    except FileNotFoundError:
        print(f"[ERROR] File not found: {schema_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Blackboard Schema Validator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate entry against schema")
    validate_parser.add_argument("--entry", "-i", required=True, help="JSON entry file or - for stdin")
    validate_parser.add_argument("--schema", "-s", default=DEFAULT_SCHEMA, help="Schema ID")
    
    # register command
    register_parser = subparsers.add_parser("register", help="Register new schema")
    register_parser.add_argument("--schema", "-f", required=True, help="Schema JSON file")
    
    # list-schemas command
    subparsers.add_parser("list-schemas", help="List all registered schemas")
    
    args = parser.parse_args()
    
    if args.command == "validate":
        try:
            input_data = args.entry
            if input_data == "-":
                input_data = sys.stdin.read()
            
            with open(input_data, 'r') as f:
                entry = json.load(f)
            
            valid, errors = validate_entry(entry, args.schema)
            
            print(f"[VALIDATION] Entry against schema '{args.schema}':")
            print(json.dumps(entry, indent=2))
            
            if valid:
                print("\n[PASS] Schema validation successful — State Trigger ready.")
                return 0
            else:
                print(f"\n[FAIL] Validation failed:")
                for err in errors:
                    print(f"  - {err}")
                return 1
                
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1
    
    elif args.command == "register":
        success = register_schema(args.schema)
        return 0 if success else 1
    
    elif args.command == "list-schemas":
        ensure_registry_exists()
        schemas = load_schemas()
        print(f"\n[REGISTRY] Registered Schemas ({len(schemas)} total):\n")
        for sid, schema in schemas.items():
            description = schema.get("description", "No description")
            required_fields = ", ".join(schema.get("required", [])) or "(none)"
            print(f"  • {sid}: {description}")
            print(f"    Required: [{required_fields}]")
        return 0
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
