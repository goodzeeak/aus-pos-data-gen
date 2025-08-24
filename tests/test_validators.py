"""
Comprehensive tests for Australian business validators.

Tests ABN validation, GST calculations, address validation, business hours,
and Australian business compliance validation following ATO requirements.
"""

import pytest
import re
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from aus_pos_data_gen.validators import (
    ABNValidator,
    GSTCalculator,
    AustralianAddressValidator,
    BusinessHoursValidator,
    ReceiptValidator
)
from aus_pos_data_gen.models import GSTCode


class TestABNValidator:
    """Test Australian Business Number validation."""

    def test_valid_abn_format(self):
        """Test ABN format validation."""
        # Valid formats with spaces
        valid_abns = [
            "12 345 678 901",
            "83 914 571 673",
            "12 345 678 901"
        ]
        for abn in valid_abns:
            assert ABNValidator.validate_format(abn)

        # Valid formats without spaces
        valid_abns_no_spaces = [
            "12345678901",
            "83914571673",
            "98765432109"
        ]
        for abn in valid_abns_no_spaces:
            assert ABNValidator.validate_format(abn)

        # Invalid formats - too short
        invalid_abns_short = ["123456789", "12345678", "123"]
        for abn in invalid_abns_short:
            assert not ABNValidator.validate_format(abn)

        # Invalid formats - too long
        invalid_abns_long = ["123456789012", "12345678901111"]
        for abn in invalid_abns_long:
            assert not ABNValidator.validate_format(abn)

        # Invalid formats - non-digits
        invalid_abns_chars = ["12-345-678-901", "1234567890A", "ABCDEFGHIJK", "12 34A 67B 90C"]
        for abn in invalid_abns_chars:
            assert not ABNValidator.validate_format(abn)

    def test_abn_check_digit(self):
        """Test ABN check digit validation."""
        # Known valid ABNs
        valid_abns = [
            "83 914 571 673",  # Known valid ABN
            "83914571673",     # Same without spaces
        ]
        for abn in valid_abns:
            assert ABNValidator.validate_check_digit(abn)

        # Generate a few more valid ABNs for testing
        for _ in range(3):
            valid_abn = ABNValidator.generate_valid_abn()
        assert ABNValidator.validate_check_digit(valid_abn)

        # Known invalid ABNs (wrong check digit)
        invalid_abns = [
            "12 345 678 900",
            "83 914 571 670",
            "12345678900"
        ]
        for abn in invalid_abns:
            assert not ABNValidator.validate_check_digit(abn)

    def test_complete_abn_validation(self):
        """Test complete ABN validation with error messages."""
        # Valid ABN
        valid_abn = "83 914 571 673"
        is_valid, message = ABNValidator.validate_abn(valid_abn)
        assert is_valid == True
        assert message == "Valid ABN"

        # Invalid format
        invalid_format = "123456789"
        is_valid, message = ABNValidator.validate_abn(invalid_format)
        assert is_valid == False
        assert "11 digits" in message

        # Invalid check digit
        invalid_check = "12 345 678 900"
        is_valid, message = ABNValidator.validate_abn(invalid_check)
        assert is_valid == False
        assert "check digit" in message

    def test_abn_formatting(self):
        """Test ABN formatting."""
        test_cases = [
            ("83914571673", "83 914 571 673"),
            ("12345678901", "12 345 678 901"),
            ("98765432109", "98 765 432 109"),
            ("11111111111", "11 111 111 111")
        ]

        for raw_abn, expected_formatted in test_cases:
            formatted = ABNValidator.format_abn(raw_abn)
            assert formatted == expected_formatted
            assert len(formatted) == 14  # XX XXX XXX XXX format

    def test_generate_valid_abn(self):
        """Test generation of valid ABN."""
        # Generate multiple ABNs to ensure consistency
        for _ in range(10):
            abn = ABNValidator.generate_valid_abn()
            assert len(abn) == 11
            assert abn.isdigit()
            assert ABNValidator.validate_check_digit(abn)
            assert ABNValidator.validate_format(abn)

    def test_generate_valid_abn_max_attempts(self):
        """Test ABN generation with max attempts."""
        # This should work within reasonable attempts
        abn = ABNValidator.generate_valid_abn(max_attempts=1000)
        assert len(abn) == 11
        assert ABNValidator.validate_check_digit(abn)

    def test_generate_valid_abn_failure(self):
        """Test ABN generation failure when max attempts exceeded."""
        # Mock a scenario where generation always fails (though unlikely in practice)
        with pytest.raises(ValueError) as exc_info:
            ABNValidator.generate_valid_abn(max_attempts=1)  # Very low attempts

        assert "Could not generate valid ABN" in str(exc_info.value)


