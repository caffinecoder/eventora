from rest_framework import serializers
from .models import Event, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug']


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing events (cards view)."""
    category_name   = serializers.CharField(source='category.name', read_only=True)
    spots_remaining = serializers.IntegerField(read_only=True)
    is_free         = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Event
        fields = [
            'id', 'title', 'slug', 'emoji', 'category_name',
            'event_date', 'start_time', 'venue', 'department',
            'registration_fee', 'is_free', 'status',
            'capacity', 'spots_remaining',
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    """Full serializer for event detail view."""
    category        = CategorySerializer(read_only=True)
    category_id     = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    spots_remaining = serializers.IntegerField(read_only=True)
    is_free         = serializers.BooleanField(read_only=True)
    is_full         = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    # ── Accept both YYYY-MM-DD and dd/mm/yyyy from the admin form ─────────────
    event_date = serializers.DateField(
        input_formats=['%Y-%m-%d', '%d/%m/%Y', 'iso-8601']
    )
    registration_deadline = serializers.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d', '%d/%m/%Y', 'iso-8601'],
        required=False, allow_null=True
    )

    class Meta:
        model  = Event
        fields = [
            'id', 'title', 'slug', 'description', 'emoji',
            'category', 'category_id',
            'event_date', 'start_time', 'end_time',
            'venue', 'department',
            'capacity', 'spots_remaining', 'is_full',
            'registration_fee', 'is_free',
            'registration_deadline', 'status',
            'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def create(self, validated_data):
        from django.utils.text import slugify
        import uuid
        title = validated_data.get('title', '')
        validated_data['slug'] = slugify(title) + '-' + str(uuid.uuid4())[:8]
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)