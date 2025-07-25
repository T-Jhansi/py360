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

    # Get the highest existing case number
    latest_case = RenewalCase.objects.filter(
        case_number__startswith=prefix
    ).order_by('-case_number').first()

    if latest_case:
        # Extract the number part and increment
        try:
            # Remove the prefix "CASE-" and get the number part
            number_part = latest_case.case_number[len(prefix):]
            last_number = int(number_part)
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1

    return f"{prefix}{next_number:03d}"

def generate_policy_number():
    """Generate unique policy number like POL-00001"""
    prefix = "POL-"

    # Get the highest existing policy number
    latest_policy = Policy.objects.filter(
        policy_number__startswith=prefix
    ).order_by('-policy_number').first()

    if latest_policy:
        # Extract the number part and increment
        try:
            # Remove the prefix "POL-" and get the number part
            number_part = latest_policy.policy_number[len(prefix):]
            last_number = int(number_part)
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1

    return f"{prefix}{next_number:05d}"
