from .serializers import NestedModelSerializer
from .validators import has_id_field


class NestedModelField(NestedModelSerializer):
    class Meta(object):
        validators = (has_id_field, )

    def to_internal_value(self, data):
        if 'id' not in data:
            return None
        try:
            return self.Meta.model.objects.get(pk=data['id'])
        except self.Meta.model.DoesNotExist as exc:
            return str(exc)
