# 🇦🇺 Australian POS Data Generator

A comprehensive synthetic Australian Point-of-Sale (POS) transaction data generator with GST compliance, realistic business rules, and rich CLI interface. Generate businesses, customers, transactions, and returns in multiple formats or stream directly to databases.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

### 🎯 Australian Context
- **ABN Validation**: Proper Australian Business Number generation and validation
- **GST Compliance**: Accurate GST codes, rates, and rounding rules
- **Realistic Geography**: State-based distributions and Australian postcodes
- **Local Business Patterns**: Australian payment methods and seasonal variations

### 📊 Data Generation
- **Comprehensive Entities**: Businesses, Customers, Transactions, Line Items, Returns
- **Realistic Relationships**: Complex business rules and transaction patterns
- **Configurable Volume**: Scale from small samples to enterprise datasets
- **Time Series**: Historical data with seasonal and daily patterns

### 🚀 Output Formats
- **Static Files**: CSV, JSON, Parquet, Excel (XLSX)
- **Live Streaming**: Console, Database (SQLite, PostgreSQL, MySQL, MariaDB)
- **Flexible Export**: Batch generation or real-time streaming

### 🎮 User Experience
- **Interactive CLI**: Full-featured wizard with navigation control
- **Batch Commands**: Direct command-line generation
- **Rich Interface**: Colorful progress bars and status updates
- **Type Safety**: Strong typing and validation via Pydantic

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip or conda package manager

### Quick Install
```bash
# Clone the repository
git clone <repository-url>
cd aus-retail-data-gen

# Install with pip
pip install -e .

# Or create conda environment
conda env create -f environment.yml
conda activate aus-pos-data-gen
pip install -e .
```

### Verify Installation
```bash
aus-pos-gen --help
```

## 🚀 Quick Start

### Interactive Mode (Recommended)
The interactive wizard provides the easiest way to configure and generate data:

```bash
aus-pos-gen interactive
```

This launches a full-featured CLI wizard with:
- ✅ Step-by-step parameter configuration
- ✅ Input validation and smart defaults
- ✅ Full navigation control (go back to any step)
- ✅ Progress tracking and status updates
- ✅ Graceful exit handling (Ctrl+C)

### Command Line Usage

#### Batch Generation
Generate complete datasets in various formats:

```bash
# Generate CSV files (default format)
aus-pos-gen generate --businesses 5 --customers 1000 --days 30 --format csv

# Generate JSON with custom output directory
aus-pos-gen generate --businesses 10 --customers 2000 --days 7 --format json --output-dir ./my_data

# Generate Excel file
aus-pos-gen generate --businesses 3 --customers 500 --days 14 --format xlsx --output sample_data.xlsx

# Generate Parquet for analytics
aus-pos-gen generate --businesses 8 --customers 1500 --days 60 --format parquet
```

#### Live Streaming
Stream real-time transactions for testing and development:

```bash
# Stream to console (1 transaction per second)
aus-pos-gen stream --businesses 3 --customers 500 --rate 1 --format console

# Stream to CSV file
aus-pos-gen stream --businesses 5 --customers 800 --rate 2 --format csv --output live_data.csv

# Stream to database (PostgreSQL example)
aus-pos-gen stream \
  --businesses 3 --customers 500 --rate 2 --format database \
  --db-type postgresql --db-host localhost --db-port 5432 \
  --db-name pos_data --db-username postgres --db-password password \
  --db-table-prefix live_ --db-schema public

# Stream to SQLite (simpler setup)
aus-pos-gen stream \
  --businesses 2 --customers 300 --rate 1 --format database \
  --db-type sqlite --db-file pos_data.db --db-table-prefix stream_
```

## 📁 Project Structure

```
aus-retail-data-gen/
├── src/aus_pos_data_gen/           # Main package
│   ├── __init__.py                 # Package initialization
│   ├── cli.py                      # CLI interface and commands
│   ├── interactive_handlers.py     # Interactive wizard handlers
│   ├── config.py                   # Configuration classes
│   ├── generator.py                # Core data generation logic
│   ├── database_manager.py         # Enhanced database connectivity
│   ├── models.py                   # Pydantic data models
│   └── validators.py               # ABN and GST validation
├── scripts/                        # Utility scripts
│   ├── generate_sample_data.py     # Programmatic usage example
│   └── test_db_connectivity.py     # Database connection testing
├── tests/                          # Test suite
├── data/processed/                 # Default output directory
├── pyproject.toml                  # Package configuration
├── environment.yml                 # Conda environment
├── pytest.ini                     # Test configuration
└── README.md                       # This file
```

