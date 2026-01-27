import sys
import os
import logging
import pandas as pd
from datetime import datetime
from sqlmodel import Session
from app.models.filing import Filing, FilingStatus, Holding
from app.core.config import settings

# Add project root to sys path to ensure EDGAR imports work
sys.path.append(str(settings.BASE_DIR))

try:
    from EDGAR.edgar_downloader import EDGARReportDownloader
    from EDGAR.sec_13f_extractor import SEC13FExtractor
except ImportError as e:
    logging.error(f"Failed to import EDGAR modules: {e}")
    EDGARReportDownloader = None
    SEC13FExtractor = None

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class EdgarService:
    def __init__(self):
        # We initialize the downloader with the path to the config file in the EDGAR directory
        config_path = os.path.join(settings.EDGAR_DIR, "config.json")

        if EDGARReportDownloader:
            self.downloader = EDGARReportDownloader(config_path=config_path)
            # Setup paths to keep files organized within the EDGAR directory structure
            self.downloader.config["download_settings"]["download_directory"] = (
                os.path.join(settings.EDGAR_DIR, "SEC_Filings")
            )
            self.downloader.config["conversion_settings"]["json_output_directory"] = (
                os.path.join(settings.EDGAR_DIR, "JSON_Reports")
            )
            self.downloader.config["cache_settings"]["cache_file"] = os.path.join(
                settings.EDGAR_DIR, "ticker_cik_cache.json"
            )

            # Ensure directories exist
            os.makedirs(
                self.downloader.config["download_settings"]["download_directory"],
                exist_ok=True,
            )
            os.makedirs(
                self.downloader.config["conversion_settings"]["json_output_directory"],
                exist_ok=True,
            )
        else:
            self.downloader = None

        self.extractor = SEC13FExtractor() if SEC13FExtractor else None

    async def process_filing_task(self, filing_id: int, session: Session):
        """
        Background task to download and process a 13F filing.
        """
        filing = session.get(Filing, filing_id)
        if not filing:
            logger.error(f"Filing {filing_id} not found")
            return

        if not self.downloader:
            filing.status = FilingStatus.FAILED
            filing.error_message = "EDGAR Downloader not initialized"
            session.add(filing)
            session.commit()
            return

        filing.status = FilingStatus.PROCESSING
        session.add(filing)
        session.commit()

        try:
            logger.info(
                f"Starting actual download for {filing.company_name} ({filing.cik}) {filing.year} {filing.quarter}"
            )

            # 1. Search for the specific filing
            # Logic: We define 'Year' as the Report Year.
            # Q1 Report (due May): Filed in same year
            # Q2 Report (due Aug): Filed in same year
            # Q3 Report (due Nov): Filed in same year
            # Q4 Report (due Feb next year): Filed in year + 1

            search_start_year = filing.year
            search_end_year = filing.year + 1

            # Defines a helper to try finding a filing of a specific type
            def try_find_filing(form_type):
                f_list, f_comp_name = self.downloader._get_filings(
                    filing.cik, form_type, search_start_year, search_end_year
                )

                # Auto-update company name if available and needed
                if f_comp_name and f_comp_name != "Unknown":
                    # We update it in the outer scope's 'filing' object if needed
                    # checking logic inside the loop or just once is fine
                    pass

                match = self._find_matching_quarter_filing(
                    f_list, filing.year, filing.quarter
                )
                return match, f_list, f_comp_name

            # First try 13F-HR
            target_filing, filings_list, fetched_company_name = try_find_filing(
                "13F-HR"
            )

            # Update company name logic (moved here to apply for the first successful fetch)
            if fetched_company_name and fetched_company_name != "Unknown":
                if (
                    not filing.company_name
                    or filing.company_name == "Unknown Company"
                    or filing.company_name.isdigit()
                ):
                    filing.company_name = fetched_company_name
                    session.add(filing)
                    try:
                        session.commit()
                        logger.info(
                            f"Updated company name for {filing.cik} to: {filing.company_name}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to commit company name update: {e}")

            # If not found, try 13F-HR/A (Amendment)
            if not target_filing:
                logger.info("No 13F-HR found, trying 13F-HR/A...")
                target_filing, _, _ = try_find_filing("13F-HR/A")
                if target_filing:
                    target_filing["formType"] = (
                        "13F-HR/A"  # Ensure type is set for downloader
                    )
                else:
                    target_filing, _, _ = try_find_filing(
                        "13F-HR/A"
                    )  # Retry logic logic fix? No, just the variable name
                    pass

            if not target_filing:
                # Log available filings for debugging
                available_dates = [f.get("filingDate") for f in filings_list]
                logger.warning(
                    f"Failed to find filing for {filing.year} {filing.quarter}. "
                    f"Available 13F-HR dates in {search_start_year}-{search_end_year}: {available_dates}"
                )

                # Enhanced User Error Message
                if fetched_company_name and fetched_company_name != "Unknown":
                    raise Exception(
                        f"Successfully found entity '{fetched_company_name}' (CIK {filing.cik}), but NO 13F filings were found for {filing.year} {filing.quarter} (or amendments). "
                        "This often happens when using an Individual's CIK (who files Form 4) instead of their Firm's CIK (who files 13F). "
                        "Please verify the CIK."
                    )
                else:
                    raise Exception(
                        f"No 13F-HR or 13F-HR/A filing found for {filing.year} {filing.quarter}. "
                        "Please check if the CIK is correct and the company existed/filed in that period."
                    )

            # 2. Download and Process
            # Use company name from DB as placeholder for filename (sanitized)
            safe_company_name = "".join(
                c for c in filing.company_name if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            ticker_placeholder = safe_company_name.replace(" ", "_") or "UNKNOWN"

            # Call the internal download method
            # Ensure formType is set (it might be 13F-HR or 13F-HR/A)
            if "formType" not in target_filing:
                target_filing["formType"] = "13F-HR"

            logger.info(
                f"Dowloading filing type {target_filing['formType']} dated {target_filing['filingDate']}"
            )

            success = self.downloader._download_and_process_13f(
                ticker_placeholder, filing.cik, target_filing
            )

            if success:
                filing.status = FilingStatus.COMPLETED
                filing.filing_date = datetime.strptime(
                    target_filing["filingDate"], "%Y-%m-%d"
                ).date()

                # Update file paths
                filing_date_str = target_filing["filingDate"]
                form_type_sanitized = target_filing["formType"].replace(
                    "/", "-"
                )  # Handle 13F-HR/A -> 13F-HR-A

                # Note: edgar_downloader might save with specific naming convention.
                # We need to match what downloader uses.
                # Downloader uses f"{ticker}_CIK_{cik}_FORM_13F-HR_{filing_date}.xml" hardcoded for 13F-HR processing?
                # Let's check downloader code.
                # Downloader code: xml_filename = f"{ticker}_CIK_{cik}_FORM_13F-HR_{filing_date}.xml"
                # It does NOT use the dynamic form_type in the filename for 13F (hardcoded "FORM_13F-HR").
                # This is a minor issue if we download 13F-HR/A but it saves as 13F-HR.
                # However, since we are calling _download_and_process_13f directly, let's verify if it uses the passed form_type?
                # The _download_and_process_13f method uses hardcoded "FORM_13F-HR" in filename generation.
                # So we should expect the filename to use "FORM_13F-HR".

                xml_filename = f"{ticker_placeholder}_CIK_{filing.cik}_FORM_13F-HR_{filing_date_str}.xml"
                json_filename = f"{ticker_placeholder}_CIK_{filing.cik}_FORM_13F-HR_{filing_date_str}.json"

                filing.raw_file_path = os.path.join(
                    self.downloader.config["download_settings"]["download_directory"],
                    xml_filename,
                )
                filing.processed_file_path = os.path.join(
                    self.downloader.config["conversion_settings"][
                        "json_output_directory"
                    ],
                    json_filename,
                )

                # 3. Auto-correct Company Name
                try:
                    import json

                    if os.path.exists(filing.processed_file_path):
                        with open(
                            filing.processed_file_path, "r", encoding="utf-8"
                        ) as f:
                            data = json.load(f)
                            official_name = data.get("document_metadata", {}).get(
                                "filing_manager"
                            )
                            if official_name and official_name != "Unknown":
                                filing.company_name = official_name
                                logger.info(
                                    f"Auto-corrected company name to: {official_name}"
                                )
                except Exception as e:
                    logger.warning(f"Failed to auto-correct company name: {e}")

                # 4. Save to DB
                try:
                    self._save_holdings_to_db(filing, session)
                except Exception as e:
                    logger.error(f"Failed to save holdings to DB: {e}")

            else:
                raise Exception("Download failed in EDGARReportDownloader")

        except Exception as e:
            logger.error(f"Task failed: {e}")
            filing.status = FilingStatus.FAILED
            filing.error_message = str(e)

        finally:
            session.add(filing)
            session.commit()

    def _find_matching_quarter_filing(
        self, filings: list, target_year: int, target_quarter: str
    ):
        """
        Filter filings to find the one corresponding to the report period.
        """
        # Iterate backwards to find the latest filing (e.g. latest amendment)
        # Assuming filings is sorted by date ascending.
        for f in reversed(filings):
            f_date = pd.to_datetime(f["filingDate"])
            f_month = f_date.month
            f_year = f_date.year

            is_match = False

            # Heuristic for 13F filing dates
            if target_quarter == "Q1":
                # Filed in April/May/June of target_year
                if f_year == target_year and 4 <= f_month <= 6:
                    is_match = True
            elif target_quarter == "Q2":
                # Filed in July/Aug/Sep of target_year
                if f_year == target_year and 7 <= f_month <= 9:
                    is_match = True
            elif target_quarter == "Q3":
                # Filed in Oct/Nov/Dec of target_year
                if f_year == target_year and 10 <= f_month <= 12:
                    is_match = True
            elif target_quarter == "Q4":
                # Filed in Jan/Feb/Mar of NEXT year
                if f_year == target_year + 1 and 1 <= f_month <= 3:
                    is_match = True

            # Relaxed heuristic for late filings (e.g. Q3 filed in Jan)
            # This is risky but helps catch delayed filings.
            # Only apply if no match found? No, we need to match here.
            # Let's keep strict for now to avoid ambiguity.

            if is_match:
                return f

        return None

    def _save_holdings_to_db(self, filing: Filing, session: Session):
        """Parse the generated JSON and save holdings to the database."""
        import json

        if not filing.processed_file_path or not os.path.exists(
            filing.processed_file_path
        ):
            logger.warning("No processed JSON file found to save to DB")
            return

        with open(filing.processed_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        holdings_list = data.get("holdings", [])

        db_holdings = []
        for h in holdings_list:
            shares_info = h.get("shares_or_principal", {})

            # Extract put_call info safely
            put_call_val = h.get("put_call")

            db_holding = Holding(
                filing_id=filing.id,
                issuer_name=h.get("issuer_name", "Unknown"),
                title_of_class=h.get("title_of_class", "Unknown"),
                cusip=h.get("cusip", "Unknown"),
                value_usd=h.get("value_usd", 0.0),
                shares_amount=shares_info.get("amount", 0.0),
                shares_type=shares_info.get("type", "SH"),
                put_call=put_call_val,
                investment_discretion=h.get("investment_discretion", "Unknown"),
            )
            db_holdings.append(db_holding)

        session.add_all(db_holdings)
        session.commit()
        logger.info(
            f"Saved {len(db_holdings)} holdings to database for filing {filing.id}"
        )


edgar_service = EdgarService()
