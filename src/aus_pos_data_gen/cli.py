"""
Command-line interface for the Australian POS data generator.

Provides easy-to-use CLI commands for generating synthetic Australian
retail transaction data with proper GST compliance and business rules.
"""

import json
import sys
import signal
import atexit
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import typer
from loguru import logger
from rich.console import Console

# Force UTF-8 encoding for Windows
if os.name == 'nt':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import codecs
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, OSError):
            pass
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich.live import Live
from rich.status import Status
from rich.spinner import Spinner

from .config import POSGeneratorConfig, DatabaseConfig
from .generator import POSDataGenerator

# Initialize Typer app
app = typer.Typer(
    name="aus-pos-gen",
    help="Generate synthetic Australian POS transaction data",
    add_completion=False,
)

console = Console(force_terminal=True, legacy_windows=False)

# Global cleanup registry for graceful shutdown
_cleanup_handlers = []
_active_db_manager = None
_cleanup_registered = False

def register_cleanup_handler(handler):
    """Register a cleanup handler to be called on exit."""
    global _cleanup_handlers
    _cleanup_handlers.append(handler)

def cleanup_on_exit():
    """Execute all registered cleanup handlers."""
    global _cleanup_handlers, _active_db_manager
    
    if _active_db_manager:
        try:
            console.print("\n[yellow]🔄 Gracefully closing database connections...[/yellow]")
            if _active_db_manager.batch_buffer.size() > 0:
                console.print(f"[yellow]💾 Flushing {_active_db_manager.batch_buffer.size()} remaining records...[/yellow]")
                _active_db_manager.flush_batch()
            _active_db_manager.close()
            console.print("[green]✅ Database connections closed successfully[/green]")
        except Exception as e:
            console.print(f"[red]⚠️ Error during database cleanup: {e}[/red]")
    
    for handler in _cleanup_handlers:
        try:
            handler()
        except Exception as e:
            console.print(f"[red]⚠️ Error in cleanup handler: {e}[/red]")

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    global _cleanup_registered
    if _cleanup_registered:
        return
    
    def signal_handler(signum, frame):
        console.print(f"\n[red]🛑 Ctrl+C pressed - Exiting program completely...[/red]")
        cleanup_on_exit()
        console.print("[green]👋 Goodbye![/green]")
        # Force exit to bypass any exception handling
        os._exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C - Always exit completely
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler) # Termination signal
    
    # Register atexit handler
    atexit.register(cleanup_on_exit)
    _cleanup_registered = True


def safe_convert_param(param, default_value=None):
    """Convert OptionInfo objects to their actual values."""
    if hasattr(param, 'value'):
        return param.value
    return param if param is not None else default_value


