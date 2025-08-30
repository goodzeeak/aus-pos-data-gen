"""
Interactive wizard handlers for the Australian POS data generator.

Provides step-by-step configuration with full navigation control.
"""

import os
import sys

# Force UTF-8 encoding for Windows
if os.name == 'nt':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Force compatibility with modern terminals on Windows
    os.environ['TERM'] = 'xterm-256color'
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, OSError):
            pass

import questionary
from questionary import Separator

# Patch questionary for Windows terminal compatibility
def patch_questionary_for_windows():
    """Patch questionary to work better with Windows terminals."""
    if os.name == 'nt':
        try:
            from prompt_toolkit.input import create_input
            from prompt_toolkit.output import create_output
            
            # Create compatible input/output for Windows
            input_obj = create_input()
            output_obj = create_output()
            
            # Monkey patch questionary's default settings
            questionary.get_default_kbi_message = lambda: "Cancelled by user"
            
        except ImportError:
            pass

patch_questionary_for_windows()
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from datetime import datetime, timedelta

console = Console(force_terminal=True, legacy_windows=False)


def handle_ctrl_c_exit(result):
    """Simple check for Ctrl+C (None result) and exit if needed."""
    if result is None:
        console.print("\n[red]🛑 Exiting program...[/red]")
        import sys
        sys.exit(0)
    return result


def validate_positive_int(value):
    """Validate positive integer input."""
    try:
        return int(value) > 0
    except ValueError:
        return False


def validate_positive_float(value):
    """Validate positive float input."""
    try:
        return float(value) > 0
    except ValueError:
        return False


