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
    # Map by CUSIP (or issuer+class if CUSIP missing, but CUSIP is standard)
    prev_map = {h.cusip: h for h in prev_holdings}
    curr_map = {h.cusip: h for h in current_holdings}

    result = {
        "metadata": {
            "current": {
                "year": year,
                "quarter": quarter,
                "filing_date": current_filing.filing_date,
            },
            "previous": {
                "year": prev_year,
                "quarter": prev_quarter,
                "filing_date": prev_filing.filing_date if prev_filing else None,
            },
        },
        "holdings": [],
        "stats": {
            "total_value": sum(h.value_usd for h in current_holdings),
            "total_count": len(current_holdings),
            "new_count": 0,
            "increased_count": 0,
            "decreased_count": 0,
            "sold_count": 0,
        },
    }

    # Process Current Holdings (New, Increased, Decreased, Unchanged)
    for cusip, curr_h in curr_map.items():
        prev_h = prev_map.get(cusip)

        item = {
            "issuer": curr_h.issuer_name,
            "class": curr_h.title_of_class,
            "cusip": curr_h.cusip,
            "value": curr_h.value_usd,
            "shares": curr_h.shares_amount,
            "put_call": curr_h.put_call,
            "change_type": "unchanged",
            "shares_change": 0,
        }

        if not prev_h:
            item["change_type"] = "new"
            item["shares_change"] = curr_h.shares_amount
            result["stats"]["new_count"] += 1
        else:
            diff = curr_h.shares_amount - prev_h.shares_amount
            item["shares_change"] = diff
            if diff > 0:
                item["change_type"] = "increased"
                result["stats"]["increased_count"] += 1
            elif diff < 0:
                item["change_type"] = "decreased"
                result["stats"]["decreased_count"] += 1
            # else unchanged

        result["holdings"].append(item)

    # Process Sold Out (In Prev but not in Curr)
    for cusip, prev_h in prev_map.items():
        if cusip not in curr_map:
            item = {
                "issuer": prev_h.issuer_name,
                "class": prev_h.title_of_class,
                "cusip": prev_h.cusip,
                "value": 0,
                "shares": 0,
                "put_call": prev_h.put_call,
                "change_type": "sold",
                "shares_change": -prev_h.shares_amount,
            }
            result["holdings"].append(item)
            result["stats"]["sold_count"] += 1

    return result