def interactive_wizard():
    """Main interactive wizard with full navigation control."""
    try:
        import questionary
        from questionary import Separator
    except ImportError as e:
        console.print(f"[red]❌ Interactive mode requires questionary package: {e}[/red]")
        console.print("[yellow]💡 Install with: pip install questionary[/yellow]")
        raise typer.Exit(1)

    setup_signal_handlers()  # Enable Ctrl+C handling
    
    # State management for full navigation
    navigation_stack = []
    current_step = "main_menu"
    user_choices = {}
    
    console.clear()
    
    while True:
        try:
            if current_step == "main_menu":
                # Enhanced welcome with Rich panel
                welcome_panel = Panel.fit(
                    Align.center(
                        Text.from_markup(
                            "🇦🇺 [bold cyan]Australian POS Data Generator[/bold cyan]\n"
                            "[bold yellow]Interactive Configuration Wizard[/bold yellow]\n\n"
                            "🎯 [green]Full Navigation Control:[/green] Go back to any step\n"
                            "📊 [blue]Smart Defaults:[/blue] Sensible starting values\n"
                            "✅ [magenta]Input Validation:[/magenta] Real-time error checking\n"
                            "🚀 [red]Quick Start:[/red] Ready in minutes\n\n"
                            "[dim]Use ↑↓ arrows to navigate, Enter to select, Ctrl+C to exit completely[/dim]"
                        )
                    ),
                    title="[bold magenta]🎮 Interactive Mode[/bold magenta]",
                    border_style="blue",
                    padding=(1, 2)
                )

                console.print(welcome_panel)
                console.print()

                choices = [
                    {"name": "🎲 Generate Batch Data", "value": "generate"},
                    {"name": "🌊 Stream Live Data", "value": "stream"},
                    {"name": "ℹ️  Show Configuration Info", "value": "info"},
                    Separator(),
                    {"name": "🚪 Exit Program", "value": "exit"}
                ]

                operation_choice = questionary.select(
                    "What would you like to do?",
                    choices=choices
                ).ask()
                
                # Ctrl+C returns None
                if operation_choice is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    return

                if operation_choice == "exit":
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    return
                elif operation_choice == "info":
                    show_config_info()
                    input("\nPress Enter to return to main menu...")
                    console.clear()
                    continue
                else:
                    user_choices["operation"] = operation_choice
                    navigation_stack.append("main_menu")
                    if operation_choice == "generate":
                        current_step = "generate_params"
                    else:
                        current_step = "stream_params"
                    console.clear()

            elif current_step == "generate_params":
                from .interactive_handlers import handle_generate_params
                current_step = handle_generate_params(user_choices, navigation_stack)
                if current_step == "back":
                    current_step = navigation_stack.pop()
                    console.clear()

            elif current_step == "stream_params":
                from .interactive_handlers import handle_stream_params
                current_step = handle_stream_params(user_choices, navigation_stack)
                if current_step == "back":
                    current_step = navigation_stack.pop()
                    console.clear()

            elif current_step == "execute":
                from .interactive_handlers import execute_user_choices
                execute_user_choices(user_choices)
                input("\nPress Enter to return to main menu...")
                user_choices.clear()
                navigation_stack.clear()
                current_step = "main_menu"
                console.clear()

        except KeyboardInterrupt:
            # This should be handled by signal handler, but just in case
            console.print("\n[red]🛑 Ctrl+C pressed - Exiting...[/red]")
            return
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            console.print("[yellow]Returning to main menu...[/yellow]")
            current_step = "main_menu"
            console.clear()

