# Outstanding Amounts API Documentation

## Overview
This document describes the Outstanding Amounts APIs for the Case Tracking module in the Insurance Policy Renewal System.

## Base URL
All APIs are available under the case tracking module:
```
/api/case-tracking/
```

## Authentication
All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### 1. Get Outstanding Summary

**Endpoint:** `GET /cases/{case_id}/outstanding-amounts/summary/`

**Description:** Get outstanding amounts summary for a specific renewal case.

**Parameters:**
- `case_id` (path): Renewal case ID

**Response:**
```json
{
  "success": true,
  "data": {
    "total_outstanding": 240500.00,
    "oldest_due_date": "2024-03-31",
    "latest_due_date": "2025-03-31",
    "average_amount": 48100.00,
    "pending_count": 5,
    "overdue_count": 3,
    "installments": [
      {
        "id": 1,
        "period": "Q1 2024 (Jan-Mar)",
        "amount": 46250.00,
        "due_date": "2024-03-31",
        "days_overdue": 544,
        "status": "overdue",
        "description": "Quarterly premium for family health insurance - Q1 2024"
      },
      {
        "id": 2,
        "period": "Q2 2024 (Apr-Jun)",
        "amount": 46250.00,
        "due_date": "2024-06-30",
        "days_overdue": 453,
        "status": "overdue",
        "description": "Quarterly premium for family health insurance - Q2 2024"
      }
    ]
  }
}
```

### 2. Initiate Payment

**Endpoint:** `POST /cases/{case_id}/outstanding-amounts/pay/`

**Description:** Initiate payment for outstanding installments.

**Parameters:**
- `case_id` (path): Renewal case ID

**Request Body:**
```json
{
  "installment_ids": [1, 2, 3],  // Optional: specific installments to pay
  "payment_mode": "upi",         // Payment method
  "payment_notes": "Payment notes" // Optional
}
```

**Payment Mode Options:**
- `credit_card`
- `debit_card`
- `net_banking`
- `upi`
- `wallet`
- `bank_transfer`
- `cheque`
- `cash`
- `emi`
- `auto_debit`

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Payment initiated for 3 installments",
    "payment_id": 123,
    "transaction_id": "TXN_ABC123DEF456",
    "total_amount": 138750.00
  }
}
```

### 3. Setup Payment Plan

**Endpoint:** `POST /cases/{case_id}/outstanding-amounts/setup-payment-plan/`

**Description:** Setup a custom payment plan for outstanding amounts.

**Parameters:**
- `case_id` (path): Renewal case ID

**Request Body:**
```json
{
  "installment_count": 3,           // Number of installments (2-12)
  "start_date": "2024-01-01",       // Start date for the plan
  "payment_frequency": "monthly",   // weekly, monthly, quarterly
  "payment_method": "auto_debit",   // Payment method
  "auto_payment_enabled": true,     // Enable auto payments
  "plan_notes": "Plan notes"        // Optional
}
```

**Payment Frequency Options:**
- `weekly`
- `monthly`
- `quarterly`

**Payment Method Options:**
- `credit_card`
- `debit_card`
- `net_banking`
- `upi`
- `wallet`
- `bank_transfer`
- `cheque`
- `cash`
- `emi`
- `auto_debit`
- `standing_instruction`
- `nach`
- `enach`

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Payment plan created with 3 installments",
    "total_amount": 240500.00,
    "installment_amount": 80166.67,
    "installment_count": 3,
    "payment_frequency": "monthly",
    "schedules_created": 3
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message",
  "message": "Detailed error description"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Case not found
- `500 Internal Server Error`: Server error

## Example Usage

### Get Outstanding Summary
```bash
curl -X GET \
  "http://localhost:8000/api/case-tracking/cases/1/outstanding-amounts/summary/" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Initiate Payment
```bash
curl -X POST \
  "http://localhost:8000/api/case-tracking/cases/1/outstanding-amounts/pay/" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_mode": "upi",
    "payment_notes": "Payment for outstanding installments"
  }'
```

### Setup Payment Plan
```bash
curl -X POST \
  "http://localhost:8000/api/case-tracking/cases/1/outstanding-amounts/setup-payment-plan/" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "installment_count": 3,
    "start_date": "2024-01-01",
    "payment_frequency": "monthly",
    "payment_method": "auto_debit",
    "auto_payment_enabled": true
  }'
```

## Notes

1. **Dynamic Calculation**: Outstanding amounts are calculated dynamically from existing `CustomerInstallment` and `PaymentSchedule` tables.

2. **No Duplicate Tables**: The implementation uses existing tables and doesn't create duplicate data storage.

3. **Real-time Updates**: Outstanding amounts are calculated in real-time, ensuring accuracy.

4. **Payment Integration**: Payment initiation creates `CustomerPayment` records and updates installment statuses.

5. **Flexible Payment Plans**: Payment plans can be customized with different frequencies and methods.

6. **Error Handling**: Comprehensive error handling with detailed error messages.

7. **Authentication**: All endpoints require valid JWT authentication.

8. **Validation**: Request data is validated using Django REST Framework serializers.
