# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
# On Windows: venv\Scripts\activate  
# On macOS/Linux: source venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Code Quality & Testing
```bash
# Format code
black src tests scripts
isort src tests scripts

# Lint
flake8 src tests scripts

# Type check
mypy src

# Run tests with coverage
pytest -v --cov=aus_pos_data_gen --cov-report=term-missing

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow running tests
```

### Application Usage
```bash
# CLI entry point
aus-pos-gen --help

# Interactive wizard (recommended)
aus-pos-gen interactive

# Generate batch data
aus-pos-gen generate --businesses 5 --customers 1000 --days 30 --format csv

# Stream live data
aus-pos-gen stream --businesses 3 --customers 500 --rate 1 --format console
```

## Architecture Overview

### Core Components

1. **CLI Interface** (`cli.py`)
   - Typer-based command structure with rich console interface
   - Three main commands: `generate`, `stream`, `interactive`
   - Graceful shutdown handling with signal management
   - Windows UTF-8 encoding support

2. **Data Generator** (`generator.py`)
   - Central orchestrator for all data generation
   - Manages businesses, customers, transactions, and returns
   - Supports multiple export formats (CSV, JSON, Parquet, XLSX)
   - Database streaming capabilities

3. **Configuration System** (`config.py`)
   - Pydantic-based configuration with validation
   - `POSGeneratorConfig`: Main generation parameters
   - `DatabaseConfig`: Database connection settings
   - Australian-specific constants (states, payment methods, GST rules)

4. **Data Models** (`models.py`)
   - Pydantic models for all entities (Business, Customer, Transaction, etc.)
   - Australian-specific enums (states, payment methods, GST codes)
   - Type-safe data structures throughout

5. **Validators** (`validators.py`)
   - ABN (Australian Business Number) validation and generation
   - GST calculation with proper rounding rules
   - Australian address validation

6. **Database Manager** (`database_manager.py`)
   - Multi-database support (SQLite, PostgreSQL, MySQL, MariaDB)
   - Connection pooling and enhanced error handling
   - Schema creation and data insertion

7. **Interactive Handlers** (`interactive_handlers.py`)
   - Rich CLI wizard with navigation control
   - Step-by-step parameter configuration
   - Input validation and user experience enhancements

### Data Flow Architecture

1. **Configuration Phase**: Parse CLI args or run interactive wizard → create `POSGeneratorConfig`
2. **Generation Phase**: Create businesses → customers → transactions → returns (with realistic relationships)
3. **Export Phase**: Stream to console/files or batch export to multiple formats
4. **Database Integration**: Optional real-time streaming to databases with connection pooling

### Australian Business Logic

- **GST Compliance**: 0% and 10% rates with proper rounding to nearest 5 cents
- **ABN Generation**: Valid Australian Business Numbers with check digit validation  
- **Geographic Distribution**: State-based customer/business distribution matching Australian demographics
- **Seasonal Patterns**: Christmas, EOFY, back-to-school transaction multipliers
- **Payment Methods**: EFTPOS-dominant with realistic Australian payment distribution

### Testing Structure

Tests are organized by component with pytest markers:
- `unit`: Fast unit tests for individual functions
- `integration`: Cross-component integration tests
- `slow`: Long-running tests (data generation, database operations)
- `config`, `models`, `validators`, `generator`, `cli`: Component-specific tests

Coverage target: 80% minimum with detailed HTML reports in `htmlcov/`

### Output Formats & Streaming

**Batch Generation**: CSV, JSON, Parquet, XLSX with configurable output directories
**Live Streaming**: Console display, file streaming, database insertion (real-time)
**Database Support**: SQLite (simple), PostgreSQL/MySQL/MariaDB (production)

### Key Development Notes

- Uses `rich` library extensively for enhanced CLI experience
- Faker with Australian locale for realistic synthetic data
- Decimal arithmetic for financial calculations (GST compliance)
- Comprehensive logging with loguru (configurable verbosity)
- Windows-specific encoding handling for cross-platform compatibility
- Signal handling for graceful shutdown in streaming modes