from rest_framework import serializers

from common.models import Document
from common.serializers import DocumentSerializer
from .models import User, Address, Skill, Portfolio, Certificate, Education, Experience, AvailableTimeSlot


class BaseMeta:
    exclude = ('user',)


class UserAndDocumentMixin(serializers.ModelSerializer):
    def handle_documents(self, instance, documents_data):
        for doc_data in documents_data:
            doc_id = doc_data.get('id')
            if doc_id:
                # Update an existing document if an ID is provided
                Document.objects.filter(id=doc_id).update(**doc_data)
            else:
                # Create a new document and add it to the instance
                new_doc = Document.objects.create(**doc_data)
                instance.documents.add(new_doc)

    def create(self, validated_data):
        documents_data = validated_data.pop('documents', [])
        validated_data['user'] = self.context['request'].user
        instance = super().create(validated_data)
        self.handle_documents(instance, documents_data)
        return instance

    def update(self, instance, validated_data):
        documents_data = validated_data.pop('documents', [])
        instance.user = self.context['request'].user
        instance = super().update(instance, validated_data)
        self.handle_documents(instance, documents_data)
        return instance


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Address
        exclude = ('user',)


class SkillSerializer(serializers.ModelSerializer):
    sub_skills = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    parents = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all(), required=False)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'type', 'equivalents', 'description', 'parents', 'sub_skills']


class PortfolioReadSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Portfolio
        exclude = ('user',)


class PortfolioWriteSerializer(UserAndDocumentMixin):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Portfolio
        exclude = ('user',)


class CertificateReadSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateWriteSerializer(UserAndDocumentMixin):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Certificate
        exclude = ('user',)


class EducationReadSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Education
        fields = '__all__'


class EducationWriteSerializer(UserAndDocumentMixin):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Education
        exclude = ('user',)


class ExperienceReadSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Experience
        fields = '__all__'


class ExperienceWriteSerializer(UserAndDocumentMixin):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Experience
        exclude = ('user',)


class AvailableTimeSlotSerializer(serializers.ModelSerializer):
    occurrences = serializers.SerializerMethodField()

    def get_occurrences(self, obj):
        return obj.occurrences()

    class Meta:
        model = AvailableTimeSlot
        fields = '__all__'


class UserBaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}


class UserBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('skills',)
        extra_kwargs = {'password': {'write_only': True}}


class UserListSerializer(serializers.ModelSerializer):
    feedback_aggregates = serializers.SerializerMethodField()

    @staticmethod
    def get_feedback_aggregates(obj):
        return obj.get_feedback_aggregates()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'company_name', 'points', 'level', 'feedback_aggregates']


class UserWithRelatedFieldsSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, required=False)
    feedback_aggregates = serializers.SerializerMethodField()
    experiences = ExperienceReadSerializer(many=True, required=False)
    educations = EducationReadSerializer(many=True, required=False)
    certificates = CertificateReadSerializer(many=True, required=False)
    portfolios = PortfolioReadSerializer(many=True, required=False)
    available_time_slots = AvailableTimeSlotSerializer(many=True, required=False)

    skills = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    @staticmethod
    def get_feedback_aggregates(obj):
        return obj.get_feedback_aggregates()

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

# class UserSerializer(serializers.ModelSerializer):
#     addresses = AddressSerializer(many=True, required=False)
#     feedback_aggregates = serializers.SerializerMethodField()
#     bee = serializers.SerializerMethodField()
#     experiences = ExperienceSerializer(many=True, required=False)
#     educations = EducationSerializer(many=True, required=False)
#     certificates = CertificateSerializer(many=True, required=False)
#     portfolios = PortfolioSerializer(many=True, required=False)
#     available_time_slots = AvailableTimeSlotSerializer(many=True, required=False)
#
#     skills = serializers.ListField(
#         child=serializers.CharField(),
#         write_only=True,
#         required=False
#     )
#
#     def get_bee(self, obj):
#         from honeycomb.serializers import BeeSerializer
#         try:
#             bee = obj.bee
#         except ObjectDoesNotExist:
#             return None
#         return BeeSerializer(bee).data
#
#     @staticmethod
#     def get_feedback_aggregates(obj):
#         return obj.get_feedback_aggregates()
#
#     class Meta:
#         model = User
#         fields = '__all__'
#         extra_kwargs = {'password': {'write_only': True}}
#
#     @transaction.atomic
#     def create(self, validated_data):
#         nested_data = self.extract_nested_data(validated_data)
#         user = User.objects.create(**validated_data)
#         self.setup_nested_data(user, nested_data)
#         return user
#
#     @transaction.atomic
#     def update(self, instance, validated_data):
#         nested_data = self.extract_nested_data(validated_data)
#         instance = super(UserSerializer, self).update(instance, validated_data)
#         self.setup_nested_data(instance, nested_data)
#         return instance
#
#     def extract_nested_data(self, validated_data):
#         nested_data = {
#             'skills': validated_data.pop('skills', []),
#         }
#         return nested_data
#
#     def setup_nested_data(self, user, nested_data):
#         self.set_skills(user, nested_data['skills'])
#
#     def set_skills(self, user, skill_names):
#         skill_objs = []
#         for name in skill_names:
#             skill, _ = Skill.objects.get_or_create(name=name)
#             skill_objs.append(skill)
#         user.skills.set(skill_objs)
