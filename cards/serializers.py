from rest_framework import serializers

from .models import Card, Category, Transaction

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'user', 'card_name','card_num', 'mm_yy', 'balance']
        read_only_fields = ['user', 'balance']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name',read_only=True)
    card_name = serializers.CharField(source='card.card_name',read_only=True)
    from_card = CardSerializer()
    to_card = CardSerializer()

    class Meta:
        model = Transaction
        fields = ['id', 'datetime', 'value', 'from_card', 'to_card', 'category_name', 'card_name']
class PaymentSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    card_id = serializers.IntegerField()
