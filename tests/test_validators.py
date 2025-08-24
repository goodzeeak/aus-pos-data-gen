"""
Tests for Australian business validators.

Tests ABN validation, GST calculations, and Australian business compliance
validation following ATO requirements.
"""

import pytest
from decimal import Decimal
from aus_pos_data_gen.validators import ABNValidator, GSTCalculator
from aus_pos_data_gen.models import GSTCode


class TestABNValidator:
    """Test Australian Business Number validation."""

    def test_valid_abn_format(self):
        """Test ABN format validation."""
        valid_abn = "12 345 678 901"
        assert ABNValidator.validate_format(valid_abn)

        invalid_abn = "123456789"  # Too short
        assert not ABNValidator.validate_format(invalid_abn)

        invalid_abn = "12 345 678 901 2"  # Too long
        assert not ABNValidator.validate_format(invalid_abn)

    def test_abn_check_digit(self):
        """Test ABN check digit validation."""
        valid_abn = "83 914 571 673"  # Known valid ABN
        assert ABNValidator.validate_check_digit(valid_abn)

        invalid_abn = "12 345 678 900"  # Invalid check digit
        assert not ABNValidator.validate_check_digit(invalid_abn)

    def test_abn_formatting(self):
        """Test ABN formatting."""
        raw_abn = "83914571673"
        formatted = ABNValidator.format_abn(raw_abn)
        assert formatted == "83 914 571 673"

    def test_generate_valid_abn(self):
        """Test generation of valid ABN."""
        abn = ABNValidator.generate_valid_abn()
        assert len(abn) == 11
        assert ABNValidator.validate_check_digit(abn)


class TestGSTCalculator:
    """Test Australian GST calculations."""

    def test_gst_components_calculation(self):
        """Test GST component calculations."""
        amount_inc_gst = Decimal("110.00")
        gst_calc = GSTCalculator.calculate_gst_components(amount_inc_gst, GSTCode.GST)

        assert gst_calc.gst_inclusive_amount == amount_inc_gst
        assert gst_calc.gst_exclusive_amount == Decimal("100.00")
        assert gst_calc.gst_amount == Decimal("10.00")
        assert gst_calc.gst_rate == Decimal("0.10")

    def test_gst_free_calculation(self):
        """Test GST-free item calculations."""
        amount = Decimal("100.00")
        gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.GST_FREE)

        assert gst_calc.gst_inclusive_amount == amount
        assert gst_calc.gst_exclusive_amount == amount
        assert gst_calc.gst_amount == Decimal("0.00")
        assert gst_calc.gst_rate == Decimal("0.00")

    def test_gst_rounding(self):
        """Test Australian GST rounding rules."""
        amount = Decimal("104.99")
        gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.GST)

        # GST should be rounded to nearest cent
        expected_gst = (amount * Decimal("1")) / Decimal("11")
        rounded_gst = expected_gst.quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")

        assert gst_calc.gst_amount == rounded_gst

    def test_gst_validation(self):
        """Test GST calculation validation."""
        inc_gst = Decimal("110.00")
        ex_gst = Decimal("100.00")
        gst_amount = Decimal("10.00")

        assert GSTCalculator.validate_gst_calculation(inc_gst, ex_gst, gst_amount)

        # Test invalid calculation
        invalid_gst = Decimal("15.00")
        assert not GSTCalculator.validate_gst_calculation(inc_gst, ex_gst, invalid_gst)


class TestAustralianCompliance:
    """Test Australian business compliance validation."""

    def test_state_postcode_validation(self):
        """Test Australian state-postcode validation."""
        from aus_pos_data_gen.validators import AustralianAddressValidator

        # Valid NSW postcode
        assert AustralianAddressValidator.validate_postcode_state("2000", "NSW")

        # Invalid postcode for state
        assert not AustralianAddressValidator.validate_postcode_state("3000", "NSW")  # 3000 is VIC

        # Invalid postcode format
        assert not AustralianAddressValidator.validate_postcode_state("200", "NSW")  # Too short
        assert not AustralianAddressValidator.validate_postcode_state("200000", "NSW")  # Too long
