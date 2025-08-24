"""
Pydantic models for Australian POS data structures.

All models include validation and Australian business compliance
rules including GST calculations, ABN validation, and proper formatting.
"""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from .config import GSTConfiguration


class PaymentMethod(str, Enum):
    """Australian payment methods."""

    CASH = "CASH"
    EFTPOS = "EFTPOS"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    CONTACTLESS = "CONTACTLESS"
    GIFT_CARD = "GIFT_CARD"
    AFTERPAY = "AFTERPAY"
    ZIP = "ZIP"
    BUY_NOW_PAY_LATER = "BUY_NOW_PAY_LATER"


class GSTCode(str, Enum):
    """Australian GST codes."""

    GST = "GST"
    GST_FREE = "GST_FREE"
    INPUT_TAXED = "INPUT_TAXED"
    GST_EXEMPT = "GST_EXEMPT"


class TransactionType(str, Enum):
    """Transaction types."""

    SALE = "SALE"
    RETURN = "RETURN"
    VOID = "VOID"
    EXCHANGE = "EXCHANGE"
    LAYBY = "LAYBY"


class ReturnReason(str, Enum):
    """Return reason codes."""

    DEFECTIVE = "DEFECTIVE"
    WRONG_SIZE = "WRONG_SIZE"
    WRONG_ITEM = "WRONG_ITEM"
    CHANGE_MIND = "CHANGE_MIND"
    DUPLICATE = "DUPLICATE"
    GIFT_RETURN = "GIFT_RETURN"
    WARRANTY = "WARRANTY"
    DAMAGED_SHIPPING = "DAMAGED_SHIPPING"


class AustralianState(str, Enum):
    """Australian states and territories."""

    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    WA = "WA"
    SA = "SA"
    TAS = "TAS"
    NT = "NT"
    ACT = "ACT"


