/**
 * Clase Meteogram mejorada - Visualización meteorológica completa
 * Incluye todos los datos, ciclo día/noche y mejor representación
 */
class Meteogram {
    constructor(json, containerId, options = {}) {
        // Validación inicial del contenedor
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Contenedor con ID '${containerId}' no encontrado`);
        }

        // Limpiar contenedor antes de crear el gráfico
        this.container.innerHTML = '';

        // Datos meteorológicos
        this.weatherData = [];
        this.temperatures = [];
        this.precipitations = [];
        this.winds = [];
        this.pressures = [];
        this.humidities = [];
        this.dewPoints = [];
        this.visibility = [];

        // Configuración
        this.json = json;
        this.lat = options.lat || 0;
        this.long = options.long || 0;
        this.timezone = options.timezone || 'UTC';
        this.apiBaseUrl = options.apiBaseUrl || 'http://127.0.0.1:8000';

        // Estado del gráfico
        this.chart = null;
        this.weatherSymbolsGroup = null;
        this.dayNightBackgrounds = [];

        // Inicialización
        this.parseData();
    }

    /**
     * Diccionario de estados del tiempo
     */
    static weatherDictionary = {
        clearsky: {
            day: {symbol: '☀️', color: '#FFD700', text: 'Cielo despejado'},
            night: {symbol: '🌙', color: '#DAA520', text: 'Cielo despejado'}
        },
        partlycloudy: {
            day: {symbol: '⛅', color: '#87CEEB', text: 'Parcialmente nublado'},
            night: {symbol: '🌤️', color: '#4682B4', text: 'Parcialmente nublado'}
        },
        cloudy: {
            day: {symbol: '☁️', color: '#A9A9A9', text: 'Nublado'},
            night: {symbol: '☁️', color: '#696969', text: 'Nublado'}
        },
        lightrain: {
            day: {symbol: '🌦️', color: '#6495ED', text: 'Lluvia ligera'},
            night: {symbol: '🌧️', color: '#4169E1', text: 'Lluvia ligera'}
        },
        rain: {
            day: {symbol: '🌧️', color: '#1E90FF', text: 'Lluvia'},
            night: {symbol: '🌧️', color: '#0000CD', text: 'Lluvia'}
        },
        heavyrain: {
            day: {symbol: '⛈️', color: '#000080', text: 'Lluvia intensa'},
            night: {symbol: '⛈️', color: '#191970', text: 'Lluvia intensa'}
        },
        snow: {
            day: {symbol: '❄️', color: '#ADD8E6', text: 'Nieve'},
            night: {symbol: '❄️', color: '#B0E0E6', text: 'Nieve'}
        },
        fog: {
            day: {symbol: '🌫️', color: '#D3D3D3', text: 'Niebla'},
            night: {symbol: '🌫️', color: '#C0C0C0', text: 'Niebla'}
        },
        thunderstorm: {
            day: {symbol: '⚡', color: '#FF4500', text: 'Tormenta'},
            night: {symbol: '⚡', color: '#FF8C00', text: 'Tormenta'}
        },
        sleet: {
            day: {symbol: '🌨️', color: '#B0C4DE', text: 'Aguanieve'},
            night: {symbol: '🌨️', color: '#778899', text: 'Aguanieve'}
        }
    };

    /**
     * Determina si es de día basado en la posición geográfica y hora
     */
    isDaytime(timestamp, lat, long) {
        const date = new Date(timestamp);
        const hours = date.getUTCHours() + (this.timezone === 'UTC' ? 0 : date.getTimezoneOffset() / 60);
        const isSummer = date.getUTCMonth() >= 4 && date.getUTCMonth() <= 9;

        let dayStart = 6, dayEnd = 20;
        if (lat > 40 && isSummer) {
            dayStart = 5;
            dayEnd = 21;
        } else if (lat < -40 && !isSummer) {
            dayStart = 5;
            dayEnd = 21;
        }

        return hours >= dayStart && hours < dayEnd;
    }

    /**
     * Determina el estado del tiempo considerando todas las variables
     */
    getWeatherCondition(data) {
        const {temp, rain, clf, rh, windSpeed, td} = data;

        // Condiciones especiales
        if (windSpeed > 15 && rain > 5) return 'thunderstorm';
        if (temp <= 0 && rain > 0.1) return 'snow';
        if (temp > 0 && temp < 3 && rain > 0.1) return 'sleet';

        // Condiciones de precipitación
        if (rain > 0.1) {
            if (rain < 2) return 'lightrain';
            if (rain < 5) return 'rain';
            return 'heavyrain';
        }

        // Condiciones de nubosidad y humedad
        if (rh > 90 && clf > 0.8) return 'fog';
        if (Math.abs(temp - td) < 2 && rh > 85) return 'fog';
        if (clf < 0.2) return 'clearsky';
        if (clf < 0.6) return 'partlycloudy';
        return 'cloudy';
    }

    /**
     * Dibuja fondos para indicar día/noche
     */
    drawDayNightBackground(chart) {
        this.dayNightBackgrounds.forEach(bg => bg.destroy());
        this.dayNightBackgrounds = [];

        const xAxis = chart.xAxis[0];
        const plotHeight = chart.plotHeight;
        const plotTop = chart.plotTop;

        const days = {};
        this.weatherData.forEach(point => {
            const date = new Date(point.time);
            const dayKey = date.toISOString().split('T')[0];

            if (!days[dayKey]) {
                days[dayKey] = {
                    start: point.time,
                    end: point.time,
                    isDay: point.isDay
                };
            } else {
                days[dayKey].end = point.time;
                if (days[dayKey].isDay !== point.isDay) {
                    days[dayKey].isDay = this.isDaytime(
                        new Date(point.time).setHours(12, 0, 0, 0),
                        this.lat,
                        this.long
                    );
                }
            }
        });

        Object.values(days).forEach(day => {
            const x1 = xAxis.toPixels(Date.parse(day.start), false);
            const x2 = xAxis.toPixels(Date.parse(day.end), false);

            if (!isNaN(x1) && !isNaN(x2)) {
                const bg = chart.renderer.rect(
                    x1,
                    plotTop,
                    x2 - x1,
                    plotHeight
                ).attr({
                    fill: day.isDay ? 'rgba(255, 255, 200, 0.1)' : 'rgba(0, 50, 100, 0.1)',
                    stroke: 'none',
                    zIndex: -1
                }).add();

                this.dayNightBackgrounds.push(bg);
            }
        });
    }

    /**
     * Dibuja símbolos del tiempo sobre la línea de temperatura
     */

    /**
     * Dibuja símbolos del estado del tiempo sobre los puntos de temperatura
     */
    /**
     * Dibuja símbolos del estado del tiempo sobre los puntos de temperatura
     */
    /**
 * Dibuja símbolos del estado del tiempo con tamaño aumentado y mejor visibilidad
 */
drawWeatherSymbols(chart) {
    if (!chart || !chart.renderer) return;

    // Limpiar símbolos anteriores
    if (this.weatherSymbolsGroup) {
        this.weatherSymbolsGroup.destroy();
    }

    this.weatherSymbolsGroup = chart.renderer.g()
        .attr({ class: 'weather-symbols', zIndex: 5 })
        .add();

    const tempSeries = chart.get('temperatura');
    if (!tempSeries) return;

    // Configuración de tamaño y estilo
    const SYMBOL_SIZE = 36; // Tamaño aumentado (36px)
    const Y_OFFSET = -20;   // Mayor desplazamiento vertical
    const STYLE = {
        fontSize: `${SYMBOL_SIZE}px`,
        fontWeight: 'bold',
        textShadow: '0 0 8px white, 0 0 4px black'
    };

    this.weatherData.forEach((weather, i) => {
        const point = tempSeries.data[i];
        if (!point || !point.plotX || !point.plotY) return;

        const condition = this.getWeatherCondition(weather);
        const weatherType = Meteogram.weatherDictionary[condition];
        if (!weatherType) return;

        const variant = weather.isDay ? 'day' : 'night';
        const symbol = weatherType[variant].symbol;

        // Posición del símbolo
        const x = point.plotX + chart.plotLeft;
        const y = point.plotY + chart.plotTop + Y_OFFSET;

        // Crear símbolo con estilo mejorado
        const symbolElement = chart.renderer.text(symbol, x, y)
            .attr({
                ...STYLE,
                title: `${weatherType[variant].text}\n${new Date(weather.time).toLocaleString()}`
            })
            .add(this.weatherSymbolsGroup);

        // Centrado preciso
        symbolElement.translate(
            -symbolElement.getBBox().width / 2,
            -symbolElement.getBBox().height / 2
        );
    });
}

    /**
     * Configuración completa del gráfico
     */
    getChartOptions() {
        return {
            chart: {
                renderTo: this.container,
                marginBottom: 120, // Aumentado para la leyenda
                marginRight: 40,
                marginTop: 60,
                plotBorderWidth: 1,
                height: 500,
                alignTicks: false,
                scrollablePlotArea: {
                    minWidth: 800
                },
                events: {
                    load: (e) => this.onChartLoad(e.target),
                    redraw: () => {
                        this.drawDayNightBackground(this.chart);
                        this.drawWeatherSymbols(this.chart);
                    }
                }
            },
            title: {
                text: 'Meteograma Completo',
                align: 'left',
                style: {
                    fontSize: '18px',
                    fontWeight: 'bold'
                }
            },
            subtitle: {
                text: `Ubicación: Lat ${this.lat.toFixed(3)}, Long ${this.long.toFixed(3)}`,
                align: 'left'
            },
            tooltip: {
                shared: true,
                useHTML: true,
                headerFormat:
                    '<small>{point.x:%A, %b %e, %H:%M}</small><br>' +
                    '<b>{point.point.weatherDescription}</b><br>',
                style: {
                    fontSize: '12px'
                }
            },
            xAxis: [{
                type: 'datetime',
                tickInterval: 3 * 36e5,
                minorTickInterval: 36e5,
                gridLineWidth: 1,
                gridLineColor: 'rgba(128, 128, 128, 0.1)',
                labels: {
                    format: '{value:%H}',
                    style: {fontSize: '12px'}
                },
                crosshair: true
            }, {
                linkedTo: 0,
                type: 'datetime',
                tickInterval: 24 * 36e5,
                labels: {
                    format: '{value:<span style="font-weight:bold">%a</span> %e %b}',
                    align: 'left',
                    style: {fontSize: '12px'}
                },
                opposite: true,
                tickLength: 20
            }],
            yAxis: [
                // Eje 0: Temperatura
                {
                    title: {text: 'Temperatura (°C)'},
                    labels: {format: '{value:.1f}°'},
                    plotLines: [{value: 0, color: '#888', width: 1}],
                    minRange: 10
                },
                // Eje 1: Precipitación
                {
                    title: {text: 'Precipitación (mm)'},
                    opposite: true,
                    min: 0
                },
                // Eje 2: Presión
                {
                    title: {text: 'Presión (hPa)'},
                    opposite: true,
                    minRange: 20
                },
                // Eje 3: Humedad
                {
                    title: {text: 'Humedad (%)'},
                    min: 0,
                    max: 100,
                    visible: false
                }
            ],
            legend: {
                align: 'center',
                verticalAlign: 'bottom',
                layout: 'horizontal',
                itemStyle: {fontSize: '12px'},
                padding: 10,
                margin: 20,
                itemDistance: 20,
                symbolHeight: 12,
                symbolWidth: 12,
                symbolRadius: 0
            },
            plotOptions: {
                series: {
                    pointPlacement: 'on',
                    marker: {enabled: false},
                    states: {
                        hover: {
                            halo: {
                                size: 5,
                                opacity: 0.1
                            }
                        }
                    }
                },
                column: {
                    grouping: false,
                    shadow: false,
                    borderWidth: 0
                }
            },
            series: [
                // Temperatura
                {
                    id: 'temperatura',
                    name: 'Temperatura',
                    type: 'spline',
                    data: this.temperatures,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    },
                    color: '#FF4500',
                    yAxis: 0,
                    zIndex: 3,
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(1) + '°';
                        },
                        style: {
                            fontSize: '10px',
                            textOutline: 'none'
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -20
                    }
                },
                // Punto de rocío
                {
                    name: 'Punto de rocío',
                    type: 'spline',
                    data: this.dewPoints,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    },
                    color: '#00BFFF',
                    yAxis: 0,
                    zIndex: 2,
                    dashStyle: 'ShortDot',
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(1) + '°';
                        },
                        style: {
                            fontSize: '10px',
                            textOutline: 'none',
                            color: '#00BFFF'
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -35
                    }
                },
                // Precipitación
                {
                    name: 'Precipitación',
                    type: 'column',
                    data: this.precipitations,
                    color: '#1E90FF',
                    yAxis: 1,
                    zIndex: 1,
                    tooltip: {
                        valueSuffix: ' mm',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y > 0 ? this.y.toFixed(1) + 'mm' : '';
                        },
                        style: {
                            fontSize: '10px',
                            textOutline: 'none',
                            color: '#1E90FF'
                        },
                        verticalAlign: 'top',
                        inside: false,
                        y: -15
                    }
                },
                // Presión
                {
                    name: 'Presión',
                    type: 'spline',
                    data: this.pressures,
                    color: '#3CB371',
                    yAxis: 2,
                    dashStyle: 'ShortDot',
                    zIndex: 2,
                    tooltip: {
                        valueSuffix: ' hPa',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(0) + 'hPa';
                        },
                        style: {
                            fontSize: '10px',
                            textOutline: 'none',
                            color: '#3CB371'
                        },
                        align: 'center',
                        verticalAlign: 'bottom',
                        y: 15
                    }
                },
                // Humedad
                {
                    name: 'Humedad',
                    type: 'areaspline',
                    data: this.humidities,
                    color: 'rgba(100, 200, 255, 0.3)',
                    yAxis: 3,
                    zIndex: 0,
                    tooltip: {
                        valueSuffix: '%',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(0) + '%';
                        },
                        style: {
                            fontSize: '10px',
                            textOutline: 'none',
                            color: '#64C8FF'
                        },
                        align: 'center',
                        verticalAlign: 'middle',
                        y: 0
                    }
                },
                // Viento (sin dataLabels ya que no queremos mostrar la dirección)
                {
                    name: 'Viento',
                    type: 'windbarb',
                    data: this.winds,
                    color: '#9370DB',
                    yAxis: 0,
                    vectorLength: 18,
                    zIndex: 4,
                    tooltip: {
                        pointFormatter: function () {
                            return `<b>Viento:</b> ${this.value.toFixed(1)} km/h, dirección ${this.direction.toFixed(0)}°`;
                        },
                        valueDecimals: 1
                    }
                }
            ],
            credits: {
                enabled: true,
                text: 'Datos meteorológicos',
                href: `${this.apiBaseUrl}/meteogram/`,
                position: {
                    align: 'right',
                    x: -10
                }
            }
        };
    }

    /**
     * Eventos después de cargar el gráfico
     */
    onChartLoad(chart) {
        this.drawDayNightBackground(chart);
        // Pequeño delay para asegurar la renderización completa
        setTimeout(() => this.drawWeatherSymbols(chart), 50);

        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.reflow();
                setTimeout(() => this.drawWeatherSymbols(this.chart), 100);
            }
        });
    }

    /**
     * Procesa los datos de la API
     */
    parseData() {
        if (!this.json || !this.json.times) {
            this.showError('Datos meteorológicos no disponibles');
            return;
        }

        const {times, T2, RAINC, PSFC, U10, V10, CLF, RH2, TD2, VIS} = this.json;

        const validateArray = (arr, name, defaultValue = 0) => {
            if (!arr || !arr.value || arr.value.length !== times.length) {
                console.warn(`Array ${name} no existe o tiene longitud incorrecta. Usando valores por defecto.`);
                return Array(times.length).fill(defaultValue);
            }
            return arr.value;
        };

        const temps = validateArray(T2, 'T2');
        const rains = validateArray(RAINC, 'RAINC');
        const pressures = validateArray(PSFC, 'PSFC', 1013);
        const uWinds = validateArray(U10, 'U10');
        const vWinds = validateArray(V10, 'V10');
        const cloudiness = validateArray(CLF, 'CLF');
        const humidities = validateArray(RH2, 'RH2', 50);
        const dewPoints = validateArray(TD2, 'TD2');
        const visibilities = VIS ? validateArray(VIS, 'VIS', 10) : Array(times.length).fill(10);

        times.forEach((time, i) => {
            const timestamp = new Date(time).getTime();
            const temp = temps[i];
            const rain = rains[i];
            const windSpeed = Math.sqrt(Math.pow(uWinds[i], 2) + Math.pow(vWinds[i], 2)) * 3.6; // Convertir a km/h
            const windDir = (270 - (Math.atan2(vWinds[i], uWinds[i]) * 180 / Math.PI)) % 360;
            const isDay = this.isDaytime(timestamp, this.lat, this.long);
            const condition = this.getWeatherCondition({
                temp,
                rain,
                clf: cloudiness[i] / 100,
                rh: humidities[i],
                windSpeed,
                td: dewPoints[i]
            });

            // Almacenar datos meteorológicos
            this.weatherData.push({
                time: timestamp,
                condition,
                isDay,
                temp,
                rain,
                windSpeed,
                windDir,
                humidity: humidities[i],
                pressure: pressures[i],
                visibility: visibilities[i],
                dewPoint: dewPoints[i]
            });

            // Datos para series del gráfico
            this.temperatures.push({
                x: timestamp,
                y: temp,
                weatherDescription: Meteogram.weatherDictionary[condition][isDay ? 'day' : 'night'].text,
                isDay: isDay, // Asegurar que esta propiedad está incluida
                humidity: humidities[i],
                dewPoint: dewPoints[i],
                visibility: visibilities[i],
                windSpeed,
                windDir,
                color: temp > 0 ? '#FF4500' : '#00BFFF'
            });

            this.precipitations.push({
                x: timestamp,
                y: rain,
                color: rain > 0 ? '#1E90FF' : 'transparent',
            });

            this.pressures.push({
                x: timestamp,
                y: pressures[i],
            });

            this.humidities.push({
                x: timestamp,
                y: humidities[i],
            });

            this.dewPoints.push({
                x: timestamp,
                y: dewPoints[i],
            });

            // Viento en TODOS los puntos
            this.winds.push({
                x: timestamp,
                value: windSpeed,
                direction: windDir,
            });
        });

        this.createChart();
    }

    /**
     * Crea el gráfico Highcharts
     */
    createChart() {
        try {
            if (!Highcharts) {
                throw new Error('Highcharts no está cargado');
            }

            // Verificar nuevamente que el contenedor existe
            if (!this.container) {
                throw new Error('Contenedor no disponible');
            }

            // Asegurarse de que el contenedor esté visible
            this.container.style.display = 'block';

            // Destruir gráfico existente
            if (this.chart) {
                this.chart.destroy();
            }

            // Crear nuevo gráfico con opciones actualizadas
            const options = this.getChartOptions();
            options.chart.renderTo = this.container; // Usar el elemento DOM directamente

            this.chart = new Highcharts.Chart(options);

        } catch (error) {
            console.error('Error al crear el gráfico:', error);
            this.showError(`Error al crear el gráfico: ${error.message}`);
        }
    }

    /**
     * Muestra errores en el contenedor
     */
    showError(message) {
        const container = document.getElementById(this.container);
        if (container) {
            container.innerHTML = `
                <div style="
                    padding: 20px;
                    margin: 20px;
                    background: #FFEBEE;
                    border-left: 4px solid #F44336;
                    color: #B71C1C;
                ">
                    <span style="font-size:24px">⚠️</span>
                    <strong>Error:</strong> ${message}
                    <div style="margin-top:10px;font-size:12px">
                        <a href="javascript:window.location.reload()">Recargar página</a>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Destruye la instancia y limpia recursos
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.weatherSymbolsGroup) {
            this.weatherSymbolsGroup.destroy();
        }
        this.dayNightBackgrounds.forEach(bg => bg.destroy());
        window.removeEventListener('resize', this.handleResize);
    }
}