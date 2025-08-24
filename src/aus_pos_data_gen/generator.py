"""
Main POS data generator for Australian retail transactions.

This module orchestrates the generation of realistic Australian POS data
with proper GST calculations, business compliance, and seasonal patterns.
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterator
from faker import Faker
from loguru import logger
from rich.progress import Progress, TaskID
from rich.progress import TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console

from .config import POSGeneratorConfig, AustralianStates, ReturnRates, DatabaseConfig
from .models import (
    Transaction, TransactionItem, ReturnTransaction, Customer, Business,
    PaymentMethod, TransactionType, GSTCode, AustralianState
)
from .validators import ABNValidator, GSTCalculator, AustralianAddressValidator


class POSDataGenerator:
    """Main generator for Australian POS transaction data."""

    def __init__(self, config: Optional[POSGeneratorConfig] = None):
        """Initialize the POS data generator with configuration."""
        try:
            self.config = config or POSGeneratorConfig()
            self.faker = Faker(self.config.locale)
            self.faker.seed_instance(self.config.seed)
            random.seed(self.config.seed)

            # Initialize data containers
            self.businesses: List[Business] = []
            self.customers: List[Customer] = []
            self.transactions: List[Transaction] = []
            self.returns: List[ReturnTransaction] = []

            # Sequence counters
            self.transaction_sequence = 1
            self.receipt_sequence = 1

            # Product catalog
            self.product_catalog = self._generate_product_catalog()

            logger.info("Initialized POS Data Generator with seed: {}", self.config.seed)
        except Exception as e:
            logger.error("Error initializing POS Data Generator: {}", e)
            raise

    def _generate_product_catalog(self) -> Dict[str, Dict]:
        """Generate a realistic Australian retail product catalog."""
        return {
            # Food items
            "coffee_regular": {
                "name": "Regular Coffee",
                "category": "beverages",
                "brand": "Local Roasters",
                "sku": "COFFEE-REG",
                "barcode": "9312345678901",
                "unit_price": Decimal("4.50"),
                "gst_code": GSTCode.GST,
            },
            "sandwich_ham": {
                "name": "Ham & Cheese Sandwich",
                "category": "food",
                "brand": "Café Kitchen",
                "sku": "SANDWICH-HAM",
                "barcode": "9312345678918",
                "unit_price": Decimal("12.00"),
                "gst_code": GSTCode.GST,
            },
            "muffin_choc": {
                "name": "Chocolate Muffin",
                "category": "food",
                "brand": "Bakery Co",
                "sku": "MUFFIN-CHOC",
                "barcode": "9312345678925",
                "unit_price": Decimal("5.50"),
                "gst_code": GSTCode.GST,
            },
            "water_bottle": {
                "name": "Bottled Water 600ml",
                "category": "beverages",
                "brand": "Pure Spring",
                "sku": "WATER-BOTTLE",
                "barcode": "9312345678932",
                "unit_price": Decimal("3.00"),
                "gst_code": GSTCode.GST,
            },
            # Clothing items
            "tshirt_basic": {
                "name": "Basic Cotton T-Shirt",
                "category": "clothing",
                "brand": "Fashion Basics",
                "sku": "TSHIRT-BASIC",
                "barcode": "9323456789012",
                "unit_price": Decimal("29.95"),
                "gst_code": GSTCode.GST,
            },
            "jeans_blue": {
                "name": "Blue Denim Jeans",
                "category": "clothing",
                "brand": "Denim Co",
                "sku": "JEANS-BLUE",
                "barcode": "9323456789029",
                "unit_price": Decimal("89.95"),
                "gst_code": GSTCode.GST,
            },
            # Electronics items
            "phone_case": {
                "name": "Universal Phone Case",
                "category": "electronics",
                "brand": "Tech Accessories",
                "sku": "PHONE-CASE",
                "barcode": "9334567890123",
                "unit_price": Decimal("24.95"),
                "gst_code": GSTCode.GST,
            },
            "headphones": {
                "name": "Wireless Headphones",
                "category": "electronics",
                "brand": "Audio Tech",
                "sku": "HEADPHONES-WL",
                "barcode": "9334567890130",
                "unit_price": Decimal("79.95"),
                "gst_code": GSTCode.GST,
            },
            # Health & Beauty
            "pain_relief": {
                "name": "Pain Relief Tablets",
                "category": "pharmacy",
                "brand": "Pharma Plus",
                "sku": "PAIN-RELIEF-24",
                "barcode": "9345678901234",
                "unit_price": Decimal("12.95"),
                "gst_code": GSTCode.GST_FREE,
            },
            "shampoo": {
                "name": "Herbal Shampoo 500ml",
                "category": "health",
                "brand": "Natural Care",
                "sku": "SHAMPOO-HERBAL",
                "barcode": "9345678901241",
                "unit_price": Decimal("15.95"),
                "gst_code": GSTCode.GST,
            },
        }

    def generate_businesses(self, count: int = 5, progress_callback=None) -> List[Business]:
        """Generate Australian businesses with proper ABNs."""
        logger.info("Generating {} businesses", count)
        businesses = []

        for i in range(count):
            try:
                # Generate valid ABN
                abn = ABNValidator.generate_valid_abn()
                formatted_abn = ABNValidator.format_abn(abn)

                # Select state based on distribution
                state = random.choices(
                    list(AustralianStates.STATES.keys()),
                    weights=[self.config.states_distribution[state] for state in AustralianStates.STATES.keys()]
                )[0]

                # Generate address
                state_info = AustralianStates.STATES[state]
                postcode = f"{random.choice(list(state_info['postcodes'])):04d}"

                # Generate business data
                business_data = {
                    "store_id": f"{i+1:02d}",
                    "business_name": self.faker.company(),
                    "abn": formatted_abn,
                    "trading_name": None,
                    "store_address": self.faker.street_address(),
                    "suburb": self.faker.city(),
                    "state": AustralianState(state),
                    "postcode": postcode,
                    "phone": self.faker.phone_number(),
                    "email": self.faker.company_email(),
                    "gst_registered": True,
                    "pos_system_type": random.choice(["Square", "Shopify", "Clover", "Hike"]),
                    "terminal_count": random.randint(1, 5)
                }

                logger.debug(f"Creating business with data: {business_data}")
                business = Business(**business_data)
                businesses.append(business)
                logger.debug(f"Generated business {i+1}: {business.business_name}")

                # Update progress if callback provided
                if progress_callback:
                    progress_callback()

            except Exception as e:
                logger.error(f"Error generating business {i+1}: {e}")
                raise

        self.businesses = businesses
        logger.info("Generated {} businesses", len(businesses))
        return businesses

    def generate_customers(self, count: int = 1000, progress_callback=None) -> List[Customer]:
        """Generate Australian customers with realistic demographics."""
        logger.info("Generating {} customers", count)
        customers = []

        for i in range(count):
            customer_type = random.choices(
                ["INDIVIDUAL", "BUSINESS", "LOYALTY", "STAFF"],
                weights=[0.7, 0.15, 0.1, 0.05]
            )[0]

            # Generate basic customer data
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()

            # Generate address
            state = random.choices(
                list(AustralianStates.STATES.keys()),
                weights=[self.config.states_distribution[state] for state in AustralianStates.STATES.keys()]
            )[0]
            state_info = AustralianStates.STATES[state]
            postcode = f"{random.choice(list(state_info['postcodes'])):04d}"

            customer = Customer(
                customer_id=f"{i+1:06d}",
                customer_type=customer_type,
                first_name=first_name if customer_type != "BUSINESS" else None,
                last_name=last_name if customer_type != "BUSINESS" else None,
                company_name=self.faker.company() if customer_type == "BUSINESS" else None,
                email=self.faker.email(),
                phone=self.faker.phone_number(),
                date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=80) if customer_type == "INDIVIDUAL" else None,
                loyalty_member=random.random() < 0.3,  # 30% are loyalty members
                loyalty_points_earned=random.randint(0, 1000),
                loyalty_points_redeemed=random.randint(0, 500),
                address=self.faker.street_address(),
                suburb=self.faker.city(),
                state=AustralianState(state),
                postcode=postcode,
                customer_abn=ABNValidator.generate_valid_abn() if customer_type == "BUSINESS" else None
            )
            customers.append(customer)

            # Update progress if callback provided
            if progress_callback:
                progress_callback()

        self.customers = customers
        logger.info("Generated {} customers", len(customers))
        return customers

    def generate_transaction_date_range(self) -> Iterator[datetime]:
        """Generate business dates within the configured range."""
        current_date = self.config.start_date

        while current_date <= self.config.end_date:
            # Skip weekends (optional - Australian retail often open weekends)
            if current_date.weekday() < 5:  # Monday to Friday
                yield current_date
            current_date += timedelta(days=1)

    def generate_daily_transactions(self, business: Business, date: datetime) -> List[Transaction]:
        """Generate transactions for a specific business on a specific date."""
        # Determine store size and transaction volume
        store_size = self._get_store_size(business.store_id)
        daily_range = self.config.daily_transactions[store_size]
        transaction_count = random.randint(*daily_range)

        # Apply seasonal multiplier
        transaction_count = int(transaction_count * self._get_seasonal_multiplier(date))

        transactions = []

        for _ in range(transaction_count):
            transaction = self._generate_single_transaction(business, date)
            transactions.append(transaction)

        return transactions

    def _get_store_size(self, store_id: str) -> str:
        """Determine store size based on configuration."""
        # Simple hash-based distribution
        hash_val = hash(store_id) % 100 / 100.0
        cumulative = 0

        for size, weight in self.config.store_size_distribution.items():
            cumulative += weight
            if hash_val <= cumulative:
                return size

        return "medium"  # fallback

    def _get_seasonal_multiplier(self, date: datetime) -> float:
        """Get seasonal transaction multiplier."""
        month = date.month

        if 10 <= month <= 12:  # Q4
            return self.config.seasonal_multipliers["q4"]
        elif 1 <= month <= 3:  # Q1
            return self.config.seasonal_multipliers["q1"]
        else:  # Q2, Q3
            return 1.0

    def _generate_single_transaction(self, business: Business, date: datetime) -> Transaction:
        """Generate a single transaction with line items."""
        transaction_id = str(uuid.uuid4())[:16].upper()

        # Generate transaction timestamp during business hours
        hour = random.choices(
            list(range(9, 18)),  # 9 AM to 6 PM
            weights=[1, 2, 3, 4, 5, 4, 3, 2, 1]  # Peak around lunch time
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        transaction_datetime = date.replace(hour=hour, minute=minute, second=second)

        # Select customer (some transactions are cash/anonymous)
        customer = None
        if random.random() < 0.7:  # 70% have customer data
            customer = random.choice(self.customers)

        # Generate line items
        items = self._generate_line_items(transaction_id)

        # Calculate totals
        subtotal_ex_gst = sum(item.line_subtotal_ex_gst for item in items)
        gst_amount = sum(item.line_gst_amount for item in items)
        total_inc_gst = sum(item.line_total_inc_gst for item in items)

        # Select payment method
        payment_method = random.choices(
            list(self.config.payment_methods.keys()),
            weights=list(self.config.payment_methods.values())
        )[0]

        # Calculate tender and change
        tender_amount = total_inc_gst
        if payment_method == "CASH":
            # Cash transactions may include change
            tender_amount = self._round_to_cash_payment(total_inc_gst)

        change_amount = tender_amount - total_inc_gst

        transaction = Transaction(
            transaction_id=transaction_id,
            store_id=business.store_id,
            workstation_id=f"{random.randint(1, 10):02d}",
            employee_id=f"{random.randint(1, 50):04d}",
            transaction_type=TransactionType.SALE,
            business_day_date=date,
            transaction_datetime=transaction_datetime,
            sequence_number=self.transaction_sequence,
            receipt_number=f"{self.receipt_sequence:08d}",
            customer_id=customer.customer_id if customer else None,
            subtotal_ex_gst=subtotal_ex_gst,
            gst_amount=gst_amount,
            total_inc_gst=total_inc_gst,
            payment_method=PaymentMethod(payment_method),
            tender_amount=tender_amount,
            change_amount=change_amount,
            currency_code="AUD",
            operator_id=f"{random.randint(1, 50):04d}",
            shift_id=f"{random.randint(1, 3):04d}",
            business_abn=business.abn,
            items=items
        )

        self.transaction_sequence += 1
        self.receipt_sequence += 1

        return transaction

    def _generate_line_items(self, transaction_id: str) -> List[TransactionItem]:
        """Generate line items for a transaction."""
        item_count = random.randint(*self.config.items_per_transaction)
        items = []

        for line_num in range(1, item_count + 1):
            product = random.choice(list(self.product_catalog.values()))

            # Random quantity (1-5 for most items)
            quantity = random.randint(1, 5)

            # Calculate pricing
            unit_price_inc_gst = product["unit_price"]
            gst_calc = GSTCalculator.calculate_gst_components(
                unit_price_inc_gst * quantity,
                product["gst_code"]
            )

            line_total_inc_gst = unit_price_inc_gst * quantity
            line_gst_amount = gst_calc.gst_amount
            line_subtotal_ex_gst = gst_calc.gst_exclusive_amount
            unit_price_ex_gst = line_subtotal_ex_gst / quantity

            item = TransactionItem(
                transaction_id=transaction_id,
                line_number=line_num,
                item_type="SALE",
                product_id=f"{line_num:06d}",
                sku=product["sku"],
                barcode=product["barcode"],
                product_name=product["name"],
                category=product["category"],
                brand=product["brand"],
                quantity=Decimal(str(quantity)),
                unit_price_ex_gst=unit_price_ex_gst,
                unit_price_inc_gst=unit_price_inc_gst,
                line_subtotal_ex_gst=line_subtotal_ex_gst,
                line_gst_amount=line_gst_amount,
                line_total_inc_gst=line_total_inc_gst,
                gst_code=product["gst_code"]
            )
            items.append(item)

        return items

    def _round_to_cash_payment(self, amount: Decimal) -> Decimal:
        """Round cash payment to nearest 5 cents (Australian cash rounding)."""
        # Australian cash rounding to nearest 5 cents
        remainder = amount % Decimal("0.05")
        if remainder < Decimal("0.025"):
            return amount - remainder
        else:
            return amount + (Decimal("0.05") - remainder)

    def generate_all_data(self, business_count: int = 5, customer_count: int = 1000) -> Dict:
        """Generate complete dataset with businesses, customers, and transactions."""
        logger.info("Starting complete data generation...")

        # Use Rich progress bars for visual feedback
        console = Console()
        with Progress(
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(complete_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
            auto_refresh=True,
            refresh_per_second=10
        ) as progress:
            # Generate businesses
            business_task = progress.add_task("Generating businesses...", total=business_count)
            self.generate_businesses(business_count, lambda: progress.update(business_task, advance=1))

            # Generate customers
            customer_task = progress.add_task("Generating customers...", total=customer_count)
            self.generate_customers(customer_count, lambda: progress.update(customer_task, advance=1))

            # Generate transactions for each business and date
            total_dates = sum(1 for _ in self.generate_transaction_date_range())
            transaction_task = progress.add_task("Generating transactions...", total=total_dates * len(self.businesses))

            self.transactions = []
            for business in self.businesses:
                for date in self.generate_transaction_date_range():
                    daily_transactions = self.generate_daily_transactions(business, date)
                    self.transactions.extend(daily_transactions)
                    progress.update(transaction_task, advance=1)

        # Generate returns
        self._generate_returns()

        result = {
            "businesses": self.businesses,
            "customers": self.customers,
            "transactions": self.transactions,
            "returns": self.returns,
            "summary": {
                "total_businesses": len(self.businesses),
                "total_customers": len(self.customers),
                "total_transactions": len(self.transactions),
                "total_returns": len(self.returns),
                "date_range": {
                    "start": self.config.start_date.isoformat(),
                    "end": self.config.end_date.isoformat()
                }
            }
        }

        logger.info("Data generation completed!")
        logger.info("Summary: {} businesses, {} customers, {} transactions, {} returns",
                   len(self.businesses), len(self.customers),
                   len(self.transactions), len(self.returns))

        return result

    def _generate_returns(self):
        """Generate return transactions based on return rates."""
        logger.info("Generating return transactions...")
        returns = []

        for transaction in self.transactions:
            for item in transaction.items:
                return_rate = ReturnRates.get_by_category(item.category)
                if random.random() < return_rate:
                    return_transaction = self._generate_return(transaction, item)
                    returns.append(return_transaction)

        self.returns = returns
        logger.info("Generated {} return transactions", len(returns))

    def _generate_return(self, original_transaction: Transaction, item: TransactionItem) -> ReturnTransaction:
        """Generate a return transaction for a specific item."""
        return_id = str(uuid.uuid4())[:16].upper()

        # Return within 30 days
        return_date = original_transaction.transaction_datetime + timedelta(days=random.randint(1, 30))

        return_reasons = {
            "clothing": ["WRONG_SIZE", "WRONG_ITEM", "CHANGE_MIND"],
            "electronics": ["DEFECTIVE", "WRONG_ITEM", "WARRANTY"],
            "food": ["CHANGE_MIND", "DEFECTIVE"],
            "beverages": ["CHANGE_MIND", "DEFECTIVE"],
        }

        category_reasons = return_reasons.get(item.category, ["CHANGE_MIND"])
        return_reason = random.choice(category_reasons)

        return ReturnTransaction(
            return_id=return_id,
            original_transaction_id=original_transaction.transaction_id,
            original_receipt_number=original_transaction.receipt_number,
            return_date=return_date.date(),
            return_time=return_date,
            return_reason_code=return_reason,
            return_reason_description=f"Customer returned {item.product_name} due to {return_reason.lower().replace('_', ' ')}",
            returned_by_customer_id=original_transaction.customer_id,
            processed_by_employee_id=f"{random.randint(1, 50):04d}",
            refund_method=original_transaction.payment_method,
            refund_amount=item.line_total_inc_gst,
            original_purchase_date=original_transaction.transaction_datetime.date()
        )

    def export_to_csv(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all generated data to CSV files."""
        import pandas as pd

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Export businesses
        if self.businesses:
            businesses_df = pd.DataFrame([b.dict() for b in self.businesses])
            businesses_file = output_dir / "businesses.csv"
            businesses_df.to_csv(businesses_file, index=False)
            exported_files["businesses"] = businesses_file

        # Export customers
        if self.customers:
            customers_df = pd.DataFrame([c.dict() for c in self.customers])
            customers_file = output_dir / "customers.csv"
            customers_df.to_csv(customers_file, index=False)
            exported_files["customers"] = customers_file

        # Export transactions
        if self.transactions:
            transactions_data = []
            for transaction in self.transactions:
                tx_dict = transaction.dict()
                tx_dict["items"] = [item.dict() for item in transaction.items]
                transactions_data.append(tx_dict)

            transactions_df = pd.DataFrame(transactions_data)
            transactions_file = output_dir / "transactions.csv"
            transactions_df.to_csv(transactions_file, index=False)
            exported_files["transactions"] = transactions_file

        # Export returns
        if self.returns:
            returns_df = pd.DataFrame([r.dict() for r in self.returns])
            returns_file = output_dir / "returns.csv"
            returns_df.to_csv(returns_file, index=False)
            exported_files["returns"] = returns_file

        logger.info("Exported data to: {}", output_dir)
        return exported_files

    def export_line_items(self, output_dir: Optional[Path] = None) -> Path:
        """Export transaction line items to separate CSV."""
        import pandas as pd

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        line_items_data = []
        for transaction in self.transactions:
            for item in transaction.items:
                line_items_data.append(item.dict())

        line_items_df = pd.DataFrame(line_items_data)
        line_items_file = output_dir / "transaction_items.csv"
        line_items_df.to_csv(line_items_file, index=False)

        logger.info("Exported line items to: {}", line_items_file)
        return line_items_file

    def export_to_json(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all data to JSON files."""
        import json

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Export businesses
        if self.businesses:
            businesses_data = [b.dict() for b in self.businesses]
            businesses_file = output_dir / "businesses.json"
            with open(businesses_file, 'w') as f:
                json.dump(businesses_data, f, indent=2, default=str)
            exported_files["businesses"] = businesses_file

        # Export customers
        if self.customers:
            customers_data = [c.dict() for c in self.customers]
            customers_file = output_dir / "customers.json"
            with open(customers_file, 'w') as f:
                json.dump(customers_data, f, indent=2, default=str)
            exported_files["customers"] = customers_file

        # Export transactions
        if self.transactions:
            transactions_data = []
            for transaction in self.transactions:
                tx_dict = transaction.dict()
                tx_dict["items"] = [item.dict() for item in transaction.items]
                transactions_data.append(tx_dict)

            transactions_file = output_dir / "transactions.json"
            with open(transactions_file, 'w') as f:
                json.dump(transactions_data, f, indent=2, default=str)
            exported_files["transactions"] = transactions_file

        # Export returns
        if self.returns:
            returns_data = [r.dict() for r in self.returns]
            returns_file = output_dir / "returns.json"
            with open(returns_file, 'w') as f:
                json.dump(returns_data, f, indent=2, default=str)
            exported_files["returns"] = returns_file

        logger.info("Exported data to JSON files in: {}", output_dir)
        return exported_files

    def export_to_excel(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all data to Excel file with multiple sheets."""
        import pandas as pd

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        excel_file = output_dir / "aus_pos_data.xlsx"
        exported_files = {"excel": excel_file}

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Export businesses
            if self.businesses:
                businesses_df = pd.DataFrame([b.dict() for b in self.businesses])
                businesses_df.to_excel(writer, sheet_name='Businesses', index=False)

            # Export customers
            if self.customers:
                customers_df = pd.DataFrame([c.dict() for c in self.customers])
                customers_df.to_excel(writer, sheet_name='Customers', index=False)

            # Export transactions
            if self.transactions:
                transactions_data = []
                for transaction in self.transactions:
                    tx_dict = transaction.dict()
                    tx_dict["items"] = [item.dict() for item in transaction.items]
                    transactions_data.append(tx_dict)

                transactions_df = pd.DataFrame(transactions_data)
                transactions_df.to_excel(writer, sheet_name='Transactions', index=False)

            # Export returns
            if self.returns:
                returns_df = pd.DataFrame([r.dict() for r in self.returns])
                returns_df.to_excel(writer, sheet_name='Returns', index=False)

            # Export line items separately
            if self.transactions:
                line_items_data = []
                for transaction in self.transactions:
                    for item in transaction.items:
                        line_items_data.append(item.dict())

                line_items_df = pd.DataFrame(line_items_data)
                line_items_df.to_excel(writer, sheet_name='Line_Items', index=False)

        logger.info("Exported data to Excel file: {}", excel_file)
        return exported_files

    def export_to_parquet(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all data to Parquet files (efficient for large datasets)."""
        import pandas as pd

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Export businesses
        if self.businesses:
            businesses_df = pd.DataFrame([b.dict() for b in self.businesses])
            businesses_file = output_dir / "businesses.parquet"
            businesses_df.to_parquet(businesses_file, index=False)
            exported_files["businesses"] = businesses_file

        # Export customers
        if self.customers:
            customers_df = pd.DataFrame([c.dict() for c in self.customers])
            customers_file = output_dir / "customers.parquet"
            customers_df.to_parquet(customers_file, index=False)
            exported_files["customers"] = customers_file

        # Export transactions
        if self.transactions:
            transactions_data = []
            for transaction in self.transactions:
                tx_dict = transaction.dict()
                tx_dict["items"] = [item.dict() for item in transaction.items]
                transactions_data.append(tx_dict)

            transactions_df = pd.DataFrame(transactions_data)
            transactions_file = output_dir / "transactions.parquet"
            transactions_df.to_parquet(transactions_file, index=False)
            exported_files["transactions"] = transactions_file

        # Export returns
        if self.returns:
            returns_df = pd.DataFrame([r.dict() for r in self.returns])
            returns_file = output_dir / "returns.parquet"
            returns_df.to_parquet(returns_file, index=False)
            exported_files["returns"] = returns_file

        logger.info("Exported data to Parquet files in: {}", output_dir)
        return exported_files

    def export_to_sqlite(self, output_dir: Optional[Path] = None) -> Path:
        """Export all data to SQLite database."""
        import sqlite3
        import pandas as pd

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        db_file = output_dir / "aus_pos_data.db"

        # Create SQLite database
        conn = sqlite3.connect(db_file)

        try:
            # Export businesses
            if self.businesses:
                businesses_df = pd.DataFrame([b.dict() for b in self.businesses])
                businesses_df.to_sql('businesses', conn, if_exists='replace', index=False)

            # Export customers
            if self.customers:
                customers_df = pd.DataFrame([c.dict() for c in self.customers])
                customers_df.to_sql('customers', conn, if_exists='replace', index=False)

            # Export transactions
            if self.transactions:
                transactions_data = []
                for transaction in self.transactions:
                    tx_dict = transaction.dict()
                    tx_dict["items"] = [item.dict() for item in transaction.items]
                    transactions_data.append(tx_dict)

                transactions_df = pd.DataFrame(transactions_data)
                transactions_df.to_sql('transactions', conn, if_exists='replace', index=False)

            # Export returns
            if self.returns:
                returns_df = pd.DataFrame([r.dict() for r in self.returns])
                returns_df.to_sql('returns', conn, if_exists='replace', index=False)

            # Export line items separately
            if self.transactions:
                line_items_data = []
                for transaction in self.transactions:
                    for item in transaction.items:
                        line_items_data.append(item.dict())

                line_items_df = pd.DataFrame(line_items_data)
                line_items_df.to_sql('transaction_items', conn, if_exists='replace', index=False)

            logger.info("Exported data to SQLite database: {}", db_file)

        finally:
            conn.close()

        return db_file

    def export_to_database(self, db_config: DatabaseConfig) -> Dict[str, str]:
        """Export all data to external database using SQLAlchemy."""
        from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
        from sqlalchemy.dialects.postgresql import JSON as PGJSON
        from sqlalchemy.dialects.mysql import JSON as MyJSON
        import pandas as pd

        logger.info(f"Exporting data to {db_config.db_type} database...")

        try:
            # Create database engine
            engine = create_engine(
                db_config.get_connection_string(),
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                echo=db_config.echo
            )

            # Test connection
            with engine.connect() as conn:
                logger.info("✅ Database connection successful")

            # Define table schemas
            metadata = MetaData()

            # Businesses table
            businesses_table = Table(
                db_config.get_table_name('businesses'),
                metadata,
                Column('store_id', String(10), primary_key=True),
                Column('business_name', String(255)),
                Column('abn', String(15)),
                Column('acn', String(15)),
                Column('trading_name', String(255)),
                Column('store_address', String(255)),
                Column('suburb', String(100)),
                Column('state', String(5)),
                Column('postcode', String(10)),
                Column('phone', String(20)),
                Column('email', String(255)),
                Column('gst_registered', Boolean),
                Column('pos_system_type', String(50)),
                Column('terminal_count', Integer),
                schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
            )

            # Customers table
            customers_table = Table(
                db_config.get_table_name('customers'),
                metadata,
                Column('customer_id', String(20), primary_key=True),
                Column('customer_type', String(20)),
                Column('first_name', String(100)),
                Column('last_name', String(100)),
                Column('email', String(255)),
                Column('phone', String(20)),
                Column('date_of_birth', DateTime),
                Column('gender', String(10)),
                Column('address_line_1', String(255)),
                Column('address_line_2', String(255)),
                Column('suburb', String(100)),
                Column('state', String(5)),
                Column('postcode', String(10)),
                Column('loyalty_member', Boolean),
                Column('loyalty_points', Integer),
                Column('registration_date', DateTime),
                schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
            )

            # Transactions table
            json_type = JSON
            if db_config.db_type == 'postgresql':
                json_type = PGJSON
            elif db_config.db_type in ('mysql', 'mariadb'):
                json_type = MyJSON

            transactions_table = Table(
                db_config.get_table_name('transactions'),
                metadata,
                Column('transaction_id', String(30), primary_key=True),
                Column('store_id', String(10)),
                Column('workstation_id', String(10)),
                Column('employee_id', String(10)),
                Column('transaction_type', String(20)),
                Column('business_day_date', DateTime),
                Column('transaction_datetime', DateTime),
                Column('sequence_number', Integer),
                Column('receipt_number', String(20)),
                Column('customer_id', String(20)),
                Column('subtotal_ex_gst', Float),
                Column('gst_amount', Float),
                Column('total_inc_gst', Float),
                Column('payment_method', String(30)),
                Column('tender_amount', Float),
                Column('change_amount', Float),
                Column('currency_code', String(5)),
                Column('operator_id', String(10)),
                Column('shift_id', String(10)),
                Column('business_abn', String(15)),
                Column('items', json_type),
                schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
            )

            # Transaction items table
            transaction_items_table = Table(
                db_config.get_table_name('transaction_items'),
                metadata,
                Column('transaction_id', String(30)),
                Column('line_number', Integer),
                Column('item_type', String(20)),
                Column('product_id', String(20)),
                Column('sku', String(50)),
                Column('barcode', String(50)),
                Column('product_name', String(255)),
                Column('category', String(50)),
                Column('brand', String(100)),
                Column('quantity', Integer),
                Column('unit_price_ex_gst', Float),
                Column('unit_price_inc_gst', Float),
                Column('line_subtotal_ex_gst', Float),
                Column('line_gst_amount', Float),
                Column('line_total_inc_gst', Float),
                Column('gst_code', String(20)),
                Column('discount_amount', Float),
                Column('discount_type', String(20)),
                Column('promotion_id', String(20)),
                schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
            )

            # Returns table
            returns_table = Table(
                db_config.get_table_name('returns'),
                metadata,
                Column('return_id', String(30), primary_key=True),
                Column('original_transaction_id', String(30)),
                Column('original_receipt_number', String(20)),
                Column('return_date', DateTime),
                Column('return_time', DateTime),
                Column('return_reason_code', String(20)),
                Column('return_reason_description', String(255)),
                Column('returned_by_customer_id', String(20)),
                Column('processed_by_employee_id', String(10)),
                Column('refund_method', String(30)),
                Column('refund_amount', Float),
                Column('store_credit_issued', Float),
                Column('restocking_fee', Float),
                Column('condition_code', String(20)),
                Column('original_purchase_date', DateTime),
                schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
            )

            # Create tables
            metadata.create_all(engine)
            logger.info("✅ Database tables created successfully")

            # Export data using pandas
            exported_tables = {}

            # Export businesses
            if self.businesses:
                businesses_df = pd.DataFrame([b.dict() for b in self.businesses])
                businesses_df.to_sql(
                    businesses_table.name,
                    engine,
                    if_exists='replace',
                    index=False,
                    schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
                )
                exported_tables['businesses'] = businesses_table.name
                logger.info(f"✅ Exported {len(businesses_df)} businesses")

            # Export customers
            if self.customers:
                customers_df = pd.DataFrame([c.dict() for c in self.customers])
                customers_df.to_sql(
                    customers_table.name,
                    engine,
                    if_exists='replace',
                    index=False,
                    schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
                )
                exported_tables['customers'] = customers_table.name
                logger.info(f"✅ Exported {len(customers_df)} customers")

            # Export transactions
            if self.transactions:
                transactions_data = []
                for transaction in self.transactions:
                    tx_dict = transaction.dict()
                    tx_dict["items"] = [item.dict() for item in transaction.items]
                    transactions_data.append(tx_dict)

                transactions_df = pd.DataFrame(transactions_data)
                transactions_df.to_sql(
                    transactions_table.name,
                    engine,
                    if_exists='replace',
                    index=False,
                    schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
                )
                exported_tables['transactions'] = transactions_table.name
                logger.info(f"✅ Exported {len(transactions_df)} transactions")

            # Export transaction items
            if self.transactions:
                line_items_data = []
                for transaction in self.transactions:
                    for item in transaction.items:
                        line_items_data.append(item.dict())

                line_items_df = pd.DataFrame(line_items_data)
                line_items_df.to_sql(
                    transaction_items_table.name,
                    engine,
                    if_exists='replace',
                    index=False,
                    schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
                )
                exported_tables['transaction_items'] = transaction_items_table.name
                logger.info(f"✅ Exported {len(line_items_df)} transaction items")

            # Export returns
            if self.returns:
                returns_df = pd.DataFrame([r.dict() for r in self.returns])
                returns_df.to_sql(
                    returns_table.name,
                    engine,
                    if_exists='replace',
                    index=False,
                    schema=db_config.db_schema if db_config.db_type == 'postgresql' else None
                )
                exported_tables['returns'] = returns_table.name
                logger.info(f"✅ Exported {len(returns_df)} returns")

            # Close engine
            engine.dispose()

            logger.info("✅ Database export completed successfully")
            return exported_tables

        except Exception as e:
            logger.error(f"❌ Database export failed: {e}")
            raise

    def export_to_postgresql(self, db_config: DatabaseConfig) -> Dict[str, str]:
        """Export data to PostgreSQL database."""
        if db_config.db_type != 'postgresql':
            raise ValueError("Database config must be for PostgreSQL")
        return self.export_to_database(db_config)

    def export_to_mysql(self, db_config: DatabaseConfig) -> Dict[str, str]:
        """Export data to MySQL/MariaDB database."""
        if db_config.db_type not in ('mysql', 'mariadb'):
            raise ValueError("Database config must be for MySQL or MariaDB")
        return self.export_to_database(db_config)
