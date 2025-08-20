from rest_framework import serializers
class IntegerFieldFromString(serializers.IntegerField):
    """
    A custom serializer field to convert string values to integers.
    """

    def to_internal_value(self, data):
        # Convert the string value to an integer.
        try:
            return int(data)
        except (TypeError, ValueError):
            self.fail("invalid", input=data)