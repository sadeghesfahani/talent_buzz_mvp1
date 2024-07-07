from django.contrib.auth import get_user_model
from django.db import transaction

from user.models import Skill

User = get_user_model()


class UserService:

    @staticmethod
    @transaction.atomic
    def create_user(email, first_name, last_name, phone_number, skills, certificates, education, bio, tags,
                    **extra_fields):
        """
        Create a user and associated details like personal, freelancer, etc.

        :param email: Email of the user
        :param first_name: First name of the user
        :param last_name: Last name of the user
        :param phone_number: Phone number of the user
        :param skills: List of skill names
        :param certificates: List of certificates
        :param education: List of education details
        :param bio: Biography of the user
        :param tags: Tags associated with the user
        :param extra_fields: Extra fields that may be provided
        """
        # Create the user
        user = User.objects.create_user(
            email=email,
            password=extra_fields.get('password', None),  # Assuming password might be provided in extra_fields
            phone_number=phone_number,
            **extra_fields
        )
        # Set additional fields if provided
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Handle Personal Details, assumes there's a bio and tags field
        # personal_detail.tags.set(tags)

        # Assuming skills are to be related to user via many-to-many
        if skills is None:
            skills = []
        for skill_name in skills:
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            user.skills.add(skill)
        user.save()

        return user

