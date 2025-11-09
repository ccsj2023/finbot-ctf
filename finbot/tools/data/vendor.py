"""Vendor data tools"""

import logging
from typing import Any

from finbot.core.auth.session import SessionContext
from finbot.core.data.database import get_db
from finbot.core.data.repositories import VendorRepository

logger = logging.getLogger(__name__)


async def get_vendor_details(
    vendor_id: int, session_context: SessionContext
) -> dict[str, Any]:
    """Get the details of the vendor

    Args:
        vendor_id: The ID of the vendor to retrieve
        session_context: The session context

    Returns:
        Dictionary containing vendor details
    """
    logger.info("Getting vendor details for vendor_id: %s", vendor_id)
    db = next(get_db())
    vendor_repo = VendorRepository(db, session_context)
    vendor = vendor_repo.get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    return vendor.to_dict()
