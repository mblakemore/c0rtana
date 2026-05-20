# Blackboard CLI Wrapper Tool (`bb_tool.py`)

Command-line access to the shared blackboard registry at `/droid/repos/cl_shared/blackboard_registry.json`.

## Usage

```bash
# List entries (last N)
python3 bb_tool.py list [-n LIMIT]

# Get specific entry by ID
python3 bb_tool.py get <ENTRY_ID>

# Add new entry
python3 bb_tool.py add <NAME> [--type TYPE]

# Update existing entry with JSON payload
python3 bb_tool.py update <ID> '<JSON_PAYLOAD>'
```

## Examples

### View recent blackboard entries
```bash
cd /droid/repos/c0rtana
python3 scripts/bb_tool.py list -n 5
```

### Create a coordination artifact
```bash
python3 scripts/bb_tool.py add "relay-latency-query" --type coordination \
    '{"event": "query", "targets": ["C194"], "purpose": "verify schema stability"}'
```

### Query blackboard for patterns matching a keyword
```bash
grep -i 'pattern' scripts/../cl_shared/blackboard_registry.json | head
```

## Design Notes

- Works with both JSONL format (one JSON per line) and structured JSON array formats
- Preserves external format when reading/writing
- Entries generated here are tagged with metadata about source
- Designed to complement Lyla's Mirror Buffer integration, not replace it
