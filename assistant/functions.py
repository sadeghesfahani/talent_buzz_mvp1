from datetime import datetime
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from user.models import Skill, Education, Certificate, Experience, Portfolio
from user.serializers import SkillMinimalSerializer

User = get_user_model()


def update_user_basic_data(

        first_name: str,
        last_name: str,
        phone_number: str,
        bio: str,
        headline: str,
        tags: List[str],
        user: User,
        **kwargs

):
    """
    By calling this function, user's basic data will be updated with the provided information.

    :param first_name: First name of the user
    :param last_name: Last name of the user
    :param phone_number: Phone number of the user
    :param bio: Biography of the user
    :param headline: Headline of the user
    :param tags: Tags associated with the user
    :param user: User instance to update
    """

    # user = kwargs.get('user')
    # if user:
    #     raise ValueError("User must be provided")

    user.first_name = first_name
    user.last_name = last_name
    user.phone_number = phone_number
    user.bio = bio
    user.headline = headline

    if tags:
        user.tags.set(tags)

    user.save()
    print(f"User's basic data updated successfully: {user.first_name} {user.last_name}")


def update_user_skills(skills: List[str], user: User, **kwargs):
    """
    Updates user's skills based on the provided list of skill names.
    :param skills: List of skill names to be added or updated for the user.
    """
    # user = kwargs.get('user')
    # if not user:
    #     raise ValueError("User must be provided")

    existing_skills = Skill.objects.filter(name__in=skills)
    existing_skill_names = set(existing_skills.values_list('name', flat=True))
    not_found_skills = set(skills) - existing_skill_names

    # Add existing skills to the user
    if existing_skills:
        user.skills.add(*existing_skills)
        print(f"Added/updated skills for user {user.username}: {', '.join(skill.name for skill in existing_skills)}")

    # Handle skills not found in the database
    if not_found_skills:
        handle_no_skills_found(user, list(not_found_skills))


def handle_no_skills_found(user: User, skills: List[str]):
    """
    Handles the case where no skills are found matching the provided list.
    Attempts to retrieve parent skills from an assistant, retrying once if the initial attempt fails.

    :param user: User instance to process.
    :param skills: List of skill names that were not found.
    """
    from .tools import Assistant  # Ensure Assistant is properly implemented and imported
    expected_dictionary = {"parents": [1, 5, 12, 55, 156], "is_found_parents": True}

    assistant_object = Assistant(user=user, document_query=None,
                                 instruction="Find the parents for the skills by calling 'get_server_skills'. You will receive serialized data of all skills available on the server.",
                                 format_type="json_object",
                                 model="gpt-3.5-turbo",
                                 expected_dictionary=expected_dictionary,
                                 functions=[get_server_skills])

    for skill_name in skills:
        expected_dictionary_response = assistant_object.send_message(
            f"The skill I am looking for its parents is {skill_name}")

        new_skill, created = Skill.objects.get_or_create(name=skill_name)
        if created:
            print(f"Created new skill: {new_skill.name}")

        if expected_dictionary_response.is_found_parents:
            parent_ids = expected_dictionary_response.parents
            parents = Skill.objects.filter(id__in=parent_ids)
            new_skill.parents.set(parents)
            print(f"Skill '{new_skill.name}' has been linked to parent skills.")

        user.skills.add(new_skill)

    user.save()
    print("User's skills updated successfully.")


def get_server_skills():
    return SkillMinimalSerializer(Skill.objects.all(), many=True).data


def create_user_education(degree: str, major: Optional[str], university: Optional[str], user: User, **kwargs):
    """
     Create a new education record for the user.
    :param degree: it can be like, a bachelor, master, etc.
    :param major: what is the field of study, etc.
    :param university: university name
    :return: text message
    """

    # user = kwargs.get('user')
    # if not user:
    #     raise ValueError("User must be provided")
    Education.objects.create(user=user, degree=degree, major=major, university=university)
    print(f"Education record created for user {user.username}")


def create_certificate(user: User, title: str, institution: str, date_earned: Optional[str] = None,
                       description: Optional[str] = "", **kwargs):
    """
    Create a new certificate record for the user.
    :param title: title of the certificate
    :param institution: institution name
    :param date_earned: date when the certificate was earned in the format of "YYYY-MM-DD", optional
    :param description: description of the certificate, optional
    :return: text message
    """

    # user = kwargs.get('user')
    # if not user:
    #     raise ValueError("User must be provided")

    # Convert date_earned from string to date object if provided
    if date_earned:
        try:
            date_earned = datetime.strptime(date_earned, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")

    # Create the certificate entry in the database
    Certificate.objects.create(
        user=user,
        title=title,
        institution=institution,
        date_earned=date_earned,
        description=description
    )
    print(f"Certificate record created for user {user.username}")

    return f"Certificate for {title} from {institution} successfully created."


def create_experience(user: User, position: Optional[str], company: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None, description: Optional[str] = "", **kwargs):
    """
    Create a new experience record for the user.
    :param user: User instance to whom the experience belongs
    :param position: Position title, optional
    :param company: Company name
    :param start_date: Start date of the experience in the format "YYYY-MM-DD", optional
    :param end_date: End date of the experience in the format "YYYY-MM-DD", optional
    :param description: Description of the experience, optional
    """

    # user = kwargs.get('user')

    # Initialize date variables
    date_start = None
    date_end = None

    # Convert start_date from string to date object if provided
    if start_date:
        try:
            date_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid start date format. Please use YYYY-MM-DD format.")

    # Convert end_date from string to date object if provided
    if end_date:
        try:
            date_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid end date format. Please use YYYY-MM-DD format.")

    # Create the experience entry in the database
    Experience.objects.create(
        user=user,
        position=position,
        company=company,
        start_date=date_start,
        end_date=date_end,
        description=description
    )

    print(f"Experience record created for user {user.username} at {company}")
    return f"Experience record created for user {user.username} at {company}."


def create_portfolio(user: User, title: str, description: Optional[str] = "", link: Optional[str] = None, **kwargs):
    """
    Create a new portfolio record for the user.
    :param user: User instance to whom the portfolio belongs
    :param title: Title of the portfolio entry
    :param description: Description of the portfolio entry, optional
    :param link: URL link to the portfolio item, optional
    :return: Portfolio instance
    """

    # user = kwargs.get('user')

    # Create the portfolio entry in the database
    Portfolio.objects.create(
        user=user,
        title=title,
        description=description,
        link=link
    )

    print(f"Portfolio record created for user {user.username} with title '{title}'")
    return f"Portfolio record created for user {user.username} with title '{title}'"
