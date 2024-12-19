from rest_framework import serializers
from .models import Country, Hotel, Tour, Review, Booking, Person, BookingPerson


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'photo_url']


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'rating', 'country', 'nutrition', 'info', 'photo_url']


class TourSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_info = serializers.CharField(source="hotel.info",read_only=True)

    class Meta:
        model = Tour
        fields = ['id', 'name', 'country', 'hotel', 'date', 'photo_url', 'country_name', 'hotel_name','hotel_info']


class ReviewSerializer(serializers.ModelSerializer):
    star = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ['id', 'hotel', 'user', 'star', 'description']



class BookingPersonSerializer(serializers.ModelSerializer):
    person_category = serializers.CharField(source='person.category', read_only=True)
    person_price = serializers.DecimalField(source='person.price', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = BookingPerson
        fields = ['person_category', 'count', 'person_price']

class BookingSerializer(serializers.ModelSerializer):
    total_price = serializers.ReadOnlyField()
    booking_people = BookingPersonSerializer(many=True)
    tour = TourSerializer(read_only=True)
    tour_id = serializers.CharField(source='tour.id', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'tour', 'total_price', 'booking_people', 'is_paid', 'tour_id','datetime']

    def create(self, validated_data):
        people_data = validated_data.pop('booking_people', [])
        booking = super().create(validated_data)

        total_price = 0
        for person_data in people_data:
            category = person_data.get("category")
            count = person_data.get("count", 0)

            if count < 1 or not category:
                continue

            person = Person.objects.get(category=category)

            BookingPerson.objects.create(person=person, booking=booking, count=count)
            total_price += count * person.price

        booking.total_price = total_price
        booking.save()

        return booking


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'category', 'price']
        read_only_fields = ['id']