class TestGSTCalculator:
    """Test Australian GST calculations."""

    def test_gst_components_calculation_standard(self):
        """Test standard GST component calculations."""
        test_cases = [
            (Decimal("110.00"), Decimal("100.00"), Decimal("10.00")),
            (Decimal("121.00"), Decimal("110.00"), Decimal("11.00")),
            (Decimal("115.50"), Decimal("105.00"), Decimal("10.50")),
            (Decimal("1000.00"), Decimal("909.09"), Decimal("90.91")),
        ]

        for amount_inc_gst, expected_ex_gst, expected_gst in test_cases:
            gst_calc = GSTCalculator.calculate_gst_components(amount_inc_gst, GSTCode.GST)

            assert gst_calc.gst_inclusive_amount == amount_inc_gst
            assert gst_calc.gst_exclusive_amount == expected_ex_gst
            assert gst_calc.gst_amount == expected_gst
            assert gst_calc.gst_rate == Decimal("0.10")
            assert gst_calc.gst_code == GSTCode.GST

    def test_gst_free_calculation(self):
        """Test GST-free item calculations."""
        test_amounts = [Decimal("100.00"), Decimal("50.00"), Decimal("999.99")]

        for amount in test_amounts:
            gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.GST_FREE)

            assert gst_calc.gst_inclusive_amount == amount
            assert gst_calc.gst_exclusive_amount == amount
            assert gst_calc.gst_amount == Decimal("0.00")
            assert gst_calc.gst_rate == Decimal("0.00")
            assert gst_calc.gst_code == GSTCode.GST_FREE

    def test_input_taxed_calculation(self):
        """Test input-taxed item calculations."""
        test_amounts = [Decimal("200.00"), Decimal("75.50"), Decimal("1500.00")]

        for amount in test_amounts:
            gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.INPUT_TAXED)

            assert gst_calc.gst_inclusive_amount == amount
            assert gst_calc.gst_exclusive_amount == amount
            assert gst_calc.gst_amount == Decimal("0.00")
            assert gst_calc.gst_rate == Decimal("0.00")
            assert gst_calc.gst_code == GSTCode.INPUT_TAXED

    def test_gst_exempt_calculation(self):
        """Test GST-exempt item calculations."""
        test_amounts = [Decimal("300.00"), Decimal("42.99"), Decimal("800.00")]

        for amount in test_amounts:
            gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.GST_EXEMPT)

            assert gst_calc.gst_inclusive_amount == amount
            assert gst_calc.gst_exclusive_amount == amount
            assert gst_calc.gst_amount == Decimal("0.00")
            assert gst_calc.gst_rate == Decimal("0.00")
            assert gst_calc.gst_code == GSTCode.GST_EXEMPT

    def test_gst_rounding_precision(self):
        """Test Australian GST rounding rules and precision."""
        test_cases = [
            # (input, expected_gst, expected_ex_gst)
            (Decimal("115.00"), Decimal("10.45"), Decimal("104.55")),
            (Decimal("104.99"), Decimal("9.54"), Decimal("95.45")),
            (Decimal("101.00"), Decimal("9.18"), Decimal("91.82")),
            (Decimal("199.99"), Decimal("18.18"), Decimal("181.81")),
        ]

        for amount_inc_gst, expected_gst, expected_ex_gst in test_cases:
            gst_calc = GSTCalculator.calculate_gst_components(amount_inc_gst, GSTCode.GST)

            assert gst_calc.gst_amount == expected_gst
            assert gst_calc.gst_exclusive_amount == expected_ex_gst
            assert gst_calc.gst_inclusive_amount == amount_inc_gst

            # Verify mathematical correctness
            assert abs((gst_calc.gst_exclusive_amount + gst_calc.gst_amount) - gst_calc.gst_inclusive_amount) < Decimal("0.01")

    def test_gst_rounding_half_up(self):
        """Test rounding to nearest cent (half-up rule)."""
        # Test cases that should round up
        amount = Decimal("104.995")  # Should round to 105.00
        gst_calc = GSTCalculator.calculate_gst_components(amount, GSTCode.GST)

        expected_gst = Decimal("9.55")  # 104.995 / 11 = 9.545 rounds to 9.55
        assert gst_calc.gst_amount == expected_gst

    def test_gst_validation(self):
        """Test GST calculation validation."""
        # Valid calculations
        valid_cases = [
            (Decimal("110.00"), Decimal("100.00"), Decimal("10.00")),
            (Decimal("121.00"), Decimal("110.00"), Decimal("11.00")),
            (Decimal("1000.00"), Decimal("909.09"), Decimal("90.91")),
        ]

        for inc_gst, ex_gst, gst_amount in valid_cases:
            assert GSTCalculator.validate_gst_calculation(inc_gst, ex_gst, gst_amount)

        # Invalid calculations
        invalid_cases = [
            (Decimal("110.00"), Decimal("100.00"), Decimal("15.00")),  # GST too high
            (Decimal("121.00"), Decimal("100.00"), Decimal("11.00")),  # EX GST wrong
            (Decimal("1000.00"), Decimal("909.09"), Decimal("100.00")), # GST too high
        ]

        for inc_gst, ex_gst, gst_amount in invalid_cases:
            assert not GSTCalculator.validate_gst_calculation(inc_gst, ex_gst, gst_amount)

    def test_calculate_gst_exclusive(self):
        """Test GST-exclusive amount calculation from GST-inclusive."""
        test_cases = [
            (Decimal("110.00"), Decimal("100.00")),
            (Decimal("121.00"), Decimal("110.00")),
            (Decimal("115.00"), Decimal("104.55")),
        ]

        for inc_gst, expected_ex_gst in test_cases:
            result = GSTCalculator.calculate_gst_exclusive(inc_gst)
            assert result == expected_ex_gst

    def test_calculate_gst_amount(self):
        """Test GST amount calculation from GST-inclusive."""
        test_cases = [
            (Decimal("110.00"), Decimal("10.00")),
            (Decimal("121.00"), Decimal("11.00")),
            (Decimal("115.00"), Decimal("10.45")),
        ]

        for inc_gst, expected_gst in test_cases:
            result = GSTCalculator.calculate_gst_amount(inc_gst)
            assert result == expected_gst

    def test_calculate_gst_inclusive(self):
        """Test GST-inclusive amount calculation from GST-exclusive."""
        test_cases = [
            (Decimal("100.00"), Decimal("110.00"), Decimal("10.00")),
            (Decimal("110.00"), Decimal("121.00"), Decimal("11.00")),
            (Decimal("200.00"), Decimal("220.00"), Decimal("20.00")),
        ]

        for ex_gst, expected_inc_gst, expected_gst in test_cases:
            inc_gst, gst_amount = GSTCalculator.calculate_gst_inclusive(ex_gst)
            assert inc_gst == expected_inc_gst
            assert gst_amount == expected_gst

    def test_round_to_nearest_cent(self):
        """Test rounding to nearest cent."""
        test_cases = [
            (Decimal("10.001"), Decimal("10.00")),
            (Decimal("10.005"), Decimal("10.01")),
            (Decimal("10.004"), Decimal("10.00")),
            (Decimal("10.994"), Decimal("10.99")),
            (Decimal("10.995"), Decimal("11.00")),
        ]

        for input_amount, expected_rounded in test_cases:
            result = GSTCalculator.round_to_nearest_cent(input_amount)
            assert result == expected_rounded


