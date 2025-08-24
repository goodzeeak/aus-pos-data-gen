"""
Configuration module for Australian POS data generator.

Provides comprehensive configuration management with validation
using Pydantic for type safety and settings validation.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta


class AustralianPaymentMethods:
    """Australian payment method distributions based on market data."""

    EFTPOS = 0.45
    CONTACTLESS = 0.30
    CREDIT_CARD = 0.15
    CASH = 0.08
    BUY_NOW_PAY_LATER = 0.02

    @classmethod
    def get_distribution(cls) -> Dict[str, float]:
        return {
            "EFTPOS": cls.EFTPOS,
            "CONTACTLESS": cls.CONTACTLESS,
            "CREDIT_CARD": cls.CREDIT_CARD,
            "CASH": cls.CASH,
            "BUY_NOW_PAY_LATER": cls.BUY_NOW_PAY_LATER,
        }


class AustralianStates:
    """Australian states and territories with their postcodes."""

    STATES = {
        "NSW": {"name": "New South Wales", "postcodes": (1000, 2999)},
        "VIC": {"name": "Victoria", "postcodes": (3000, 3999)},
        "QLD": {"name": "Queensland", "postcodes": (4000, 4999)},
        "WA": {"name": "Western Australia", "postcodes": (6000, 6999)},
        "SA": {"name": "South Australia", "postcodes": (5000, 5999)},
        "TAS": {"name": "Tasmania", "postcodes": (7000, 7999)},
        "NT": {"name": "Northern Territory", "postcodes": (800, 999)},
        "ACT": {"name": "Australian Capital Territory", "postcodes": (200, 299)},
    }


class GSTConfiguration:
    """GST calculation and compliance settings."""

    STANDARD_RATE = 0.10  # 10% GST
    ROUNDING_PRECISION = 2

    GST_CODES = {
        "GST": "Standard 10% GST-inclusive items",
        "GST_FREE": "GST-free items (basic food, medicine, exports)",
        "INPUT_TAXED": "Input-taxed items (financial services, residential rent)",
        "GST_EXEMPT": "Non-taxable items",
    }


class BusinessHours:
    """Australian retail business hours configuration."""

    WEEKDAYS = {
        "start": "09:00",
        "end": "17:00",
        "peak_lunch": ("12:00", "14:00"),
        "peak_after_work": ("17:00", "19:00"),
    }

    WEEKENDS = {
        "start": "10:00",
        "end": "16:00",
        "peak": ("11:00", "15:00"),
    }

    PUBLIC_HOLIDAYS = [
        "01-01",  # New Year's Day
        "01-26",  # Australia Day
        "04-25",  # ANZAC Day
        "12-25",  # Christmas Day
        "12-26",  # Boxing Day
    ]


@dataclass
class ReturnRates:
    """Return rates by product category."""

    ELECTRONICS = 0.12
    CLOTHING = 0.25
    GROCERIES = 0.03
    BOOKS_MEDIA = 0.10
    HEALTH_BEAUTY = 0.15

    @classmethod
    def get_by_category(cls, category: str) -> float:
        """Get return rate for a specific category."""
        rates = {
            "electronics": cls.ELECTRONICS,
            "clothing": cls.CLOTHING,
            "fashion": cls.CLOTHING,
            "groceries": cls.GROCERIES,
            "food": cls.GROCERIES,
            "books": cls.BOOKS_MEDIA,
            "media": cls.BOOKS_MEDIA,
            "health": cls.HEALTH_BEAUTY,
            "beauty": cls.HEALTH_BEAUTY,
        }
        return rates.get(category.lower(), 0.08)  # Default 8% return rate


class POSGeneratorConfig(BaseModel):
    """Main configuration for POS data generator."""

    # Basic settings
    seed: int = Field(default=42, description="Random seed for reproducibility")
    locale: str = Field(default="en_AU", description="Locale for data generation")

    # Business settings
    business_name: str = Field(default="Sample Retail Pty Ltd", description="Business name")
    abn: Optional[str] = Field(default=None, description="Australian Business Number")

    # Date range settings
    start_date: datetime = Field(
        default_factory=lambda: datetime.now() - timedelta(days=365),
        description="Start date for transaction generation"
    )
    end_date: datetime = Field(
        default_factory=datetime.now,
        description="End date for transaction generation"
    )

    # Volume settings
    daily_transactions: Dict[str, int] = Field(
        default_factory=lambda: {
            "small": (50, 150),
            "medium": (150, 500),
            "large": (500, 1200),
        },
        description="Daily transaction volumes by store size"
    )

    # Store size distribution
    store_size_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "small": 0.6,
            "medium": 0.3,
            "large": 0.1,
        },
        description="Distribution of store sizes"
    )

    # Transaction settings
    items_per_transaction: tuple[int, int] = Field(
        default=(1, 8),
        description="Range of items per transaction"
    )

    # Output settings
    output_dir: Path = Field(
        default_factory=lambda: Path("data/processed"),
        description="Output directory for generated data"
    )

    # Australian-specific settings
    payment_methods: Dict[str, float] = Field(
        default_factory=AustralianPaymentMethods.get_distribution,
        description="Payment method distribution"
    )

    states_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "NSW": 0.32,
            "VIC": 0.26,
            "QLD": 0.20,
            "WA": 0.11,
            "SA": 0.07,
            "TAS": 0.02,
            "NT": 0.01,
            "ACT": 0.01,
        },
        description="State population distribution"
    )

    # Product categories and GST treatment
    product_categories: Dict[str, Dict] = Field(
        default_factory=lambda: {
            "food": {"gst_code": "GST", "return_rate": 0.03},
            "beverages": {"gst_code": "GST", "return_rate": 0.05},
            "clothing": {"gst_code": "GST", "return_rate": 0.25},
            "electronics": {"gst_code": "GST", "return_rate": 0.12},
            "books": {"gst_code": "GST", "return_rate": 0.10},
            "health": {"gst_code": "GST_FREE", "return_rate": 0.15},
            "pharmacy": {"gst_code": "GST_FREE", "return_rate": 0.08},
        },
        description="Product categories with GST and return settings"
    )

    # Seasonal multipliers
    seasonal_multipliers: Dict[str, float] = Field(
        default_factory=lambda: {
            "q4": 1.4,  # Oct-Dec (Christmas)
            "q1": 0.8,  # Jan-Mar (post-Christmas)
            "q2": 1.0,  # Apr-Jun
            "q3": 1.0,  # Jul-Sep
        },
        description="Seasonal transaction multipliers"
    )

    # Validation
    @validator("abn")
    def validate_abn(cls, v):
        """Validate ABN format if provided."""
        if v is not None:
            if len(v.replace(" ", "")) != 11:
                raise ValueError("ABN must be 11 digits")
        return v

    @validator("start_date", "end_date")
    def validate_dates(cls, v):
        """Ensure end date is after start date."""
        if hasattr(cls, "end_date") and v >= cls.end_date:
            raise ValueError("Start date must be before end date")
        return v

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True


# Default configuration instance
DEFAULT_CONFIG = POSGeneratorConfig()
