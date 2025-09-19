from rest_framework import serializers
from .models import Institution, Event, Review


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    event_name = serializers.CharField(source="event.name", read_only=True, allow_null=True)

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ["created_at"]

    def validate_institution(self, value):
        if not value:
            raise serializers.ValidationError("Institution is required")
        return value

    def validate_confidence(self, value):
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("Confidence should be between 0.0 and 1.0")
        return value
