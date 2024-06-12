from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import User, PersonalDetails, CompanyDetails, FreelancerDetails, Address


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Address
        exclude = ('user',)


class PersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDetails
        exclude = ('user',)


class CompanyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyDetails
        exclude = ('user',)


class FreelancerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreelancerDetails
        exclude = ('user',)


class UserSerializer(serializers.ModelSerializer):
    personal_details = PersonalDetailsSerializer(required=False)
    company_details = CompanyDetailsSerializer(required=False)
    freelancer_details = FreelancerDetailsSerializer(required=False)
    addresses = AddressSerializer(many=True, required=False)
    feedback_aggregates = serializers.SerializerMethodField()
    bee = serializers.SerializerMethodField()

    def get_bee(self, obj):
        from honeycomb.serializers import BeeSerializer
        try:
            bee = obj.bee
        except ObjectDoesNotExist:
            return None
        return BeeSerializer(bee).data

    @staticmethod
    def get_feedback_aggregates(obj):
        return obj.get_feedback_aggregates()

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    @staticmethod
    def update_or_create_nested_instance(user, association_name, associated_model, data):
        if data:
            associated_instance, _ = associated_model.objects.update_or_create(user=user, defaults=data)
            setattr(user, association_name, associated_instance)

    @staticmethod
    def update_or_create_addresses(user, addresses_data):
        existing_addresses = {address.id: address for address in user.addresses.all()}
        new_address_ids = []

        for address_data in addresses_data:
            address_id = address_data.get('id')
            if address_id and address_id in existing_addresses:
                # If the address exists, update its fields
                address = existing_addresses[address_id]
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
                new_address_ids.append(address_id)
            else:
                # If the address does not exist, create a new one
                new_address = Address.objects.create(user=user, **address_data)
                new_address_ids.append(new_address.id)

        # Remove addresses that are not included in the update
        for address_id in existing_addresses.keys():
            if address_id not in new_address_ids:
                existing_addresses[address_id].delete()

    def create(self, validated_data):
        personal_details_data = validated_data.pop('personal_details', None)
        company_details_data = validated_data.pop('company_details', None)
        freelancer_details_data = validated_data.pop('freelancer_details', None)
        addresses_data = validated_data.pop('addresses', None)
        password = validated_data.pop('password', None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        self.update_or_create_nested_instance(user, 'personal_details', PersonalDetails, personal_details_data)
        self.update_or_create_nested_instance(user, 'company_details', CompanyDetails, company_details_data)
        self.update_or_create_nested_instance(user, 'freelancer_details', FreelancerDetails, freelancer_details_data)
        if addresses_data:
            self.update_or_create_addresses(user, addresses_data)

        return user

    def update(self, instance, validated_data):
        personal_details_data = validated_data.pop('personal_details', None)
        company_details_data = validated_data.pop('company_details', None)
        freelancer_details_data = validated_data.pop('freelancer_details', None)
        addresses_data = validated_data.pop('addresses', None)
        password = validated_data.pop('password', None)

        # Update User instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        self.update_or_create_nested_instance(instance, 'personal_details', PersonalDetails, personal_details_data)
        self.update_or_create_nested_instance(instance, 'company_details', CompanyDetails, company_details_data)
        self.update_or_create_nested_instance(instance, 'freelancer_details', FreelancerDetails, freelancer_details_data)
        if addresses_data is not None:
            self.update_or_create_addresses(instance, addresses_data)

        return instance
