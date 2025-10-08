# WhatsApp Business Provider

A comprehensive Django app for managing multiple WhatsApp Business API accounts, sending messages, and handling webhooks.

## 🚀 Features

### ✅ **Completed Features**

- **Multiple WABA Account Management** - Support for multiple WhatsApp Business Accounts per user
- **Phone Number Management** - Multiple phone numbers per WABA account
- **Message Templates** - Create, manage, and track approved message templates
- **Message Sending** - Send text, template, and interactive messages via WhatsApp Cloud API
- **Webhook Handling** - Process incoming messages, status updates, and account events
- **Account Health Monitoring** - Health checks and usage tracking
- **Analytics & Reporting** - Message delivery statistics and performance metrics
- **WhatsApp Flows Support** - Interactive message forms and data collection
- **Admin Interface** - Complete Django admin integration
- **API Endpoints** - RESTful API for all operations

### 🔄 **Pending Features**

- **Embedded Signup Integration** - Allow users to create WABAs directly from the platform
- **Frontend Setup Wizard** - 6-step account setup UI (matching your images)
- **Campaign Integration** - Integration with existing campaign system
- **Advanced Flows** - More complex interactive message flows

## 📊 **Database Models**

### Core Models

1. **WhatsAppBusinessAccount** - Main WABA account configuration
2. **WhatsAppPhoneNumber** - Phone numbers associated with WABA accounts
3. **WhatsAppMessageTemplate** - Approved message templates
4. **WhatsAppMessage** - Individual messages sent/received
5. **WhatsAppWebhookEvent** - Webhook events from WhatsApp API
6. **WhatsAppFlow** - Interactive message flows
7. **WhatsAppAccountHealthLog** - Health check logs
8. **WhatsAppAccountUsageLog** - Usage tracking and analytics

### Model Relationships

```
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppPhoneNumber
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppMessageTemplate
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppMessage
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppFlow
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppWebhookEvent
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppAccountHealthLog
WhatsAppBusinessAccount (1) ──→ (N) WhatsAppAccountUsageLog
```

## 🔧 **API Endpoints**

### Account Management
- `GET /api/whatsapp/accounts/` - List all WABA accounts
- `POST /api/whatsapp/accounts/` - Create new WABA account
- `GET /api/whatsapp/accounts/{id}/` - Get specific WABA account
- `PUT /api/whatsapp/accounts/{id}/` - Update WABA account
- `DELETE /api/whatsapp/accounts/{id}/` - Delete WABA account

### Account Setup
- `POST /api/whatsapp/accounts/setup/` - Complete 6-step account setup

### Phone Numbers
- `GET /api/whatsapp/phone-numbers/` - List phone numbers
- `POST /api/whatsapp/phone-numbers/` - Add new phone number

### Message Templates
- `GET /api/whatsapp/templates/` - List message templates
- `POST /api/whatsapp/templates/` - Create new template
- `POST /api/whatsapp/templates/{id}/submit_for_approval/` - Submit template for Meta approval

### Message Sending
- `POST /api/whatsapp/accounts/{id}/send_message/` - Send message via WABA account

### Flows
- `GET /api/whatsapp/flows/` - List WhatsApp flows
- `POST /api/whatsapp/flows/` - Create new flow

### Webhooks
- `GET /api/whatsapp/webhook/webhook/` - Webhook verification
- `POST /api/whatsapp/webhook/webhook/` - Receive webhook events

### Analytics
- `GET /api/whatsapp/analytics/dashboard/` - Dashboard analytics
- `GET /api/whatsapp/accounts/{id}/analytics/` - Account-specific analytics

## 🛠️ **Setup Instructions**

### 1. Database Setup
The migrations have been created and applied. The following tables are now available:
- `whatsapp_business_accounts`
- `whatsapp_phone_numbers`
- `whatsapp_message_templates`
- `whatsapp_messages`
- `whatsapp_webhook_events`
- `whatsapp_flows`
- `whatsapp_account_health_logs`
- `whatsapp_account_usage_logs`

### 2. Environment Variables
Add the following to your `.env` file:

```env
# WhatsApp Business API Configuration
WHATSAPP_ENCRYPTION_KEY=your-32-character-encryption-key-here
WHATSAPP_WEBHOOK_BASE_URL=https://yourdomain.com
```

### 3. URL Configuration
The app is already added to the main URL configuration at `/api/whatsapp/`

### 4. Admin Interface
Access the admin interface to manage WhatsApp accounts:
- Go to `/admin/`
- Navigate to "WhatsApp Business Provider" section
- Manage accounts, phone numbers, templates, and messages

## 📝 **Usage Examples**

### Creating a WABA Account (6-Step Setup)