class TestAustralianAddressValidator:
    """Test Australian address validation."""

    def test_postcode_state_validation(self):
        """Test Australian state-postcode validation."""
        # Valid combinations
        valid_combinations = [
            ("2000", "NSW"), ("3000", "VIC"), ("4000", "QLD"),
            ("5000", "SA"), ("6000", "WA"), ("7000", "TAS"),
            ("0800", "NT"), ("0260", "ACT")  # ACT postcodes are 200-299
        ]

        for postcode, state in valid_combinations:
            assert AustralianAddressValidator.validate_postcode_state(postcode, state)

        # Invalid combinations - wrong state for postcode
        invalid_combinations = [
            ("3000", "NSW"),  # 3000 is VIC, not NSW
            ("2000", "VIC"),  # 2000 is NSW, not VIC
            ("4000", "WA"),   # 4000 is QLD, not WA
            ("5000", "NT"),   # 5000 is SA, not NT
        ]

        for postcode, state in invalid_combinations:
            assert not AustralianAddressValidator.validate_postcode_state(postcode, state)

        # Invalid postcode formats
        invalid_postcodes = [
            ("200", "NSW"),     # Too short
            ("200000", "NSW"),  # Too long
            ("ABCD", "NSW"),    # Non-digits
            ("20A0", "NSW"),    # Contains letter
        ]

        for postcode, state in invalid_postcodes:
            assert not AustralianAddressValidator.validate_postcode_state(postcode, state)

    def test_format_address(self):
        """Test Australian address formatting."""
        test_cases = [
            (
                {
                    "street_address": "123 Main Street",
                    "suburb": "Sydney",
                    "state": "NSW",
                    "postcode": "2000"
                },
                "123 Main Street, Sydney, NSW 2000"
            ),
            (
                {
                    "street_address": "45 Business Ave",
                    "suburb": "Melbourne",
                    "state": "VIC",
                    "postcode": "3000"
                },
                "45 Business Ave, Melbourne, VIC 3000"
            ),
            (
                {
                    "street_address": "Unit 5, 789 Commercial Rd",
                    "suburb": "Brisbane",
                    "state": "QLD",
                    "postcode": "4000"
                },
                "Unit 5, 789 Commercial Rd, Brisbane, QLD 4000"
            ),
        ]

        for address_dict, expected_formatted in test_cases:
            result = AustralianAddressValidator.format_address(address_dict)
            assert result == expected_formatted

    def test_format_address_missing_fields(self):
        """Test address formatting with missing fields."""
        test_cases = [
            (
                {"street_address": "123 Main Street", "suburb": "Sydney"},
                "123 Main Street, Sydney"
            ),
            (
                {"suburb": "Sydney", "state": "NSW", "postcode": "2000"},
                "Sydney, NSW 2000"
            ),
            (
                {"street_address": "", "suburb": "Sydney", "state": "NSW", "postcode": "2000"},
                "Sydney, NSW 2000"
            ),
        ]

        for address_dict, expected_formatted in test_cases:
            result = AustralianAddressValidator.format_address(address_dict)
            assert result == expected_formatted