def show_config_info():
    """Show current configuration info."""
    config = POSGeneratorConfig()
    
    info_panel = Panel.fit(
        Align.left(
            Text.from_markup(
                f"[bold cyan]📋 Current Configuration:[/bold cyan]\n\n"
                f"[green]🌱 Seed:[/green] {config.seed}\n"
                f"[green]📅 Start Date:[/green] {config.start_date.date()}\n"
                f"[green]📅 End Date:[/green] {config.end_date.date()}\n"
                f"[green]📂 Output Directory:[/green] {config.output_dir}\n"
                f"[green]💳 Payment Methods:[/green] {len(config.payment_methods)} supported\n"
                f"[green]🏛️ Australian States:[/green] {len(config.states_distribution)} states/territories"
            )
        ),
        title="[bold blue]⚙️ Configuration Details[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(info_panel)


@app.command()
def interactive():
    """Interactive mode with step-by-step configuration wizard."""
    interactive_wizard()


@app.command()
def stream(
    businesses: int = typer.Option(3, "--businesses", "-b", help="Number of businesses to stream from"),
    customers: int = typer.Option(500, "--customers", "-c", help="Number of customers in the system"),
    rate: float = typer.Option(1.0, "--rate", "-r", help="Transactions per second"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Duration in seconds (unlimited if not set)"),
    format: str = typer.Option("console", "--format", "-f", help="Streaming format: console, json, csv, database"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (for json/csv formats)"),

    # Database options (for database format)
    db_type: str = typer.Option("sqlite", "--db-type", help="Database type: sqlite, postgresql, mysql, mariadb"),
    db_host: Optional[str] = typer.Option(None, "--db-host", help="Database host"),
    db_port: Optional[int] = typer.Option(None, "--db-port", help="Database port"),
    db_name: Optional[str] = typer.Option(None, "--db-name", help="Database name"),
    db_username: Optional[str] = typer.Option(None, "--db-username", help="Database username"),
    db_password: Optional[str] = typer.Option(None, "--db-password", help="Database password"),
    db_table_prefix: str = typer.Option("", "--db-table-prefix", help="Database table prefix"),
    db_schema: Optional[str] = typer.Option(None, "--db-schema", help="Database schema (PostgreSQL)"),

    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for reproducibility"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Stream live Australian POS transaction data."""
    import time
    import json
    import random

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    global _active_db_manager
    
    # Convert parameters safely
    businesses = safe_convert_param(businesses, 3)
    customers = safe_convert_param(customers, 500)
    rate = safe_convert_param(rate, 1.0)
    duration = safe_convert_param(duration, None)
    format = safe_convert_param(format, "console")
    output = safe_convert_param(output, None)
    seed = safe_convert_param(seed, 42)
    verbose = safe_convert_param(verbose, False)

    # Helper function to convert Decimal objects to float for JSON serialization
    def convert_decimals_to_float(obj):
        """Convert Decimal objects to float in nested data structures."""
        from decimal import Decimal
        if isinstance(obj, dict):
            return {key: convert_decimals_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    # Create generator config
    config = POSGeneratorConfig(
        seed=seed,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )

    # Initialize generator
    generator = POSDataGenerator(config)

    # Generate initial data
    generator.generate_businesses(businesses)
    generator.generate_customers(customers)

    businesses_list = list(generator.businesses)
    customers_list = list(generator.customers)

    console.print(f"[green]✅ Initialized with {len(businesses_list)} businesses and {len(customers_list)} customers[/green]")
    console.print(f"[green]🚀 Starting live {format.upper()} transaction stream...[/green]")
    console.print(f"[red]🛑 Press Ctrl+C to exit program completely[/red]")
    console.print(f"[yellow]📊 Streaming will show progress every 10 transactions[/yellow]")
    console.print()

    # Initialize streaming components
    csv_writer = None
    parquet_buffer = None
    xlsx_buffer = None

    # Initialize database manager for streaming (optional)
    db_manager = None
    if format.lower() == "database":
        if not any([db_type, db_host, db_name]):
            console.print("[red]❌ Error: Database streaming requires database configuration[/red]")
            console.print("[yellow]💡 Tip: Use other formats like 'console', 'json', 'csv' to avoid database dependency[/yellow]")
            raise typer.Exit(1)

        with console.status("[bold green]Setting up enhanced database connection...[/bold green]") as status:
            try:
                from .database_manager import EnhancedDatabaseManager, RetryConfig

                db_config = DatabaseConfig(
                    db_type=db_type,
                    host=db_host,
                    port=db_port,
                    database=db_name,
                    username=db_username,
                    password=db_password,
                    table_prefix=db_table_prefix,
                    schema=db_schema
                )

                # Create enhanced database manager optimized for streaming
                retry_config = RetryConfig(max_attempts=3, base_delay=0.5, max_delay=5.0)
                db_manager = EnhancedDatabaseManager(
                    db_config=db_config,
                    batch_size=50,    # Smaller batch size for streaming
                    batch_timeout=10, # Shorter timeout for streaming
                    retry_config=retry_config
                )

                # Register with global cleanup system
                _active_db_manager = db_manager

                # Perform health check
                health = db_manager.health_check()
                if health['status'] != 'healthy':
                    raise Exception(f"Database health check failed: {health.get('error', 'Unknown error')}")

                console.print(f"[green]✅ Enhanced database connection successful! (Response time: {health['response_time_ms']:.2f}ms)[/green]")
                console.print(f"[green]✅ Database tables ready with batching (batch_size={50}, timeout={10}s)[/green]")

            except Exception as e:
                console.print(f"[red]❌ Database connection failed: {e}[/red]")
                console.print("[yellow]💡 You can continue without database by using formats like 'console', 'json', or 'csv'[/yellow]")
                raise typer.Exit(1)

    # Set up file streaming if requested
    elif format.lower() == "csv" and output:
        import csv
        csv_file = open(output, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'transaction_id', 'store_id', 'workstation_id', 'employee_id',
            'transaction_type', 'business_day_date', 'transaction_datetime',
            'receipt_number', 'customer_id', 'subtotal_ex_gst', 'gst_amount',
            'total_inc_gst', 'payment_method', 'tender_amount', 'change_amount',
            'currency_code', 'operator_id', 'shift_id', 'business_abn'
        ])
        console.print(f"[green]✅ CSV file opened: {output}[/green]")

    # Stream transactions
    transaction_count = 0
    start_time = time.time()
    graceful_exit = False

    try:
        while True:
            # Check duration limit
            if duration and (time.time() - start_time) >= duration:
                break

            # Generate random transaction
            business = random.choice(businesses_list)
            transaction = generator._generate_single_transaction(
                business,
                datetime.now()
            )
            transaction_count += 1

            # Output transaction based on format
            if format.lower() == "console":
                console.print(f"[green]#{transaction_count:04d}[/green] "
                            f"Store: {transaction.store_id} | "
                            f"Amount: ${transaction.total_inc_gst:.2f} | "
                            f"Items: {len(transaction.items)}")

            elif format.lower() == "json":
                transaction_json = json.dumps(convert_decimals_to_float(transaction.model_dump()), indent=2)
                if output:
                    with open(output, 'a') as f:
                        f.write(transaction_json + '\n')
                else:
                    console.print(transaction_json)

            elif format.lower() == "csv" and csv_writer:
                try:
                    transaction_data = convert_decimals_to_float(transaction.model_dump())
                    csv_writer.writerow([
                        transaction_data.get('transaction_id', ''),
                        transaction_data.get('store_id', ''),
                        transaction_data.get('workstation_id', ''),
                        transaction_data.get('employee_id', ''),
                        transaction_data.get('transaction_type', ''),
                        transaction_data.get('business_day_date', ''),
                        transaction_data.get('transaction_datetime', ''),
                        transaction_data.get('receipt_number', ''),
                        transaction_data.get('customer_id', ''),
                        transaction_data.get('subtotal_ex_gst', 0),
                        transaction_data.get('gst_amount', 0),
                        transaction_data.get('total_inc_gst', 0),
                        transaction_data.get('payment_method', ''),
                        transaction_data.get('tender_amount', 0),
                        transaction_data.get('change_amount', 0),
                        transaction_data.get('currency_code', 'AUD'),
                        transaction_data.get('operator_id', ''),
                        transaction_data.get('shift_id', ''),
                        transaction_data.get('business_abn', '')
                    ])
                    csv_file.flush()
                except Exception as e:
                    console.print(f"[red]CSV write error: {e}[/red]")

            elif format.lower() == "database":
                if db_manager:
                    try:
                        success = db_manager.insert_transaction_stream(transaction)
                        if not success:
                            console.print(f"[red]Failed to queue transaction {transaction.transaction_id} for database insert[/red]")
                    except Exception as e:
                        console.print(f"[red]Database streaming error: {e}[/red]")

            # Control rate
            time.sleep(1.0 / rate)

            # Progress update
            if transaction_count % 10 == 0:
                elapsed = time.time() - start_time
                rate_actual = transaction_count / elapsed if elapsed > 0 else 0
                console.print(f"[dim]Streamed {transaction_count} transactions "
                            f"({rate_actual:.1f} tps) - Press Ctrl+C to exit[/dim]", end='\r')

    except KeyboardInterrupt:
        # Ctrl+C should exit completely (handled by signal handler)
        console.print("\n[red]🛑 Ctrl+C pressed - exiting program...[/red]")
        raise

    except Exception as e:
        graceful_exit = True
        console.print(f"\n[red]💥 Stream error: {e}[/red]")
        console.print("[yellow]💡 Streaming stopped due to error - performing cleanup...[/yellow]")

    finally:
        # Clean up streaming components
        if csv_writer and 'csv_file' in locals():
            csv_file.close()
            console.print("[green]✅ CSV file closed[/green]")

        if db_manager:
            try:
                # Force flush any remaining batched data
                stats = db_manager.get_connection_stats()
                if db_manager.batch_buffer.size() > 0:
                    console.print(f"[yellow]Flushing {db_manager.batch_buffer.size()} remaining transactions to database...[/yellow]")
                    db_manager.flush_batch()
                
                # Get final statistics
                final_stats = db_manager.get_connection_stats()
                console.print(f"[green]✅ Database streaming completed: {final_stats['successful_operations']} successful operations, {final_stats['failed_operations']} failed operations[/green]")
                
                # Close database manager
                db_manager.close()
                console.print("[green]✅ Enhanced database connection closed[/green]")
            except Exception as e:
                console.print(f"[red]Error closing database manager: {e}[/red]")

        # Calculate final statistics
        elapsed = time.time() - start_time
        final_rate = transaction_count / elapsed if elapsed > 0 else 0

        console.print(f"\n[cyan]📊 Final Statistics:[/cyan]")
        console.print(f"  • Transactions Generated: {transaction_count:,}")
        console.print(f"  • Duration: {elapsed:.1f} seconds")
        console.print(f"  • Average Rate: {final_rate:.2f} TPS")
        console.print(f"  • Format: {format.upper()}")

        if graceful_exit:
            console.print("[yellow]⚠️  Stream ended due to error[/yellow]")
        elif duration:
            console.print("[green]✅ Stream completed successfully (duration limit reached)![/green]")
        else:
            console.print("[green]✅ Stream completed successfully![/green]")


@app.command()
def generate(
    businesses: int = typer.Option(5, "--businesses", "-b", help="Number of businesses to generate"),
    customers: int = typer.Option(1000, "--customers", "-c", help="Number of customers to generate"),
    days: int = typer.Option(365, "--days", "-d", help="Number of days of transaction data"),
    output_dir: Path = typer.Option("data/processed", "--output", "-o", help="Output directory"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for reproducibility"),
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json, xlsx, parquet, sqlite"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Show detailed debug information during generation"),

    # Database options
    db_type: str = typer.Option("sqlite", "--db-type", help="Database type: sqlite, postgresql, mysql, mariadb"),
    db_host: Optional[str] = typer.Option(None, "--db-host", help="Database host (for external databases)"),
    db_port: Optional[int] = typer.Option(None, "--db-port", help="Database port"),
    db_name: Optional[str] = typer.Option(None, "--db-name", help="Database name"),
    db_username: Optional[str] = typer.Option(None, "--db-username", help="Database username"),
    db_password: Optional[str] = typer.Option(None, "--db-password", help="Database password"),
    db_table_prefix: str = typer.Option("", "--db-table-prefix", help="Database table prefix"),
    db_schema: Optional[str] = typer.Option(None, "--db-schema", help="Database schema (PostgreSQL)")
):
    """🎯 Generate Australian POS transaction dataset with beautiful progress visualization."""
    
    # Configure logging based on debug parameter
    logger.remove()  # Remove all default handlers
    if debug:
        # Enable detailed logging for debug mode
        logger.add(sys.stderr, level="DEBUG")
    # Note: If debug=False, no handler is added, so no logging output
    
    # Convert parameters safely to handle OptionInfo objects
    businesses = safe_convert_param(businesses, 5)
    customers = safe_convert_param(customers, 1000)
    days = safe_convert_param(days, 365)
    output_dir = safe_convert_param(output_dir, Path("data/processed"))
    seed = safe_convert_param(seed, 42)
    format = safe_convert_param(format, "csv")
    verbose = safe_convert_param(verbose, False)
    debug = safe_convert_param(debug, False)
    db_type = safe_convert_param(db_type, "sqlite")
    db_host = safe_convert_param(db_host, None)
    db_port = safe_convert_param(db_port, None)
    db_name = safe_convert_param(db_name, None)
    db_username = safe_convert_param(db_username, None)
    db_password = safe_convert_param(db_password, None)
    db_table_prefix = safe_convert_param(db_table_prefix, "")
    db_schema = safe_convert_param(db_schema, None)
    
    # Enhanced welcome message with Rich
    welcome_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                "🇦🇺 [bold cyan]Australian POS Data Generator[/bold cyan]\n\n"
                f"📊 [green]Businesses:[/green] {businesses}  "
                f"👥 [green]Customers:[/green] {customers}  "
                f"📅 [green]Days:[/green] {days}\n"
                f"🎯 [blue]Format:[/blue] {format.upper()}  "
                f"🌱 [yellow]Seed:[/yellow] {seed}"
            )
        ),
        title="[bold magenta]🚀 Data Generation Started[/bold magenta]",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(welcome_panel)
    console.print()

    # Initialize generator with simple status indicator
    try:
        with console.status("[bold green]Initializing data generator...[/bold green]") as status:
            # Create config with the specified parameters
            config = POSGeneratorConfig(
                seed=seed,
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now(),
                output_dir=output_dir
            )

            # Initialize generator
            generator = POSDataGenerator(config)

        # Generate all data with beautiful progress indicators
        data = generator.generate_all_data(
            business_count=businesses,
            customer_count=customers,
            show_progress=not debug,  # Hide progress in debug mode to avoid noise
            verbose=verbose,
            debug=debug
        )

        console.print()
        console.print(f"[green]✅ Generated {len(data['businesses'])} businesses, "
                     f"{len(data['customers'])} customers, "
                     f"{len(data['transactions'])} transactions, and "
                     f"{len(data['returns'])} returns[/green]")

        # Export data based on format
        if format == "csv":
            exported_files = generator.export_to_csv(verbose=verbose)
            console.print(f"[green]📄 CSV files exported to: {', '.join(exported_files)}[/green]")

        elif format == "json":
            exported_files = generator.export_to_json(verbose=verbose)
            console.print(f"[green]📄 JSON files exported to: {', '.join(exported_files)}[/green]")

        elif format == "xlsx":
            exported_file = generator.export_to_excel(verbose=verbose)
            console.print(f"[green]📊 Excel workbook exported to: {exported_file}[/green]")

        elif format == "parquet":
            exported_files = generator.export_to_parquet(verbose=verbose)
            console.print(f"[green]📦 Parquet files exported to: {', '.join(exported_files)}[/green]")

        elif format == "sqlite":
            exported_file = generator.export_to_sqlite(verbose=verbose)
            console.print(f"[green]🗄️ SQLite database exported to: {exported_file}[/green]")

        else:
            # Try database export
            if any([db_host, db_name]):
                try:
                    db_config = DatabaseConfig(
                        db_type=db_type,
                        host=db_host,
                        port=db_port,
                        database=db_name,
                        username=db_username,
                        password=db_password,
                        table_prefix=db_table_prefix,
                        schema=db_schema
                    )
                    
                    exported_tables = generator.export_to_database(db_config)
                    console.print(f"[green]🌐 Data exported to {db_type} database: {', '.join(exported_tables.keys())}[/green]")
                    
                except Exception as e:
                    console.print(f"[red]❌ Database export failed: {e}[/red]")
                    console.print("[yellow]💡 Falling back to CSV export...[/yellow]")
                    exported_files = generator.export_to_csv(verbose=verbose)
                    console.print(f"[green]📄 CSV files exported to: {', '.join(exported_files)}[/green]")
            else:
                console.print(f"[yellow]⚠️ Unknown format '{format}', defaulting to CSV[/yellow]")
                exported_files = generator.export_to_csv(verbose=verbose)
                console.print(f"[green]📄 CSV files exported to: {', '.join(exported_files)}[/green]")

        console.print()
        console.print("[green]🎉 Data generation completed successfully![/green]")

    except Exception as e:
        console.print(f"\n[red]❌ Generation failed: {e}[/red]")
        if debug:
            import traceback
            console.print(f"[red]Debug traceback:\n{traceback.format_exc()}[/red]")
        raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()