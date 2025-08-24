"""
Command-line interface for the Australian POS data generator.

Provides easy-to-use CLI commands for generating synthetic Australian
retail transaction data with proper GST compliance and business rules.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import typer
from loguru import logger
from rich.console import Console
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

# Initialize CLI app
app = typer.Typer(
    name="aus-pos-gen",
    help="Generate synthetic Australian POS transaction data",
    add_completion=False,
)

console = Console()


@app.command()
def stream(
    businesses: int = typer.Option(3, "--businesses", "-b", help="Number of businesses to stream from"),
    customers: int = typer.Option(500, "--customers", "-c", help="Number of customers in the system"),
    rate: float = typer.Option(1.0, "--rate", "-r", help="Transactions per second"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Stream duration in seconds (None for infinite)"),
    format: str = typer.Option("console", "--format", "-f", help="Stream format: console, json, websocket"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file for file streaming"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for reproducibility"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Stream live Australian POS transaction data."""
    import time
    import json
    import random
    from datetime import datetime, timedelta

    # Logging is handled by the generator module

    console.print("[bold blue]Australian POS Data Streamer[/bold blue]")
    console.print(f"Streaming {rate} transactions/second from {businesses} businesses")
    console.print(f"Format: {format.upper()}")
    if duration:
        console.print(f"Duration: {duration} seconds")
    else:
        console.print("[yellow]Duration: Infinite (Ctrl+C to stop)[/yellow]")
    console.print()

    # Create configuration
    config = POSGeneratorConfig(
        seed=seed,
        start_date=datetime.now() - timedelta(days=30),  # Look back 30 days for realistic data
        end_date=datetime.now(),
        output_dir=Path("stream_output"),
    )

    # Initialize generator
    generator = POSDataGenerator(config)

    # Generate initial data
    with console.status("[bold green]Initializing stream data...") as status:
        result = generator.generate_all_data(businesses, customers)

    businesses_list = list(generator.businesses)
    customers_list = list(generator.customers)

    console.print(f"[green]✓ Initialized with {len(businesses_list)} businesses and {len(customers_list)} customers[/green]")
    console.print("[green]✓ Starting live transaction stream...[/green]")
    console.print()

    # Stream transactions
    transaction_count = 0
    start_time = time.time()

    try:
        while True:
            # Check duration limit
            if duration and (time.time() - start_time) >= duration:
                break

            # Generate transaction
            transaction = generator._generate_single_transaction(
                random.choice(businesses_list),
                datetime.now()
            )

            transaction_count += 1

            # Format and output transaction
            if format.lower() == "console":
                console.print(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] "
                            f"[cyan]{transaction.business_abn}[/cyan] → "
                            f"[green]${transaction.total_inc_gst}[/green] "
                            f"({transaction.payment_method})")

            elif format.lower() == "json":
                transaction_data = transaction.dict()
                transaction_data["items"] = [item.dict() for item in transaction.items]

                if output:
                    with open(output, 'a') as f:
                        f.write(json.dumps(transaction_data, default=str) + '\n')
                else:
                    console.print(json.dumps(transaction_data, indent=2, default=str))

            elif format.lower() == "websocket":
                console.print("[red]WebSocket streaming not yet implemented[/red]")
                break

            else:
                console.print(f"[red]Unknown format: {format}[/red]")
                break

            # Control rate
            time.sleep(1.0 / rate)

            # Progress update
            if transaction_count % 10 == 0:
                elapsed = time.time() - start_time
                rate_actual = transaction_count / elapsed if elapsed > 0 else 0
                console.print(f"[dim]Streamed {transaction_count} transactions "
                            f"({rate_actual:.1f} tps) - Press Ctrl+C to stop[/dim]", end='\r')

    except KeyboardInterrupt:
        console.print("\n[yellow]Stream interrupted by user[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Stream error: {e}[/red]")

    finally:
        elapsed = time.time() - start_time
        final_rate = transaction_count / elapsed if elapsed > 0 else 0

        console.print("\n[bold green]Stream Summary:[/bold green]")
        console.print(f"  Total Transactions: {transaction_count}")
        console.print(f"  Duration: {elapsed:.1f} seconds")
        console.print(f"  Average Rate: {final_rate:.1f} transactions/second")
        console.print(f"  Target Rate: {rate} transactions/second")
        console.print("\n[green]Stream completed successfully![/green]")


