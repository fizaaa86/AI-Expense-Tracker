"""Reading receipt photos with Gemini, and checking the result with plain maths."""
import os
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import ReceiptExtraction, ReceiptValidation

load_dotenv()
# If Google is busy (429/503 errors), wait and retry up to 4 times before giving up
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
       http_options=types.HttpOptions(
        timeout=60_000,   # give up on one attempt after 60 seconds (the value is in milliseconds)
        retry_options=types.HttpRetryOptions(attempts=4),
    ),

)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

TOLERANCE = 1.00   # allow 5 paise of rounding difference

#extract_receipt packs the photo and the instructions together, sends them to Gemini, and says "reply in this JSON shape". Then Pydantic checks the reply. feedback is used only on the second try, to tell Gemini what it got wrong the first time.
#validate_receipt is ordinary maths, with no AI involved. It checks four things: is there a merchant, is there a valid date, is there a total, and do the items add up? It accepts both kinds of receipt: tax added on top, or tax already included in the item prices (common in India).
#TOLERANCE: computers store decimal numbers slightly inaccurately (0.1 + 0.2 = 0.30000000000000004!), so we allow a tiny difference.




PROMPT = """You are reading a photo of a shop receipt. Extract the fields exactly as printed.
Rules:
- items: every purchased line with its final line price. Do NOT include subtotal, tax,
  discount, rounding or total lines as items.
- tax: the total tax on the receipt (0 if none is shown).
- discount: the total of all discounts as a positive number (0 if none is shown).
- total: the final amount paid.
- expense_date: YYYY-MM-DD.
- If a value cannot be read clearly, use null. Never guess numbers."""


def extract_receipt(image: bytes, mime_type: str, feedback: str | None = None) -> ReceiptExtraction:
    """Send the photo to Gemini and get back a ReceiptExtraction."""
    prompt = PROMPT
    if feedback:   # second attempt: tell Gemini what was wrong last time
        prompt += f"\n\nA previous reading of this receipt had these problems:\n{feedback}\nLook at the image again carefully and correct them."

    response = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=image, mime_type=mime_type), prompt],
        config={
            "response_mime_type": "application/json",                     # reply with JSON...
            "response_json_schema": ReceiptExtraction.model_json_schema(),  # ...in exactly this shape
        },
    )
    return ReceiptExtraction.model_validate_json(response.text)   # Pydantic checks Gemini's answer


def validate_receipt(receipt: ReceiptExtraction) -> ReceiptValidation:
    """Plain Python checks. The AI is never trusted to check itself."""
    problems = []

    if not receipt.merchant:
        problems.append("The merchant name is missing.")

    if not receipt.expense_date:
        problems.append("The date is missing.")
    else:
        try:
            date.fromisoformat(receipt.expense_date)
        except ValueError:
            problems.append(f"The date '{receipt.expense_date}' is not in YYYY-MM-DD format.")

    if receipt.total is None or receipt.total <= 0:
        problems.append("The total is missing or not a positive number.")
    elif receipt.items:
        items_sum = round(sum(item.price for item in receipt.items), 2)
        discount = receipt.discount or 0
        tax = receipt.tax or 0
        # Some receipts add tax on top; others (common with GST) already include it in prices
        tax_on_top = abs(items_sum - discount + tax - receipt.total) <= TOLERANCE
        tax_included = abs(items_sum - discount - receipt.total) <= TOLERANCE
        if not (tax_on_top or tax_included):
            problems.append(
                f"The items add up to {items_sum:.2f} (discount {discount:.2f}, tax {tax:.2f}), "
                f"but the total is {receipt.total:.2f}."
            )


    return ReceiptValidation(ok=not problems, problems=problems)
