"""
Australian business validators and calculators.

Includes ABN validation, GST calculations, and Australian business
compliance validation following ATO requirements.
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional
from datetime import datetime
from loguru import logger
from .models import GSTCode, GSTCalculation


class ABNValidator:
    """Australian Business Number (ABN) validator.

    Implements the ATO ABN check digit algorithm.
    ABN format: XX XXX XXX XXX (11 digits with spaces for display)
    """

    # ABN weights for check digit calculation (excluding the check digit itself)
    WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    @classmethod
    def validate_format(cls, abn: str) -> bool:
        """Validate ABN format (11 digits, may include spaces)."""
        # Remove spaces and check if all digits
        cleaned = abn.replace(" ", "")
        if not cleaned.isdigit():
            return False
        if len(cleaned) != 11:
            return False
        return True

    @classmethod
    def validate_check_digit(cls, abn: str) -> bool:
        """Validate ABN check digit using ATO algorithm."""
        cleaned = abn.replace(" ", "")

        if len(cleaned) != 11:
            return False

        try:
            digits = [int(d) for d in cleaned]

            # Step 1: Subtract 1 from the first digit
            digits[0] -= 1

            # Step 2: Multiply each digit by its weight
            weighted_sum = sum(d * w for d, w in zip(digits, cls.WEIGHTS))

            # Step 3: Divide by 89, check remainder is 0
            remainder = weighted_sum % 89

            return remainder == 0

        except (ValueError, IndexError) as e:
            logger.error(f"ABN validation error: {e}")
            return False

    @classmethod
    def validate_abn(cls, abn: str) -> Tuple[bool, str]:
        """Complete ABN validation with error messages."""
        if not cls.validate_format(abn):
            return False, "ABN must be 11 digits (spaces allowed)"

        if not cls.validate_check_digit(abn):
            return False, "Invalid ABN check digit"

        return True, "Valid ABN"

    @classmethod
    def format_abn(cls, abn: str) -> str:
        """Format ABN with spaces: XX XXX XXX XXX."""
        cleaned = abn.replace(" ", "")
        if len(cleaned) != 11:
            raise ValueError("ABN must be 11 digits")

        return f"{cleaned[:2]} {cleaned[2:5]} {cleaned[5:8]} {cleaned[8:]}"

    @classmethod
    def generate_valid_abn(cls, max_attempts: int = 1000) -> str:
        """Generate a valid ABN for testing purposes."""
        import random

        for attempt in range(max_attempts):
            # Generate random 11-digit number
            digits = [random.randint(0, 9) for _ in range(11)]
            abn_str = "".join(str(d) for d in digits)

            # Check if it's valid
            if cls.validate_check_digit(abn_str):
                return abn_str

        # If we can't generate a valid ABN after max attempts, raise an error
        raise ValueError(f"Could not generate valid ABN after {max_attempts} attempts")


class GSTCalculator:
    """Australian GST calculator with proper rounding rules."""

    STANDARD_RATE = Decimal("0.10")  # 10% GST
    ROUNDING_PRECISION = Decimal("0.01")

    @classmethod
    def calculate_gst_components(cls, amount_inc_gst: Decimal, gst_code: GSTCode) -> GSTCalculation:
        """Calculate GST components using Australian ATO rules."""
        return GSTCalculation.calculate_gst(amount_inc_gst, gst_code)

    @classmethod
    def calculate_gst_exclusive(cls, amount_inc_gst: Decimal) -> Decimal:
        """Calculate GST-exclusive amount from GST-inclusive amount."""
        gst_amount = cls.calculate_gst_amount(amount_inc_gst)
        return amount_inc_gst - gst_amount

    @classmethod
    def calculate_gst_amount(cls, amount_inc_gst: Decimal) -> Decimal:
        """Calculate GST amount using Australian formula."""
        # GST Amount = (GST-Inclusive Price × 1) ÷ 11
        gst_amount = (amount_inc_gst * Decimal("1")) / Decimal("11")
        return gst_amount.quantize(cls.ROUNDING_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_gst_inclusive(cls, amount_ex_gst: Decimal) -> Tuple[Decimal, Decimal]:
        """Calculate GST-inclusive amount from GST-exclusive amount."""
        gst_amount = (amount_ex_gst * cls.STANDARD_RATE).quantize(
            cls.ROUNDING_PRECISION, rounding=ROUND_HALF_UP
        )
        total_inc_gst = amount_ex_gst + gst_amount
        return total_inc_gst, gst_amount

    @classmethod
    def round_to_nearest_cent(cls, amount: Decimal) -> Decimal:
        """Round to nearest cent (Australian rounding rule)."""
        return amount.quantize(cls.ROUNDING_PRECISION, rounding=ROUND_HALF_UP)

    @classmethod
    def validate_gst_calculation(cls, inc_gst: Decimal, ex_gst: Decimal, gst_amount: Decimal) -> bool:
        """Validate that GST calculation is mathematically correct."""
        expected_ex_gst = inc_gst - gst_amount
        expected_gst = inc_gst - ex_gst

        return (
            abs(expected_ex_gst - ex_gst) < Decimal("0.01") and
            abs(expected_gst - gst_amount) < Decimal("0.01")
        )


class AustralianAddressValidator:
    """Australian address validation."""

    # Australian state postcodes ranges
    STATE_POSTCODES = {
        "NSW": range(1000, 3000),
        "VIC": range(3000, 4000),
        "QLD": range(4000, 5000),
        "WA": range(6000, 7000),
        "SA": range(5000, 6000),
        "TAS": range(7000, 8000),
        "NT": range(800, 1000),
        "ACT": range(200, 300),
    }

    @classmethod
    def validate_postcode_state(cls, postcode: str, state: str) -> bool:
        """Validate that postcode belongs to the correct state."""
        try:
            pc_int = int(postcode)
            if state in cls.STATE_POSTCODES:
                return pc_int in cls.STATE_POSTCODES[state]
            return False
        except ValueError:
            return False

    @classmethod
    def format_address(cls, address: dict) -> str:
        """Format Australian address properly."""
        parts = [
            address.get("street_address", ""),
            address.get("suburb", ""),
            f"{address.get('state', '')} {address.get('postcode', '')}",
        ]
        return ", ".join(part for part in parts if part.strip())


class BusinessHoursValidator:
    """Australian retail business hours validator."""

    @classmethod
    def is_business_hours(cls, dt: datetime, is_weekend: bool = False) -> bool:
        """Check if datetime is within typical Australian business hours."""
        hour = dt.hour

        if is_weekend:
            # Weekend hours: typically 10:00-16:00
            return 10 <= hour <= 16
        else:
            # Weekday hours: typically 9:00-17:00
            return 9 <= hour <= 17

    @classmethod
    def is_peak_hour(cls, dt: datetime) -> bool:
        """Check if datetime is during peak retail hours."""
        hour = dt.hour

        # Peak periods: lunch (12-14) and after work (17-19)
        return (12 <= hour <= 14) or (17 <= hour <= 19)


class ReceiptValidator:
    """Receipt format and compliance validator."""

    @classmethod
    def validate_receipt_fields(cls, transaction_data: dict) -> Tuple[bool, list]:
        """Validate mandatory receipt fields for transactions >$75."""
        errors = []
        total_amount = transaction_data.get("total_inc_gst", 0)

        # Transactions >$75 require receipt with specific fields
        if total_amount > 75:
            required_fields = [
                "business_name",
                "abn",
                "transaction_datetime",
                "receipt_number",
                "total_inc_gst",
            ]

            for field in required_fields:
                if not transaction_data.get(field):
                    errors.append(f"Missing required field: {field}")

            # GST breakdown required for tax invoices
            if not transaction_data.get("gst_amount"):
                errors.append("GST breakdown required for tax invoice")

        return len(errors) == 0, errors

    @classmethod
    def generate_receipt_number(cls, store_id: str, sequence: int) -> str:
        """Generate properly formatted receipt number."""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{store_id}-{date_str}-{sequence:03d}"
