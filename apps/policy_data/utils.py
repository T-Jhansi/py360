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
    """Generate unique case number like CASE20250001"""
    current_year = datetime.datetime.now().year
    year_prefix = f"CASE{current_year}"

    # Get the highest existing case number for this year
    latest_case = RenewalCase.objects.filter(
        case_number__startswith=year_prefix
    ).order_by('-case_number').first()

    if latest_case:
        # Extract the number part and increment
        try:
            last_number = int(latest_case.case_number[len(year_prefix):])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1

    return f"{year_prefix}{next_number:04d}"

def generate_policy_number():
    """Generate unique policy number like POL-2025-001"""
    import time
    import random
    # Use timestamp + random for uniqueness
    timestamp_part = int(time.time()) % 10000  
    random_part = random.randint(1, 99)
    unique_id = timestamp_part * 100 + random_part
    current_year = datetime.datetime.now().year
    return f"POL-{current_year}-{unique_id:06d}"
