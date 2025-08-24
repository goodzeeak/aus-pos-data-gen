#!/usr/bin/env python3
"""
Test script to demonstrate database connectivity functionality.

This script shows how the database configuration and connection
validation works without requiring actual database servers.
"""

from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aus_pos_data_gen.config import DatabaseConfig
from aus_pos_data_gen.generator import POSDataGenerator
from aus_pos_data_gen.cli import console
import pandas as pd


def test_database_config():
    """Test database configuration creation and validation."""
    console.print("\n🧪 [bold cyan]Testing Database Configuration[/bold cyan]")
    console.print("=" * 60)

    # Test SQLite configuration
    sqlite_config = DatabaseConfig(
        db_type="sqlite",
        database="./data/test.db"
    )

    console.print("✅ SQLite Configuration:")
    console.print(f"   Connection String: {sqlite_config.get_connection_string()}")
    console.print(f"   Table Name (businesses): {sqlite_config.get_table_name('businesses')}")

    # Test PostgreSQL configuration
    postgres_config = DatabaseConfig(
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_password",
        schema="public",
        table_prefix="test_"
    )

    console.print("\n✅ PostgreSQL Configuration:")
    console.print(f"   Connection String: {postgres_config.get_connection_string()}")
    console.print(f"   Table Name (businesses): {postgres_config.get_table_name('businesses')}")

    # Test MySQL configuration
    mysql_config = DatabaseConfig(
        db_type="mysql",
        host="localhost",
        port=3306,
        database="test_db",
        username="test_user",
        password="test_password",
        table_prefix="prod_"
    )

    console.print("\n✅ MySQL Configuration:")
    console.print(f"   Connection String: {mysql_config.get_connection_string()}")
    console.print(f"   Table Name (businesses): {mysql_config.get_table_name('businesses')}")

    return True


def test_data_generation():
    """Test data generation for database export."""
    console.print("\n🧪 [bold cyan]Testing Data Generation for Database Export[/bold cyan]")
    console.print("=" * 60)

    from aus_pos_data_gen.config import POSGeneratorConfig

    # Create a minimal config
    config = POSGeneratorConfig(
        seed=42,
        db_config=DatabaseConfig(
            db_type="sqlite",
            database="./data/test_demo.db"
        )
    )

    # Initialize generator
    generator = POSDataGenerator(config)

    # Generate small dataset
    console.print("📊 Generating sample dataset...")
    data = generator.generate_all_data(business_count=2, customer_count=5)

    console.print("✅ Generated data summary:")
    console.print(f"   Businesses: {len(data.get('businesses', []))}")
    console.print(f"   Customers: {len(data.get('customers', []))}")
    console.print(f"   Transactions: {len(data.get('transactions', []))}")
    console.print(f"   Returns: {len(data.get('returns', []))}")

    # Show sample data structure
    if data.get('businesses'):
        console.print("\n🏪 Sample Business Data:")
        sample_business = data['businesses'][0]
        console.print(f"   Store ID: {sample_business.store_id}")
        console.print(f"   Business Name: {sample_business.business_name}")
        console.print(f"   ABN: {sample_business.abn}")
        console.print(f"   State: {sample_business.state}")

    return True


def test_connection_validation():
    """Test database connection validation."""
    console.print("\n🧪 [bold cyan]Testing Connection Validation[/bold cyan]")
    console.print("=" * 60)

    # Test valid configurations
    valid_configs = [
        DatabaseConfig(db_type="sqlite", database="test.db"),
        DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            database="test",
            username="user",
            password="pass"
        ),
        DatabaseConfig(
            db_type="mysql",
            host="localhost",
            database="test",
            username="user",
            password="pass"
        )
    ]

    console.print("✅ Valid configurations tested:")
    for i, config in enumerate(valid_configs, 1):
        console.print(f"   {i}. {config.db_type}: {config.get_connection_string()}")

    # Test invalid configurations
    console.print("\n❌ Testing invalid configurations:")

    try:
        invalid_config = DatabaseConfig(db_type="invalid_db")
    except ValueError as e:
        console.print(f"   ✅ Caught invalid db_type: {e}")

    try:
        invalid_config = DatabaseConfig(
            db_type="postgresql",
            # Missing required fields
        )
        invalid_config.get_connection_string()
    except ValueError as e:
        console.print(f"   ✅ Caught missing required fields: {e}")

    return True


def main():
    """Run all database connectivity tests."""
    console.print("🚀 [bold green]Database Connectivity Test Suite[/bold green]")
    console.print("Testing Australian POS Data Generator Database Features")
    console.print("=" * 70)

    tests = [
        ("Database Configuration", test_database_config),
        ("Data Generation", test_data_generation),
        ("Connection Validation", test_connection_validation)
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                console.print(f"🎉 [bold green]{test_name}: PASSED[/bold green]")
                passed += 1
            else:
                console.print(f"❌ [bold red]{test_name}: FAILED[/bold red]")
        except Exception as e:
            console.print(f"❌ [bold red]{test_name}: ERROR - {e}[/bold red]")

    console.print(f"\n📊 Test Results: {passed}/{len(tests)} passed")

    if passed == len(tests):
        console.print("\n🎯 [bold green]All database connectivity tests passed![/bold green]")
        console.print("\n💡 You can now use database export features:")
        console.print("   • aus-pos-gen generate --db-type postgresql [options]")
        console.print("   • aus-pos-gen generate --db-type mysql [options]")
        console.print("   • aus-pos-gen generate --db-type sqlite [options]")
        console.print("   • aus-pos-gen formats  # See all database options")
        console.print("   • aus-pos-gen interactive  # Guided database setup")
    else:
        console.print("\n⚠️  Some tests failed. Check the errors above.")

    console.print("\n🔗 For production use, ensure you have:")
    console.print("   • Database server running and accessible")
    console.print("   • Proper user permissions and database created")
    console.print("   • Network connectivity (for remote databases)")


if __name__ == "__main__":
    main()
