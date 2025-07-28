"""
Management command to populate policy types with default coverage details
"""
from django.core.management.base import BaseCommand
from apps.policies.models import PolicyType


class Command(BaseCommand):
    help = 'Populate policy types with default coverage details templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing policy types that already have coverage details',
        )

    def handle(self, *args, **options):
        update_existing = options['update_existing']
        
        # Coverage templates for different policy categories
        coverage_templates = {
            'Motor': {
                "primary_coverage": {
                    "sum_insured": 2500000,
                    "deductible": 63,
                    "coverage_ratio": "100%",
                    "support_coverage": "24/7"
                },
                "vehicle_protection": {
                    "comprehensive_coverage": {
                        "amount": 2500000,
                        "description": "Collision, theft, vandalism, natural disasters"
                    },
                    "own_damage": {
                        "amount": 1875000,
                        "description": "Physical damage to your vehicle"
                    },
                    "engine_protection": {
                        "amount": 1000000,
                        "description": "Engine and gearbox protection"
                    },
                    "zero_depreciation": {
                        "included": True,
                        "description": "No depreciation on claims"
                    }
                },
                "liability_coverage": {
                    "third_party_liability": {
                        "amount": 750000,
                        "description": "Legal liability for third party damages"
                    },
                    "personal_accident_owner": {
                        "amount": 1500000,
                        "description": "Personal accident cover for owner-driver"
                    },
                    "passenger_coverage": {
                        "amount": 200000,
                        "per_person": True,
                        "description": "Personal accident cover for passengers"
                    }
                },
                "additional_benefits": {
                    "enhanced_protection": {
                        "no_claim_bonus": "50%",
                        "roadside_assistance": True,
                        "key_replacement": True,
                        "emergency_towing": True
                    },
                    "add_on_covers": {
                        "engine_protection": True,
                        "return_to_invoice": True,
                        "consumable_cover": True,
                        "depreciation_cover": True
                    },
                    "financial_benefits": {
                        "cashless_garages": "4500+",
                        "quick_settlement": True,
                        "online_claim_filing": True,
                        "premium_discount": "15%"
                    }
                }
            },
            'Health': {
                "primary_coverage": {
                    "sum_insured": 500000,
                    "deductible": 5000,
                    "coverage_ratio": "100%",
                    "support_coverage": "24/7"
                },
                "medical_coverage": {
                    "hospitalization": {
                        "room_rent": {
                            "limit": "2% of sum insured per day",
                            "icu_charges": "Covered"
                        },
                        "surgery": {
                            "coverage": "100%",
                            "day_care_procedures": "Covered"
                        },
                        "pre_post_hospitalization": {
                            "pre_days": 30,
                            "post_days": 60,
                            "coverage": "100%"
                        }
                    },
                    "outpatient": {
                        "consultation": {
                            "limit": 5000,
                            "per_year": True
                        },
                        "diagnostics": {
                            "limit": 10000,
                            "per_year": True
                        }
                    }
                },
                "additional_benefits": {
                    "wellness": {
                        "health_checkup": {
                            "frequency": "Annual",
                            "amount": 5000
                        }
                    },
                    "emergency": {
                        "ambulance": {
                            "coverage": "100%",
                            "limit": 2000
                        }
                    }
                }
            },
            'Life': {
                "primary_coverage": {
                    "sum_assured": 1000000,
                    "policy_term": "20 years",
                    "premium_paying_term": "15 years",
                    "coverage_type": "Term Life"
                },
                "death_benefit": {
                    "natural_death": {
                        "amount": 1000000,
                        "description": "Death due to natural causes"
                    },
                    "accidental_death": {
                        "amount": 2000000,
                        "description": "Additional benefit for accidental death"
                    }
                },
                "riders": {
                    "critical_illness": {
                        "amount": 500000,
                        "diseases_covered": 25,
                        "description": "Coverage for critical illnesses"
                    },
                    "disability": {
                        "amount": 500000,
                        "type": "Permanent Total Disability",
                        "waiver_of_premium": True
                    }
                }
            },
            'Property': {
                "primary_coverage": {
                    "sum_insured": 5000000,
                    "property_type": "Residential",
                    "coverage_type": "Comprehensive",
                    "deductible": 10000
                },
                "structure_coverage": {
                    "building": {
                        "amount": 3000000,
                        "description": "Structure, fixtures, fittings"
                    },
                    "contents": {
                        "amount": 2000000,
                        "description": "Household goods, personal belongings"
                    }
                },
                "additional_coverage": {
                    "temporary_accommodation": {
                        "amount": 100000,
                        "description": "Alternative accommodation during repairs"
                    }
                }
            },
            'Travel': {
                "primary_coverage": {
                    "sum_insured": 100000,
                    "trip_duration": "30 days",
                    "destination": "International",
                    "coverage_type": "Comprehensive"
                },
                "medical_coverage": {
                    "emergency_medical": {
                        "amount": 50000,
                        "description": "Emergency medical treatment abroad"
                    },
                    "evacuation": {
                        "amount": 100000,
                        "description": "Emergency evacuation to home country"
                    }
                },
                "travel_coverage": {
                    "trip_cancellation": {
                        "amount": 10000,
                        "description": "Non-refundable trip costs"
                    },
                    "baggage_loss": {
                        "amount": 5000,
                        "description": "Lost or damaged baggage"
                    }
                }
            }
        }

        updated_count = 0
        created_count = 0

        for policy_type in PolicyType.objects.all():
            category = policy_type.category
            
            # Skip if policy type already has coverage details and update_existing is False
            if policy_type.coverage_details and not update_existing:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping {policy_type.name} - already has coverage details'
                    )
                )
                continue
            
            # Get template for this category
            template = coverage_templates.get(category, {})
            
            if template:
                policy_type.coverage_details = template
                policy_type.save()
                
                if policy_type.coverage_details:
                    updated_count += 1
                    action = "Updated"
                else:
                    created_count += 1
                    action = "Created"
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} coverage details for {policy_type.name} ({category})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No template found for category: {category} (Policy: {policy_type.name})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Updated: {updated_count}, Created: {created_count} policy types'
            )
        )
