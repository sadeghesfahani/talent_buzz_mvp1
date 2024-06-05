from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
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

        # Create Hives
        self.public_hive = Hive.objects.create(name='Public Hive', description='A public hive for testing',
                                               hive_type='queen', is_public=True)
        self.public_hive.admins.add(self.user1)

        self.non_public_hive = Hive.objects.create(name='Non-Public Hive', description='A non-public hive for testing',
                                                   hive_type='queen', is_public=False)
        self.non_public_hive.admins.add(self.user1)

        # Create Nectar
        self.nectar = Nectar.objects.create(nectar_title='Test Nectar', nectar_description='A nectar for testing',
                                            nectar_hive=self.public_hive)

    def test_submit_hive_membership_application_public(self):
        """
        Test Scenario: Bee submits membership application to a public Hive.

        This test ensures that a bee can successfully submit a membership application
        to a public hive. It checks that the application is correctly linked to the hive
        and the bee, and that it is automatically accepted if the hive is public.
        """
        application = self.public_hive.submit_membership_application(self.bee1)
        self.assertEqual(application.hive, self.public_hive)
        self.assertEqual(application.bee, self.bee1)
        self.assertTrue(application.is_accepted)

        # Check that a Membership was automatically created and accepted
        membership = Membership.objects.get(hive=self.public_hive, bee=self.bee1)
        self.assertTrue(membership.is_accepted)

    def test_submit_hive_membership_application_non_public(self):
        """
        Test Scenario: Bee submits membership application to a non-public Hive.

        This test ensures that a bee can successfully submit a membership application
        to a non-public hive. It checks that the application is correctly linked to the hive
        and the bee, and that it is not automatically accepted if the hive is non-public.
        """
        application = self.non_public_hive.submit_membership_application(self.bee1)
        self.assertEqual(application.hive, self.non_public_hive)
        self.assertEqual(application.bee, self.bee1)
        self.assertFalse(application.is_accepted)

        # Check that no Membership was created
        with self.assertRaises(Membership.DoesNotExist):
            Membership.objects.get(hive=self.non_public_hive, bee=self.bee1)

    def test_accept_hive_membership_application(self):
        """
        Test Scenario: Admin accepts a bee's membership application to a Hive.

        This test ensures that a hive admin can accept a bee's membership application.
        It verifies that the application status is updated to accepted, records the
        acceptance time, and creates a corresponding membership record.
        """
        application = self.non_public_hive.submit_membership_application(self.bee1)
        application.accept_application(user=self.user1)
        self.assertTrue(application.is_accepted)
        self.assertIsNotNone(application.accepted_at)

        membership = Membership.objects.get(hive=self.non_public_hive, bee=self.bee1)
        self.assertTrue(membership.is_accepted)

    def test_submit_nectar_contract(self):
        """
        Test Scenario: Bee submits a contract application to a Nectar.

        This test checks that a bee can submit a contract application to a nectar.
        It ensures the contract is correctly linked to the nectar and the bee, and
        that it is initially not accepted.
        """
        contract = self.nectar.submit_contract(self.bee1)
        self.assertEqual(contract.nectar, self.nectar)
        self.assertEqual(contract.bee, self.bee1)
        self.assertFalse(contract.is_accepted)

    def test_accept_nectar_contract_application(self):
        """
        Test Scenario: Admin accepts a contract application for a Nectar.

        This test ensures that a hive admin can accept a bee's contract application
        for a nectar. It verifies that the contract status is updated to accepted and
        records the acceptance time.
        """
        contract = self.nectar.submit_contract(self.bee1)
        contract.accept_application(user=self.user1)
        self.assertTrue(contract.is_accepted)
        self.assertIsNotNone(contract.accepted_at)

    def test_leave_hive(self):
        """
        Test Scenario: Bee leaves a Hive.

        This test ensures that a bee can leave a hive. It verifies that the membership
        status is updated to not accepted and that the leave time is recorded.
        """
        membership = Membership.objects.create(hive=self.public_hive, bee=self.bee1,
                                               is_accepted=True)
        self.assertTrue(membership.is_accepted)
        self.assertIsNone(membership.left_at)

        membership.is_accepted = False
        membership.save()
        self.assertIsNotNone(membership.left_at)

    def test_double_application(self):
        """
        Test Scenario: Bee submits multiple applications to the same Hive.

        This test ensures that a bee cannot submit multiple membership applications
        to the same hive. It verifies that attempting to submit a second application
        raises a ValidationError.
        """
        self.public_hive.submit_membership_application(self.bee1)
        with self.assertRaises(ValidationError):
            self.public_hive.submit_membership_application(self.bee1)

    def test_hive_request_permissions(self):
        """
        Test Scenario: Non-admin user attempts to accept a Hive membership application.

        This test ensures that only hive admins can accept membership applications.
        It verifies that attempting to accept an application as a non-admin raises
        a ValidationError.
        """
        application = self.non_public_hive.submit_membership_application(self.bee1)
        with self.assertRaises(ValidationError):
            application.accept_application(user=self.user3)

    def test_nectar_contract_permissions(self):
        """
        Test Scenario: Non-admin user attempts to accept a Nectar contract application.

        This test ensures that only hive admins can accept contract applications for
        a nectar. It verifies that attempting to accept a contract application as a
        non-admin raises a ValidationError.
        """
        contract = self.nectar.submit_contract(self.bee1)
        with self.assertRaises(ValidationError):
            contract.accept_application(user=self.user3)
