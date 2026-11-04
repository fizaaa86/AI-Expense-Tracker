from datetime import date
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from google.genai import errors as genai_errors
from pydantic import ValidationError
from sqlalchemy.orm import Session

from auth import CurrentUser, get_current_user
from db import get_user_db
from schemas import ExpenseOut, ScanResult
from services import expenses as expense_service
from services import receipts as receipt_service
from services import storage

router = APIRouter(prefix="/receipts", tags=["Receipts"])

MAX_SIZE = 5 * 1024 * 1024   # 5 MB


@router.post("/scan", response_model=ScanResult)
def scan_receipt(
    file: UploadFile,
    user: CurrentUser = Depends(get_current_user),   # only logged-in users can use Gemini
    db: Session = Depends(get_user_db),
):
    """Read a receipt photo and store the image. No expense is saved; the user reviews first."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")
    image = file.file.read()
    if len(image) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image is too large (max 5 MB)")

    # 1. Read the receipt (with one retry if the numbers don't add up)
    try:
        receipt = receipt_service.extract_receipt(image, file.content_type)
        validation = receipt_service.validate_receipt(receipt)
        attempts = 1

        if not validation.ok:   # numbers don't add up -> one more try, with the problems as feedback
            receipt = receipt_service.extract_receipt(
                image, file.content_type, feedback="\n".join(validation.problems)
            )
            validation = receipt_service.validate_receipt(receipt)
            attempts = 2
    except (genai_errors.APIError, ValidationError) as e:
        raise HTTPException(status_code=502, detail=f"Could not read the receipt: {e}")

    # 2. Keep the photo in Supabase Storage (in the user's own folder)
    try:
        image_path = storage.upload_receipt_image(user.token, user.id, image, file.content_type)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Could not store the receipt image: {e}")

    # 3. Have we seen this bill before?
    duplicates = []
    if receipt.merchant and receipt.total and receipt.expense_date:
        try:
            duplicates = expense_service.find_duplicates(
                db, user.id, receipt.merchant,
                date.fromisoformat(receipt.expense_date), Decimal(str(receipt.total)),
            )
        except ValueError:
            pass   # unreadable date: validate_receipt already reported it

    return ScanResult(
        receipt=receipt,
        validation=validation,
        attempts=attempts,
        image_path=image_path,
        possible_duplicates=[ExpenseOut.model_validate(e) for e in duplicates],
    )
