from fastapi import APIRouter, Depends, HTTPException, UploadFile
from google.genai import errors as genai_errors
from pydantic import ValidationError

from auth import CurrentUser, get_current_user
from schemas import ScanResult
from services import receipts as receipt_service

router = APIRouter(prefix="/receipts", tags=["Receipts"])

MAX_SIZE = 5 * 1024 * 1024   # 5 MB

#UploadFile is how FastAPI receives a file. In /docs it shows up as a Choose File button.
#We check that it's an image and under 5 MB before sending it to Google. That avoids wasting your free quota on junk.
#Read → check → if wrong, read again with feedback → check again. This is the self-checking loop from your report. If it's still wrong after two tries, we don't silently "fix" it. We return the problems so the user can correct them.
#502 means "a service we depend on failed". We use it if Google's API errors or sends back badly shaped data.
#For now, the retry is hard-coded (a "workflow", in your report's terms). In Step 6 the AI agent will decide by itself when to re-read.

@router.post("/scan", response_model=ScanResult)
def scan_receipt(
    file: UploadFile,
    user: CurrentUser = Depends(get_current_user),   # only logged-in users can use Gemini
):
    """Read a receipt photo. Nothing is saved; the user reviews the result first."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")
    image = file.file.read()
    if len(image) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image is too large (max 5 MB)")

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

    # If it's still wrong, we don't hide it: the problems go back to the user to fix in the form
    return ScanResult(receipt=receipt, validation=validation, attempts=attempts)
