from django.db import transaction

from rest_framework import serializers
from rest_framework.fields import set_value, empty
from rest_framework.compat import OrderedDict
from rest_framework.serializers import ValidationError
from rest_framework.utils import model_meta
from rest_framework.utils.field_mapping import get_nested_relation_kwargs


class NestedListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        return_instances = []

        for child_data in validated_data:
            if child_data.get("id", empty) is empty:
                # we don't want to descend into creating objects, so throw a validation error
                # here and inform the user to create the related object before saving the
                # instance in operation
                raise ValidationError("Nested objects must exist prior to creating this parent instance.")

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
            try:
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

            except AttributeError:
                # this is an actual object, so add it to the return instances
                return_instances.append(child_data)

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
        try:
            ret = super(NestedModelSerializer, self).to_internal_value(data)
        except AssertionError:
            raise ValidationError({self.__class__.__name__: "Cannot descend and create nested objects."})

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
        m2m_fields = {}

        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer):
                child_instances = getattr(instance, key)

                # If this field is a serializer, we probably are dealing with a nested object
                if isinstance(validated_data.get(key), list):
                    # This will get handled in NestedListSerializer...
                    nested_data = validated_data.pop(key)
                    updated_data = field.update(child_instances.all(), nested_data)
                    m2m_fields[key] = updated_data

                elif isinstance(validated_data.get(key), (dict, OrderedDict)):
                    # Looks like we're dealing with some kind of ForeignKey
                    nested_data = validated_data.pop(key)
                    if nested_data.get("id", empty) is empty:
                        # No id, so it looks like we've got a create...
                        try:
                            del nested_data["id"]
                        except KeyError:
                            pass
                        child_instance = field.create(nested_data)

                    else:
                        # Update
                        ChildClass = field.Meta.model
                        try:
                            child_instance = ChildClass.objects.get(pk=nested_data["id"])
                        except ChildClass.DoesNotExist:
                            child_instance = field.create(nested_data)
                        else:
                            del nested_data["id"]
                            child_instance = field.update(child_instance, nested_data)

                    validated_data[key] = child_instance

                elif validated_data.get(key, True) is None:
                    # null value passed - check if null allowed for field
                    ModelClass = self.Meta.model
                    model_field = ModelClass._meta.get_field(key)
                    if model_field.null:
                        validated_data[key] = None

        # get the instance from super
        instance = super(NestedModelSerializer, self).update(instance, validated_data)

        # updated m2m fields
        for field_name, related_instances in m2m_fields.items():
            with transaction.atomic():
                try:
                    field = getattr(instance, field_name)
                    field.clear()
                    field.add(*related_instances)
                except Exception as exc:
                    pass

        # dump the instance
        return instance

    def create(self, validated_data):

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}

        # Save off the data
        for key, field in self.fields.items():
            if isinstance(field, serializers.BaseSerializer):
                if isinstance(validated_data.get(key), list):
                    # One-to-many...
                    nested_data = validated_data.pop(key)
                    many_to_many[key] = field.create(nested_data)

                elif isinstance(validated_data.get(key), dict):
                    import pdb
                    pdb.set_trace()
                    # ForeignKey
                    nested_data = validated_data.pop(key)
                    if nested_data.get("id", empty) is empty:
                        # we don't want to descend into creating objects, so throw a validation error
                        # here and inform the user to create the related object before saving the
                        # instance in operation
                        raise ValidationError("Nested objects must exist prior to creating this parent instance.")

                    else:
                        # Update
                        ChildClass = field.Meta.model
                        try:
                            child_instance = ChildClass.objects.get(pk=nested_data["id"])
                        except ChildClass.DoesNotExist:
                            child_instance = field.create(nested_data)
                        else:
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
