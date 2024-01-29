from rest_framework import serializers

from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Crew,
    Flight
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "capacity")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )


class RouteDetailSerializer(RouteSerializer):
    source = AirportSerializer(many=False, read_only=True)
    destination = AirportSerializer(many=False, read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "crew", "departure_time", "arrival_time")


class FlightListSerializer(FlightSerializer):
    route_source = serializers.CharField(
        source="route.source", read_only=True
    )
    route_destination = serializers.CharField(
        source="route.destination", read_only=True
    )
    airplane_name = serializers.CharField(
        source="airplane.name", read_only=True
    )
    airplane_capacity = serializers.IntegerField(
        source="airplane.capacity", read_only=True
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_source",
            "route_destination",
            "airplane_name",
            "airplane_capacity",
            "crew",
            "departure_time",
            "arrival_time",
            "tickets_available"
        )


class FlightDetailSerializer(FlightSerializer):
    route = RouteListSerializer(many=False, read_only=True)
    airplane = AirplaneSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
