#!/usr/bin/env python
"""
Test script for SendGrid integration with campaign emails
Run this script to test if SendGrid is properly configured and working
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'renewal_backend.settings')
django.setup()

from apps.email_provider.models import EmailProviderConfig
from apps.email_provider.services import EmailProviderService
from apps.campaigns.models import Campaign, CampaignRecipient
from apps.customers.models import Customer
from apps.templates.models import Template
from apps.campaigns.services import EmailCampaignService

def test_sendgrid_provider():
    """Test if SendGrid provider is configured"""
    print("🔍 Checking SendGrid provider configuration...")
    
    # Check if SendGrid provider exists
    sendgrid_providers = EmailProviderConfig.objects.filter(
        provider_type='sendgrid',
        is_active=True,
        is_deleted=False
    )
    
    if not sendgrid_providers.exists():
        print("❌ No active SendGrid providers found!")
        print("Please create a SendGrid provider in the admin panel or database.")
        return False
    
    provider = sendgrid_providers.first()
    print(f"✅ Found SendGrid provider: {provider.name}")
    print(f"   - From Email: {provider.from_email}")
    print(f"   - From Name: {provider.from_name}")
    print(f"   - Priority: {provider.priority}")
    print(f"   - Health Status: {provider.health_status}")
    
    return provider

def test_sendgrid_health(provider):
    """Test SendGrid provider health"""
    print("\n🏥 Testing SendGrid provider health...")
    
    email_service = EmailProviderService()
    
    # Test provider health
    is_healthy = email_service.check_provider_health(provider)
    
    if is_healthy:
        print("✅ SendGrid provider is healthy!")
    else:
        print("❌ SendGrid provider health check failed!")
        print("Please check your API key and configuration.")
    
    return is_healthy

def test_sendgrid_send_email(provider):
    """Test sending email via SendGrid"""
    print("\n📧 Testing SendGrid email sending...")
    
    email_service = EmailProviderService()
    
    # Test email sending
    test_email = "test@example.com"  # Change this to a real email for testing
    result = email_service.send_email(
        to_emails=[test_email],
        subject="Test Email from Insurance System",
        html_content="<h1>Test Email</h1><p>This is a test email from your insurance system.</p>",
        text_content="Test Email\n\nThis is a test email from your insurance system.",
        from_email=str(provider.from_email),
        from_name=str(provider.from_name) if provider.from_name else None
    )
    
    if result['success']:
        print("✅ SendGrid email sent successfully!")
        print(f"   - Message ID: {result.get('message_id', 'N/A')}")
        print(f"   - Response Time: {result.get('response_time', 'N/A')}s")
    else:
        print("❌ SendGrid email sending failed!")
        print(f"   - Error: {result.get('error', 'Unknown error')}")
    
    return result['success']

def test_campaign_email_integration():
    """Test campaign email integration with SendGrid"""
    print("\n🎯 Testing campaign email integration...")
    
    # Check if we have any campaigns
    campaigns = Campaign.objects.filter(status='draft')[:1]
    
    if not campaigns.exists():
        print("⚠️  No draft campaigns found for testing.")
        print("   Create a campaign first to test the integration.")
        return False
    
    campaign = campaigns.first()
    print(f"✅ Found campaign: {campaign.name}")
    
    # Check if campaign has recipients
    recipients = CampaignRecipient.objects.filter(
        campaign=campaign,
        email_status='pending'
    )[:1]
    
    if not recipients.exists():
        print("⚠️  No pending recipients found for this campaign.")
        print("   Create campaign recipients first to test the integration.")
        return False
    
    recipient = recipients.first()
    print(f"✅ Found recipient: {recipient.customer.email}")
    
    # Test sending email to this recipient
    print("📤 Testing email sending to campaign recipient...")
    
    try:
        success = EmailCampaignService._send_individual_email(recipient)
        
        if success:
            print("✅ Campaign email sent successfully via SendGrid!")
        else:
            print("❌ Campaign email sending failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing campaign email: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting SendGrid Integration Test")
    print("=" * 50)
    
    # Test 1: Check SendGrid provider
    provider = test_sendgrid_provider()
    if not provider:
        return
    
    # Test 2: Check provider health
    if not test_sendgrid_health(provider):
        print("\n⚠️  SendGrid provider is not healthy. Please check configuration.")
        return
    
    # Test 3: Test email sending
    if not test_sendgrid_send_email(provider):
        print("\n⚠️  SendGrid email sending failed. Please check API key and configuration.")
        return
    
    # Test 4: Test campaign integration
    test_campaign_email_integration()
    
    print("\n" + "=" * 50)
    print("🎉 SendGrid integration test completed!")
    print("\nNext steps:")
    print("1. Create a campaign with 'All Customers' target audience")
    print("2. Select your SendGrid provider in the campaign")
    print("3. Send the campaign emails")
    print("4. Check the campaign statistics to see delivery results")

if __name__ == "__main__":
    main()
