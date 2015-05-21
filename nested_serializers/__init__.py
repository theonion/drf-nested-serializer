__version__ = "0.1"

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from rest_framework import serializers
from rest_framework.fields import set_value, empty
from rest_framework.compat import OrderedDict


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
                

        # Delete any unattached objects (only if we have a parent model that we depend on...)
        for obj_id, obj in current_objects.items():
            obj.delete()

        return return_instances


class NestedModelSerializer(serializers.ModelSerializer):

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return NestedListSerializer(*args, **kwargs)

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
