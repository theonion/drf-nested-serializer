from rest_framework import serializers


class NestedListSerializer(serializers.ListSerializer):


    def update(self, instance, validated_data):
        # instance is a qs...
        current_objects = {obj.id: obj for obj in instance}

        return_instances = []

        for child_data in validated_data:
            if "id" in child_data:
                child_instance = current_objects.pop(child_data["id"])

                return_instances.append(self.child.update(child_instance, child_data))
            else:
                return_instances.append(self.child.create(child_data))

        # Delete any unattached objects
        for obj_id, obj in current_objects.items():
            obj.delete()

        return return_instances


class NestedModelSerializer(serializers.ModelSerializer):

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return NestedListSerializer(*args, **kwargs)

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
                field.create(nested_data)

        return instance