```python
# Step 1: Meta Business Account
data = {
    "name": "My Business WhatsApp",
    "waba_id": "123456789012345",
    "meta_business_account_id": "987654321098765",
    "app_id": "your_app_id",
    "app_secret": "your_app_secret",
    
    # Step 2: Phone Number Setup
    "phone_number_id": "123456789",
    "phone_number": "+1234567890",
    "display_phone_number": "+1 (234) 567-8900",
    
    # Step 3: Access Tokens
    "access_token": "your_permanent_access_token",
    "webhook_verify_token": "your_verify_token",
    
    # Step 4: Business Profile
    "business_name": "My Insurance Company",
    "business_description": "Leading insurance provider",
    "business_email": "contact@mycompany.com",
    "business_vertical": "Insurance",
    "business_address": "123 Business St, City, State",
    
    # Step 5: Bot Configuration
    "enable_auto_reply": True,
    "use_knowledge_base": True,
    "greeting_message": "Hello! How can I help you today?",
    "fallback_message": "I'm sorry, I didn't understand. Can you rephrase?",
    "enable_business_hours": True,
    "business_hours_start": "09:00:00",
    "business_hours_end": "17:00:00",
    "business_timezone": "UTC",
    
    # Step 6: Webhook Configuration
    "webhook_url": "https://yourdomain.com/api/whatsapp/webhook/webhook/",
    "subscribed_webhook_events": ["messages", "message_deliveries", "message_reads"]
}

# Create account
response = requests.post('/api/whatsapp/accounts/setup/', json=data)
```

### Sending a Text Message

```python
data = {
    "waba_account_id": 1,
    "to_phone_number": "+1234567890",
    "message_type": "text",
    "text_content": "Hello! This is a test message from our insurance company."
}

response = requests.post('/api/whatsapp/accounts/1/send_message/', json=data)
```

### Sending a Template Message

```python
data = {
    "waba_account_id": 1,
    "to_phone_number": "+1234567890",
    "message_type": "template",
    "template_id": 1,
    "template_params": ["John", "Policy123", "2024-01-15"]
}

response = requests.post('/api/whatsapp/accounts/1/send_message/', json=data)
```

### Sending an Interactive Message (Flow)

```python
data = {
    "waba_account_id": 1,
    "to_phone_number": "+1234567890",
    "message_type": "interactive",
    "flow_id": 1,
    "flow_token": "customer_inquiry_123"
}

response = requests.post('/api/whatsapp/accounts/1/send_message/', json=data)
```

### Creating a Message Template

```python
template_data = {
    "waba_account": 1,
    "name": "policy_renewal_reminder",
    "category": "UTILITY",
    "language": "en",
    "header_text": "Policy Renewal Reminder",
    "body_text": "Hello {{1}}, your policy {{2}} expires on {{3}}. Please renew to avoid any lapse in coverage.",
    "footer_text": "Thank you for choosing us!",
    "components": []
}

response = requests.post('/api/whatsapp/templates/', json=template_data)
```

## 🔒 **Security Features**

### Credential Encryption
- Access tokens and secrets are encrypted using Fernet encryption
- Encryption key should be stored securely in environment variables

### Webhook Verification
- All webhook events are verified using verify tokens
- Prevents unauthorized webhook calls

### Rate Limiting
- Built-in rate limiting per WABA account
- Daily and monthly message limits
- Configurable per-minute limits

### User Permissions
- Users can only access their own WABA accounts
- Admin users have full access to all accounts

## 📊 **Analytics & Monitoring**

### Health Checks
- Automatic health checks for WABA accounts
- Health status tracking and logging
- Error monitoring and alerting

### Usage Tracking
- Message count tracking (daily/monthly)
- Delivery rate monitoring
- Read rate analytics
- Failed message tracking

### Performance Metrics
- Response time monitoring
- API error tracking
- Template performance analytics
- Customer engagement metrics

## 🔄 **Webhook Events**

The system handles the following webhook events:

### Message Events
- `messages` - Incoming customer messages
- `message_deliveries` - Message delivery confirmations
- `message_reads` - Message read receipts

### Account Events
- `account_update` - WABA account changes
- `phone_number_update` - Phone number status changes

### Template Events
- `message_template_status_update` - Template approval/rejection status

## 🚀 **Next Steps**

### Immediate Next Steps
1. **Frontend Integration** - Build the 6-step setup wizard UI
2. **Embedded Signup** - Integrate Meta's Embedded Signup flow
3. **Campaign Integration** - Connect with existing campaign system

### Advanced Features
1. **AI Integration** - Smart auto-replies using knowledge base
2. **Advanced Analytics** - Customer journey tracking
3. **Multi-language Support** - Template localization
4. **A/B Testing** - Template performance testing

## 🐛 **Troubleshooting**

### Common Issues

1. **Webhook Not Receiving Events**
   - Verify webhook URL is accessible
   - Check verify token matches
   - Ensure webhook events are subscribed

2. **Message Sending Fails**
   - Verify WABA account is active and verified
   - Check rate limits haven't been exceeded
   - Ensure phone number is verified

3. **Template Not Approved**
   - Check template follows Meta guidelines
   - Verify all required fields are provided
   - Wait for Meta approval (can take 24-48 hours)

### Debug Mode
Enable debug logging by setting:
```python
LOGGING = {
    'loggers': {
        'apps.whatsapp_provider': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## 📞 **Support**

For issues or questions:
1. Check the Django admin interface for account status
2. Review webhook event logs for error details
3. Monitor health check logs for API issues
4. Check rate limiting and usage statistics

---

**Status**: ✅ **Core Implementation Complete** - Ready for frontend integration and advanced features!
