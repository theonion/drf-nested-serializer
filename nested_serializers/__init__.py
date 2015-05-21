__version__ = "0.1"

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from rest_framework import serializers
from rest_framework.fields import set_value, empty
from rest_framework.compat import OrderedDict
from rest_framework.utils.field_mapping import get_nested_relation_kwargs


class NestedListSerializer(serializers.ListSerializer):

    def update(self, instance, validated_data):
        # instance is a qs...
        current_objects = {obj.id: obj for obj in instance}

        return_instances = []

        for child_data in validated_data:
            if child_data.get("id", empty) is empty:
                # The id field is empty, so this is a create

                if "id" in child_data:
                    # Need to kill this, because it's technically a read-only field
                    del child_data["id"]

                return_instances.append(self.child.create(child_data))
            else:
                # We have an id, so let's grab this sumbitch
                child_instance = current_objects.pop(child_data["id"])

                return_instances.append(self.child.update(child_instance, child_data))
                
        if self.parent:
            parent_model = self.parent.Meta.model
            child_model = self.child.Meta.model

            dependent_fields = [f for f in child_model._meta.get_fields() if
                f.is_relation and f.related_model == parent_model and not f.null]

            if dependent_fields:
                # Delete any unattached objects
                for obj_id, obj in current_objects.items():
                    obj.delete()


        return return_instances


class NestedModelSerializer(serializers.ModelSerializer):

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return NestedListSerializer(*args, **kwargs)

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Create nested fields for forward and reverse relationships.
        """
        class NestedSerializer(NestedModelSerializer):
            class Meta:
                model = relation_info.related_model
                depth = nested_depth - 1

        field_class = NestedSerializer
        field_kwargs = get_nested_relation_kwargs(relation_info)

        return field_class, field_kwargs

    def to_internal_value(self, data):
        ret = super(NestedModelSerializer, self).to_internal_value(data)

        # So, in the case that this object is nested, we really really need the id.
        if getattr(self, 'parent', None):

            child_model = self.Meta.model
            pk_field_name = child_model._meta.pk.name

            pk_field = self.fields[pk_field_name]

            primitive_value = pk_field.get_value(data)
            set_value(ret, pk_field.source_attrs, primitive_value)

            errors = OrderedDict()

        return ret

    def update(self, instance, validated_data):

        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer) and isinstance(validated_data.get(key), (list, dict)):
                # So, this looks like a nested field.
                nested_data = validated_data.pop(key)

                child_instances = getattr(instance, key)

                field.update(child_instances.all(), nested_data)

        return super(NestedModelSerializer, self).update(instance, validated_data)

    def create(self, validated_data):

        popped_data = {}

        # Save off the data
        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer) and isinstance(validated_data.get(key), (list, dict)):
                # So, this looks like a nested field.
                popped_data[key] = validated_data.pop(key)

        # Create the base instance
        instance = super(NestedModelSerializer, self).create(validated_data)  

        # Save the related fields
        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer) and isinstance(popped_data.get(key), (list, dict)):
                nested_data = popped_data[key]

                child_instances = getattr(instance, key)
                field.update(child_instances.all(), nested_data)

        return instance
