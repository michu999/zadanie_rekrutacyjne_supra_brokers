/**
 * Weather Module - Fetches weather data via backend API proxy
 */

const weatherCache = new Map();
const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

async function getWeatherForCity(city) {
    if (!city) return null;

    const cacheKey = city.toLowerCase().trim();

    // Check cache
    if (weatherCache.has(cacheKey)) {
        const cached = weatherCache.get(cacheKey);
        if (Date.now() - cached.timestamp < CACHE_DURATION) {
            return cached.data;
        }
        weatherCache.delete(cacheKey);
    }

    try {
        const response = await fetch(`/api/weather/${encodeURIComponent(city)}/`);
        const data = await response.json();

        if (!response.ok) {
            return { error: data.error || 'Błąd pobierania danych' };
        }

        // Cache result
        weatherCache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
        });

        return data;
    } catch (error) {
        console.error(`Weather error for ${city}:`, error);
        return { error: 'Błąd połączenia' };
    }
}

async function loadWeatherForAllContacts() {
    const cells = document.querySelectorAll('.weather-cell');
    if (cells.length === 0) return;

    // Collect unique cities
    const cityMap = new Map();
    cells.forEach(cell => {
        const city = cell.dataset.city;
        if (city) {
            const key = city.toLowerCase();
            if (!cityMap.has(key)) {
                cityMap.set(key, []);
            }
            cityMap.get(key).push(cell);
        }
    });

    // Fetch weather for each unique city
    for (const [city, cellList] of cityMap) {
        const weather = await getWeatherForCity(city);
        cellList.forEach(cell => updateWeatherCell(cell, weather));
    }
}

function updateWeatherCell(cell, weather) {
    const loading = cell.querySelector('.weather-loading');
    const data = cell.querySelector('.weather-data');
    const error = cell.querySelector('.weather-error');

    if (loading) loading.classList.add('d-none');

    if (!weather || weather.error) {
        if (error) {
            error.classList.remove('d-none');
            error.innerHTML = `<i class="bi bi-cloud-slash"></i> ${weather?.error || 'Brak danych'}`;
        }
        return;
    }

    if (data) {
        data.classList.remove('d-none');
        data.innerHTML = `
            <span class="temp"><i class="bi bi-thermometer-half"></i> ${formatTemp(weather.temperature)}</span><br>
            <span class="humidity"><i class="bi bi-droplet"></i> ${formatHumidity(weather.humidity)}</span><br>
            <span class="wind"><i class="bi bi-wind"></i> ${formatWind(weather.wind_speed)}</span>
        `;
    }
}

async function loadWeatherForDetailPage() {
    const card = document.querySelector('.weather-detail-card');
    if (!card) return;

    const city = card.dataset.city;
    if (!city) return;

    const weather = await getWeatherForCity(city);
    updateWeatherDetailCard(card, weather);
}

function updateWeatherDetailCard(card, weather) {
    const loading = card.querySelector('.weather-loading');
    const content = card.querySelector('.weather-content');
    const error = card.querySelector('.weather-error');

    if (loading) loading.classList.add('d-none');

    if (!weather || weather.error) {
        if (error) error.classList.remove('d-none');
        return;
    }

    if (content) {
        content.classList.remove('d-none');

        const temp = content.querySelector('.temperature');
        const humidity = content.querySelector('.humidity');
        const wind = content.querySelector('.wind-speed');
        const desc = content.querySelector('.weather-description');

        if (temp) temp.textContent = formatTemp(weather.temperature);
        if (humidity) humidity.textContent = formatHumidity(weather.humidity);
        if (wind) wind.textContent = formatWind(weather.wind_speed);
        if (desc) desc.textContent = weather.description || '';
    }
}

function formatTemp(temp) {
    return temp != null ? `${Math.round(temp)}°C` : '--°C';
}

function formatHumidity(humidity) {
    return humidity != null ? `${Math.round(humidity)}%` : '--%';
}

function formatWind(speed) {
    return speed != null ? `${Math.round(speed)} km/h` : '-- km/h';
}