@app.command()
def interactive():
    """Interactive mode with step-by-step configuration wizard."""
    import questionary
    from questionary import Separator
    import json
    from datetime import datetime, timedelta

    # Enhanced welcome with Rich panel
    welcome_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                "🇦🇺 [bold cyan]Australian POS Data Generator[/bold cyan]\n"
                "[bold yellow]Interactive Configuration Wizard[/bold yellow]\n\n"
                "🎯 [green]Guided Setup:[/green] Step-by-step configuration\n"
                "📊 [blue]Smart Defaults:[/blue] Sensible starting values\n"
                "✅ [magenta]Input Validation:[/magenta] Real-time error checking\n"
                "🚀 [red]Quick Start:[/red] Ready in minutes\n\n"
                "[dim]Choose from the options below to get started![/dim]"
            )
        ),
        title="[bold magenta]🎮 Interactive Mode[/bold magenta]",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(welcome_panel)
    console.print()

    # Step 1: Choose operation type
    operation_choice = questionary.select(
        "What would you like to do?",
        choices=[
            {"name": "Generate Batch Data", "value": "generate"},
            {"name": "Stream Live Data", "value": "stream"},
            {"name": "Show Configuration Info", "value": "info"},
            Separator(),
            {"name": "Exit", "value": "exit"}
        ]
    ).ask()

    operation_answers = {"operation": operation_choice}

    if operation_answers['operation'] == 'exit':
        console.print("[yellow]Goodbye! 👋[/yellow]")
        return

    if operation_answers['operation'] == 'info':
        # Show current configuration info
        config = POSGeneratorConfig()
        console.print("[bold cyan]Current Configuration:[/bold cyan]")
        console.print(f"  Seed: {config.seed}")
        console.print(f"  Start Date: {config.start_date.date()}")
        console.print(f"  End Date: {config.end_date.date()}")
        console.print(f"  Output Directory: {config.output_dir}")
        console.print(f"  Payment Methods: {list(config.payment_methods.keys())}")
        return

    # Step 2: Configure parameters based on operation
    if operation_answers['operation'] == 'generate':
        # Batch generation configuration
        def validate_positive(value):
            try:
                return int(value) > 0
            except ValueError:
                return False

        businesses = questionary.text(
            "How many businesses to generate?",
            default="5",
            validate=lambda val: validate_positive(val) or "Must be a positive number"
        ).ask()

        customers = questionary.text(
            "How many customers to generate?",
            default="1000",
            validate=lambda val: validate_positive(val) or "Must be a positive number"
        ).ask()

        days = questionary.text(
            "How many days of transaction data?",
            default="30",
            validate=lambda val: validate_positive(val) or "Must be a positive number"
        ).ask()

        seed = questionary.text(
            "Random seed (for reproducibility)?",
            default="42"
        ).ask()

        format_choice = questionary.select(
            "Export format?",
            choices=[
                {"name": "CSV (Recommended)", "value": "csv"},
                {"name": "JSON", "value": "json"},
                {"name": "Excel Workbook", "value": "xlsx"},
                {"name": "Parquet (Big Data)", "value": "parquet"},
                {"name": "SQLite Database", "value": "sqlite"}
            ]
        ).ask()

        # Database configuration if needed
        db_config = {}
        if format_choice == "sqlite":
            # For SQLite, ask if they want to use direct database connection
            use_db_connection = questionary.confirm(
                "Use direct database connection for SQLite?",
                default=False
            ).ask()

            if use_db_connection:
                db_file_path = questionary.text(
                    "SQLite database file path:",
                    default="./data/aus_pos_data.db"
                ).ask()
                db_config = {
                    "db_type": "sqlite",
                    "database": db_file_path
                }
        else:
            # For other formats, ask if they want to export to external database
            use_database = questionary.confirm(
                f"Export to external database instead of {format_choice.upper()} file?",
                default=False
            ).ask()

            if use_database:
                db_type = questionary.select(
                    "Which database type?",
                    choices=[
                        {"name": "PostgreSQL", "value": "postgresql"},
                        {"name": "MySQL", "value": "mysql"},
                        {"name": "MariaDB", "value": "mariadb"}
                    ]
                ).ask()

                db_host = questionary.text(
                    f"{db_type.title()} host:",
                    default="localhost"
                ).ask()

                db_port = questionary.text(
                    f"{db_type.title()} port:",
                    default="5432" if db_type == "postgresql" else "3306"
                ).ask()

                db_name = questionary.text(
                    "Database name:",
                    default="aus_pos_data"
                ).ask()

                db_username = questionary.text(
                    "Database username:",
                    default="postgres" if db_type == "postgresql" else "root"
                ).ask()

                db_password = questionary.password(
                    "Database password:"
                ).ask()

                table_prefix = questionary.text(
                    "Table prefix (optional):",
                    default=""
                ).ask()

                db_schema = None
                if db_type == "postgresql":
                    db_schema = questionary.text(
                        "Database schema (optional):",
                        default="public"
                    ).ask()

                db_config = {
                    "db_type": db_type,
                    "host": db_host,
                    "port": int(db_port),
                    "database": db_name,
                    "username": db_username,
                    "password": db_password,
                    "table_prefix": table_prefix,
                    "db_schema": db_schema
                }

        config_answers = {
            "businesses": businesses,
            "customers": customers,
            "days": days,
            "seed": seed,
            "format": format_choice,
            "db_config": db_config
        }

        # Run batch generation
        console.print(f"\n[green]🚀 Generating {config_answers['days']} days of data for {config_answers['businesses']} businesses...[/green]")

        # Call the generate function with the answers
        if config_answers['db_config']:
            # Use database export
            db_config_dict = config_answers['db_config']
            generate(
                businesses=int(config_answers['businesses']),
                customers=int(config_answers['customers']),
                days=int(config_answers['days']),
                seed=int(config_answers['seed']),
                format=config_answers['format'],
                db_type=db_config_dict.get('db_type', 'sqlite'),
                db_host=db_config_dict.get('host'),
                db_port=db_config_dict.get('port'),
                db_name=db_config_dict.get('database'),
                db_username=db_config_dict.get('username'),
                db_password=db_config_dict.get('password'),
                db_table_prefix=db_config_dict.get('table_prefix', ''),
                db_schema=db_config_dict.get('db_schema'),
                verbose=True
            )
        else:
            # Use file export
            generate(
                businesses=int(config_answers['businesses']),
                customers=int(config_answers['customers']),
                days=int(config_answers['days']),
                seed=int(config_answers['seed']),
                format=config_answers['format'],
                verbose=True
            )

    elif operation_answers['operation'] == 'stream':
        # Streaming configuration
        def validate_positive_float(value):
            try:
                return float(value) > 0
            except ValueError:
                return False

        businesses = questionary.text(
            "How many businesses to stream from?",
            default="3",
            validate=lambda val: validate_positive(val) or "Must be a positive number"
        ).ask()

        customers = questionary.text(
            "How many customers in the system?",
            default="500",
            validate=lambda val: validate_positive(val) or "Must be a positive number"
        ).ask()

        rate = questionary.text(
            "Transactions per second?",
            default="1.0",
            validate=lambda val: validate_positive_float(val) or "Must be a positive number"
        ).ask()

        use_duration = questionary.confirm(
            "Set a time limit?",
            default=False
        ).ask()

        duration = None
        if use_duration:
            duration = questionary.text(
                "Duration in seconds?",
                default="60",
                validate=lambda val: validate_positive(val) or "Must be a positive number"
            ).ask()

        format_choice = questionary.select(
            "Streaming format?",
            choices=[
                {"name": "Console (Real-time display)", "value": "console"},
                {"name": "JSON (To console)", "value": "json"}
            ]
        ).ask()

        save_to_file = False
        output_file = None
        if format_choice == 'json':
            save_to_file = questionary.confirm(
                "Save output to file?",
                default=False
            ).ask()
            if save_to_file:
                output_file = questionary.text(
                    "Output filename?",
                    default="stream_output.json"
                ).ask()

        stream_answers = {
            "businesses": businesses,
            "customers": customers,
            "rate": rate,
            "use_duration": use_duration,
            "duration": duration,
            "format": format_choice,
            "save_to_file": save_to_file,
            "output_file": output_file
        }

        # Set duration if not specified
        duration = int(stream_answers.get('duration', 0)) if stream_answers.get('use_duration', False) else None

        console.print(f"\n[green]🌊 Starting live data stream at {stream_answers['rate']} TPS...[/green]")
        console.print("[yellow]Press Ctrl+C to stop the stream[/yellow]\n")

        # Call the stream function with the answers
        stream(
            businesses=int(stream_answers['businesses']),
            customers=int(stream_answers['customers']),
            rate=float(stream_answers['rate']),
            duration=duration,
            format=stream_answers['format'],
            output=stream_answers.get('output_file'),
            seed=42,
            verbose=False  # Reduce noise during streaming
        )


