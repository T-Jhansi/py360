from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.renewals.models import RenewalCase
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyType
from apps.channels.models import Channel
from decimal import Decimal

User = get_user_model()


class ClosedCasesAPITestCase(APITestCase):
    """Test cases for Closed Cases API"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            customer_code='CUS2025001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            profile='Normal'
        )
        
        # Create test policy type
        self.policy_type = PolicyType.objects.create(
            name='Life Insurance',
            code='LIFE001',
            category='Life'
        )
        
        # Create test policy
        self.policy = Policy.objects.create(
            policy_number='POL-00001',
            customer=self.customer,
            policy_type=self.policy_type,
            start_date='2024-01-01',
            end_date='2024-12-31',
            premium_amount=Decimal('10000.00'),
            sum_assured=Decimal('100000.00'),
            status='active'
        )
        
        # Create test channel
        self.channel = Channel.objects.create(
            channel_name='Online',
            channel_type='online',
            channel_source='Website',
            status='active'
        )
        
        # Create test renewal cases with different statuses
        self.renewed_case = RenewalCase.objects.create(
            case_number='CASE-001',
            batch_code='BATCH-2025-01-01-A',
            policy=self.policy,
            customer=self.customer,
            status='renewed',  # Closed case
            priority='medium',
            renewal_amount=Decimal('10500.00'),
            channel_id=self.channel,
            assigned_to=self.user
        )
        
        self.completed_case = RenewalCase.objects.create(
            case_number='CASE-002',
            batch_code='BATCH-2025-01-01-B',
            policy=self.policy,
            customer=self.customer,
            status='completed',  # Closed case
            priority='high',
            renewal_amount=Decimal('11000.00'),
            channel_id=self.channel,
            assigned_to=self.user
        )
        
        self.pending_case = RenewalCase.objects.create(
            case_number='CASE-003',
            batch_code='BATCH-2025-01-01-C',
            policy=self.policy,
            customer=self.customer,
            status='pending',  # Not a closed case
            priority='low',
            renewal_amount=Decimal('9500.00'),
            channel_id=self.channel,
            assigned_to=self.user
        )
    
    def test_closed_cases_list_authentication_required(self):
        """Test that authentication is required for closed cases list"""
        url = reverse('closed_cases:closed-cases-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_closed_cases_list_success(self):
        """Test successful retrieval of closed cases list"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Paginated response
        
        # Should return only closed cases (renewed and completed)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        
        # Check that only closed cases are returned
        case_numbers = [case['case_number'] for case in results]
        self.assertIn('CASE-001', case_numbers)  # renewed case
        self.assertIn('CASE-002', case_numbers)  # completed case
        self.assertNotIn('CASE-003', case_numbers)  # pending case should not be included
    
    def test_closed_cases_detail_success(self):
        """Test successful retrieval of closed case detail"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-detail', kwargs={'case_id': self.renewed_case.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('closed_case', response.data)
        
        case_data = response.data['closed_case']
        self.assertEqual(case_data['case_number'], 'CASE-001')
        self.assertEqual(case_data['status'], 'renewed')
    
    def test_closed_cases_search_functionality(self):
        """Test search functionality in closed cases"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-list')
        
        # Search by case number
        response = self.client.get(url, {'search': 'CASE-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['case_number'], 'CASE-001')
        
        # Search by customer name
        response = self.client.get(url, {'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)  # Both closed cases belong to John Doe
    
    def test_closed_cases_filter_by_priority(self):
        """Test filtering closed cases by priority"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-list')
        
        # Filter by high priority
        response = self.client.get(url, {'priority': 'high'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['case_number'], 'CASE-002')
    
    def test_closed_cases_stats_endpoint(self):
        """Test closed cases statistics endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_closed_cases', response.data)
        self.assertIn('priority_breakdown', response.data)
        self.assertIn('channel_breakdown', response.data)
        
        # Should count only closed cases
        self.assertEqual(response.data['total_closed_cases'], 2)
    
    def test_closed_cases_export_endpoint(self):
        """Test closed cases export endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('closed_cases:closed-cases-export-data')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('export_data', response.data)
        self.assertIn('total_records', response.data)
        
        # Should export only closed cases
        self.assertEqual(response.data['total_records'], 2)
        self.assertEqual(len(response.data['export_data']), 2)
