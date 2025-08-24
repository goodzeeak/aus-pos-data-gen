#!/usr/bin/env python3
"""
Sample script to demonstrate Australian POS data generation.

This script shows how to use the POSDataGenerator programmatically
to generate synthetic Australian retail transaction data.
"""

from pathlib import Path
from datetime import datetime, timedelta
from aus_pos_data_gen.config import POSGeneratorConfig
from aus_pos_data_gen.generator import POSDataGenerator
from loguru import logger


def main():
    """Generate sample Australian POS data."""

    # Configure logging
    logger.add("generation.log", rotation="10 MB", level="INFO")

    # Create custom configuration
    config = POSGeneratorConfig(
        seed=42,
        start_date=datetime.now() - timedelta(days=30),  # Last 30 days
        end_date=datetime.now(),
        output_dir=Path("sample_data"),
        business_name="Sample Australian Retail Pty Ltd"
    )

    # Initialize generator
    generator = POSDataGenerator(config)

    # Generate data
    logger.info("Starting data generation...")

    result = generator.generate_all_data(
        business_count=3,
        customer_count=500
    )

    # Display summary
    print("\n" + "="*50)
    print("AUSTRALIAN POS DATA GENERATION COMPLETE")
    print("="*50)
    print(f"Businesses Generated: {result['summary']['total_businesses']}")
    print(f"Customers Generated: {result['summary']['total_customers']}")
    print(f"Transactions Generated: {result['summary']['total_transactions']}")
    print(f"Returns Generated: {result['summary']['total_returns']}")
    print(f"Date Range: {config.start_date.date()} to {config.end_date.date()}")
    print(f"Output Directory: {config.output_dir}")

    # Export data
    logger.info("Exporting data to CSV files...")
    exported_files = generator.export_to_csv()

    print("\nGenerated Files:")
    for data_type, file_path in exported_files.items():
        print(f"  • {data_type.title()}: {file_path}")

    # Export line items separately
    line_items_file = generator.export_line_items()
    print(f"  • Line Items: {line_items_file}")

    print("\n" + "="*50)
    print("DATA GENERATION SUCCESSFUL!")
    print("="*50)
    print("Files are ready for analysis in: sample_data/")
    print("\nExample usage:")
    print("  python -c \"import pandas as pd; df = pd.read_csv('sample_data/transactions.csv'); print(df.head())\")")


if __name__ == "__main__":
    main()
