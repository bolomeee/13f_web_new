from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class Quarter(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class FilingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FilingBase(SQLModel):
    cik: str = Field(index=True)
    company_name: str
    year: int
    quarter: Quarter
    filing_date: Optional[date] = None


class Filing(FilingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Internal tracking
    status: FilingStatus = Field(default=FilingStatus.PENDING)
    raw_file_path: Optional[str] = None
    processed_file_path: Optional[str] = None
    error_message: Optional[str] = None

    # Relationships
    holdings: List["Holding"] = Relationship(back_populates="filing")


class HoldingBase(SQLModel):
    issuer_name: str
    title_of_class: str
    cusip: str = Field(index=True)
    value_usd: float
    shares_amount: float
    shares_type: str = "SH"  # SH or PRN
    put_call: Optional[str] = None  # PUT, CALL, or None
    investment_discretion: str


class Holding(HoldingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filing_id: int = Field(foreign_key="filing.id")

    filing: Filing = Relationship(back_populates="holdings")


class FilingCreate(FilingBase):
    pass


class FilingRead(FilingBase):
    id: int
    created_at: datetime
    status: FilingStatus