class TestBusinessHoursValidator:
    """Test Australian business hours validation."""

    def test_is_business_hours_weekday(self):
        """Test business hours validation for weekdays."""
        # Create weekday datetime (Monday)
        monday = datetime(2023, 10, 16, 9, 0, 0)  # Monday 9:00 AM
        assert BusinessHoursValidator.is_business_hours(monday, is_weekend=False)

        monday_afternoon = datetime(2023, 10, 16, 14, 0, 0)  # Monday 2:00 PM
        assert BusinessHoursValidator.is_business_hours(monday_afternoon, is_weekend=False)

        monday_early = datetime(2023, 10, 16, 8, 0, 0)  # Monday 8:00 AM (too early)
        assert not BusinessHoursValidator.is_business_hours(monday_early, is_weekend=False)

        monday_late = datetime(2023, 10, 16, 18, 0, 0)  # Monday 6:00 PM (too late)
        assert not BusinessHoursValidator.is_business_hours(monday_late, is_weekend=False)

    def test_is_business_hours_weekend(self):
        """Test business hours validation for weekends."""
        # Create weekend datetime (Saturday)
        saturday = datetime(2023, 10, 14, 11, 0, 0)  # Saturday 11:00 AM
        assert BusinessHoursValidator.is_business_hours(saturday, is_weekend=True)

        saturday_afternoon = datetime(2023, 10, 14, 15, 0, 0)  # Saturday 3:00 PM
        assert BusinessHoursValidator.is_business_hours(saturday_afternoon, is_weekend=True)

        saturday_early = datetime(2023, 10, 14, 9, 0, 0)  # Saturday 9:00 AM (too early)
        assert not BusinessHoursValidator.is_business_hours(saturday_early, is_weekend=True)

        saturday_late = datetime(2023, 10, 14, 17, 0, 0)  # Saturday 5:00 PM (too late)
        assert not BusinessHoursValidator.is_business_hours(saturday_late, is_weekend=True)

    def test_is_peak_hour(self):
        """Test peak hour identification."""
        # Peak hours should be 12-14 (lunch) and 17-19 (after work)
        peak_hours = [
            datetime(2023, 10, 16, 12, 30, 0),  # Lunch time
            datetime(2023, 10, 16, 13, 45, 0),  # Lunch time
            datetime(2023, 10, 16, 17, 15, 0),  # After work
            datetime(2023, 10, 16, 18, 30, 0),  # After work
        ]

        for dt in peak_hours:
            assert BusinessHoursValidator.is_peak_hour(dt)

        # Non-peak hours
        non_peak_hours = [
            datetime(2023, 10, 16, 9, 0, 0),   # Morning
            datetime(2023, 10, 16, 11, 0, 0),  # Mid-morning
            datetime(2023, 10, 16, 15, 0, 0),  # Afternoon
            datetime(2023, 10, 16, 20, 0, 0),  # Evening
        ]

        for dt in non_peak_hours:
            assert not BusinessHoursValidator.is_peak_hour(dt)


