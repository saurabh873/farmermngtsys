from rest_framework import serializers
from .models import Farmer

class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'added_by']

    def validate_aadhar_id(self, value):
        """Ensure Aadhar ID is exactly 12 digits long."""
        if len(value) != 12 or not value.isdigit():
            raise serializers.ValidationError("Aadhar ID must be a 12-digit number")
        return value