## 🔧 Configuration

### Core Settings
Key parameters available in `POSGeneratorConfig`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `businesses` | Number of businesses to generate | 5 |
| `customers` | Number of customers to generate | 1000 |
| `days` | Days of transaction data | 30 |
| `seed` | Random seed for reproducibility | 42 |
| `daily_transactions` | Base transactions per day | 100-500 |
| `items_per_transaction` | Items per transaction range | 1-8 |

### Australian-Specific Features
- **States Distribution**: Realistic population-based state distribution
- **Payment Methods**: Cash, EFTPOS, Credit Card, Digital Wallet
- **GST Rates**: 0%, 10% with proper rounding
- **Seasonal Patterns**: Christmas, EOFY, back-to-school multipliers
- **Business Categories**: Retail, hospitality, services with appropriate item types

### Database Support
Supports multiple database backends with connection pooling:

```python
# Example database configuration
DatabaseConfig(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="pos_data",
    username="postgres",
    password="password",
    schema="public",
    table_prefix="aus_pos_"
)
```

## 📊 Generated Data Schema

### Businesses
```csv
business_id,abn,name,state,postcode,category,size
```

### Customers  
```csv
customer_id,name,state,postcode,registration_date
```

### Transactions
```csv
transaction_id,business_id,customer_id,timestamp,subtotal_excl_gst,gst_amount,total_incl_gst,payment_method,items
```

### Transaction Items
```csv
transaction_id,item_id,name,category,quantity,unit_price_excl_gst,gst_rate,gst_amount,total_incl_gst
```

### Returns
```csv
return_id,original_transaction_id,customer_id,return_date,reason,refund_amount
```

## 🛠 Development

### Setup Development Environment
```bash
# Clone and setup
git clone <repository-url>
cd aus-retail-data-gen
conda env create -f environment.yml
conda activate aus-pos-data-gen
pip install -e ".[dev]"
```

### Code Quality
```bash
# Format code
black src tests scripts
isort src tests scripts

# Lint
flake8 src tests scripts

# Type check
mypy src
```

### Testing
```bash
# Run tests with coverage
pytest -v --cov=aus_pos_data_gen --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=aus_pos_data_gen --cov-report=html
# View: htmlcov/index.html
```

### Database Testing
```bash
# Test database connectivity
python scripts/test_db_connectivity.py
```

## 📈 Usage Examples

### Programmatic Usage
```python
from pathlib import Path
from datetime import datetime, timedelta
from aus_pos_data_gen.config import POSGeneratorConfig
from aus_pos_data_gen.generator import POSDataGenerator

# Configure generator
config = POSGeneratorConfig(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    output_dir=Path("sample_data"),
    seed=12345
)

# Generate data
generator = POSDataGenerator(config)
result = generator.generate_all_data(
    business_count=10,
    customer_count=2000
)

# Export to files
generator.export_to_csv()
generator.export_to_json()
generator.export_line_items()

print(f"Generated {len(result['transactions'])} transactions")
```

### Database Export
```python
from aus_pos_data_gen.config import DatabaseConfig
from aus_pos_data_gen.database_manager import EnhancedDatabaseManager

# Configure database
db_config = DatabaseConfig(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="analytics",
    username="analyst",
    password="password"
)

# Export with enhanced connection management
result = generator.export_to_database(db_config)
print(f"Exported to database: {result}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🆘 Support

- **Documentation**: Check this README for comprehensive usage examples
- **Issues**: Report bugs or request features via GitHub Issues  
- **Development**: See the Development section for contribution guidelines

## 🔮 Roadmap

- [ ] Additional export formats (Apache Arrow, ORC)
- [ ] Cloud database support (AWS RDS, Azure SQL, Google Cloud SQL)  
- [ ] REST API interface
- [ ] Data quality metrics and validation reports
- [ ] Advanced seasonality modeling
- [ ] Multi-tenant business modeling

---

**Built with ❤️ for the Australian retail analytics community**