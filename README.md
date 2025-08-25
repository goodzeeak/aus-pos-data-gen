# AUS POS Data Generator

Synthetic Australian POS transaction dataset generator with GST compliance, realistic business rules, and rich CLI. Generates businesses, customers, transactions, and returns in CSV/JSON/Parquet/Excel or streams directly to databases.

## Features

- Australian context: ABN validation, state distributions, GST codes and rounding
- Realistic entities: Businesses, Customers, Transactions, Line Items, Returns
- Output formats: CSV, JSON, Parquet, Excel (xlsx)
- Streaming: Console, JSON, CSV, Parquet, Excel, Database (SQLite/Postgres/MySQL/MariaDB)
- CLI: Batch generation, live streaming, interactive wizard
- Strong typing/validation via Pydantic
- Rich progress and colorful console output

## Project Structure

- `src/aus_pos_data_gen/`
  - `config.py`: `POSGeneratorConfig`, `DatabaseConfig`, Australian settings
  - `generator.py`: `POSDataGenerator` orchestration, exports
  - `models.py`: Pydantic models (`Transaction`, `TransactionItem`, etc.)
  - `validators.py`: ABN and GST validators/calculations
  - `cli.py`: Typer-based CLI (`aus-pos-gen`)
- `scripts/generate_sample_data.py`: Programmatic example
- `data/processed/`: Default output directory (created on demand)
- `pyproject.toml`: Packaging and entry point
- `environment.yml`: Conda env (Python 3.11)
- `tests/`: Test placeholders

## Installation

Choose one of:

- Pip (Python 3.11):
  ```bash
  pip install -e .
  ```

- Conda environment:
  ```bash
  conda env create -f environment.yml
  conda activate aus-pos-data-gen
  pip install -e .
  ```

## Quick Start

After installing, the CLI entry point `aus-pos-gen` is available.

- Help
  ```bash
  aus-pos-gen --help
  ```

- Interactive wizard
  ```bash
  aus-pos-gen interactive
  ```

- Batch generation to CSV (default output `data/processed/`)
  ```bash
  aus-pos-gen generate --businesses 5 --customers 1000 --days 30 --format csv
  ```

- Live stream to console (1 tps)
  ```bash
  aus-pos-gen stream --businesses 3 --customers 500 --rate 1 --format console
  ```

- Live stream to Postgres (example)
  ```bash
  aus-pos-gen stream \
    --businesses 3 --customers 500 --rate 2 --format database \
    --db-type postgresql --db-host localhost --db-port 5432 \
    --db-name aus_pos_data --db-username postgres --db-password <password> \
    --db-table-prefix pos_ --db-schema public
  ```

- Write Parquet during streaming
  ```bash
  aus-pos-gen stream --format parquet --output stream.parquet
  ```

- Programmatic usage
  ```python
  from pathlib import Path
  from datetime import datetime, timedelta
  from aus_pos_data_gen.config import POSGeneratorConfig
  from aus_pos_data_gen.generator import POSDataGenerator

  config = POSGeneratorConfig(
      start_date=datetime.now() - timedelta(days=30),
      end_date=datetime.now(),
      output_dir=Path("sample_data"),
  )
  gen = POSDataGenerator(config)
  result = gen.generate_all_data(business_count=3, customer_count=500)
  gen.export_to_csv()
  gen.export_line_items()
  ```

## Outputs

- Businesses: `businesses.(csv|json)`
- Customers: `customers.(csv|json)`
- Transactions: `transactions.(csv|json)` with nested `items`
- Line items: `transaction_items.csv` (flattened)
- Returns: `returns.(csv|json)`

## Configuration Highlights

Key settings in `POSGeneratorConfig` (`src/aus_pos_data_gen/config.py`):

- Date range: `start_date` to `end_date`
- Volume: `daily_transactions`, `store_size_distribution`, `items_per_transaction`
- Australian specifics: `payment_methods`, `states_distribution`, `product_categories`, `seasonal_multipliers`
- Database export: `DatabaseConfig` with `get_connection_string()` for SQLite/Postgres/MySQL/MariaDB

## Development

- Lint/format:
  ```bash
  black . && isort . && flake8
  ```

- Type check:
  ```bash
  mypy src
  ```

- Tests & coverage:
  ```bash
  pytest -v --cov=aus_pos_data_gen --cov-report=term-missing
  ```
  HTML report: `htmlcov/index.html`

## License

MIT License. See `pyproject.toml` for metadata.
