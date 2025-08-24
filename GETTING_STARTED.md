# Getting Started with Australian POS Data Generator

This guide will help you set up and start using the Australian POS Transaction Dataset Generator.

## Project Overview

You've successfully created a comprehensive Python package for generating synthetic Australian POS (Point-of-Sale) transaction data that complies with Australian Taxation Office (ATO) requirements and Australian retail business practices.

## Project Structure

```
aus-retail-data-gen/
├── environment.yml          # Conda environment specification
├── pyproject.toml           # Modern Python project configuration
├── setup.py                 # Legacy setup script
├── README.md                # Comprehensive documentation
├── setup_environment.bat    # Windows setup script
├── setup_environment.ps1    # PowerShell setup script
├── scripts/
│   └── generate_sample_data.py  # Example usage script
├── src/aus_pos_data_gen/    # Main package (src layout)
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration management
│   ├── generator.py         # Main data generator
│   ├── models.py            # Pydantic data models
│   └── validators.py        # Australian business validators
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_validators.py   # Validator tests
├── data/                    # Data directories
│   ├── raw/                 # Raw generated data
│   └── processed/           # Processed/cleaned data
└── docs/                    # Documentation
```

## Setup Instructions

### Prerequisites
- **Conda** (Miniconda or Anaconda) - for environment management
- **Windows PowerShell** or **Command Prompt**

### Step 1: Verify Conda Installation

Open PowerShell or Command Prompt and check conda:

```bash
conda --version
```

If conda is not installed, download and install Miniconda from: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Navigate to Project Directory

```bash
cd C:\Users\Goodzy\Desktop\DevOps\Projects\aus-retail-data-gen
```

### Step 3: Create Conda Environment

The environment specification is already created in `environment.yml`. Create the environment:

```bash
conda env create -f environment.yml
```

This will create a conda environment named `aus-pos-data-gen` with all required dependencies.

### Step 4: Activate Environment and Install Package

#### Option A: Use the Setup Script (Recommended)

For Windows Command Prompt:
```cmd
setup_environment.bat
```

For PowerShell:
```powershell
.\setup_environment.ps1
```

#### Option B: Manual Setup

1. **Activate the environment**:
   ```bash
   conda activate aus-pos-data-gen
   ```

2. **Install the package**:
   ```bash
   python -m pip install -e .
   ```

### Step 5: Verify Installation

Check that everything is working:

```bash
# Check the CLI is available
aus-pos-gen --help

# Get information about the generator
aus-pos-gen info
```

## Usage Examples

### Basic Data Generation

Generate 30 days of data for 5 businesses:

```bash
aus-pos-gen generate --days 30 --businesses 5 --customers 1000
```

### Custom Output Directory

```bash
aus-pos-gen generate --output ./my-custom-data --days 90
```

### Generate with Specific Seed (Reproducible)

```bash
aus-pos-gen generate --seed 12345 --days 365
```

### Validate Australian Business Number

```bash
aus-pos-gen validate-abn "12 345 678 901"
```

### Calculate GST

```bash
aus-pos-gen calculate-gst 100.00
```

### Generate Valid ABN

```bash
aus-pos-gen generate-abn
```

## Programmatic Usage

You can also use the generator programmatically:

```python
from aus_pos_data_gen.config import POSGeneratorConfig
from aus_pos_data_gen.generator import POSDataGenerator

# Create configuration
config = POSGeneratorConfig(
    seed=42,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Initialize generator
generator = POSDataGenerator(config)

# Generate data
data = generator.generate_all_data(
    business_count=3,
    customer_count=500
)

# Export to CSV
files = generator.export_to_csv()
```

## Generated Data Structure

The generator creates several CSV files:

### Transactions (`transactions.csv`)
- Complete transaction records with GST calculations
- Australian business compliance
- Payment method distributions
- Customer and employee information

### Transaction Items (`transaction_items.csv`)
- Line-level item details
- Product information with barcodes
- GST codes and calculations
- Quantity and pricing details

### Businesses (`businesses.csv`)
- Australian businesses with valid ABNs
- Business addresses and contact details
- POS system information
- GST registration status

### Customers (`customers.csv`)
- Customer demographics
- Loyalty program information
- Australian addresses
- Business customer ABNs

### Returns (`returns.csv`)
- Return transactions
- Return reasons and conditions
- Refund processing
- Original transaction references

## Australian Compliance Features

### ABN Validation
- 11-digit format validation
- Check-digit algorithm verification
- Formatted display (XX XXX XXX XXX)

### GST Calculations
- 10% standard GST rate
- Proper GST-exclusive/inclusive calculations
- Australian rounding rules
- GST-free and exempt item handling

### Payment Methods
- Realistic Australian payment distributions
- EFTPOS (45%), Contactless (30%), Credit Cards (15%)
- Cash with 5-cent rounding
- Buy Now Pay Later options

### Business Rules
- Australian state and postcode validation
- Retail business hours (9 AM - 5 PM weekdays)
- Peak trading periods
- Seasonal transaction patterns

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=aus_pos_data_gen --cov-report=html

# Run specific tests
python -m pytest tests/test_validators.py
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Troubleshooting

### Common Issues

1. **Conda activation fails**
   - Ensure conda is properly installed
   - Try running `conda init` if needed
   - Use the setup scripts provided

2. **Python not found**
   - Use `conda run -n aus-pos-data-gen python` instead of `python`
   - Ensure the environment is activated

3. **Import errors**
   - Make sure you're in the correct directory
   - Check that the package is installed: `pip list | findstr aus-pos-data-gen`

4. **GST calculation issues**
   - Verify ATO compliance requirements
   - Check the validators.py for calculation logic

### Getting Help

- Check the README.md for detailed documentation
- Review the Australian compliance requirements
- Examine the test files for usage examples
- Create an issue if you encounter problems

## Next Steps

1. **Explore the generated data** in the `data/processed/` directory
2. **Customize the configuration** in `src/aus_pos_data_gen/config.py`
3. **Add new products** to the catalog in `generator.py`
4. **Extend the test suite** with additional test cases
5. **Create custom reports** using the generated CSV files

## Australian Business Resources

- [ATO GST Calculator](https://www.ato.gov.au/business/gst/)
- [ABN Lookup](https://abr.business.gov.au/)
- [Australian Retail Industry Statistics](https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade)

---

**Congratulations!** You now have a fully functional Australian POS data generator that creates realistic, compliant synthetic data for testing and development purposes.
