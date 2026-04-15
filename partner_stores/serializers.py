from rest_framework import serializers


class SavePlayerPartnerStoresSerializer(serializers.Serializer):
    player_id = serializers.IntegerField(required=True)
    store_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=False,
    )
