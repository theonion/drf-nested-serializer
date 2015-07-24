from rest_framework.serializers import ValidationError
from six import string_types

def has_id_field(value):
    if value is None:
        raise ValidationError('Nested object must contain an `id` attribute.')
    if isinstance(value, string_types):
        raise ValidationError(value)
