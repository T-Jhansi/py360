# utils.py
from apps.customers.models import Customer
from apps.renewals.models import RenewalCase
from apps.policies.models import Policy
import datetime

def generate_customer_code():
    """Generate unique customer code like CUS2025001"""
    current_year = datetime.datetime.now().year
    year_prefix = f"CUS{current_year}"

    latest_customer = Customer.objects.filter(
        customer_code__startswith=year_prefix
    ).order_by('-customer_code').first()

    if latest_customer:
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

    case_numbers = RenewalCase.objects.filter(
        case_number__startswith=prefix
    ).values_list('case_number', flat=True)

    max_number = 0
    for case_number in case_numbers:
        try:
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
    current_year = datetime.datetime.now().year
    year_prefix = f"POL-{current_year}-"
    simple_prefix = "POL-"

    year_based_policies = Policy.objects.filter(
        policy_number__startswith=year_prefix
    ).values_list('policy_number', flat=True)

    if year_based_policies:
        max_number = 0
        for policy_number in year_based_policies:
            try:
                number_part = policy_number[len(year_prefix):]
                number = int(number_part)
                if number > max_number:
                    max_number = number
            except (ValueError, IndexError):
                continue

        next_number = max_number + 1
        return f"{year_prefix}{next_number:03d}"
    else:
        simple_policies = Policy.objects.filter(
            policy_number__startswith=simple_prefix,
            policy_number__regex=r'^POL-\d{5}$' 
        ).values_list('policy_number', flat=True)

        max_number = 0
        for policy_number in simple_policies:
            try:
              
                number_part = policy_number[len(simple_prefix):]
                number = int(number_part)
                if number > max_number:
                    max_number = number
            except (ValueError, IndexError):
                continue

        next_number = max_number + 1
        return f"{simple_prefix}{next_number:05d}"


def generate_batch_code():
    from datetime import date
    import string

    today = date.today()
    date_str = today.strftime('%Y-%m-%d')

    today_batches = RenewalCase.objects.filter(
        batch_code__startswith=f'BATCH-{date_str}-'
    ).values_list('batch_code', flat=True).distinct()

    used_letters = []
    for batch_code in today_batches:
        try:
            suffix = batch_code.split('-')[-1]
            if len(suffix) == 1 and suffix.isalpha():
                used_letters.append(suffix.upper())
        except (IndexError, AttributeError):
            continue
    for letter in string.ascii_uppercase:
        if letter not in used_letters:
            return f"BATCH-{date_str}-{letter}"

    for first_letter in string.ascii_uppercase:
        for second_letter in string.ascii_uppercase:
            double_letter = f"{first_letter}{second_letter}"
            if double_letter not in used_letters:
                return f"BATCH-{date_str}-{double_letter}"
    import uuid
    return f"BATCH-{date_str}-{str(uuid.uuid4())[:8].upper()}"
