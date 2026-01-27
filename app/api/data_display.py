from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from app.core.database import get_session
from app.models.filing import Filing, Holding, Quarter

router = APIRouter()


@router.get("/companies")
async def get_companies(session: Session = Depends(get_session)):
    """Get list of unique companies with available data."""
    # Group by CIK to get unique companies
    statement = select(Filing.cik, Filing.company_name).distinct()
    results = session.exec(statement).all()

    companies = []
    seen_ciks = set()
    for cik, name in results:
        if cik not in seen_ciks:
            companies.append({"cik": cik, "name": name})
            seen_ciks.add(cik)

    return companies


@router.get("/comparison")
async def get_comparison_data(
    cik: str, year: int, quarter: Quarter, session: Session = Depends(get_session)
):
    """
    Get comparing data between selected quarter and previous quarter.
    """
    # 1. Get Current Filing
    stmt = select(Filing).where(
        Filing.cik == cik,
        Filing.year == year,
        Filing.quarter == quarter,
        Filing.status == "completed",
    )
    current_filing = session.exec(stmt).first()

    if not current_filing:
        raise HTTPException(status_code=404, detail="Current filing not found")

    # 2. Determine Previous Quarter
    prev_year = year
    if quarter == Quarter.Q1:
        prev_quarter = Quarter.Q4
        prev_year = year - 1
    elif quarter == Quarter.Q2:
        prev_quarter = Quarter.Q1
    elif quarter == Quarter.Q3:
        prev_quarter = Quarter.Q2
    else:  # Q4
        prev_quarter = Quarter.Q3

    # 3. Get Previous Filing
    stmt_prev = select(Filing).where(
        Filing.cik == cik,
        Filing.year == prev_year,
        Filing.quarter == prev_quarter,
        Filing.status == "completed",
    )
    prev_filing = session.exec(stmt_prev).first()

    # 4. Fetch Holdings
    current_holdings = session.exec(
        select(Holding).where(Holding.filing_id == current_filing.id)
    ).all()
    prev_holdings = []
    if prev_filing:
        prev_holdings = session.exec(
            select(Holding).where(Holding.filing_id == prev_filing.id)
        ).all()

    # 5. Compare Logic
    # Compare Logic
    prev_map = {h.cusip: h for h in prev_holdings}
    curr_map = {h.cusip: h for h in current_holdings}

    # Lists for analysis
    increased_list = []
    decreased_list = []
    call_list = []
    put_list = []

    # Process Current Holdings
    for cusip, curr_h in curr_map.items():
        prev_h = prev_map.get(cusip)

        # Options check
        if curr_h.put_call == "CALL":
            call_list.append(curr_h)
        elif curr_h.put_call == "PUT":
            put_list.append(curr_h)

        # Change check
        change_pct = 0.0
        diff = 0
        if prev_h:
            diff = curr_h.shares_amount - prev_h.shares_amount
            if prev_h.shares_amount > 0:
                change_pct = (diff / prev_h.shares_amount) * 100
            else:
                change_pct = 100.0  # Treat new from 0 as 100%? Or handle separately?
        else:
            diff = curr_h.shares_amount
            change_pct = 100.0  # New position

        # Only track significant changes for main lists
        # Filter out options from main change lists if needed? usually strictly equity.
        # But for now assume all.
        # Note: Options might have huge % swings.

        if diff > 0:
            increased_list.append(
                {
                    "issuer": curr_h.issuer_name,
                    "ticker": curr_h.issuer_name,  # User requested Company Name in bold
                    "change_pct": change_pct,
                }
            )
        elif diff < 0:
            decreased_list.append(
                {
                    "issuer": curr_h.issuer_name,
                    "ticker": curr_h.issuer_name,  # User requested Company Name in bold
                    "change_pct": change_pct,
                }
            )

    # Sort Lists
    # Top 10 Increased
    increased_list.sort(key=lambda x: x["change_pct"], reverse=True)
    top_increased = increased_list[:10]

    # Top 10 Decreased (most negative first)
    decreased_list.sort(key=lambda x: x["change_pct"])
    top_decreased = decreased_list[:10]

    # Top 10 Calls (Value)
    call_list.sort(key=lambda x: x.value_usd, reverse=True)
    top_calls = [
        {"issuer": h.issuer_name, "ticker": h.issuer_name, "value": h.value_usd}
        for h in call_list[:10]
    ]

    # Top 10 Puts (Value)
    put_list.sort(key=lambda x: x.value_usd, reverse=True)
    top_puts = [
        {"issuer": h.issuer_name, "ticker": h.issuer_name, "value": h.value_usd}
        for h in put_list[:10]
    ]

    return {
        "metadata": {
            "current": {"year": year, "quarter": quarter},
            "previous": {"year": prev_year, "quarter": prev_quarter},
        },
        "analysis": {
            "top_increased": top_increased,
            "top_decreased": top_decreased,
            "top_calls": top_calls,
            "top_puts": top_puts,
        },
    }