def handle_generate_params(user_choices, navigation_stack):
    """Handle batch generation parameter configuration."""
    
    # Show current progress
    show_progress_indicator("Batch Generation", ["✅ Operation Selected", "📊 Configure Parameters", "🚀 Execute"])
    
    while True:
        # Show current selections if any
        if len(user_choices) > 1:
            show_current_selections(user_choices)
        
        choice = questionary.select(
            "Configure batch generation parameters:",
            choices=[
                {"name": f"🏪 Businesses: {user_choices.get('businesses', '[Not Set]')}", "value": "businesses"},
                {"name": f"👥 Customers: {user_choices.get('customers', '[Not Set]')}", "value": "customers"},
                {"name": f"📅 Days of Data: {user_choices.get('days', '[Not Set]')}", "value": "days"},
                {"name": f"🌱 Random Seed: {user_choices.get('seed', '[Not Set]')}", "value": "seed"},
                {"name": f"📋 Export Format: {user_choices.get('format', '[Not Set]')}", "value": "format"},
                Separator(),
                {"name": "🚀 Continue to Execution (if all set)", "value": "continue"},
                {"name": "← Back to Main Menu", "value": "back"}
            ]
        ).ask()
        
        # Handle Ctrl+C
        if choice is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if choice == "back":
            return "back"
        elif choice == "continue":
            # Check if all required params are set
            required_params = ['businesses', 'customers', 'days', 'seed', 'format']
            missing = [p for p in required_params if p not in user_choices]
            
            if missing:
                console.print(f"[red]❌ Please configure: {', '.join(missing)}[/red]")
                input("Press Enter to continue...")
                console.clear()
                continue
            else:
                navigation_stack.append("generate_params")
                return "execute"
        else:
            # Handle parameter configuration
            if choice == "businesses":
                result = questionary.text(
                    "How many businesses to generate?",
                    default=str(user_choices.get('businesses', 5)),
                    validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['businesses'] = int(result)
                
            elif choice == "customers":
                result = questionary.text(
                    "How many customers to generate?",
                    default=str(user_choices.get('customers', 1000)),
                    validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['customers'] = int(result)
                
            elif choice == "days":
                result = questionary.text(
                    "How many days of transaction data?",
                    default=str(user_choices.get('days', 30)),
                    validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['days'] = int(result)
                
            elif choice == "seed":
                result = questionary.text(
                    "Random seed (for reproducibility)?",
                    default=str(user_choices.get('seed', 42))
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['seed'] = int(result) if result.isdigit() else 42
                
            elif choice == "format":
                format_result = handle_format_selection(user_choices)
                if format_result == "back":
                    continue
            
            console.clear()


def handle_format_selection(user_choices):
    """Handle format selection with database configuration."""
    
    while True:
        console.print("[dim]💡 File formats work without any database setup[/dim]")
        
        format_choice = questionary.select(
            "Select export format:",
            choices=[
                {"name": "📄 CSV (Recommended - no database required)", "value": "csv"},
                {"name": "📄 JSON (Simple format - no database required)", "value": "json"},
                {"name": "📊 Excel Workbook (Business reports - no database required)", "value": "xlsx"},
                {"name": "📦 Parquet (Big Data format - no database required)", "value": "parquet"},
                {"name": "🗄️ SQLite Database (Local database file)", "value": "sqlite"},
                {"name": "🌐 External Database (Requires credentials)", "value": "external_db"},
                Separator(),
                {"name": "← Back to Parameter Selection", "value": "back"}
            ]
        ).ask()
        if format_choice is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if format_choice == "back":
            return "back"
        
        user_choices['format'] = format_choice
        
        # Handle database configuration if needed
        if format_choice == "sqlite":
            db_file = questionary.text(
                "SQLite database file path:",
                default=user_choices.get('db_file', "./data/aus_pos_data.db")
            ).ask()
            if db_file is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            user_choices['db_file'] = db_file
            break
            
        elif format_choice == "external_db":
            db_result = handle_external_db_config(user_choices)
            if db_result == "back":
                continue
            else:
                break
        else:
            # File format selected, no additional config needed
            break
    
    return "configured"


def handle_external_db_config(user_choices):
    """Handle external database configuration."""
    
    while True:
        db_type = questionary.select(
            "Select database type:",
            choices=[
                {"name": "PostgreSQL (Popular enterprise database)", "value": "postgresql"},
                {"name": "MySQL (Popular web database)", "value": "mysql"},
                {"name": "MariaDB (MySQL-compatible)", "value": "mariadb"},
                Separator(),
                {"name": "← Back to Format Selection", "value": "back"}
            ]
        ).ask()
        if db_type is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if db_type == "back":
            return "back"
        
        console.print(f"\n[yellow]⚠️ {db_type.upper()} requires database credentials[/yellow]")
        console.print("[dim]You'll need: host, port, database name, username, and password[/dim]")
        
        proceed = questionary.select(
            f"How would you like to proceed with {db_type.upper()}?",
            choices=[
                {"name": f"✅ I have {db_type.upper()} credentials - continue setup", "value": "continue"},
                {"name": "← Back to Database Type Selection", "value": "back_db"},
                {"name": "← Back to Format Selection", "value": "back_format"}
            ]
        ).ask()
        if proceed is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if proceed == "back_db":
            continue
        elif proceed == "back_format":
            return "back"
        else:
            # Collect database credentials
            user_choices['db_type'] = db_type
            
            user_choices['db_host'] = questionary.text(
                f"{db_type.title()} host:",
                default=user_choices.get('db_host', 'localhost')
            ).ask()
            if user_choices['db_host'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            default_port = "5432" if db_type == "postgresql" else "3306"
            user_choices['db_port'] = questionary.text(
                f"{db_type.title()} port:",
                default=str(user_choices.get('db_port', default_port))
            ).ask()
            if user_choices['db_port'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            user_choices['db_name'] = questionary.text(
                "Database name:",
                default=user_choices.get('db_name', 'aus_pos_data')
            ).ask()
            if user_choices['db_name'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            default_user = "postgres" if db_type == "postgresql" else "root"
            user_choices['db_username'] = questionary.text(
                "Database username:",
                default=user_choices.get('db_username', default_user)
            ).ask()
            if user_choices['db_username'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            user_choices['db_password'] = questionary.password(
                "Database password:"
            ).ask()
            if user_choices['db_password'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            user_choices['db_table_prefix'] = questionary.text(
                "Table prefix (optional):",
                default=user_choices.get('db_table_prefix', '')
            ).ask()
            if user_choices['db_table_prefix'] is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            if db_type == "postgresql":
                user_choices['db_schema'] = questionary.text(
                    "Database schema:",
                    default=user_choices.get('db_schema', 'public')
                ).ask()
                if user_choices['db_schema'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
            
            break
    
    return "configured"


def handle_stream_params(user_choices, navigation_stack):
    """Handle streaming parameter configuration."""
    
    # Show current progress
    show_progress_indicator("Live Streaming", ["✅ Operation Selected", "📊 Configure Parameters", "🚀 Execute"])
    
    while True:
        # Show current selections if any
        if len(user_choices) > 1:
            show_current_selections(user_choices)
        
        choice = questionary.select(
            "Configure streaming parameters:",
            choices=[
                {"name": f"🏪 Businesses: {user_choices.get('businesses', '[Not Set]')}", "value": "businesses"},
                {"name": f"👥 Customers: {user_choices.get('customers', '[Not Set]')}", "value": "customers"},
                {"name": f"⚡ Rate (TPS): {user_choices.get('rate', '[Not Set]')}", "value": "rate"},
                {"name": f"⏱️ Duration: {user_choices.get('duration', '[Unlimited]')}", "value": "duration"},
                {"name": f"📋 Stream Format: {user_choices.get('format', '[Not Set]')}", "value": "format"},
                {"name": f"🌱 Random Seed: {user_choices.get('seed', '[Not Set]')}", "value": "seed"},
                Separator(),
                {"name": "🚀 Continue to Execution (if all set)", "value": "continue"},
                {"name": "← Back to Main Menu", "value": "back"}
            ]
        ).ask()
        if choice is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if choice == "back":
            return "back"
        elif choice == "continue":
            # Check if all required params are set
            required_params = ['businesses', 'customers', 'rate', 'format']
            missing = [p for p in required_params if p not in user_choices]
            
            if missing:
                console.print(f"[red]❌ Please configure: {', '.join(missing)}[/red]")
                input("Press Enter to continue...")
                console.clear()
                continue
            else:
                navigation_stack.append("stream_params")
                return "execute"
        else:
            # Handle parameter configuration
            if choice == "businesses":
                result = questionary.text(
                    "How many businesses to stream from?",
                    default=str(user_choices.get('businesses', 3)),
                    validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['businesses'] = int(result)
                
            elif choice == "customers":
                result = questionary.text(
                    "How many customers in the system?",
                    default=str(user_choices.get('customers', 500)),
                    validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['customers'] = int(result)
                
            elif choice == "rate":
                result = questionary.text(
                    "Transactions per second?",
                    default=str(user_choices.get('rate', 1.0)),
                    validate=lambda val: validate_positive_float(val) or "Must be a positive number"
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['rate'] = float(result)
                
            elif choice == "duration":
                use_duration = questionary.confirm(
                    "Set a time limit for streaming?",
                    default=user_choices.get('use_duration', False)
                ).ask()
                if use_duration is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                if use_duration:
                    duration = questionary.text(
                        "Duration in seconds?",
                        default=str(user_choices.get('duration', 60)),
                        validate=lambda val: validate_positive_int(val) or "Must be a positive number"
                    ).ask()
                    if duration is None:
                        console.print("\n[red]🛑 Exiting program...[/red]")
                        import sys
                        sys.exit(0)
                    user_choices['duration'] = int(duration)
                    user_choices['use_duration'] = True
                else:
                    user_choices['duration'] = None
                    user_choices['use_duration'] = False
                
            elif choice == "format":
                format_result = handle_stream_format_selection(user_choices)
                if format_result == "back":
                    continue
                    
            elif choice == "seed":
                result = questionary.text(
                    "Random seed (for reproducibility)?",
                    default=str(user_choices.get('seed', 42))
                ).ask()
                if result is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['seed'] = int(result) if result.isdigit() else 42
            
            console.clear()


def handle_stream_format_selection(user_choices):
    """Handle streaming format selection."""
    
    while True:
        console.print("[dim]💡 Console, JSON, and CSV work without any database setup[/dim]")
        
        format_choice = questionary.select(
            "Choose streaming format:",
            choices=[
                {"name": "📺 Console (Real-time display - no database required)", "value": "console"},
                {"name": "📄 JSON (To console or file - no database required)", "value": "json"},
                {"name": "📊 CSV (To file - no database required)", "value": "csv"},
                {"name": "🗄️ Database (Requires database connection)", "value": "database"},
                Separator(),
                {"name": "← Back to Parameter Selection", "value": "back"}
            ]
        ).ask()
        if format_choice is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if format_choice == "back":
            return "back"
        
        user_choices['format'] = format_choice
        
        # Handle format-specific configuration
        if format_choice == "json":
            save_to_file = questionary.confirm(
                "Save JSON output to file?",
                default=user_choices.get('save_to_file', False)
            ).ask()
            if save_to_file is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            if save_to_file:
                output_file = questionary.text(
                    "Output filename:",
                    default=user_choices.get('output_file', 'stream_output.json')
                ).ask()
                if output_file is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                user_choices['output_file'] = output_file
            user_choices['save_to_file'] = save_to_file
            
        elif format_choice == "csv":
            output_file = questionary.text(
                "CSV output filename:",
                default=user_choices.get('output_file', 'stream_output.csv')
            ).ask()
            if output_file is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            user_choices['output_file'] = output_file
            
        elif format_choice == "database":
            db_result = handle_stream_db_config(user_choices)
            if db_result == "back":
                continue
        
        break
    
    return "configured"


def handle_stream_db_config(user_choices):
    """Handle streaming database configuration."""
    
    while True:
        db_type = questionary.select(
            "Select database type for streaming:",
            choices=[
                {"name": "🗄️ SQLite (Local file - easiest setup)", "value": "sqlite"},
                {"name": "🐘 PostgreSQL (Requires credentials)", "value": "postgresql"},
                {"name": "🐬 MySQL (Requires credentials)", "value": "mysql"},
                {"name": "🦭 MariaDB (Requires credentials)", "value": "mariadb"},
                Separator(),
                {"name": "← Back to Format Selection", "value": "back"}
            ]
        ).ask()
        if db_type is None:
            console.print("\n[red]🛑 Exiting program...[/red]")
            import sys
            sys.exit(0)
        
        if db_type == "back":
            return "back"
        
        user_choices['db_type'] = db_type
        
        if db_type == "sqlite":
            db_file = questionary.text(
                "SQLite database file path:",
                default=user_choices.get('db_file', './data/stream_data.db')
            ).ask()
            if db_file is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            user_choices['db_file'] = db_file
            break
        else:
            # External database setup (similar to generate)
            console.print(f"\n[yellow]⚠️ {db_type.upper()} streaming requires database credentials[/yellow]")
            
            proceed = questionary.select(
                f"How would you like to proceed with {db_type.upper()}?",
                choices=[
                    {"name": f"✅ I have {db_type.upper()} credentials - continue setup", "value": "continue"},
                    {"name": "← Back to Database Type Selection", "value": "back_db"},
                    {"name": "← Back to Format Selection", "value": "back_format"}
                ]
            ).ask()
            if proceed is None:
                console.print("\n[red]🛑 Exiting program...[/red]")
                import sys
                sys.exit(0)
            
            if proceed == "back_db":
                continue
            elif proceed == "back_format":
                return "back"
            else:
                # Collect credentials (same as generate function)
                user_choices['db_host'] = questionary.text(
                    f"{db_type.title()} host:",
                    default=user_choices.get('db_host', 'localhost')
                ).ask()
                if user_choices['db_host'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                default_port = "5432" if db_type == "postgresql" else "3306"
                user_choices['db_port'] = questionary.text(
                    f"{db_type.title()} port:",
                    default=str(user_choices.get('db_port', default_port))
                ).ask()
                if user_choices['db_port'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                user_choices['db_name'] = questionary.text(
                    "Database name:",
                    default=user_choices.get('db_name', 'stream_data')
                ).ask()
                if user_choices['db_name'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                default_user = "postgres" if db_type == "postgresql" else "root"
                user_choices['db_username'] = questionary.text(
                    "Database username:",
                    default=user_choices.get('db_username', default_user)
                ).ask()
                if user_choices['db_username'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                user_choices['db_password'] = questionary.password(
                    "Database password:"
                ).ask()
                if user_choices['db_password'] is None:
                    console.print("\n[red]🛑 Exiting program...[/red]")
                    import sys
                    sys.exit(0)
                
                break
    
    return "configured"


def show_progress_indicator(operation_type, steps):
    """Show progress indicator for current operation."""
    console.print(f"[bold cyan]📋 {operation_type} Configuration[/bold cyan]")
    console.print(" → ".join(steps))
    console.print()


def show_current_selections(user_choices):
    """Show current user selections in a panel."""
    selections_text = []
    for key, value in user_choices.items():
        if key == "operation":
            continue
        if key == "db_password":
            value = "***" if value else "[Not Set]"
        selections_text.append(f"[green]{key.title()}:[/green] {value}")
    
    if selections_text:
        panel = Panel.fit(
            Align.left(Text.from_markup("\n".join(selections_text))),
            title="[bold blue]📊 Current Selections[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        console.print(panel)
        console.print()


def execute_user_choices(user_choices):
    """Execute the user's configuration choices."""
    from .cli import stream, generate
    
    console.print("[bold green]🚀 Executing your configuration...[/bold green]")
    console.print()
    
    try:
        if user_choices["operation"] == "generate":
            # Execute batch generation
            if user_choices.get('format') == 'external_db':
                # Database generation
                generate(
                    businesses=user_choices['businesses'],
                    customers=user_choices['customers'],
                    days=user_choices['days'],
                    seed=user_choices['seed'],
                    format='csv',  # Default format for database export
                    db_type=user_choices.get('db_type', 'sqlite'),
                    db_host=user_choices.get('db_host'),
                    db_port=user_choices.get('db_port'),
                    db_name=user_choices.get('db_name'),
                    db_username=user_choices.get('db_username'),
                    db_password=user_choices.get('db_password'),
                    db_table_prefix=user_choices.get('db_table_prefix', ''),
                    db_schema=user_choices.get('db_schema'),
                    verbose=True
                )
            else:
                # File generation
                generate(
                    businesses=user_choices['businesses'],
                    customers=user_choices['customers'],
                    days=user_choices['days'],
                    seed=user_choices['seed'],
                    format=user_choices['format'],
                    verbose=True
                )
                
        elif user_choices["operation"] == "stream":
            # Execute streaming
            if user_choices.get('format') == 'database':
                # Database streaming
                stream(
                    businesses=user_choices['businesses'],
                    customers=user_choices['customers'],
                    rate=user_choices['rate'],
                    duration=user_choices.get('duration'),
                    format=user_choices['format'],
                    output=user_choices.get('output_file'),
                    db_type=user_choices.get('db_type', 'sqlite'),
                    db_host=user_choices.get('db_host'),
                    db_port=user_choices.get('db_port'),
                    db_name=user_choices.get('db_name', user_choices.get('db_file')),
                    db_username=user_choices.get('db_username'),
                    db_password=user_choices.get('db_password'),
                    seed=user_choices['seed']
                )
            else:
                # File streaming
                stream(
                    businesses=user_choices['businesses'],
                    customers=user_choices['customers'],
                    rate=user_choices['rate'],
                    duration=user_choices.get('duration'),
                    format=user_choices['format'],
                    output=user_choices.get('output_file'),
                    seed=user_choices['seed']
                )
        
        console.print("[bold green]✅ Execution completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Execution failed: {e}[/red]")
        console.print("[yellow]💡 Check your configuration and try again[/yellow]")