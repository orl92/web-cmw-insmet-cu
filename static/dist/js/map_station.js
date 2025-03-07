// Crear el elemento raíz
var root = am5.Root.new("chartdiv");

// Establecer temas
root.setThemes([
    am5themes_Animated.new(root)
]);

// Crear el gráfico del mapa
var chart = root.container.children.push(am5map.MapChart.new(root, {
    panX: "none",
    panY: "none",
    projection: am5map.geoMercator(),
    maxZoomLevel: 1,
}));

// Cargar datos geográficos
am5.net.load("static/dist/json/contry_data.json", chart).then(function (result) {
    var geo = am5.JSONParser.parse(result.response);
    loadGeodata(geo.country_code);
});

// Crear serie de polígonos para continentes
var polygonSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {
    calculateAggregates: true,
    valueField: "value"
}));

// Función para cargar geodatos
function loadGeodata(country) {
    // Cálculo de qué mapa usar
    am5.net.load("static/dist/json/camagueyLow.json", chart).then(function (result) {
        var geodata = am5.JSONParser.parse(result.response);
        var data = [];
        for (var i = 0; i < geodata.features.length; i++) {
            data.push({
                id: geodata.features[i].id,
                value: Math.round(Math.random() * 10000)
            });
        }
        polygonSeries.set("geoJSON", geodata);
        polygonSeries.data.setAll(data);
    });
}

// Crear serie de puntos para las estaciones
var pointSeries = chart.series.push(
    am5map.MapPointSeries.new(root, {})
);


// Función para cargar las estaciones desde la API
function cargarEstaciones() {
    fetch('/api/stations/')
        .then(response => response.json())
        .then(data => {
            data.forEach(station => {
                addCity(station.longitude, station.latitude, station.name, station.number);
            });
        });
}

// Definir los SVG como strings
var windSvg = '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-wind" width="44" height="44" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 8h8.5a2.5 2.5 0 1 0 -2.34 -3.24" /><path d="M3 12h15.5a2.5 2.5 0 1 1 -2.34 3.24" /><path d="M4 16h5.5a2.5 2.5 0 1 1 -2.34 3.24" /></svg>';
var rainSvg = '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-cloud-rain" width="44" height="44" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 18a4.6 4.4 0 0 1 0 -9a5 4.5 0 0 1 11 2h1a3.5 3.5 0 0 1 0 7" /><path d="M11 13v2m0 3v2m4 -5v2m0 3v2" /></svg>';
var humiditySvg = '<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-droplet" width="44" height="44" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7.502 19.423c2.602 2.105 6.395 2.105 8.996 0c2.602 -2.105 3.262 -5.708 1.566 -8.546l-4.89 -7.26c-.42 -.625 -1.287 -.803 -1.936 -.397a1.376 1.376 0 0 0 -.41 .397l-4.893 7.26c-1.695 2.838 -1.035 6.441 1.567 8.546z" /></svg>';

// Definir las variables para almacenar los datos
var temperaturasDelDia = {};