class Customer(BaseModel):
    """Customer model with Australian address validation."""

    customer_id: str = Field(..., description="Unique customer identifier")
    customer_type: str = Field(..., description="INDIVIDUAL, BUSINESS, LOYALTY, STAFF")
    first_name: Optional[str] = Field(None, description="Customer first name")
    last_name: Optional[str] = Field(None, description="Customer last name")
    company_name: Optional[str] = Field(None, description="Company name for business customers")
    email: Optional[str] = Field(None, description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    date_of_birth: Optional[datetime] = Field(None, description="Customer date of birth")
    loyalty_member: bool = Field(default=False, description="Loyalty program member")
    loyalty_points_earned: int = Field(default=0, description="Points earned")
    loyalty_points_redeemed: int = Field(default=0, description="Points redeemed")
    address: Optional[str] = Field(None, description="Street address")
    suburb: Optional[str] = Field(None, description="Suburb")
    state: Optional[AustralianState] = Field(None, description="State")
    postcode: Optional[str] = Field(None, description="Postcode")
    customer_abn: Optional[str] = Field(None, description="ABN for business customers")

    @validator("customer_abn")
    def validate_customer_abn(cls, v, values):
        """Validate customer ABN for business customers."""
        if values.get("customer_type") == "BUSINESS" and v is None:
            raise ValueError("Business customers must have an ABN")
        return v

    @validator("postcode")
    def validate_postcode(cls, v, values):
        """Validate postcode format for Australian addresses."""
        if v is not None:
            if not v.isdigit() or len(v) != 4:
                raise ValueError("Australian postcodes must be 4 digits")
        return v

    class Config:
        use_enum_values = True


class Business(BaseModel):
    """Business/store model with Australian business validation."""

    store_id: str = Field(..., description="Unique store identifier")
    business_name: str = Field(..., description="Registered business name")
    abn: str = Field(..., description="Australian Business Number")
    acn: Optional[str] = Field(None, description="Australian Company Number")
    trading_name: Optional[str] = Field(None, description="Trading name if different")
    store_address: str = Field(..., description="Store street address")
    suburb: str = Field(..., description="Suburb")
    state: AustralianState = Field(..., description="State")
    postcode: str = Field(..., description="Postcode")
    phone: str = Field(..., description="Business phone")
    email: str = Field(..., description="Business email")
    gst_registered: bool = Field(default=True, description="GST registration status")
    pos_system_type: str = Field(default="Square", description="POS system type")
    terminal_count: int = Field(default=1, description="Number of POS terminals")

    @validator("abn")
    def validate_abn_format(cls, v):
        """Validate ABN format (11 digits)."""
        if len(v.replace(" ", "")) != 11:
            raise ValueError("ABN must be 11 digits")
        return v

    @validator("acn")
    def validate_acn_format(cls, v):
        """Validate ACN format if provided (9 digits)."""
        if v is not None and len(v.replace(" ", "")) != 9:
            raise ValueError("ACN must be 9 digits")
        return v

    @validator("postcode")
    def validate_postcode(cls, v):
        """Validate Australian postcode."""
        if not v.isdigit() or len(v) != 4:
            raise ValueError("Postcode must be 4 digits")
        return v

    class Config:
        use_enum_values = True


class TransactionItem(BaseModel):
    """Individual line item in a transaction."""

    transaction_id: str = Field(..., description="Parent transaction ID")
    line_number: int = Field(..., description="Line item number")
    item_type: str = Field(default="SALE", description="SALE or RETURN")
    product_id: str = Field(..., description="Unique product identifier")
    sku: str = Field(..., description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, description="Product barcode")
    product_name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    quantity: Decimal = Field(..., description="Quantity sold")
    unit_price_ex_gst: Decimal = Field(..., description="Unit price excluding GST")
    unit_price_inc_gst: Decimal = Field(..., description="Unit price including GST")
    line_subtotal_ex_gst: Decimal = Field(..., description="Line subtotal excluding GST")
    line_gst_amount: Decimal = Field(..., description="GST amount for this line")
    line_total_inc_gst: Decimal = Field(..., description="Line total including GST")
    gst_code: GSTCode = Field(..., description="GST classification")
    discount_amount: Decimal = Field(default=Decimal("0.00"), description="Discount amount")
    discount_type: str = Field(default="NONE", description="Discount type")
    promotion_id: Optional[str] = Field(None, description="Promotion identifier")

    @validator("quantity")
    def validate_quantity(cls, v):
        """Ensure quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    @validator("unit_price_ex_gst", "unit_price_inc_gst")
    def validate_prices(cls, v):
        """Ensure prices are non-negative."""
        if v < 0:
            raise ValueError("Prices cannot be negative")
        return v

    class Config:
        use_enum_values = True


class Transaction(BaseModel):
    """Main transaction model with Australian compliance."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    store_id: str = Field(..., description="Store identifier")
    workstation_id: str = Field(..., description="POS terminal identifier")
    employee_id: str = Field(..., description="Employee processing transaction")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    business_day_date: datetime = Field(..., description="Business day date")
    transaction_datetime: datetime = Field(..., description="Transaction timestamp")
    sequence_number: int = Field(..., description="Sequential transaction number")
    receipt_number: str = Field(..., description="Receipt number")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    subtotal_ex_gst: Decimal = Field(..., description="Subtotal excluding GST")
    gst_amount: Decimal = Field(..., description="Total GST amount")
    total_inc_gst: Decimal = Field(..., description="Total including GST")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    tender_amount: Decimal = Field(..., description="Amount tendered")
    change_amount: Decimal = Field(default=Decimal("0.00"), description="Change given")
    currency_code: str = Field(default="AUD", description="Currency code")
    operator_id: str = Field(..., description="POS operator identifier")
    shift_id: str = Field(..., description="Work shift identifier")
    business_abn: str = Field(..., description="Business ABN")
    items: List[TransactionItem] = Field(default_factory=list, description="Transaction line items")

    @validator("total_inc_gst")
    def validate_total_amount(cls, v):
        """Ensure total is reasonable."""
        if v <= 0:
            raise ValueError("Total amount must be positive")
        return v

    @validator("tender_amount")
    def validate_tender_amount(cls, v, values):
        """Ensure tender amount is sufficient."""
        total = values.get("total_inc_gst")
        if total is not None and v < total:
            raise ValueError("Tender amount must be at least the total amount")
        return v

    @validator("change_amount")
    def calculate_change_amount(cls, v, values):
        """Calculate change amount automatically."""
        tender = values.get("tender_amount")
        total = values.get("total_inc_gst")
        if tender is not None and total is not None:
            calculated_change = tender - total
            if v != calculated_change:
                return calculated_change
        return v

    class Config:
        use_enum_values = True


class ReturnTransaction(BaseModel):
    """Return transaction model."""

    return_id: str = Field(..., description="Unique return identifier")
    original_transaction_id: str = Field(..., description="Original transaction ID")
    original_receipt_number: str = Field(..., description="Original receipt number")
    return_date: datetime = Field(..., description="Return date")
    return_time: datetime = Field(..., description="Return time")
    return_reason_code: ReturnReason = Field(..., description="Return reason code")
    return_reason_description: str = Field(..., description="Return reason description")
    returned_by_customer_id: Optional[str] = Field(None, description="Customer ID")
    processed_by_employee_id: str = Field(..., description="Employee processing return")
    refund_method: PaymentMethod = Field(..., description="Refund method")
    refund_amount: Decimal = Field(..., description="Refund amount")
    store_credit_issued: Decimal = Field(default=Decimal("0.00"), description="Store credit issued")
    restocking_fee: Decimal = Field(default=Decimal("0.00"), description="Restocking fee")
    condition_code: str = Field(default="NEW", description="Item condition")
    original_purchase_date: Optional[datetime] = Field(None, description="Original purchase date")

    @validator("refund_amount")
    def validate_refund_amount(cls, v):
        """Ensure refund amount is positive."""
        if v <= 0:
            raise ValueError("Refund amount must be positive")
        return v

    class Config:
        use_enum_values = True


class GSTCalculation(BaseModel):
    """GST calculation result."""

    gst_inclusive_amount: Decimal = Field(..., description="Amount including GST")
    gst_exclusive_amount: Decimal = Field(..., description="Amount excluding GST")
    gst_amount: Decimal = Field(..., description="GST component")
    gst_rate: Decimal = Field(default=Decimal("0.10"), description="GST rate")
    gst_code: GSTCode = Field(..., description="GST classification")

    @classmethod
    def calculate_gst(cls, amount_inc_gst: Decimal, gst_code: GSTCode) -> "GSTCalculation":
        """Calculate GST components using Australian rules."""
        if gst_code == GSTCode.GST_FREE:
            return cls(
                gst_inclusive_amount=amount_inc_gst,
                gst_exclusive_amount=amount_inc_gst,
                gst_amount=Decimal("0.00"),
                gst_rate=Decimal("0.00"),
                gst_code=gst_code,
            )

        if gst_code == GSTCode.GST:
            # GST Amount = (GST-Inclusive Price × 1) ÷ 11
            gst_amount = (amount_inc_gst * Decimal("1")) / Decimal("11")
            # Round to nearest cent (0.5 rounds up)
            gst_amount = gst_amount.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            gst_exclusive = amount_inc_gst - gst_amount

            return cls(
                gst_inclusive_amount=amount_inc_gst,
                gst_exclusive_amount=gst_exclusive,
                gst_amount=gst_amount,
                gst_rate=Decimal("0.10"),
                gst_code=gst_code,
            )

        # For INPUT_TAXED and GST_EXEMPT, treat as GST-free
        return cls(
            gst_inclusive_amount=amount_inc_gst,
            gst_exclusive_amount=amount_inc_gst,
            gst_amount=Decimal("0.00"),
            gst_rate=Decimal("0.00"),
            gst_code=gst_code,
        )
