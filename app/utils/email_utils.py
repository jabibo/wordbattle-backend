from typing import Optional


def normalize_email(email: Optional[str]) -> Optional[str]:
    """
    Normalize email addresses for consistent storage and comparisons.

    - Trims surrounding whitespace
    - Converts to lowercase
    """
    if not email:
        return email
    return email.strip().lower()


def emails_match(email_a: Optional[str], email_b: Optional[str]) -> bool:
    """Compare two email addresses using normalized values."""
    return normalize_email(email_a) == normalize_email(email_b)