// Función para agregar una estación al mapa
function addCity(longitude, latitude, title, numero) {
    var hour = obtenerHorarioUTC();
    // console.log(`Solicitando datos para la estación ${numero} a la hora ${hour}`);

    fetch(`/api/station/observation/${hour}/${numero}/`)
        .then(response => response.json())
        .then(datos => {
            // Seleccionar los elementos HTML
            var stationDetails = document.getElementById('station-details');
            var stationDate = document.getElementById('station-date');
            var stationTitle = document.getElementById('station-title');
            var stationWeather = document.getElementById('station-weather');
            var stationTemperature = document.getElementById('station-temperature');
            var stationTemperatures = document.getElementById('station-temperatures');
            var stationHumidity = document.getElementById('station-humidity');
            var stationWind = document.getElementById('station-wind');
            var stationRain3h = document.getElementById('station-rain-3h');
            var stationRain24h = document.getElementById('station-rain-24h');

            // Si hay datos, actualizar el contenido de los elementos y almacenar los datos en las variables
            if (datos && datos.data && datos.data.temperatura !== undefined) {
                stationDate.textContent = `${datos.data.dia} ${datos.data.hora}`;
                stationTitle.textContent = `${title}, No. ${numero}`;
                stationWeather.textContent = `${datos.data["estado del cielo"]}`;
                stationTemperature.innerHTML = `<strong>${datos.data.temperatura} °C</strong>`;
                
                // Comprobar si las temperaturas máximas y mínimas están disponibles
                if (datos.data["temperatura maxima"] !== undefined && datos.data["temperatura minima"] !== undefined) {
                    // Si no existe un objeto para esta estación, inicializar uno
                    if (!temperaturasDelDia[numero]) {
                        temperaturasDelDia[numero] = {};
                    }
                    // Si están disponibles, actualizar las temperaturas máximas y mínimas del día
                    if (!temperaturasDelDia[numero].maxima || datos.data["temperatura maxima"] > temperaturasDelDia[numero].maxima) {
                        temperaturasDelDia[numero].maxima = datos.data["temperatura maxima"];
                    }
                    if (!temperaturasDelDia[numero].minima || datos.data["temperatura minima"] < temperaturasDelDia[numero].minima) {
                        temperaturasDelDia[numero].minima = datos.data["temperatura minima"];
                    }
                }

                // Mostrar las temperaturas máximas y mínimas del día
                stationTemperatures.textContent = `${temperaturasDelDia[numero].maxima} / ${temperaturasDelDia[numero].minima}`;

                // Mostrar el resto de los datos directamente desde la API
                stationHumidity.innerHTML = `${humiditySvg} ${datos.data["humedad relativa"]} %`;
                stationWind.innerHTML = `${windSvg} <strong>${datos.data["velocidad del viento"]} km/h</strong> ${datos.data["direccion del viento"]}`;
                stationRain3h.innerHTML = `${rainSvg} <strong>${datos.data["precipitacion en 3 horas"]} mm</strong> Últimas 3h`;
                stationRain24h.innerHTML = `${rainSvg} <strong>${datos.data["precipitacion en 24 horas"]} mm</strong> Últimas 24h`;

                // Definir el color del punto en el mapa
                var fillColor = am5.color('#00FF00');

                // Agregar el punto al mapa
                pointSeries.data.push({
                    geometry: { type: "Point", coordinates: [longitude, latitude] },
                    title: title,
                    fillColor: fillColor,
                    tooltipContent: stationDetails.innerHTML // Agregar el contenido del tooltip
                });
            } else {
                // Si no hay datos
                var fillColor = am5.color('#FF0000');
                pointSeries.data.push({
                    geometry: { type: "Point", coordinates: [longitude, latitude] },
                    title: title,
                    fillColor: fillColor,
                    tooltipContent: `${title}, No. ${numero}<hr>No existen datos para mostrar.` // Agregar el contenido del tooltip
                });
            }
        });
}


// Configuración de los puntos (bullets)
pointSeries.bullets.push(function (root, series, dataItem) {
    var circle = am5.Circle.new(root, {
        radius: 5,
        tooltipText: dataItem.dataContext.title, // Solo mostrar el nombre de la estación en el tooltip
        tooltipY: 0,
        fill: dataItem.dataContext.fillColor,
        stroke: root.interfaceColors.get("background"),
        strokeWidth: 2
    });

    // Actualizar la información de la estación al pasar el mouse sobre un punto
    circle.events.on("pointerover", function() {
        var dataContext = dataItem.dataContext;
        var stationDetails = document.getElementById('station-details');
        stationDetails.innerHTML = dataContext.tooltipContent;
        document.body.style.cursor = "pointer"
    });

    // Restablecer el cursor a default
    circle.events.on("pointerout", function() {
        document.body.style.cursor = "default"
    });

    return am5.Bullet.new(root, {
        sprite: circle
    });
});

// Llamar a la función para cargar las estaciones después de inicializar el mapa
cargarEstaciones();

// Animar elementos al cargar
chart.appear(1000, 100);

function obtenerHorarioUTC() {
    var fechaLocal = new Date();
    var horaLocal = fechaLocal.getHours();
    var hour;

    // Define los rangos de horas locales y sus correspondientes horarios UTC
    var rangosHorariosUTC = [
        { localStart: 0, localEnd: 4, utc: '06' },   // 0 AM a 3:59 AM
        { localStart: 4, localEnd: 7, utc: '09' },   // 4 AM a 6:59 AM
        { localStart: 7, localEnd: 10, utc: '12' },  // 7 AM a 9:59 AM
        { localStart: 10, localEnd: 13, utc: '15' }, // 10 AM a 12:59 PM
        { localStart: 13, localEnd: 16, utc: '18' }, // 1 PM a 3:59 PM
        { localStart: 16, localEnd: 19, utc: '21' }, // 4 PM a 6:59 PM
        { localStart: 19, localEnd: 22, utc: '00' }, // 7 PM a 9:59 PM
        { localStart: 22, localEnd: 24, utc: '03' }  // 10 PM a 12:59 AM
    ];

    // Encuentra el rango que corresponde a la hora local actual
    for (var i = 0; i < rangosHorariosUTC.length; i++) {
        if (horaLocal >= rangosHorariosUTC[i].localStart && horaLocal < rangosHorariosUTC[i].localEnd) {
            hour = rangosHorariosUTC[i].utc;
            break;
        }
    }

    // Si no se encuentra un rango, puedes definir un valor predeterminado o manejar el caso como prefieras
    if (hour === undefined) {
        hour = 'Hora no definida en los rangos';
    }

    return hour;
}