class TestReceiptValidator:
    """Test receipt format and compliance validation."""

    def test_validate_receipt_fields_under_75(self):
        """Test receipt validation for transactions under $75."""
        # Transaction under $75 doesn't require all fields
        transaction_data = {
            "total_inc_gst": 50.00,
            "transaction_datetime": datetime.now(),
            "receipt_number": "R001001"
        }

        is_valid, errors = ReceiptValidator.validate_receipt_fields(transaction_data)
        assert is_valid == True
        assert len(errors) == 0

    def test_validate_receipt_fields_over_75(self):
        """Test receipt validation for transactions over $75."""
        # Transaction over $75 requires specific fields
        valid_transaction = {
            "business_name": "Test Store Pty Ltd",
            "abn": "12345678901",
            "transaction_datetime": datetime.now(),
            "receipt_number": "R001001",
            "total_inc_gst": 150.00,
            "gst_amount": 13.64
        }

        is_valid, errors = ReceiptValidator.validate_receipt_fields(valid_transaction)
        assert is_valid == True
        assert len(errors) == 0

        # Missing required fields
        invalid_transaction = {
            "transaction_datetime": datetime.now(),
            "receipt_number": "R001001",
            "total_inc_gst": 150.00
        }

        is_valid, errors = ReceiptValidator.validate_receipt_fields(invalid_transaction)
        assert is_valid == False
        assert len(errors) > 0
        assert any("business_name" in error for error in errors)
        assert any("abn" in error for error in errors)

        # Missing GST breakdown
        no_gst_transaction = {
            "business_name": "Test Store Pty Ltd",
            "abn": "12345678901",
            "transaction_datetime": datetime.now(),
            "receipt_number": "R001001",
            "total_inc_gst": 150.00
        }

        is_valid, errors = ReceiptValidator.validate_receipt_fields(no_gst_transaction)
        assert is_valid == False
        assert any("GST breakdown" in error for error in errors)

    def test_generate_receipt_number(self):
        """Test receipt number generation."""
        store_id = "STORE001"
        sequence = 123

        receipt_number = ReceiptValidator.generate_receipt_number(store_id, sequence)
        # Format: STORE001-YYYYMMDD-123
        assert len(receipt_number) > 15  # Should be longer with date
        assert receipt_number.startswith("STORE001-")
        assert receipt_number.endswith("-123")

        # Should contain today's date
        from datetime import datetime
        today_str = datetime.now().strftime("%Y%m%d")
        assert today_str in receipt_number


class TestAustralianCompliance:
    """Test overall Australian business compliance validation."""

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
