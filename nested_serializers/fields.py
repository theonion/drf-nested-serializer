from rest_framework.validators import UniqueTogetherValidator

from .serializers import NestedModelSerializer
from .validators import has_id_field


class NestedModelField(NestedModelSerializer):
    class Meta(object):
        validators = (has_id_field, )

    def __init__(self, *args, **kwargs):
        """removes UniqueTogetherValidator because it's shit code - it's enforced by the db anyway
        """
        super(NestedModelField, self).__init__(*args, **kwargs)
        validators = []
        for validator in self.validators:
            if not isinstance(validator, UniqueTogetherValidator):
                validators.append(validator)
        self.validators = validators

    def to_internal_value(self, data):
        if 'id' not in data:
            return None
        try:
            return self.Meta.model.objects.get(pk=data['id'])
        except self.Meta.model.DoesNotExist as exc:
            return str(exc)