@app.command()
def generate(
    businesses: int = typer.Option(5, "--businesses", "-b", help="Number of businesses to generate"),
    customers: int = typer.Option(1000, "--customers", "-c", help="Number of customers to generate"),
    days: int = typer.Option(365, "--days", "-d", help="Number of days of transaction data"),
    output_dir: Path = typer.Option("data/processed", "--output", "-o", help="Output directory"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for reproducibility"),
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json, xlsx, parquet, sqlite"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),

    # Database options
    db_type: str = typer.Option("sqlite", "--db-type", help="Database type: sqlite, postgresql, mysql, mariadb"),
    db_host: Optional[str] = typer.Option(None, "--db-host", help="Database host (for external databases)"),
    db_port: Optional[int] = typer.Option(None, "--db-port", help="Database port"),
    db_name: Optional[str] = typer.Option(None, "--db-name", help="Database name"),
    db_username: Optional[str] = typer.Option(None, "--db-username", help="Database username"),
    db_password: Optional[str] = typer.Option(None, "--db-password", help="Database password"),
    db_connection_string: Optional[str] = typer.Option(None, "--db-connection-string", help="Full database connection string"),
    db_table_prefix: str = typer.Option("", "--db-table-prefix", help="Prefix for database table names"),
    db_schema: Optional[str] = typer.Option(None, "--db-schema", help="Database schema (PostgreSQL)"),
):
    """🎯 Generate Australian POS transaction dataset with beautiful progress visualization."""

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

    # Initialize generator with progress tracking
    try:
        with Status("[bold green]Initializing data generator...[/bold green]", spinner="dots") as status:
            # Create config with the specified parameters
            config = POSGeneratorConfig(
                seed=seed,
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now()
            )

            generator = POSDataGenerator(config=config)

            # Generate businesses and customers with the specified counts
            businesses_data = generator.generate_businesses(count=businesses)
            customers_data = generator.generate_customers(count=customers)

            status.update("[bold green]✅ Generator initialized successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error initializing generator:[/bold red] {e}")
        raise typer.Exit(1)

    # Progress tracking for data generation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    ) as progress:

        # Main generation task
        main_task = progress.add_task("[bold cyan]Generating data...[/bold cyan]", total=100)

        try:
            # Generate businesses with progress
            business_task = progress.add_task("🏪 Generating businesses...", total=businesses)
            businesses_data = generator.generate_businesses()
            progress.update(business_task, completed=businesses)
            progress.update(main_task, advance=20)

            # Generate customers with progress
            customer_task = progress.add_task("👥 Generating customers...", total=customers)
            customers_data = generator.generate_customers()
            progress.update(customer_task, completed=customers)
            progress.update(main_task, advance=30)

            # Generate all data using the main method
            all_data_task = progress.add_task("💳 Generating complete dataset...", total=100)

            all_data = generator.generate_all_data(
                business_count=businesses,
                customer_count=customers
            )

            progress.update(all_data_task, completed=100)
            progress.update(main_task, advance=50)

            # Extract data from the result
            businesses_data = all_data.get('businesses', [])
            customers_data = all_data.get('customers', [])
            transactions_data = all_data.get('transactions', [])
            returns_data = all_data.get('returns', [])

        except Exception as e:
            console.print(f"[bold red]❌ Error during generation:[/bold red] {e}")
            raise typer.Exit(1)

    # Export data with progress
    export_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                f"[bold green]📤 Exporting to {format.upper()} format[/bold green]\n"
                f"📂 [blue]Output directory:[/blue] {output_dir}"
            )
        ),
        title="[bold magenta]💾 Data Export[/bold magenta]",
        border_style="green",
        padding=(1, 2)
    )

    console.print()
    console.print(export_panel)
    console.print()

    try:
        # Check if database export is requested
        if db_type != "sqlite" or any([db_host, db_name, db_username, db_connection_string]):
            # Database export
            with Status(f"[bold blue]Exporting to {db_type.upper()} database...[/bold blue]", spinner="bouncingBall") as status:
                # Create database configuration
                db_config = DatabaseConfig(
                    db_type=db_type,
                    host=db_host,
                    port=db_port,
                    database=db_name,
                    username=db_username,
                    password=db_password,
                    connection_string=db_connection_string,
                    table_prefix=db_table_prefix,
                    schema=db_schema
                )

                # Export to database
                exported_tables = generator.export_to_database(db_config)

                status.update("[bold green]✅ Database export completed successfully![/bold green]")

                # Show database export summary
                db_summary_table = Table(title="[bold cyan]🗄️ Database Export Summary[/bold cyan]", show_header=True, header_style="bold magenta")
                db_summary_table.add_column("Table", style="cyan", no_wrap=True)
                db_summary_table.add_column("Records", style="green", justify="right")
                db_summary_table.add_column("Status", style="white")

                # Add database connection info
                db_info_panel = Panel.fit(
                    Align.center(
                        Text.from_markup(
                            f"[bold blue]Database:[/bold blue] {db_type.upper()}\n"
                            f"[bold blue]Connection:[/bold blue] {db_config.get_connection_string().split('://')[0]}://***:***@{db_host or 'localhost'}:{db_port or 'default'}\n"
                            f"[bold blue]Schema:[/bold blue] {db_schema or 'default'}"
                        )
                    ),
                    title="[bold cyan]🔗 Database Connection[/bold cyan]",
                    border_style="blue",
                    padding=(1, 2)
                )

                console.print()
                console.print(db_info_panel)
                console.print()

        else:
            # File-based export
            with Status(f"[bold blue]Exporting to {format.upper()}...[/bold blue]", spinner="bouncingBall") as status:
                # Create output directory
                output_dir.mkdir(parents=True, exist_ok=True)

                # Export based on format
                if format.lower() == "csv":
                    generator.export_to_csv(output_dir)
                elif format.lower() == "json":
                    generator.export_to_json(output_dir)
                elif format.lower() == "xlsx":
                    generator.export_to_excel(output_dir)
                elif format.lower() == "parquet":
                    generator.export_to_parquet(output_dir)
                elif format.lower() == "sqlite":
                    generator.export_to_sqlite(output_dir)
                else:
                    raise ValueError(f"Unsupported format: {format}")

                status.update("[bold green]✅ Export completed successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error during export:[/bold red] {e}")
        raise typer.Exit(1)

    # Generate summary table
    summary_table = Table(title="[bold cyan]📊 Generation Summary[/bold cyan]", show_header=True, header_style="bold magenta")
    summary_table.add_column("Data Type", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="green", justify="right")
    summary_table.add_column("Details", style="white")

    summary_table.add_row("🏪 Businesses", str(len(businesses_data)), "Australian businesses with valid ABNs")
    summary_table.add_row("👥 Customers", str(len(customers_data)), "Customers with Australian addresses")
    summary_table.add_row("💳 Transactions", str(len(transactions_data)), "Sales transactions with GST")
    summary_table.add_row("🔄 Returns", str(len(returns_data)), "Return transactions")

    console.print(summary_table)

    # Files created table
    files_table = Table(title="[bold cyan]📁 Files Created[/bold cyan]", show_header=True, header_style="bold blue")
    files_table.add_column("File", style="cyan")
    files_table.add_column("Size", style="green", justify="right")
    files_table.add_column("Status", style="white")

    output_files = {
        f"businesses.{format}": "Business data",
        f"customers.{format}": "Customer data",
        f"transactions.{format}": "Transaction data",
        f"returns.{format}": "Return data",
        "generation_config.json": "Configuration"
    }

    for filename, description in output_files.items():
        file_path = output_dir / filename
        if file_path.exists():
            size = f"{file_path.stat().st_size / 1024:.1f} KB"
            files_table.add_row(f"📄 {filename}", size, f"✅ {description}")
        else:
            files_table.add_row(f"📄 {filename}", "-", "❌ Missing")

    console.print(files_table)

    # Success message
    success_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                "[bold green]🎉 Data generation completed successfully![/bold green]\n\n"
                f"📊 [cyan]Total records generated:[/cyan] {len(businesses_data) + len(customers_data) + len(transactions_data) + len(returns_data)}\n"
                f"📂 [blue]Output location:[/blue] {output_dir.absolute()}\n"
                f"🇦🇺 [yellow]Ready for Australian retail analytics![/yellow]"
            )
        ),
        title="[bold green]✅ Success![/bold green]",
        border_style="green",
        padding=(1, 2)
    )

    console.print()
    console.print(success_panel)

    # Create configuration
    config = POSGeneratorConfig(
        seed=seed,
        start_date=datetime.now() - timedelta(days=days),
        end_date=datetime.now(),
        output_dir=output_dir,
    )

    # Initialize generator
    generator = POSDataGenerator(config)

    # Generate data with progress display
    with console.status("[bold green]Generating data...") as status:
        result = generator.generate_all_data(businesses, customers)

    # Display summary
    table = Table(title="Generation Summary")
    table.add_column("Data Type", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Details", style="green")

    table.add_row("Businesses", str(result["summary"]["total_businesses"]), "Australian businesses with valid ABNs")
    table.add_row("Customers", str(result["summary"]["total_customers"]), "Customers with Australian addresses")
    table.add_row("Transactions", str(result["summary"]["total_transactions"]), "Sales transactions with GST")
    table.add_row("Returns", str(result["summary"]["total_returns"]), "Return transactions")

    console.print(table)

    # Export data
    export_msg = f"[bold green]Exporting data to {format.upper()}..."
    with console.status(export_msg) as status:
        if format.lower() == "csv":
            exported_files = generator.export_to_csv()
            generator.export_line_items()
        elif format.lower() == "json":
            exported_files = generator.export_to_json()
        elif format.lower() == "xlsx":
            exported_files = generator.export_to_excel()
        elif format.lower() == "parquet":
            exported_files = generator.export_to_parquet()
        elif format.lower() == "sqlite":
            exported_files = generator.export_to_sqlite()
        else:
            console.print(f"[red]Error: Unsupported format '{format}'[/red]")
            raise typer.Exit(1)

    # Display export results
    console.print(f"\n[bold green]Data exported successfully to {format.upper()}![/bold green]")
    if isinstance(exported_files, dict):
        for data_type, file_path in exported_files.items():
            console.print(f"  • {data_type.title()}: {file_path}")
    else:
        console.print(f"  • Database: {exported_files}")

    # Save configuration for reference
    config_file = output_dir / "generation_config.json"
    config_dict = {
        "businesses": businesses,
        "customers": customers,
        "days": days,
        "seed": seed,
        "format": format,
        "date_range": {
            "start": config.start_date.isoformat(),
            "end": config.end_date.isoformat(),
        },
        "generated_at": datetime.now().isoformat(),
        "summary": result["summary"],
    }

    with open(config_file, "w") as f:
        json.dump(config_dict, f, indent=2)

    console.print(f"  • Configuration: {config_file}")

    console.print("\n[bold green]Generation complete![/bold green]")


@app.command()
def validate_abn(abn: str):
    """Validate an Australian Business Number (ABN)."""
    from .validators import ABNValidator

    is_valid, message = ABNValidator.validate_abn(abn)

    if is_valid:
        console.print(f"[green]✓ Valid ABN: {ABNValidator.format_abn(abn)}[/green]")
    else:
        console.print(f"[red]✗ Invalid ABN: {message}[/red]")


@app.command()
def calculate_gst(amount: float, gst_code: str = "GST"):
    """Calculate GST components for an amount."""
    from decimal import Decimal
    from .models import GSTCode
    from .validators import GSTCalculator

    try:
        gst_enum = GSTCode(gst_code)
        amount_decimal = Decimal(str(amount))
        gst_calc = GSTCalculator.calculate_gst_components(amount_decimal, gst_enum)

        table = Table(title=f"GST Calculation for ${amount}")
        table.add_column("Component", style="cyan")
        table.add_column("Amount", style="magenta")

        table.add_row("GST-Inclusive Amount", f"${gst_calc.gst_inclusive_amount}")
        table.add_row("GST-Exclusive Amount", f"${gst_calc.gst_exclusive_amount}")
        table.add_row("GST Amount", f"${gst_calc.gst_amount}")
        table.add_row("GST Rate", f"{gst_calc.gst_rate * 100}%")

        console.print(table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def generate_abn():
    """Generate a valid Australian Business Number for testing."""
    from .validators import ABNValidator

    abn = ABNValidator.generate_valid_abn()
    formatted = ABNValidator.format_abn(abn)

    console.print(f"[green]Generated ABN: {formatted}[/green]")
    console.print(f"[dim]Raw: {abn}[/dim]")


@app.command()
def info():
    """📊 Display comprehensive information about the Australian POS data generator with beautiful formatting."""

    config = POSGeneratorConfig()

    # Main info panel
    info_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                "🇦🇺 [bold cyan]Australian POS Data Generator[/bold cyan]\n"
                "[bold yellow]Professional Synthetic Data for Australian Retail Analytics[/bold yellow]\n\n"
                "[green]Version:[/green] 0.1.0  "
                "[green]Status:[/green] ✅ Active\n"
                "[blue]Seed:[/blue] {config.seed}  "
                "[blue]Start Date:[/blue] {config.start_date.date()}\n"
                "[magenta]Payment Methods:[/magenta] {len(config.payment_methods)} supported\n"
                "[yellow]GST Rate:[/yellow] {config.gst_rate * 100}%"
            )
        ),
        title="[bold magenta]🚀 System Overview[/bold magenta]",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(info_panel)
    console.print()

    # Features table with enhanced styling
    features_table = Table(
        title="[bold cyan]✨ Core Features[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    features_table.add_column("🎯 Feature", style="cyan", no_wrap=True)
    features_table.add_column("📋 Description", style="white")
    features_table.add_column("⭐ Status", style="green", justify="center")

    features_table.add_row(
        "GST Compliance",
        "Full Australian GST calculations with ATO compliance",
        "✅"
    )
    features_table.add_row(
        "ABN Validation",
        "Valid Australian Business Numbers with check digit validation",
        "✅"
    )
    features_table.add_row(
        "Payment Methods",
        "Realistic Australian payment method distributions (EFTPOS, Cash, Credit)",
        "✅"
    )
    features_table.add_row(
        "Business Rules",
        "Australian retail business hours and seasonal patterns",
        "✅"
    )
    features_table.add_row(
        "Address Validation",
        "Proper Australian postcodes and state validation",
        "✅"
    )
    features_table.add_row(
        "Return Processing",
        "Industry-standard return rates and processing",
        "✅"
    )

    console.print(features_table)
    console.print()

    # Export formats table
    formats_table = Table(
        title="[bold cyan]📤 Export Formats[/bold cyan]",
        show_header=True,
        header_style="bold blue"
    )
    formats_table.add_column("Format", style="cyan", no_wrap=True)
    formats_table.add_column("Description", style="white")
    formats_table.add_column("Best For", style="green")

    formats = [
        ("CSV", "Comma-separated values", "Data analysis, spreadsheets"),
        ("JSON", "Structured JSON data", "API testing, web apps"),
        ("Excel", "Multi-sheet workbook", "Business reporting"),
        ("Parquet", "Columnar storage", "Big data, analytics"),
        ("SQLite", "Relational database", "Complex queries")
    ]

    for fmt, desc, use in formats:
        formats_table.add_row(fmt, desc, use)

    console.print(formats_table)
    console.print()

    # Usage examples with syntax highlighting
    usage_panel = Panel.fit(
        Align.left(
            Text.from_markup(
                "[bold green]📝 Popular Commands:[/bold green]\n\n"
                "[cyan]aus-pos-gen generate --businesses 10 --days 30[/cyan]\n"
                "[cyan]aus-pos-gen generate --format parquet --days 90[/cyan]\n"
                "[cyan]aus-pos-gen generate --format sqlite --customers 500[/cyan]\n"
                "[cyan]aus-pos-gen stream --rate 2.0 --duration 60[/cyan]\n"
                "[cyan]aus-pos-gen stream --format json --output live_stream.json[/cyan]\n\n"
                "[bold yellow]🎮 Interactive Mode:[/bold yellow]\n"
                "[cyan]aus-pos-gen interactive[/cyan]  [dim]# Step-by-step wizard[/dim]\n\n"
                "[bold blue]🔍 Information Commands:[/bold blue]\n"
                "[cyan]aus-pos-gen info[/cyan]  [dim]# This overview[/dim]\n"
                "[cyan]aus-pos-gen formats[/cyan]  [dim]# Show export formats[/dim]\n"
                "[cyan]aus-pos-gen stream-formats[/cyan]  [dim]# Show streaming options[/dim]"
            )
        ),
        title="[bold magenta]💡 Usage Examples[/bold magenta]",
        border_style="green",
        padding=(1, 2)
    )

    console.print(usage_panel)

    # Quick stats panel
    stats_panel = Panel.fit(
        Align.center(
            Text.from_markup(
                "[bold cyan]📊 Quick Stats[/bold cyan]\n\n"
                "[green]🇦🇺 Australian States:[/green] 8 supported\n"
                "[blue]💳 Payment Methods:[/blue] 9+ options\n"
                "[yellow]🏪 Business Types:[/yellow] 15+ categories\n"
                "[magenta]📦 Product Categories:[/magenta] 50+ items\n"
                "[red]🔄 Return Rate:[/red] 3-8% (realistic)\n\n"
                "[bold white]Ready to generate realistic Australian retail data![/bold white]"
            )
        ),
        title="[bold yellow]📈 System Stats[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )

    console.print()
    console.print(stats_panel)


@app.command()
def stream_formats():
    """List all available streaming formats and their descriptions."""
    from rich.table import Table

    table = Table(title="Available Streaming Formats")
    table.add_column("Format", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Use Case", style="yellow")

    table.add_row(
        "console",
        "Real-time console output with colored formatting",
        "Monitoring, development, demos"
    )
    table.add_row(
        "json",
        "JSON lines to console or file",
        "API testing, data pipelines, logging"
    )
    table.add_row(
        "websocket",
        "WebSocket streaming (planned)",
        "Real-time dashboards, web applications"
    )

    console.print(table)

    console.print("\n[bold]Usage:[/bold]")
    console.print("  aus-pos-gen stream --format <format> [other options]")
    console.print("\n[bold]Examples:[/bold]")
    console.print("  aus-pos-gen stream --format console --rate 1.0")
    console.print("  aus-pos-gen stream --format json --output stream.json")
    console.print("  aus-pos-gen stream --rate 0.5 --duration 300")  # 2 tpm for 5 minutes


@app.command()
def formats():
    """📊 List all available export formats and database options with beautiful formatting."""

    # File formats table
    file_table = Table(
        title="[bold cyan]📤 File Export Formats[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    file_table.add_column("Format", style="cyan", no_wrap=True)
    file_table.add_column("Extension", style="blue", no_wrap=True)
    file_table.add_column("Description", style="white")
    file_table.add_column("Best For", style="green")

    file_formats = [
        ("CSV", ".csv", "Comma-separated values with headers", "Excel analysis, basic data processing"),
        ("JSON", ".json", "Structured JSON with nested data", "API integration, web applications"),
        ("Excel", ".xlsx", "Multi-sheet Excel workbook", "Business reporting, presentations"),
        ("Parquet", ".parquet", "Columnar storage format", "Big data analytics, data lakes"),
        ("SQLite", ".db", "Local SQLite database file", "Complex queries, data relationships"),
    ]

    for fmt, ext, desc, use in file_formats:
        file_table.add_row(fmt, ext, desc, use)

    # Database formats table
    db_table = Table(
        title="[bold cyan]🗄️ Direct Database Export[/bold cyan]",
        show_header=True,
        header_style="bold blue",
        show_lines=True
    )
    db_table.add_column("Database", style="cyan", no_wrap=True)
    db_table.add_column("Driver", style="blue", no_wrap=True)
    db_table.add_column("Description", style="white")
    db_table.add_column("Use Case", style="green")

    db_formats = [
        ("PostgreSQL", "psycopg2", "Enterprise-grade open source database", "Production applications, analytics"),
        ("MySQL", "PyMySQL", "Popular open source database", "Web applications, reporting"),
        ("MariaDB", "PyMySQL", "MySQL-compatible database", "Cost-effective MySQL alternative"),
        ("SQLite", "sqlite3", "Local file-based database", "Development, testing, small apps"),
    ]

    for db, driver, desc, use in db_formats:
        db_table.add_row(db, driver, desc, use)

    console.print(file_table)
    console.print()
    console.print(db_table)
    console.print()

    # Usage examples panel
    usage_panel = Panel.fit(
        Align.left(
            Text.from_markup(
                "[bold green]📝 File Export Examples:[/bold green]\n\n"
                "[cyan]aus-pos-gen generate --format csv --businesses 10[/cyan]\n"
                "[cyan]aus-pos-gen generate --format parquet --days 365[/cyan]\n"
                "[cyan]aus-pos-gen generate --format sqlite --customers 5000[/cyan]\n\n"
                "[bold yellow]🗄️ Database Export Examples:[/bold yellow]\n\n"
                "[cyan]aus-pos-gen generate --db-type postgresql --db-host localhost --db-name pos_data --db-username user --db-password pass[/cyan]\n"
                "[cyan]aus-pos-gen generate --db-type mysql --db-host 192.168.1.100 --db-port 3306 --db-name retail_db --db-username admin --db-password secret[/cyan]\n"
                "[cyan]aus-pos-gen generate --db-connection-string 'postgresql://user:pass@localhost:5432/pos_db' --db-schema public[/cyan]\n\n"
                "[bold blue]📋 Table Prefix Examples:[/bold blue]\n\n"
                "[cyan]aus-pos-gen generate --db-table-prefix 'aus_' --db-type postgresql[/cyan]  [dim]# Creates: aus_businesses, aus_customers, etc.[/dim]\n"
                "[cyan]aus-pos-gen generate --db-table-prefix 'pos_' --db-type mysql[/cyan]  [dim]# Creates: pos_businesses, pos_customers, etc.[/dim]"
            )
        ),
        title="[bold magenta]💡 Usage Examples[/bold magenta]",
        border_style="green",
        padding=(1, 2)
    )

    console.print(usage_panel)


@app.command()
def export_config(output: Path = typer.Option("config.json", "--output", "-o")):
    """Export default configuration to JSON file."""
    config = POSGeneratorConfig()
    config_dict = {
        "seed": config.seed,
        "locale": config.locale,
        "date_range": {
            "start": config.start_date.isoformat(),
            "end": config.end_date.isoformat(),
        },
        "payment_methods": config.payment_methods,
        "states_distribution": config.states_distribution,
        "seasonal_multipliers": config.seasonal_multipliers,
        "daily_transactions": config.daily_transactions,
        "store_size_distribution": config.store_size_distribution,
    }

    with open(output, "w") as f:
        json.dump(config_dict, f, indent=2)

    console.print(f"[green]Configuration exported to: {output}[/green]")


def main():
    """Main entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
