# Python Scripts & Utilities Suite

A modular CLI utility suite with subcommands, built using Python's standard library.

## Project Structure

```
python_scripts/
├── main.py                 # Central CLI dispatcher with subcommands
├── utils/                  # Modular utilities package
│   ├── __init__.py         # Package exports
│   └── fs_utils.py         # Filesystem tools (e.g., clean-empty-dirs)
└── tests/                  # Automated unit and CLI integration tests
    ├── __init__.py
    ├── test_cli.py         # CLI parsing and command invocation tests
    └── test_fs_utils.py    # Unit tests for filesystem logic
```

## Running Utilities

### 1. Delete Empty Directories (`clean-empty-dirs`)

Recursively deletes empty directories across all subdirectories bottom-up:

```bash
# Preview what would be deleted without making any changes (dry run)
python3 main.py clean-empty-dirs /path/to/folder -n

# Remove empty subdirectories
python3 main.py clean-empty-dirs /path/to/folder

# Remove empty subdirectories quietly (summary only)
python3 main.py clean-empty-dirs /path/to/folder -q

# Also remove the target root directory itself if it ends up empty
python3 main.py clean-empty-dirs /path/to/folder --delete-root
```

*Alias available:* `delete-empty-dirs` can be used in place of `clean-empty-dirs`.

### 2. General Help

```bash
python3 main.py --help
python3 main.py <command> --help
```

---

## Adding Future Utilities

To add a new utility tool (e.g., text utils, network utils, or media utils):

1. **Create your utility module** inside `utils/` (e.g., `utils/text_utils.py`):
   ```python
   import argparse

   def run_my_tool(args: argparse.Namespace) -> int:
       print("Running tool with", args)
       return 0

   def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
       parser = subparsers.add_parser("my-tool", help="Description of my tool")
       parser.add_argument("--my-flag", action="store_true")
       parser.set_defaults(func=run_my_tool)
   ```

2. **Register the module** in `main.py`:
   ```python
   from utils import fs_utils, text_utils

   COMMAND_MODULES = [
       fs_utils,
       text_utils,
   ]
   ```

3. **Add corresponding tests** in `tests/test_text_utils.py`.

---

## Running Tests

Run all unit and integration tests using Python's standard `unittest`:

```bash
python3 -m unittest discover tests
```
