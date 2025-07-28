# utils.py
from apps.customers.models import Customer
from apps.renewals.models import RenewalCase
from apps.policies.models import Policy
import datetime

def generate_customer_code():
    """Generate unique customer code like CUS2025001"""
    current_year = datetime.datetime.now().year
    year_prefix = f"CUS{current_year}"

    # Get the highest existing customer code for this year
    latest_customer = Customer.objects.filter(
        customer_code__startswith=year_prefix
    ).order_by('-customer_code').first()

    if latest_customer:
        # Extract the number part and increment
        try:
            last_number = int(latest_customer.customer_code[len(year_prefix):])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1

    return f"{year_prefix}{next_number:03d}"

def generate_case_number():
    """Generate unique case number like CASE-001"""
    prefix = "CASE-"

    # Get all case numbers with the prefix and find the highest number
    case_numbers = RenewalCase.objects.filter(
        case_number__startswith=prefix
    ).values_list('case_number', flat=True)

    max_number = 0
    for case_number in case_numbers:
        try:
            # Extract the number part after the prefix
            number_part = case_number[len(prefix):]
            number = int(number_part)
            if number > max_number:
                max_number = number
        except (ValueError, IndexError):
            continue

    next_number = max_number + 1
    return f"{prefix}{next_number:03d}"

def generate_policy_number():
    """Generate unique policy number like POL-00001"""
    import datetime

    # Check if we're using year-based format (POL-2025-001) or simple format (POL-00001)
    current_year = datetime.datetime.now().year
    year_prefix = f"POL-{current_year}-"
    simple_prefix = "POL-"

    # Check if there are any year-based policy numbers
    year_based_policies = Policy.objects.filter(
        policy_number__startswith=year_prefix
    ).values_list('policy_number', flat=True)

    if year_based_policies:
        # Use year-based format: POL-2025-001
        max_number = 0
        for policy_number in year_based_policies:
            try:
                # Extract the number part after POL-YYYY-
                number_part = policy_number[len(year_prefix):]
                number = int(number_part)
                if number > max_number:
                    max_number = number
            except (ValueError, IndexError):
                continue

        next_number = max_number + 1
        return f"{year_prefix}{next_number:03d}"
    else:
        # Use simple format: POL-00001
        simple_policies = Policy.objects.filter(
            policy_number__startswith=simple_prefix,
            policy_number__regex=r'^POL-\d{5}$'  # Match POL-##### format only
        ).values_list('policy_number', flat=True)

        max_number = 0
        for policy_number in simple_policies:
            try:
                # Extract the number part after POL-
                number_part = policy_number[len(simple_prefix):]
                number = int(number_part)
                if number > max_number:
                    max_number = number
            except (ValueError, IndexError):
                continue

        next_number = max_number + 1
        return f"{simple_prefix}{next_number:05d}"


def generate_batch_code():
    """
    Generate unique batch code in format BATCH-2025-07-25-A, BATCH-2025-07-25-B, etc.
    Each day starts with A and increments for each new file upload.
    """
    from datetime import date
    import string

    today = date.today()
    date_str = today.strftime('%Y-%m-%d')

    # Find existing batch codes for today
    today_batches = RenewalCase.objects.filter(
        batch_code__startswith=f'BATCH-{date_str}-'
    ).values_list('batch_code', flat=True).distinct()

    # Extract the letter suffixes (A, B, C, etc.)
    used_letters = []
    for batch_code in today_batches:
        try:
            # Extract the last part after the last dash
            suffix = batch_code.split('-')[-1]
            if len(suffix) == 1 and suffix.isalpha():
                used_letters.append(suffix.upper())
        except (IndexError, AttributeError):
            continue

    # Find the next available letter
    for letter in string.ascii_uppercase:
        if letter not in used_letters:
            return f"BATCH-{date_str}-{letter}"

    # If we've used all letters A-Z, start with AA, AB, etc.
    # This handles the unlikely case of more than 26 uploads in one day
    for first_letter in string.ascii_uppercase:
        for second_letter in string.ascii_uppercase:
            double_letter = f"{first_letter}{second_letter}"
            if double_letter not in used_letters:
                return f"BATCH-{date_str}-{double_letter}"

    # Fallback - should never reach here
    import uuid
    return f"BATCH-{date_str}-{str(uuid.uuid4())[:8].upper()}"
