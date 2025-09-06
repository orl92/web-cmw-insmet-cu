
// Clase Meteogram con mejoras para Tabler.io
class Meteogram {
    constructor(json, containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Contenedor con ID '${containerId}' no encontrado`);
        }

        this.container.innerHTML = '';

        this.weatherData = [];
        this.temperatures = [];
        this.precipitations = [];
        this.winds = [];
        this.pressures = [];
        this.humidities = [];
        this.dewPoints = [];
        this.visibility = [];

        this.json = json;
        this.lat = options.lat || 0;
        this.long = options.long || 0;
        this.timezone = options.timezone || 'UTC';
        this.apiBaseUrl = options.apiBaseUrl || 'http://127.0.0.1:8000';

        this.chart = null;
        this.weatherSymbolsGroup = null;
        this.dayNightBackgrounds = [];

        this.parseData();
    }

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

    isDaytime(timestamp, lat, long) {
        const date = new Date(timestamp);
        const hours = date.getUTCHours();
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

    getWeatherCondition(data) {
        const {temp, rain, clf, rh, windSpeed, td} = data;

        if (windSpeed > 15 && rain > 5) return 'thunderstorm';
        if (temp <= 0 && rain > 0.1) return 'snow';
        if (temp > 0 && temp < 3 && rain > 0.1) return 'sleet';

        if (rain > 0.1) {
            if (rain < 2) return 'lightrain';
            if (rain < 5) return 'rain';
            return 'heavyrain';
        }

        if (rh > 90 && clf > 0.8) return 'fog';
        if (Math.abs(temp - td) < 2 && rh > 85) return 'fog';
        if (clf < 0.2) return 'clearsky';
        if (clf < 0.6) return 'partlycloudy';
        return 'cloudy';
    }

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

    drawWeatherSymbols(chart) {
        if (!chart || !chart.renderer) return;

        if (this.weatherSymbolsGroup) {
            this.weatherSymbolsGroup.destroy();
        }

        this.weatherSymbolsGroup = chart.renderer.g()
            .attr({ class: 'weather-symbols', zIndex: 5 })
            .add();

        const tempSeries = chart.get('temperatura');
        if (!tempSeries) return;

        const SYMBOL_SIZE = 28;
        const Y_OFFSET = -24;
        const STYLE = {
            fontSize: `${SYMBOL_SIZE}px`,
            fontWeight: 'normal',
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)'
        };

        this.weatherData.forEach((weather, i) => {
            const point = tempSeries.data[i];
            if (!point || !point.plotX || !point.plotY) return;

            const condition = this.getWeatherCondition(weather);
            const weatherType = Meteogram.weatherDictionary[condition];
            if (!weatherType) return;

            const variant = weather.isDay ? 'day' : 'night';
            const symbol = weatherType[variant].symbol;

            const x = point.plotX + chart.plotLeft;
            const y = point.plotY + chart.plotTop + Y_OFFSET;

            const symbolElement = chart.renderer.text(symbol, x, y)
                .attr({
                    ...STYLE,
                    title: `${weatherType[variant].text}\n${new Date(weather.time).toLocaleString()}`,
                    cursor: 'pointer'
                })
                .css({
                    pointerEvents: 'all'
                })
                .add(this.weatherSymbolsGroup);

            symbolElement.translate(
                -symbolElement.getBBox().width / 2,
                -symbolElement.getBBox().height / 2
            );

            symbolElement.on('mouseover', function() {
                chart.tooltip.refresh([{
                    series: tempSeries,
                    point: point,
                    x: point.x,
                    y: point.y
                }], point.x);
            });

            symbolElement.on('mouseout', function() {
                chart.tooltip.hide();
            });
        });
    }

    getChartOptions() {
        // Detectar tema actual
        const isDarkMode = document.body.getAttribute('data-bs-theme') === 'dark';
        
        // Colores adaptativos para modo claro/oscuro
        const colors = {
            temperature: isDarkMode ? '#4299e1' : '#206bc4',
            dewPoint: isDarkMode ? '#7e9cd8' : '#5c7cfa',
            precipitation: isDarkMode ? '#48bb78' : '#2fb344',
            pressure: isDarkMode ? '#ed8936' : '#f76707',
            humidity: isDarkMode ? '#9f7aea' : '#ae3ec9',
            wind: isDarkMode ? '#5c7cfa' : '#4263eb',
            gridLine: isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(107, 107, 107, 0.1)',
            text: isDarkMode ? '#f5f5f5' : '#495057',
            background: isDarkMode ? 'rgba(0, 0, 0, 0.2)' : 'transparent'
        };

        return {
            time: {
                useUTC: true,
                timezoneOffset: 0
            },
            chart: {
                renderTo: this.container,
                marginBottom: 100,
                marginRight: 30,
                marginTop: 70,
                marginLeft: 60,
                plotBorderWidth: 0,
                height: 550,
                alignTicks: false,
                backgroundColor: colors.background,
                style: {
                    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                },
                scrollablePlotArea: {
                    minWidth: 800,
                    scrollPositionX: 0
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
                    fontWeight: '600',
                    color: colors.text,
                    marginBottom: '15px' // Margen inferior aumentado
                },
                margin: 25, // Margen general aumentado
                y: 20       // Posición vertical ajustada
            },
            tooltip: {
                shared: true,
                useHTML: true,
                backgroundColor: isDarkMode ? 'rgba(33, 37, 41, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                borderWidth: 0,
                borderRadius: 4,
                shadow: true,
                style: {
                    fontSize: '13px',
                    color: colors.text
                },
                headerFormat: 
                '<div style="border-bottom: 1px solid ' + (isDarkMode ? '#495057' : '#e9ecef') + '; padding-bottom: 5px; margin-bottom: 5px;">' +
                '<small>{point.x:%A, %b %e, %H:%M} UTC</small><br>' +
                '<span style="font-size: 16px; margin-right: 5px;">{point.point.weatherSymbol}</span>' +
                '<b>{point.point.weatherDescription}</b>' +
                '</div>',
                pointFormat: 
                    '<span style="color:{point.color}">●</span> {series.name}: <b>{point.y}</b>{series.tooltipOptions.valueSuffix}<br/>'
            },
            xAxis: [{
                type: 'datetime',
                tickInterval: 3 * 36e5,
                minorTickInterval: 36e5,
                gridLineWidth: 0,
                gridLineColor: colors.gridLine,  // Usa el color definido
                lineWidth: 0,
                labels: {
                    format: '{value:%H}',
                    style: {
                        fontSize: '11px',
                        color: colors.text
                    }
                },
                crosshair: {
                    width: 1,
                    color: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                    zIndex: 5
                }
            }, {
                linkedTo: 0,
                type: 'datetime',
                tickInterval: 24 * 36e5,
                labels: {
                    format: '{value:<span style="font-weight:600">%a</span> %e %b}',
                    align: 'left',
                    style: {
                        fontSize: '11px',
                        color: colors.text
                    }
                },
                opposite: true,
                tickLength: 20,
                lineWidth: 0,
                gridLineWidth: 0,
                gridLineColor: colors.gridLine,  // Usa el color definido
            }],
            yAxis: [
                {
                    title: {
                        text: 'Temperatura (°C)',
                        style: {
                            color: colors.text,
                            fontWeight: '500'
                        }
                    },
                    labels: {
                        format: '{value:.0f}°',
                        style: {
                            color: colors.temperature
                        }
                    },
                    plotLines: [{
                        value: 0, 
                        color: colors.gridLine,  // Usa el mismo color para las líneas de referencia
                        width: 1,
                        zIndex: 2
                    }],
                    minRange: 10,
                    gridLineWidth: 0,
                    gridLineColor: colors.gridLine,  // Usa el color definido
                    lineWidth: 0,
                },
                {
                    title: {
                        text: 'Precipitación (mm)',
                        style: {
                            color: colors.text,
                            fontWeight: '500'
                        }
                    },
                    opposite: true,
                    min: 0,
                    gridLineWidth: 0,
                    gridLineColor: colors.gridLine,  // Usa el color definido
                    lineWidth: 0,
                    labels: {
                        style: {
                            color: colors.precipitation
                        }
                    }
                },
                {
                    title: {
                        text: 'Presión (hPa)',
                        style: {
                            color: colors.text,
                            fontWeight: '500'
                        }
                    },
                    opposite: true,
                    minRange: 20,
                    gridLineWidth: 0,
                    gridLineColor: colors.gridLine,  // Usa el color definido
                    lineWidth: 0,
                    labels: {
                        style: {
                            color: colors.pressure
                        }
                    }
                },
                {
                    title: {
                        text: 'Humedad (%)',
                        style: {
                            color: colors.text,
                            fontWeight: '500'
                        }
                    },
                    min: 0,
                    max: 100,
                    visible: false,
                    gridLineWidth: 0,
                    gridLineColor: colors.gridLine,  // Usa el color definido
                    lineWidth: 0,
                }
            ],
            legend: {
                align: 'center',
                verticalAlign: 'bottom',
                layout: 'horizontal',
                itemStyle: {
                    fontSize: '12px',
                    color: colors.text,
                    fontWeight: 'normal'
                },
                itemHoverStyle: {
                    color: colors.text
                },
                padding: 15,
                margin: 20,
                itemDistance: 15,
                symbolHeight: 10,
                symbolWidth: 10,
                symbolRadius: 3,
                backgroundColor: 'transparent',
                borderWidth: 0
            },
            plotOptions: {
                series: {
                    pointPlacement: 'on',
                    marker: {
                        enabled: false,
                        states: {
                            hover: {
                                enabled: true,
                                radius: 4
                            }
                        }
                    },
                    states: {
                        hover: {
                            halo: {
                                size: 6,
                                opacity: 0.15
                            }
                        },
                        inactive: {
                            opacity: 0.4
                        }
                    }
                },
                column: {
                    grouping: false,
                    shadow: false,
                    borderWidth: 0,
                    borderRadius: 2,
                    pointPadding: 0.1,
                    groupPadding: 0
                },
                spline: {
                    lineWidth: 2.5,
                    marker: {
                        enabled: false
                    }
                },
                areaspline: {
                    fillOpacity: 0.4,
                    lineWidth: 1,
                    marker: {
                        enabled: false
                    }
                }
            },
            series: [
                {
                    id: 'temperatura',
                    name: 'Temperatura',
                    type: 'spline',
                    data: this.temperatures,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    },
                    color: colors.temperature,
                    yAxis: 0,
                    zIndex: 3,
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(0);
                        },
                        style: {
                            fontSize: '9px',
                            textOutline: 'none',
                            fontWeight: '500',
                            color: colors.temperature
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -32,
                        x: 0
                    }
                },
                {
                    name: 'Punto de rocío',
                    type: 'spline',
                    data: this.dewPoints,
                    tooltip: {
                        valueSuffix: '°C',
                        valueDecimals: 1
                    },
                    color: colors.dewPoint,
                    yAxis: 0,
                    zIndex: 2,
                    dashStyle: 'ShortDot',
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y.toFixed(0);
                        },
                        style: {
                            fontSize: '9px',
                            textOutline: 'none',
                            color: colors.dewPoint,
                            fontWeight: '500'
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -32,
                        x: 0
                    }
                },
                {
                    name: 'Precipitación',
                    type: 'column',
                    data: this.precipitations,
                    color: colors.precipitation,
                    yAxis: 1,
                    zIndex: 1,
                    tooltip: {
                        valueSuffix: ' mm',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            return this.y > 0.5 ? this.y.toFixed(1): '';
                        },
                        style: {
                            fontSize: '9px',
                            textOutline: 'none',
                            color: colors.precipitation,
                            fontWeight: '500'
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -32,
                        x: 0
                    }
                },
                {
                    name: 'Presión',
                    type: 'spline',
                    data: this.pressures,
                    color: colors.pressure,
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
                            return this.y.toFixed(0);
                        },
                        style: {
                            fontSize: '9px',
                            textOutline: 'none',
                            color: colors.pressure,
                            fontWeight: '500'
                        },
                        align: 'center',
                        verticalAlign: 'top',
                        y: -32,
                        x: 0
                    }
                },
                {
                    name: 'Humedad',
                    type: 'areaspline',
                    data: this.humidities,
                    color: colors.humidity,
                    yAxis: 3,
                    zIndex: 0,
                    tooltip: {
                        valueSuffix: '%',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: false
                    }
                },
                {
                    name: 'Viento',
                    type: 'windbarb',
                    data: this.winds,
                    color: colors.wind,
                    yAxis: 0,
                    vectorLength: 16,
                    zIndex: 4,
                    tooltip: {
                        pointFormatter: function () {
                            return `<b>Viento:</b> ${this.value.toFixed(1)} km/h, dirección ${this.direction.toFixed(0)}°`;
                        },
                        valueDecimals: 1
                    }
                }
            ],
        };
    }

    onChartLoad(chart) {
        this.drawDayNightBackground(chart);
        setTimeout(() => this.drawWeatherSymbols(chart), 50);

        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.reflow();
                setTimeout(() => this.drawWeatherSymbols(this.chart), 100);
            }
        });
    }

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
            const timestamp = Date.parse(time + 'Z');
            const temp = temps[i];
            const rain = rains[i];
            const windSpeed = Math.sqrt(Math.pow(uWinds[i], 2) + Math.pow(vWinds[i], 2)) * 3.6;
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

            const weatherType = Meteogram.weatherDictionary[condition];
            const variant = isDay ? 'day' : 'night';
            const weatherSymbol = weatherType[variant].symbol;
            const weatherDescription = weatherType[variant].text;

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
                dewPoint: dewPoints[i],
                weatherSymbol,
                weatherDescription
            });

            this.temperatures.push({
                x: timestamp,
                y: temp,
                weatherSymbol,
                weatherDescription,
                isDay: isDay,
                humidity: humidities[i],
                dewPoint: dewPoints[i],
                visibility: visibilities[i],
                windSpeed,
                windDir,
                color: temp > 0 ? '#206bc4' : '#5c7cfa'
            });

            this.precipitations.push({
                x: timestamp,
                y: rain,
                color: rain > 0 ? '#48bb78' : '#2fb344',
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

            this.winds.push({
                x: timestamp,
                value: windSpeed,
                direction: windDir,
            });
        });

        this.createChart();
    }

    createChart() {
        try {
            if (!Highcharts) {
                throw new Error('Highcharts no está cargado');
            }

            if (!this.container) {
                throw new Error('Contenedor no disponible');
            }

            this.container.style.display = 'block';

            if (this.chart) {
                this.chart.destroy();
            }

            const options = this.getChartOptions();
            options.chart.renderTo = this.container;

            this.chart = new Highcharts.Chart(options);

        } catch (error) {
            console.error('Error al crear el gráfico:', error);
            this.showError(`Error al crear el gráfico: ${error.message}`);
        }
    }

    showError(message) {
        if (this.container) {
            this.container.innerHTML = `
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

    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.weatherSymbolsGroup) {
            this.weatherSymbolsGroup.destroy();
        }
        this.dayNightBackgrounds.forEach(bg => bg.destroy());
    }
}