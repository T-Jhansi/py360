# utils.py
from apps.customers.models import Customer
from apps.renewals.models import RenewalCase
from apps.policies.models import Policy
import datetime

def generate_customer_code():
    """Generate unique customer code like CUS2025001"""
    import time
    import random
    # Use timestamp + random for uniqueness
    timestamp_part = int(time.time()) % 100000 
    random_part = random.randint(1, 99)
    unique_id = timestamp_part * 100 + random_part
    current_year = datetime.datetime.now().year
    return f"CUS{current_year}{unique_id:07d}"

def generate_case_number():
    """Generate unique case number like CASE20250001"""
    import time
    import random
    # Use timestamp + random for uniqueness
    timestamp_part = int(time.time()) % 100000 
    random_part = random.randint(1, 999)
    unique_id = timestamp_part * 1000 + random_part
    current_year = datetime.datetime.now().year
    return f"CASE{current_year}{unique_id:08d}"

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
