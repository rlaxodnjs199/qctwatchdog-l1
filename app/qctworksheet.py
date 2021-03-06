from functools import lru_cache
from time import sleep
from loguru import logger
import gspread
from gspread.exceptions import GSpreadException

from app.config import QCTWorksheetConfig
from app.models import RawScan


class QCTWorksheet:
    try:
        google_service_account = gspread.service_account(
            filename=QCTWorksheetConfig.google_api_token_path
        )
    except:
        google_service_account = None
        logger.exception("Failed to initiate Google service account")
    try:
        session = google_service_account.open_by_key(
            QCTWorksheetConfig.qctworksheet_api_key
        )
    except:
        session = None
        logger.exception("Failed to initiate Google spread sheet session")

    @staticmethod
    def calculate_fu(proj: str, subj: str) -> int:
        try:
            subj_list = QCTWorksheet.session.worksheet(proj).findall(subj)
            subj_scan_indexes = {subj.row for subj in subj_list}
        except GSpreadException:
            logger.warning("GSpread Exception: Quota limit")
            sleep(60)
            return QCTWorksheet.calculate_fu(proj, subj)

        return len(subj_scan_indexes)

    @staticmethod
    def check_duplicate(proj: str, subj: str, ct_date: str):
        try:
            subj_scan_list = QCTWorksheet.session.worksheet(proj).findall(subj)
            for subj_scan in subj_scan_list:
                subj_scan_ct_date = QCTWorksheet.session.worksheet(proj).row_values(
                    subj_scan.row
                )[4]
                if subj_scan_ct_date == ct_date:
                    return True
        except GSpreadException:
            logger.warning("GSpread Exception: Quota limit")
            sleep(60)
            return QCTWorksheet.check_duplicate(proj, subj, ct_date)

        return False

    @staticmethod
    def add_new_scan(scan: RawScan):
        try:
            QCTWorksheet.session.worksheet(scan.proj).append_row(
                values=[
                    scan.proj,
                    scan.subj,
                    "",
                    scan.study_id,
                    scan.ct_date,
                    scan.fu,
                    scan.dcm_path,
                ]
            )
            logger.info(f"Successfully added new scan to {scan.proj}")
        except GSpreadException:
            logger.warning("GSpread Exception: Quota limit")
            sleep(60)
            return QCTWorksheet.add_new_scan(scan)
        except:
            logger.exception(f"Sheet {scan.proj} does not exist")


@lru_cache
def get_qctworksheet():
    return QCTWorksheet()


qctworksheet = get_qctworksheet()
