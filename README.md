# 🇦🇺 Australian POS Transaction Dataset Generator

**A professional, beautiful, and comprehensive Python package for generating synthetic Australian Point-of-Sale (POS) transaction datasets with full ATO compliance and stunning CLI interface.**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conda](https://img.shields.io/badge/Conda-Ready-green.svg)](https://docs.conda.io/)
[![Rich CLI](https://img.shields.io/badge/CLI-Rich%20Enhanced-cyan.svg)](https://rich.readthedocs.io/)
[![Interactive](https://img.shields.io/badge/Interactive-Questionary-magenta.svg)](https://questionary.readthedocs.io/)

> 🎯 **Generate realistic Australian retail data with enterprise-grade CLI experience**

---

## ✨ **What Makes This Generator Special?**

### 🎨 **Beautiful, Professional CLI Interface**
- **Rich Enhanced**: Stunning terminal output with colors, progress bars, and beautiful tables
- **Interactive Mode**: Step-by-step guided setup with real-time validation
- **Live Progress**: Real-time progress bars, spinners, and status indicators
- **Professional Panels**: Organized information display with borders and styling

### 🏢 **100% Australian Business Compliant**
- **Valid ABN Generation**: Authentic Australian Business Numbers with proper check-digit validation
- **GST Calculations**: Accurate GST calculations following ATO rules (10% standard rate)
- **State & Postcode Validation**: Realistic Australian addresses with proper state-postcode matching
- **Business Hours**: Australian retail operating hours and seasonal patterns

### 💳 **Realistic Australian Payment Methods**
- **EFTPOS**: 45% distribution (most common in Australia)
- **Contactless**: 30% (Apple Pay, Google Pay, contactless cards)
- **Credit Cards**: 15% (Visa, Mastercard, Amex)
- **Cash**: 8% with Australian 5-cent rounding rules
- **Buy Now Pay Later**: 2% (Afterpay, Zip, Klarna)

### 📊 **Production-Ready Data Generation**
- **Seasonal Patterns**: Q4 peaks (December), Q1 lows (January), weekday/weekend variations
- **Return Rates**: Category-specific return rates (clothing: 25%, electronics: 12%, food: 3%)
- **Customer Demographics**: Individual, business, and loyalty program members
- **Product Catalog**: Australian retail products with proper GST classification

### 🛠️ **Enterprise Features**
- **Pydantic Models**: Type-safe data models with validation
- **Conda Environment**: Full conda support with professional dependency management
- **Multiple Formats**: Export to CSV, JSON, Excel, Parquet, SQLite with live progress
- **Reproducible**: Configurable random seeds for consistent results
- **Streaming**: Real-time data streaming for testing streaming applications

---

## 🚀 **Installation & Setup**

### Prerequisites
- **Conda** (Miniconda or Anaconda) - Required for environment management
- **Python 3.11+** - Modern Python with type hints support
- **Git** - For cloning the repository

### Quick Setup (3 Steps)

```bash
# 1. Clone the repository
git clone <repository-url>
cd aus-retail-data-gen

# 2. Create conda environment (includes all dependencies)
conda env create -f environment.yml
conda activate aus-pos-data-gen

# 3. Install the package
pip install -e .
```

### 🎨 **What's Included**
- **Rich 13.7.0** - Beautiful terminal formatting and progress bars
- **Questionary 2.1.0** - Interactive CLI with real-time validation
- **Pydantic 2.11.7** - Type-safe data models and validation
- **Loguru 0.7.3** - Professional logging with colors
- **All export formats**: CSV, JSON, Excel, Parquet, SQLite

### 🧪 **Verify Installation**

```bash
# Check the beautiful info command
aus-pos-gen info

# Test interactive mode
aus-pos-gen interactive
```

---

## 🎯 **Quick Start - Experience the Beauty!**

### ✨ **Watch the Magic in Action**

**Generate with Beautiful Progress Bars:**
```bash
# 🌟 Experience the stunning CLI with live progress bars
aus-pos-gen generate --businesses 3 --customers 50 --days 7 --format csv

# 🎨 You'll see:
# • Beautiful welcome panel with configuration summary
# • Real-time progress bars for each generation step
# • Animated spinners and status indicators
# • Rich tables with emojis and colors
# • Success panel with completion summary
```

**Interactive Mode - Step-by-Step Wizard:**
```bash
# 🎮 Guided experience with real-time validation
aus-pos-gen interactive

# 🎯 Features:
# • Step-by-step configuration with helpful prompts
# • Smart defaults and input validation
# • Clear explanations for each option
# • Beautiful panels and colored output
```

### 📊 **Sample Output - What You'll See**

**Beautiful Info Command:**
```
╭───────────────────── 🚀 System Overview ──────────────────────╮
│                                                              │
│  🇦🇺 Australian POS Data Generator                            │
│  Professional Synthetic Data for Australian Retail Analytics │
│                                                              │
│  Version: 0.1.0  Status: ✅ Active                           │
│  Seed: 42  Start Date: 2025-08-24                           │
│  Payment Methods: 9 supported  GST Rate: 10.0%             │
│                                                              │
╰───────────────────────────────────────────────────────────────╯

✨ Core Features Table with 6 features in colored rows...
📤 Export Formats Table with 5 formats...
💡 Usage Examples Panel with syntax highlighting...
📈 System Stats Panel with quick facts...
```

**Enhanced Generate Command:**
```
╭─────────── 🚀 Data Generation Started ───────────╮
│                                                  │
│  🇦🇺 Australian POS Data Generator                │
│                                                  │
│  📊 Businesses: 3  👥 Customers: 50  📅 Days: 7  │
│  🎯 Format: CSV  🌱 Seed: 42                     │
│                                                  │
╰──────────────────────────────────────────────────╯

⠋ Generating data...          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% -:--:--

  🏪 Generating businesses... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
  👥 Generating customers...  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
  💳 Generating complete dataset... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

📊 Generation Summary Table with emojis and colors...

✅ Success Panel with completion message...
```

### 🚀 **Popular Commands**

```bash
# 🎯 Quick generation with beautiful output
aus-pos-gen generate --businesses 5 --customers 1000 --days 30

# 📊 Large dataset for analytics testing
aus-pos-gen generate --businesses 10 --customers 5000 --days 365 --format parquet

# 💾 Database-ready export
aus-pos-gen generate --format sqlite --days 180 --businesses 15

# 🌊 Stream live data for testing
aus-pos-gen stream --rate 2.0 --format json --duration 60

# 🎨 Interactive mode for beginners
aus-pos-gen interactive

# 📋 View all available commands beautifully
aus-pos-gen --help
```

---

## 📤 **Export Formats - Enterprise Ready**

### 🎯 **Supported Formats with Live Progress**

| Format | Extension | Description | Best For | Progress |
|--------|-----------|-------------|----------|----------|
| **CSV** | `.csv` | Comma-separated values with headers | Excel analysis, basic data processing | ✅ |
| **JSON** | `.json` | Structured JSON with nested data | API integration, web applications | ✅ |
| **Excel** | `.xlsx` | Multi-sheet Excel workbook | Business reporting, presentations | ✅ |
| **Parquet** | `.parquet` | Columnar storage format | Big data analytics, data lakes | ✅ |
| **SQLite** | `.db` | Relational database file | Complex queries, data relationships | ✅ |

### 🚀 **Format Selection with Beautiful Progress**

```bash
# 📊 Excel workbook with live progress bars
aus-pos-gen generate --format xlsx --businesses 5

# 🏗️ Parquet for big data processing
aus-pos-gen generate --format parquet --days 365 --customers 5000

# 🗄️ SQLite database with all relationships
aus-pos-gen generate --format sqlite --businesses 10 --days 180

# 🌐 JSON for API integration
aus-pos-gen generate --format json --days 30
```

### 💡 **Format Recommendations**

**For Data Science & Analytics:**
```bash
aus-pos-gen generate --format parquet --days 365 --customers 10000
# → Optimized for big data processing, column-oriented storage
```

**For Business Reporting:**
```bash
aus-pos-gen generate --format xlsx --businesses 10 --days 90
# → Multi-sheet Excel with charts and formatting ready
```

**For API Development:**
```bash
aus-pos-gen generate --format json --days 30 --businesses 5
# → Structured JSON perfect for API testing and web apps
```

**For Database Integration:**
```bash
aus-pos-gen generate --format sqlite --days 180 --customers 5000
# → Ready-to-query SQLite database with proper relationships
```

---

## 🌊 **Live Data Streaming - Real-Time Testing**

**Stream continuous Australian POS transaction data for real-time analytics and testing:**

### 🚀 **Streaming with Beautiful Output**

```bash
# 🌊 Stream to console with real-time display
aus-pos-gen stream --rate 2.0 --format console

# 📊 Stream JSON for API testing
aus-pos-gen stream --rate 1.5 --format json --duration 300

# 🎯 High-frequency testing
aus-pos-gen stream --rate 10.0 --format json --output test_stream.json
```

**What You'll See:**
```
🌊 Starting live data stream...
📊 Rate: 2.0 transactions/second
⏱️  Duration: Continuous (press Ctrl+C to stop)

💳 Transaction #1 | $45.67 | EFTPOS | Customer: CUST001
💳 Transaction #2 | $23.45 | CONTACTLESS | Customer: CUST045
💳 Transaction #3 | $89.12 | CREDIT_CARD | Customer: CUST112
💳 Transaction #4 | $12.34 | CASH | Customer: CUST067

📈 Stream Statistics:
   • Transactions: 4
   • Total Value: $170.58
   • Average TPS: 2.0
   • Running Time: 2.0 seconds
```

### 🎮 **Interactive Mode - Step-by-Step Wizard**

**For users who prefer a guided experience:**

```bash
aus-pos-gen interactive
```

**Enhanced Interactive Features:**
- **Step-by-step configuration** with beautiful panels
- **Real-time input validation** with helpful error messages
- **Smart defaults** for all parameters
- **Clear explanations** for each option
- **Multiple operation modes** (generate/stream/info)

**Interactive Workflow:**
1. **Choose Operation**: Generate data, stream data, or show info
2. **Configure Parameters**: Businesses, customers, days, format, seed
3. **Live Progress**: Watch beautiful progress bars during generation
4. **Success Summary**: View detailed results with rich tables

---

## 🏗️ **Architecture & Technical Details**

### 🏢 **Core Components**

**Data Models (Pydantic):**
```python
class Transaction(BaseModel):
    transaction_id: str
    business_id: str
    customer_id: Optional[str]
    transaction_datetime: datetime
    subtotal_ex_gst: Decimal
    gst_amount: Decimal
    total_inc_gst: Decimal
    payment_method: PaymentMethod
    items: List[TransactionItem]
```

**Generator Classes:**
- `POSDataGenerator` - Main data generation orchestrator
- `ABNValidator` - Australian Business Number validation
- `GSTCalculator` - GST calculations with ATO compliance
- `AustralianAddressValidator` - State/postcode validation

### 🏪 **Australian Business Rules**

**Receipt Requirements:**
- Business name and ABN for transactions >$75
- GST breakdown for tax invoices
- Date, time, and item descriptions
- Total price includes GST statement

**Business Hours:**
- Weekdays: 9:00 AM - 5:00 PM (typical)
- Peak hours: 12:00 PM - 2:00 PM, 5:00 PM - 7:00 PM
- Seasonal patterns with Q4 peaks

**GST Compliance:**
```
GST Amount = (GST-Inclusive Price × 1) ÷ 11
GST-Exclusive Price = GST-Inclusive Price - GST Amount
```

---

## 📊 **Data Structure & Schema**

### Core Tables

#### Transactions
```csv
transaction_id,store_id,workstation_id,employee_id,transaction_type,business_day_date,transaction_datetime,sequence_number,receipt_number,customer_id,subtotal_ex_gst,gst_amount,total_inc_gst,payment_method,tender_amount,change_amount,currency_code,operator_id,shift_id,business_abn
TXN240824001,STR001,POS03,EMP001,SALE,2025-08-24,2025-08-24T14:32:15+10:00,1234,R240001234,CUST001,27.27,2.73,30.00,EFTPOS,30.00,0.00,AUD,EMP001,SHIFT001,"12 345 678 901"
```

#### Transaction Line Items
```csv
transaction_id,line_number,item_type,product_id,sku,barcode,product_name,category,brand,quantity,unit_price_ex_gst,unit_price_inc_gst,line_subtotal_ex_gst,line_gst_amount,line_total_inc_gst,gst_code,discount_amount,discount_type,promotion_id
TXN240824001,1,SALE,PRD001,COFFEE-REG,9312345000001,"Regular Coffee","beverages","Local Roasters",2,4.09,4.50,8.18,0.82,9.00,GST,0.00,NONE,NULL
```

#### Businesses
```csv
store_id,business_name,abn,acn,trading_name,store_address,suburb,state,postcode,phone,email,gst_registered,pos_system_type,terminal_count
STR001,"Sample Retail Pty Ltd","12 345 678 901",123456789,"Sample Trading","123 Collins Street","Melbourne","VIC","3000","(03) 9123 4567","sales@sample.com.au",true,"Square",3
```

#### Returns
```csv
return_id,original_transaction_id,original_receipt_number,return_date,return_time,return_reason_code,return_reason_description,returned_by_customer_id,processed_by_employee_id,refund_method,refund_amount,store_credit_issued,restocking_fee,condition_code,original_purchase_date
RET240824001,TXN240820045,R240000987,2025-08-24,2025-08-24T15:45:00+10:00,WRONG_SIZE,"Wrong size - too small",CUST002,EMP003,EFTPOS,89.95,0.00,0.00,UNOPENED,2025-08-20
```

---

## 🔧 **Configuration & Customization**

### Environment Variables
```bash
export AUS_POS_SEED=42
export AUS_POS_OUTPUT_DIR=./data
export AUS_POS_DEFAULT_BUSINESSES=5
export AUS_POS_DEFAULT_CUSTOMERS=1000
export AUS_POS_DEFAULT_DAYS=30
```

### Programmatic Configuration
```python
from aus_pos_data_gen.config import POSGeneratorConfig
from aus_pos_data_gen.generator import POSDataGenerator

config = POSGeneratorConfig(
    seed=12345,
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    output_dir=Path("./custom_data"),
    business_name="Custom Retail Store"
)

generator = POSDataGenerator(config)
data = generator.generate_all_data(
    business_count=15,
    customer_count=5000
)
```

---

## 🧪 **Testing & Development**

### Run Test Suite
```bash
# All tests with coverage
pytest --cov=aus_pos_data_gen --cov-report=html

# Specific test categories
pytest tests/test_validators.py
pytest tests/test_generator.py -v

# Quick validation tests
pytest tests/ -k "test_abn" -v
```

### Code Quality
```bash
# Format code
black src/aus_pos_data_gen/

# Sort imports
isort src/aus_pos_data_gen/

# Lint code
flake8 src/aus_pos_data_gen/

# Type checking
mypy src/aus_pos_data_gen/
```

### Adding New Products
```python
# Add to generator.py product catalog
self.product_catalog["new_product"] = {
    "name": "Premium Wireless Headphones",
    "category": "electronics",
    "brand": "AudioTech",
    "sku": "HEADPHONES-PREM",
    "barcode": "9334567890130",
    "unit_price": Decimal("199.95"),
    "gst_code": GSTCode.GST,
    "return_rate": 0.08  # 8% return rate
}
```

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Format code: `black src/aus_pos_data_gen/`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Development Setup
```bash
# Install in development mode
pip install -e ".[dev]"

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest
```

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Australian Taxation Office (ATO)** - For GST compliance guidelines
- **Australian Retail Industry** - For business practice insights
- **Rich Library** - For beautiful terminal formatting
- **Questionary** - For interactive CLI capabilities
- **Pydantic** - For type-safe data models
- **Open-source Python Community** - For excellent libraries

---

## 🎯 **Quick Reference**

### Most Common Commands
```bash
# Quick start
aus-pos-gen generate --businesses 5 --days 30

# Large dataset
aus-pos-gen generate --businesses 20 --customers 10000 --days 365 --format parquet

# Interactive setup
aus-pos-gen interactive

# Stream testing
aus-pos-gen stream --rate 5.0 --duration 120

# View capabilities
aus-pos-gen info
```

### CLI Help
```bash
aus-pos-gen --help           # Main help
aus-pos-gen generate --help  # Generation options
aus-pos-gen stream --help    # Streaming options
aus-pos-gen info             # Beautiful system overview
```

---

**Disclaimer**: This tool generates synthetic data for testing and development purposes. It is not intended for actual business use without proper validation and compliance review.