import requests
from urllib.parse import unquote
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.core.cache import cache

from .models import Contact
from .serializers import ContactSerializer, ContactListSerializer


# Weather API configuration
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 15

# Weather code descriptions (Polish)
WEATHER_CODES = {
    0: "Bezchmurnie", 1: "Głównie bezchmurnie", 2: "Częściowe zachmurzenie",
    3: "Pochmurno", 45: "Mgła", 48: "Szadź", 51: "Lekka mżawka",
    53: "Umiarkowana mżawka", 55: "Gęsta mżawka", 61: "Lekki deszcz",
    63: "Umiarkowany deszcz", 65: "Silny deszcz", 71: "Lekki śnieg",
    73: "Umiarkowany śnieg", 75: "Silny śnieg", 80: "Przelotne opady",
    81: "Umiarkowane przelotne opady", 82: "Silne przelotne opady",
    95: "Burza", 96: "Burza z gradem", 99: "Silna burza z gradem"
}

# Fallback coordinates for Polish cities (used when Nominatim is unreachable)
POLISH_CITIES_COORDS = {
    'warszawa': (52.2297, 21.0122),
    'kraków': (50.0647, 19.9450),
    'krakow': (50.0647, 19.9450),
    'wrocław': (51.1079, 17.0385),
    'wroclaw': (51.1079, 17.0385),
    'poznań': (52.4064, 16.9252),
    'poznan': (52.4064, 16.9252),
    'gdańsk': (54.3520, 18.6466),
    'gdansk': (54.3520, 18.6466),
    'łódź': (51.7592, 19.4560),
    'lodz': (51.7592, 19.4560),
    'szczecin': (53.4285, 14.5528),
    'lublin': (51.2465, 22.5684),
    'katowice': (50.2649, 19.0238),
    'bydgoszcz': (53.1235, 18.0084),
    'białystok': (53.1325, 23.1688),
    'bialystok': (53.1325, 23.1688),
}


class ContactListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating contacts."""

    queryset = Contact.objects.all()
    serializer_class = ContactListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search filter
        search = self.request.query_params.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(city__icontains=search)
            )

        # Status filter
        status_id = self.request.query_params.get('status', '')
        if status_id:
            queryset = queryset.filter(status_id=status_id)

        # Sorting
        sort_by = self.request.query_params.get('sort', 'date_added')
        sort_order = self.request.query_params.get('order', 'desc')

        valid_fields = ['last_name', 'date_added', 'first_name']
        if sort_by not in valid_fields:
            sort_by = 'date_added'

        order_prefix = '-' if sort_order == 'desc' else ''
        queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContactSerializer
        return ContactListSerializer

    def create(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            return Response({
                'message': 'Kontakt został utworzony pomyślnie',
                'contact': ContactSerializer(contact).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Błąd walidacji',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ContactDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for retrieving, updating, and deleting a single contact."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            contact = serializer.save()
            return Response({
                'message': 'Kontakt został zaktualizowany pomyślnie',
                'contact': ContactSerializer(contact).data
            })
        return Response({
            'message': 'Błąd walidacji',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        contact_name = f"{instance.first_name} {instance.last_name}"
        self.perform_destroy(instance)
        return Response({
            'message': f'Kontakt "{contact_name}" został usunięty pomyślnie'
        }, status=status.HTTP_200_OK)


class WeatherAPIView(APIView):
    """API endpoint for weather data with caching and fallback coordinates."""

    def get(self, request, city):
        if not city or len(city) < 2:
            return Response({'error': 'Nieprawidłowa nazwa miasta'}, status=status.HTTP_400_BAD_REQUEST)

        # Decode and normalize city name
        city_decoded = unquote(city)
        city_normalized = city_decoded.lower().strip()

        # Check cache first
        cache_key = f'weather_{city_normalized.replace(" ", "_")}'
        cached_weather = cache.get(cache_key)
        if cached_weather:
            return Response(cached_weather)

        try:
            lat, lon = None, None

            # Try fallback coordinates first for Polish cities
            if city_normalized in POLISH_CITIES_COORDS:
                lat, lon = POLISH_CITIES_COORDS[city_normalized]
            else:
                # Try Nominatim geocoding API
                try:
                    headers = {'User-Agent': 'DjangoContactManager/1.0 (recruitment-task)'}
                    params = {'q': city_decoded, 'format': 'json', 'limit': 1}
                    geo_response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                    geo_response.raise_for_status()
                    geo_data = geo_response.json()

                    if geo_data:
                        lat = float(geo_data[0]['lat'])
                        lon = float(geo_data[0]['lon'])
                except requests.RequestException:
                    pass

            if lat is None or lon is None:
                return Response({'error': 'Nie znaleziono miasta'}, status=status.HTTP_404_NOT_FOUND)

            # Fetch weather from Open-Meteo API
            weather_params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': 'true',
                'hourly': 'relativehumidity_2m',
                'timezone': 'Europe/Warsaw'
            }

            weather_response = requests.get(OPEN_METEO_URL, params=weather_params, timeout=REQUEST_TIMEOUT)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            current = weather_data.get('current_weather', {})

            # Extract humidity from hourly data
            humidity = None
            hourly = weather_data.get('hourly', {})
            if 'relativehumidity_2m' in hourly:
                from datetime import datetime
                current_hour = datetime.now().hour
                humidity_list = hourly['relativehumidity_2m']
                if current_hour < len(humidity_list):
                    humidity = humidity_list[current_hour]

            weather_code = current.get('weathercode', 0)

            response_data = {
                'city': city_decoded,
                'temperature': current.get('temperature'),
                'humidity': humidity,
                'wind_speed': current.get('windspeed'),
                'description': WEATHER_CODES.get(weather_code, 'Nieznane')
            }

            # Cache result for 30 minutes
            cache.set(cache_key, response_data, timeout=1800)

            return Response(response_data)

        except requests.Timeout:
            return Response({'error': 'Przekroczono czas oczekiwania'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.RequestException:
            return Response({'error': 'Błąd pobierania danych pogodowych'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception:
            return Response({'error': 'Wystąpił błąd'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
