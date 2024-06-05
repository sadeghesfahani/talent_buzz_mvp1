from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract

User = get_user_model()

class HiveBeePlatformTests(TestCase):

    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(email='admin1@example.com', password='pass')
        self.user2 = User.objects.create_user(email='bee1@example.com', password='pass')
        self.user3 = User.objects.create_user(email='bee2@example.com', password='pass')

        # Create Bees
        self.bee1 = Bee.objects.create(user=self.user2)
        self.bee2 = Bee.objects.create(user=self.user3)

        # Create Hive
        self.hive = Hive.objects.create(name='Test Hive', description='A hive for testing', hive_type='queen', is_public=True)
        self.hive.admins.add(self.user1)

        # Create Nectar
        self.nectar = Nectar.objects.create(nectar_title='Test Nectar', nectar_description='A nectar for testing', nectar_hive=self.hive)

    def test_submit_hive_membership_application(self):
        # Bee submits membership application to a Hive
        application = self.hive.submit_membership_application(self.bee1)
        self.assertEqual(application.hive, self.hive)
        self.assertEqual(application.bee, self.bee1)
        self.assertFalse(application.is_accepted)

    def test_accept_hive_membership_application(self):
        # Bee submits application
        application = self.hive.submit_membership_application(self.bee1)
        # Admin accepts application
        application.accept_application(user=self.user1)
        self.assertTrue(application.is_accepted)
        self.assertIsNotNone(application.accepted_at)

        # Check that a Membership was created
        membership = Membership.objects.get(membership_hive=self.hive, membership_bee=self.bee1)
        self.assertTrue(membership.is_accepted)

    def test_submit_nectar_contract(self):
        # Bee submits contract application to a Nectar
        contract = self.nectar.submit_contract(self.bee1)
        self.assertEqual(contract.nectar, self.nectar)
        self.assertEqual(contract.bee, self.bee1)
        self.assertFalse(contract.is_accepted)

    def test_accept_nectar_contract_application(self):
        # Bee submits contract application
        contract = self.nectar.submit_contract(self.bee1)
        # Admin accepts contract
        contract.accept_application(user=self.user1)
        self.assertTrue(contract.is_accepted)
        self.assertIsNotNone(contract.accepted_at)

    def test_leave_hive(self):
        # Bee joins hive
        membership = Membership.objects.create(membership_hive=self.hive, membership_bee=self.bee1, is_accepted=True)
        self.assertTrue(membership.is_accepted)
        self.assertIsNone(membership.left_at)

        # Bee leaves hive
        membership.is_accepted = False
        membership.save()
        self.assertIsNotNone(membership.left_at)

    def test_double_application(self):
        # Bee submits application
        self.hive.submit_membership_application(self.bee1)
        with self.assertRaises(ValidationError):
            # Bee tries to submit another application
            self.hive.submit_membership_application(self.bee1)

    def test_hive_request_permissions(self):
        # Bee submits application
        application = self.hive.submit_membership_application(self.bee1)
        with self.assertRaises(ValidationError):
            # Another user tries to accept the application
            application.accept_application(user=self.user3)

    def test_nectar_contract_permissions(self):
        # Bee submits contract application
        contract = self.nectar.submit_contract(self.bee1)
        with self.assertRaises(ValidationError):
            # Another user tries to accept the contract application
            contract.accept_application(user=self.user3)
