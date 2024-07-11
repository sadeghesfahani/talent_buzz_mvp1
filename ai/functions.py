from typing import List

from django.contrib.auth import get_user_model

from user.models import Skill

User = get_user_model()

def update_user_basic_data(

        first_name: str,
        last_name: str,
        phone_number: str,
        bio: str,
        tags: List[str],
        user=None,
        **kwargs

):
    """
    By calling this function, user's basic data will be updated with the provided information.

    :param first_name: First name of the user
    :param last_name: Last name of the user
    :param phone_number: Phone number of the user
    :param bio: Biography of the user
    :param tags: Tags associated with the user
    """


def update_user_skills(skills: List[str], user=None):
    """
    Updates user's skills based on the provided list of skill names.

    :param skills: List of skill names to be added or updated for the user.
    :param user: User instance whose skills are to be updated.
    """
    if not user:
        raise ValueError("User must be provided")

    # Query all skills that match any of the names in the 'skills' list
    skill_objects = Skill.objects.filter(name__in=skills)

    # If no skills are found, you can implement special logic here
    if not skill_objects.exists():
        # Special logic when no matching skills are found
        print("No matching skills found. Implementing special logic.")
        handle_no_skills_found(user, skills)
    else:
        # If skills are found, add them to the user
        user.skills.add(*skill_objects)  # Assuming 'skills' is a many-to-many field in User model
        print(f"Added/updated skills for user {user.username}: {', '.join(skill.name for skill in skill_objects)}")

def handle_no_skills_found(user: User, skills: List[str]):
    """
    Handles the case where no skills are found matching the provided list.
    Special logic to create new skills or perform other actions can be implemented here.

    :param user: User instance to process.
    :param skills: List of skill names that were not found.
    """
    # Example logic: create new skill entries and add to user
    for skill_name in skills:
        new_skill, created = Skill.objects.get_or_create(name=skill_name)
        if created:
            print(f"Created new skill: {new_skill.name}")
        user.skills.add(new_skill)
    user.save()  # Ensure to save the user instance after modifying related fields
