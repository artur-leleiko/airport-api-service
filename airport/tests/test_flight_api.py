from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Route, Airport, Airplane, Flight, Crew, AirplaneType
from airport.serializers import (
    FlightListSerializer,
    FlightDetailSerializer,
)

FLIGHT_URL = reverse("airport:flight-list")


def sample_airport(name, closest_big_city):
    return Airport.objects.create(
        name=name, closest_big_city=closest_big_city
    )


def sample_route(source, destination, distance):
    return Route.objects.create(
        source=source, destination=destination, distance=distance
    )


def sample_airplane_type(name):
    return AirplaneType.objects.create(name=name)


def sample_airplane(name, rows, seats_in_row, airplane_type):
    return Airplane.objects.create(
        name=name,
        rows=rows,
        seats_in_row=seats_in_row,
        airplane_type=airplane_type
    )


def sample_crew(first_name, last_name):
    return Crew.objects.create(first_name=first_name, last_name=last_name)


def sample_flight(route, airplane, departure_time, arrival_time, crews=None):
    if crews is None:
        crews = []

    return Flight.objects.create(
        route=route,
        airplane=airplane,
        departure_time=departure_time,
        arrival_time=arrival_time
    )


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_flights(self):
        source = sample_airport("Test-1", "Kyiv")
        destination = sample_airport("Test-2", "Singapore")
        route = sample_route(source, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)
        sample_flight(
            route, airplane, "2023-07-25T10:00:00Z", "2023-07-25T15:00:00Z"
        )

        res = self.client.get(FLIGHT_URL)

        flights = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_source(self):
        source1 = sample_airport("Test-1", "Kyiv")
        source2 = sample_airport("Test-3", "Athens")
        destination = sample_airport("Test-2", "Singapore")
        route1 = sample_route(source1, destination, 1000)
        route2 = sample_route(source2, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)
        sample_flight(
            route1, airplane, "2023-07-25T10:00:00Z", "2023-07-25T15:00:00Z"
        )
        sample_flight(
            route2, airplane, "2023-07-26T12:00:00Z", "2023-07-26T17:00:00Z"
        )

        res = self.client.get(
            FLIGHT_URL, {"source": source1.closest_big_city}
        )

        flights = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).filter(route__source=source1)
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_destination(self):
        source = sample_airport("Test-1", "Kyiv")
        destination1 = sample_airport("Test-2", "Singapore")
        destination2 = sample_airport("Test-3", "Brussels")
        route1 = sample_route(source, destination1, 1000)
        route2 = sample_route(source, destination2, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)
        sample_flight(
            route1, airplane, "2023-07-25T10:00:00Z", "2023-07-25T15:00:00Z"
        )
        sample_flight(
            route2, airplane, "2023-07-26T12:00:00Z", "2023-07-26T17:00:00Z"
        )

        res = self.client.get(
            FLIGHT_URL, {"destination": destination1.closest_big_city}
        )

        flights = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).filter(route__destination=destination1)
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_departure_time(self):
        source = sample_airport("Test-1", "Kyiv")
        destination = sample_airport("Test-2", "Singapore")
        route = sample_route(source, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)
        sample_flight(
            route, airplane, "2023-07-25T10:00:00Z", "2023-07-25T15:00:00Z"
        )
        sample_flight(
            route, airplane, "2023-07-26T12:00:00Z", "2023-07-26T17:00:00Z"
        )

        res = self.client.get(FLIGHT_URL, {"departure_time": "2023-07-25"})

        flights = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).filter(departure_time__date="2023-07-25")
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_flight_detail(self):
        source = sample_airport("Test-1", "Kyiv")
        destination = sample_airport("Test-2", "Singapore")
        route = sample_route(source, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)
        crew1 = sample_crew("John", "Doe")
        crew2 = sample_crew("Jane", "Smith")
        flight = sample_flight(
            route,
            airplane,
            "2023-07-25T10:00:00Z",
            "2023-07-25T15:00:00Z",
            crews=[crew1, crew2]
        )

        url = reverse("airport:flight-detail", args=[flight.id])
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        source = sample_airport("Test-1", "Kyiv")
        destination = sample_airport("Test-2", "Singapore")
        route = sample_route(source, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2023-07-25T10:00:00Z",
            "arrival_time": "2023-07-25T15:00:00Z",
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        source = sample_airport("Test-1", "Kyiv")
        destination = sample_airport("Test-2", "Singapore")
        route = sample_route(source, destination, 1000)
        airplane_type = sample_airplane_type("Type1")
        airplane = sample_airplane("Airplane-1", 10, 6, airplane_type)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2023-07-25T10:00:00Z",
            "arrival_time": "2023-07-25T15:00:00Z",
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
