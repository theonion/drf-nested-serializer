__version__ = "0.1"

from rest_framework import serializers
from rest_framework.fields import set_value, empty
from rest_framework.compat import OrderedDict
from rest_framework.utils import model_meta
from rest_framework.utils.field_mapping import get_nested_relation_kwargs


class NestedListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
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
                ModelClass = self.child.Meta.model

                child_instance = ModelClass.objects.get(pk=child_data["id"])
                return_instances.append(self.child.update(child_instance, child_data))

        return return_instances

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
        field_kwargs["read_only"] = False

        if field_kwargs.get("many"):
            field_kwargs["required"] = False

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
        """This methods acts just like it's parent, except that it creates and updates nested object"""

        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer):

                child_instances = getattr(instance, key)

                # TODO: DRY UP THIS SHIT....

                # If this field is a serializer, we probably are dealing with a nested object
                if isinstance(validated_data.get(key), list):
                    # This will get handled in NestedListSerializer...

                    nested_data = validated_data.pop(key)
                    field.update(child_instances.all(), nested_data)

                elif isinstance(validated_data.get(key), dict):
                    # Looks like we're dealing with some kind of ForeignKey

                    nested_data = validated_data.pop(key)
                    if nested_data.get("id", empty) is empty:
                        # No id, so it looks like we've got a create...

                        del nested_data["id"]
                        child_instance = field.create(nested_data)
                    else:
                        # Update
                        ChildClass = field.Meta.model
                        child_instance = ChildClass.objects.get(pk=nested_data["id"])

                        del nested_data["id"]

                        child_instance = field.update(child_instance, nested_data)
                    validated_data[key] = child_instance

        return super(NestedModelSerializer, self).update(instance, validated_data)

    def create(self, validated_data):

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        # Save off the data
        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer):
                if isinstance(validated_data.get(key), list):
                    # One-to-many...
                    nested_data = validated_data.pop(key)
                    field.create(nested_data)
                elif isinstance(validated_data.get(key), dict):
                    # ForeignKey
                    nested_data = validated_data.pop(key)
                    if nested_data.get("id", empty) is empty:
                        # No id, so it looks like we've got a create...

                        del nested_data["id"]
                        child_instance = field.create(nested_data)
                    else:
                        # Update
                        ChildClass = field.Meta.model
                        child_instance = ChildClass.objects.get(pk=nested_data["id"])

                        del nested_data["id"]

                        child_instance = field.update(child_instance, nested_data)

                    validated_data[key] = child_instance

        # Create the base instance
        instance = ModelClass.objects.create(**validated_data)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                setattr(instance, field_name, value)

        return instance
