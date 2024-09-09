from django.contrib.auth import get_user_model
from openai.types.beta import AssistantResponseFormatParam

from assistant.tools import Assistant
from user.services import UserService
from .functions import update_user_basic_data, update_user_skills, create_user_education, create_certificate, \
    create_experience, create_portfolio

User = get_user_model()


class AIUserService:
    user_service = UserService

    @staticmethod
    def generate_user_data_based_on_cv(user: User):
        document_queryset = user.user_documents.filter(is_ai_sync=True, purpose="cv")
        if document_queryset:
            assistant_object = Assistant(user=user, document_query=document_queryset,
                                         instruction="you need to read the cv file and generate user data",
                                         functions=[
                                             update_user_basic_data,
                                             update_user_skills,
                                             create_user_education,
                                             create_certificate,
                                             create_experience,
                                             create_portfolio
                                         ])

            try:
                assistant_object.send_message("start")
            except ValueError as e:
                print(e)

    @staticmethod
    def get_user_cv_note(user: User) -> dict:
        INSTRUCTION = """
Please analyze the attached resume and provide valuable feedback and suggestions based on the following areas:

Formatting and Layout:

Visual Appeal: Evaluate the use of fonts, spacing, and bullet points. Provide suggestions for improving the visual appeal of the resume.
Organization: Assess the structure and logical flow of sections. Recommend any improvements to the organization of information.
Content Evaluation:

Clarity and Relevance: Review the clarity of the descriptions and the relevance of the included information. Offer feedback on how to enhance these aspects.
Key Achievements: Highlight significant accomplishments. Provide suggestions for quantifying results and making key achievements stand out.
Gaps and Missing Information: Identify any gaps in work history or education. Recommend adding any missing details that would strengthen the resume.
Skills and Experience:

Skills Alignment: Assess how well the listed skills align with the job roles or career goals. Suggest ways to emphasize relevant skills.
Emphasis on Transferable Skills: Provide recommendations for highlighting transferable skills that are applicable to various roles.
Keywords and ATS Compatibility:

Relevant Keywords: Identify industry-specific keywords that should be included in the resume.
ATS-friendly Format: Offer tips on formatting the resume to ensure it is easily parsed by Applicant Tracking Systems (ATS).
Professionalism and Tone:

Writing Tone: Evaluate the overall tone of the resume, ensuring it is professional and confident. Provide feedback on any areas that could be improved.
Action Verbs: Recommend the use of strong action verbs to describe responsibilities and achievements effectively.
Customization:

Industry-specific Tips: Provide advice on tailoring the resume for specific industries.
Multiple Versions: Suggest creating different versions of the resume to target various job opportunities, if applicable.
                                        """
        document_queryset = user.user_documents.filter(is_ai_sync=True, purpose="cv")
        if document_queryset:
            example = {
                "Formatting_and_Layout": {
                    "visual_appeal": "Suggestions for using consistent fonts, proper spacing, and bullet points.",
                    "organization": "Advice on structuring sections logically, such as placing contact information at the top, followed by a summary, work experience, education, and skills."
                },
                "Content_Evaluation": {
                    "clarity_relevance": "Feedback on the clarity of descriptions and the relevance of included information.",
                    "key_achievements": "Highlighting significant accomplishments and providing suggestions for quantifying results.",
                    "gaps_missing_info": "Identifying any time gaps or missing details in work history or education."
                },
                "Skills_and_Experience": {
                    "skills_alignment": "Assessment of how well your listed skills match the job roles you are targeting.",
                    "emphasis_transferable_skills": "Suggestions for highlighting transferable skills that apply to various roles."
                },
                "Keywords_and_ATS_Compatibility": {
                    "relevant_keywords": "Identification of industry-specific keywords to include.",
                    "ATS_friendly_format": "Tips on formatting your resume to be easily parsed by ATS."
                },
                "Professionalism_and_Tone": {
                    "writing_tone": "Feedback on the overall tone of your resume, ensuring it's professional and confident.",
                    "action_verbs": "Recommendations for using strong action verbs to describe your responsibilities and achievements."
                },
                "Customization": {
                    "industry_specific_tips": "Advice on tailoring your resume for specific industries.",
                    "multiple_versions": "Suggestions for creating different versions of your resume to target various job opportunities."
                }
            }
            assistant_object = Assistant(user=user, document_query=document_queryset,
                                         instruction=INSTRUCTION,
                                         format_type={"type": "json_object"},
                                         model="gpt-4o",
                                         expected_dictionary=example
                                         )

            try:
                return assistant_object.send_message("start")
            except ValueError as e:
                print(e)
