"""
Enhanced database integration manager for Australian POS data generation.

Provides robust database operations with connection pooling, batch processing,
error handling, and retry mechanisms for both batch and streaming scenarios.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from threading import Lock
from collections import deque
import logging
from decimal import Decimal

from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Float, Text, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from sqlalchemy.dialects.mysql import JSON as MyJSON
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.pool import QueuePool
from loguru import logger
import pandas as pd

from .config import DatabaseConfig
from .models import Transaction, Customer, Business, ReturnTransaction


@dataclass
class BatchBuffer:
    """Buffer for batching database operations."""
    transactions: List[Dict] = field(default_factory=list)
    customers: List[Dict] = field(default_factory=list)
    businesses: List[Dict] = field(default_factory=list)
    returns: List[Dict] = field(default_factory=list)
    transaction_items: List[Dict] = field(default_factory=list)
    
    last_flush: datetime = field(default_factory=datetime.now)
    lock: Lock = field(default_factory=Lock)
    
    def clear(self):
        """Clear all buffers."""
        with self.lock:
            self.transactions.clear()
            self.customers.clear()
            self.businesses.clear()
            self.returns.clear()
            self.transaction_items.clear()
            self.last_flush = datetime.now()
    
    def size(self) -> int:
        """Get total number of records across all buffers."""
        with self.lock:
            return (len(self.transactions) + len(self.customers) + 
                   len(self.businesses) + len(self.returns) + 
                   len(self.transaction_items))
    
    def should_flush(self, max_size: int = 100, max_age_seconds: int = 30) -> bool:
        """Check if buffer should be flushed based on size or age."""
        with self.lock:
            age = (datetime.now() - self.last_flush).total_seconds()
            return self.size() >= max_size or age >= max_age_seconds


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        import random
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)  # Add jitter
        return delay


@dataclass
class ConnectionStats:
    """Statistics for database connections."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    retry_operations: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class EnhancedDatabaseManager:
    """Enhanced database manager with connection pooling, batching, and error handling."""
    
    def __init__(self, db_config: DatabaseConfig, batch_size: int = 100, 
                 batch_timeout: int = 30, retry_config: Optional[RetryConfig] = None):
        """Initialize the enhanced database manager.
        
        Args:
            db_config: Database configuration
            batch_size: Maximum batch size before flushing
            batch_timeout: Maximum seconds to wait before flushing batch
            retry_config: Retry configuration for failed operations
        """
        self.db_config = db_config
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.retry_config = retry_config or RetryConfig()
        
        # Initialize engine with enhanced connection pooling
        self.engine = self._create_engine()
        self.metadata = MetaData()
        self.tables: Dict[str, Table] = {}
        
        # Initialize batch buffer
        self.batch_buffer = BatchBuffer()
        
        # Statistics and monitoring
        self.stats = ConnectionStats()
        
        # Create tables on initialization
        self._create_tables()
        
        logger.info(f"Enhanced database manager initialized for {db_config.db_type}")
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with enhanced configuration."""
        connection_string = self.db_config.get_connection_string()
        
        # Enhanced engine configuration
        engine_kwargs = {
            'echo': self.db_config.echo,
            'poolclass': QueuePool,
            'pool_size': self.db_config.pool_size,
            'max_overflow': self.db_config.max_overflow,
            'pool_pre_ping': True,  # Verify connections before use
            'pool_recycle': 3600,   # Recycle connections every hour
            'pool_timeout': 30,     # Timeout for getting connection from pool
            'connect_args': {}
        }
        
        # Database-specific configurations
        if self.db_config.db_type == 'postgresql':
            engine_kwargs['connect_args'].update({
                'application_name': 'AUS-POS-DataGen',
                'connect_timeout': 10
            })
            if self.db_config.ssl_mode:
                engine_kwargs['connect_args']['sslmode'] = self.db_config.ssl_mode
        elif self.db_config.db_type in ('mysql', 'mariadb'):
            engine_kwargs['connect_args'].update({
                'charset': 'utf8mb4',
                'connect_timeout': 10
            })
        elif self.db_config.db_type == 'sqlite':
            engine_kwargs['connect_args'].update({
                'timeout': 20,
                'check_same_thread': False
            })
        
        try:
            engine = create_engine(connection_string, **engine_kwargs)
            self.stats.total_connections += 1
            return engine
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def _create_tables(self):
        """Create all database tables with proper schemas."""
        # Choose appropriate JSON type based on database
        json_type = JSON
        if self.db_config.db_type == 'postgresql':
            json_type = PGJSON
        elif self.db_config.db_type in ('mysql', 'mariadb'):
            json_type = MyJSON
        
        schema = self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None
        
        # Businesses table
        self.tables['businesses'] = Table(
            self.db_config.get_table_name('businesses'),
            self.metadata,
            Column('store_id', String(10), primary_key=True),
            Column('business_name', String(255), nullable=False),
            Column('abn', String(15), unique=True, nullable=False),
            Column('acn', String(15)),
            Column('trading_name', String(255)),
            Column('store_address', String(255)),
            Column('suburb', String(100)),
            Column('state', String(5)),
            Column('postcode', String(10)),
            Column('phone', String(20)),
            Column('email', String(255)),
            Column('gst_registered', Boolean, default=True),
            Column('pos_system_type', String(50)),
            Column('terminal_count', Integer),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            schema=schema
        )
        
        # Customers table
        self.tables['customers'] = Table(
            self.db_config.get_table_name('customers'),
            self.metadata,
            Column('customer_id', String(20), primary_key=True),
            Column('customer_type', String(20), nullable=False),
            Column('first_name', String(100)),
            Column('last_name', String(100)),
            Column('company_name', String(255)),
            Column('email', String(255)),
            Column('phone', String(20)),
            Column('date_of_birth', DateTime),
            Column('address', String(255)),
            Column('suburb', String(100)),
            Column('state', String(5)),
            Column('postcode', String(10)),
            Column('customer_abn', String(15)),
            Column('loyalty_member', Boolean, default=False),
            Column('loyalty_points_earned', Integer, default=0),
            Column('loyalty_points_redeemed', Integer, default=0),
            Column('registration_date', DateTime, default=datetime.now),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            schema=schema
        )
        
        # Transactions table
        self.tables['transactions'] = Table(
            self.db_config.get_table_name('transactions'),
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('transaction_id', String(30), unique=True, nullable=False),
            Column('store_id', String(10), nullable=False),
            Column('workstation_id', String(10)),
            Column('employee_id', String(20)),
            Column('transaction_type', String(20), nullable=False),
            Column('business_day_date', DateTime),
            Column('transaction_datetime', DateTime, nullable=False),
            Column('sequence_number', Integer),
            Column('receipt_number', String(20)),
            Column('customer_id', String(20)),
            Column('subtotal_ex_gst', Float, nullable=False),
            Column('gst_amount', Float, nullable=False),
            Column('total_inc_gst', Float, nullable=False),
            Column('payment_method', String(30), nullable=False),
            Column('tender_amount', Float),
            Column('change_amount', Float),
            Column('currency_code', String(5), default='AUD'),
            Column('operator_id', String(20)),
            Column('shift_id', String(10)),
            Column('business_abn', String(15)),
            Column('items_json', json_type),  # JSON field for items
            Column('created_at', DateTime, default=datetime.now),
            schema=schema
        )
        
        # Transaction items table (normalized)
        self.tables['transaction_items'] = Table(
            self.db_config.get_table_name('transaction_items'),
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('transaction_id', String(30), nullable=False),
            Column('line_number', Integer, nullable=False),
            Column('item_type', String(20), default='SALE'),
            Column('product_id', String(20)),
            Column('sku', String(50)),
            Column('barcode', String(50)),
            Column('product_name', String(255)),
            Column('category', String(50)),
            Column('brand', String(100)),
            Column('quantity', Float, nullable=False),
            Column('unit_price_ex_gst', Float),
            Column('unit_price_inc_gst', Float),
            Column('line_subtotal_ex_gst', Float),
            Column('line_gst_amount', Float),
            Column('line_total_inc_gst', Float),
            Column('gst_code', String(20)),
            Column('discount_amount', Float, default=0),
            Column('discount_type', String(20)),
            Column('promotion_id', String(20)),
            Column('created_at', DateTime, default=datetime.now),
            schema=schema
        )
        
        # Returns table
        self.tables['returns'] = Table(
            self.db_config.get_table_name('returns'),
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('return_id', String(30), unique=True, nullable=False),
            Column('original_transaction_id', String(30), nullable=False),
            Column('original_receipt_number', String(20)),
            Column('return_date', DateTime),
            Column('return_time', DateTime, nullable=False),
            Column('return_reason_code', String(20)),
            Column('return_reason_description', String(255)),
            Column('returned_by_customer_id', String(20)),
            Column('processed_by_employee_id', String(20)),
            Column('refund_method', String(30)),
            Column('refund_amount', Float),
            Column('store_credit_issued', Float, default=0),
            Column('restocking_fee', Float, default=0),
            Column('condition_code', String(20)),
            Column('original_purchase_date', DateTime),
            Column('created_at', DateTime, default=datetime.now),
            schema=schema
        )
        
        # Create all tables
        try:
            self.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = self.engine.connect()
            self.stats.active_connections += 1
            yield conn
        except Exception as e:
            self.stats.failed_connections += 1
            self.stats.last_error = str(e)
            self.stats.last_error_time = datetime.now()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.stats.active_connections -= 1
    
    def _retry_operation(self, operation: Callable, *args, **kwargs):
        """Execute operation with retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                return operation(*args, **kwargs)
            except (SQLAlchemyError, DisconnectionError) as e:
                last_exception = e
                self.stats.retry_operations += 1
                
                if attempt < self.retry_config.max_attempts - 1:
                    delay = self.retry_config.get_delay(attempt)
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{self.retry_config.max_attempts}), retrying in {delay:.2f}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {self.retry_config.max_attempts} attempts: {e}")
        
        self.stats.failed_operations += 1
        raise last_exception
    
    def _convert_model_to_dict(self, model) -> Dict:
        """Convert Pydantic model to dictionary with proper serialization."""
        if hasattr(model, 'model_dump'):
            data = model.model_dump()
        elif hasattr(model, 'dict'):
            data = model.dict()
        else:
            data = dict(model)
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        return convert_decimals(data)
    
    def add_to_batch(self, data_type: str, data: Union[Dict, Any]):
        """Add data to batch buffer."""
        if not isinstance(data, dict):
            data = self._convert_model_to_dict(data)
        
        with self.batch_buffer.lock:
            if data_type == 'transaction':
                # Extract items for separate table
                if 'items' in data:
                    items = data.pop('items')
                    for item in items:
                        item['transaction_id'] = data['transaction_id']
                        self.batch_buffer.transaction_items.append(item)
                
                # Store items as JSON for transactions table
                data['items_json'] = items if 'items' in locals() else []
                self.batch_buffer.transactions.append(data)
                
            elif data_type == 'customer':
                self.batch_buffer.customers.append(data)
            elif data_type == 'business':
                self.batch_buffer.businesses.append(data)
            elif data_type == 'return':
                self.batch_buffer.returns.append(data)
        
        # Auto-flush if buffer is full or old
        if self.batch_buffer.should_flush(self.batch_size, self.batch_timeout):
            self.flush_batch()
    
    def flush_batch(self) -> Dict[str, int]:
        """Flush all batched data to database."""
        if self.batch_buffer.size() == 0:
            return {}
        
        def _flush_operation():
            results = {}
            
            with self.get_connection() as conn:
                trans = conn.begin()
                try:
                    # Insert businesses
                    if self.batch_buffer.businesses:
                        df = pd.DataFrame(self.batch_buffer.businesses)
                        rows = df.to_sql(
                            self.tables['businesses'].name,
                            conn,
                            if_exists='append',
                            index=False,
                            schema=self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None,
                            method='multi'
                        )
                        results['businesses'] = len(self.batch_buffer.businesses)
                        logger.debug(f"Inserted {len(self.batch_buffer.businesses)} businesses")
                    
                    # Insert customers
                    if self.batch_buffer.customers:
                        df = pd.DataFrame(self.batch_buffer.customers)
                        rows = df.to_sql(
                            self.tables['customers'].name,
                            conn,
                            if_exists='append',
                            index=False,
                            schema=self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None,
                            method='multi'
                        )
                        results['customers'] = len(self.batch_buffer.customers)
                        logger.debug(f"Inserted {len(self.batch_buffer.customers)} customers")
                    
                    # Insert transactions
                    if self.batch_buffer.transactions:
                        df = pd.DataFrame(self.batch_buffer.transactions)
                        rows = df.to_sql(
                            self.tables['transactions'].name,
                            conn,
                            if_exists='append',
                            index=False,
                            schema=self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None,
                            method='multi'
                        )
                        results['transactions'] = len(self.batch_buffer.transactions)
                        logger.debug(f"Inserted {len(self.batch_buffer.transactions)} transactions")
                    
                    # Insert transaction items
                    if self.batch_buffer.transaction_items:
                        df = pd.DataFrame(self.batch_buffer.transaction_items)
                        rows = df.to_sql(
                            self.tables['transaction_items'].name,
                            conn,
                            if_exists='append',
                            index=False,
                            schema=self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None,
                            method='multi'
                        )
                        results['transaction_items'] = len(self.batch_buffer.transaction_items)
                        logger.debug(f"Inserted {len(self.batch_buffer.transaction_items)} transaction items")
                    
                    # Insert returns
                    if self.batch_buffer.returns:
                        df = pd.DataFrame(self.batch_buffer.returns)
                        rows = df.to_sql(
                            self.tables['returns'].name,
                            conn,
                            if_exists='append',
                            index=False,
                            schema=self.db_config.db_schema if self.db_config.db_type == 'postgresql' else None,
                            method='multi'
                        )
                        results['returns'] = len(self.batch_buffer.returns)
                        logger.debug(f"Inserted {len(self.batch_buffer.returns)} returns")
                    
                    trans.commit()
                    self.stats.successful_operations += 1
                    return results
                    
                except Exception as e:
                    trans.rollback()
                    raise e
        
        try:
            results = self._retry_operation(_flush_operation)
            self.batch_buffer.clear()
            total_records = sum(results.values())
            logger.info(f"Successfully flushed {total_records} records to database")
            return results
            
        except Exception as e:
            logger.error(f"Failed to flush batch to database: {e}")
            raise
    
    def insert_transaction_stream(self, transaction: Transaction) -> bool:
        """Insert single transaction for streaming (with batching)."""
        try:
            self.add_to_batch('transaction', transaction)
            return True
        except Exception as e:
            logger.error(f"Failed to add transaction to batch: {e}")
            return False
    
    def insert_bulk_data(self, businesses: List[Business] = None, 
                        customers: List[Customer] = None,
                        transactions: List[Transaction] = None,
                        returns: List[ReturnTransaction] = None) -> Dict[str, int]:
        """Insert bulk data with optimal batching."""
        results = {}
        
        # Add all data to batch
        if businesses:
            for business in businesses:
                self.add_to_batch('business', business)
        
        if customers:
            for customer in customers:
                self.add_to_batch('customer', customer)
        
        if transactions:
            for transaction in transactions:
                self.add_to_batch('transaction', transaction)
        
        if returns:
            for return_txn in returns:
                self.add_to_batch('return', return_txn)
        
        # Force flush all data
        return self.flush_batch()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection and operation statistics."""
        return {
            'total_connections': self.stats.total_connections,
            'active_connections': self.stats.active_connections,
            'failed_connections': self.stats.failed_connections,
            'successful_operations': self.stats.successful_operations,
            'failed_operations': self.stats.failed_operations,
            'retry_operations': self.stats.retry_operations,
            'batch_buffer_size': self.batch_buffer.size(),
            'last_error': self.stats.last_error,
            'last_error_time': self.stats.last_error_time,
            'engine_pool_size': self.engine.pool.size(),
            'engine_pool_checked_in': self.engine.pool.checkedin(),
            'engine_pool_checked_out': self.engine.pool.checkedout(),
            'engine_pool_overflow': self.engine.pool.overflow(),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        health_status = {
            'status': 'unknown',
            'timestamp': datetime.now(),
            'connection_test': False,
            'tables_exist': False,
            'response_time_ms': None,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                # Test basic connection
                result = conn.execute("SELECT 1" if self.db_config.db_type != 'sqlite' else "SELECT 1")
                health_status['connection_test'] = True
                
                # Check if tables exist
                inspector = conn.dialect.get_table_names(conn)
                expected_tables = [self.db_config.get_table_name(t) for t in ['businesses', 'customers', 'transactions', 'returns']]
                health_status['tables_exist'] = all(table in inspector for table in expected_tables)
                
                health_status['response_time_ms'] = (time.time() - start_time) * 1000
                health_status['status'] = 'healthy'
                
        except Exception as e:
            health_status['error'] = str(e)
            health_status['status'] = 'unhealthy'
            health_status['response_time_ms'] = (time.time() - start_time) * 1000
        
        return health_status
    
    def close(self):
        """Close database connection and flush any remaining batch data."""
        try:
            # Flush any remaining data
            if self.batch_buffer.size() > 0:
                self.flush_batch()
            
            # Close engine
            self.engine.dispose()
            logger.info("Database manager closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()