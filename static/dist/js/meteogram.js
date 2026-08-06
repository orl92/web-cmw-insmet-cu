// Clase Meteogram
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

        this.json = json;
        this.lat = options.lat || 0;
        this.long = options.long || 0;
        this.municipio = options.municipio || 'Municipio';
        this.datetimeInit = options.datetimeInit || '';

        // Zona horaria de Cuba (UTC-4 normalmente, UTC-5 en horario de verano)
        this.timezone = 'America/Havana';
        this.timezoneOffset = 4 * 60;

        this.chart = null;
        this.weatherSymbolsGroup = null;

        this.parseData();
    }

    static weatherDictionary = {
        clearsky: {
            day: {symbol: '01d', text: 'Cielo despejado'},
            night: {symbol: '01n', text: 'Cielo despejado'}
        },
        partlycloudy: {
            day: {symbol: '02d', text: 'Parcialmente nublado'},
            night: {symbol: '02n', text: 'Parcialmente nublado'}
        },
        cloudy: {
            day: {symbol: '04', text: 'Nublado'},
            night: {symbol: '04', text: 'Nublado'}
        },
        lightrain: {
            day: {symbol: '46', text: 'Lluvia ligera'},
            night: {symbol: '46', text: 'Lluvia ligera'}
        },
        rain: {
            day: {symbol: '09', text: 'Lluvia'},
            night: {symbol: '09', text: 'Lluvia'}
        },
        heavyrain: {
            day: {symbol: '10', text: 'Lluvia intensa'},
            night: {symbol: '10', text: 'Lluvia intensa'}
        },
        thunderstorm: {
            day: {symbol: '11', text: 'Tormenta'},
            night: {symbol: '11', text: 'Tormenta'}
        },
    };

    isDaytime(timestamp) {
        const date = new Date(timestamp);
        const cubaTime = new Date(date.getTime() - (this.timezoneOffset * 60000));
        const hours = cubaTime.getUTCHours();
        return hours >= 6 && hours <= 18;
    }

    getWeatherCondition(data) {
        const {temp, rain, clf, windSpeed} = data;

        if (windSpeed > 15 && rain > 5) return 'thunderstorm';

        if (rain > 0.1) {
            if (rain < 2) return 'lightrain';
            if (rain < 5) return 'rain';
            return 'heavyrain';
        }

        if (clf < 0.2) return 'clearsky';
        if (clf < 0.6) return 'partlycloudy';
        return 'cloudy';
    }

    drawWeatherSymbols(chart) {
        if (!chart || !chart.renderer) return;

        // Obtener la serie de temperatura
        const tempSeries = chart.get('temperatura');
        if (!tempSeries || !tempSeries.visible) {
            // Si la serie de temperatura está oculta, ocultar los símbolos
            if (this.weatherSymbolsGroup) {
                this.weatherSymbolsGroup.hide();
            }
            return;
        } else if (this.weatherSymbolsGroup) {
            // Si la serie de temperatura es visible, mostrar los símbolos
            this.weatherSymbolsGroup.show();
        }

        if (this.weatherSymbolsGroup) {
            this.weatherSymbolsGroup.destroy();
        }

        this.weatherSymbolsGroup = chart.renderer.g()
            .attr({class: 'weather-symbols', zIndex: 5})
            .add();

        const SYMBOL_SIZE = 30;
        const Y_OFFSET = -35;

        this.weatherData.forEach((weather, i) => {
            const point = tempSeries.data[i];
            if (!point || !point.plotX || !point.plotY) return;

            const condition = weather.condition;
            const weatherType = Meteogram.weatherDictionary[condition];
            if (!weatherType) return;

            const variant = weather.isDay ? 'day' : 'night';
            const symbolCode = weatherType[variant].symbol;

            const x = point.plotX + chart.plotLeft - (SYMBOL_SIZE / 2);
            const y = point.plotY + chart.plotTop + Y_OFFSET;

            const iconUrl = `https://cdn.jsdelivr.net/gh/nrkno/yr-weather-symbols@8.0.1/dist/svg/${symbolCode}.svg`;

            const symbolElement = chart.renderer.image(iconUrl, x, y, SYMBOL_SIZE, SYMBOL_SIZE)
                .attr({
                    title: `${weatherType[variant].text}\n${new Date(weather.time + (this.timezoneOffset * 60000)).toLocaleString('es-CU')}`,
                    cursor: 'pointer'
                })
                .css({
                    pointerEvents: 'all'
                })
                .add(this.weatherSymbolsGroup);

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

    onChartLoad(chart) {
        // Guardar referencia al meteograma en el chart
        chart.meteogram = this;

        setTimeout(() => this.drawWeatherSymbols(chart), 50);

        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.reflow();
                setTimeout(() => this.drawWeatherSymbols(this.chart), 100);
            }
        });
    }

    getChartOptions() {
        const isDarkMode = document.body.getAttribute('data-bs-theme') === 'dark';

        const colors = {
            temperature: isDarkMode ? '#ff9d7a' : '#ff7b4f',
            precipitation: isDarkMode ? '#4da6ff' : '#1e90ff',
            pressure: isDarkMode ? '#4cd88d' : '#3cb371',
            wind: isDarkMode ? '#d6b3ff' : '#9370db',
            gridLine: isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.1)',
            text: isDarkMode ? '#e4e6eb' : '#495057',
            background: isDarkMode ? 'rgba(0, 0, 0, 0.2)' : 'transparent'
        };

        // Formatear la fecha para el título
        let titleText = this.municipio;
        if (this.datetimeInit) {
            const formattedDate = this.datetimeInit.replace(/(\d{4})(\d{2})(\d{2})(\d{2})/, 'Inicializado $1-$2-$3 $4:00 UTC');
            titleText += ` ${formattedDate}`;
        }

        return {
            time: {
                useUTC: true,
                timezoneOffset: this.timezoneOffset
            },

            lang: {
                weekdays: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
                shortWeekdays: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
                months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
                shortMonths: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            },

            chart: {
                renderTo: this.container,
                marginBottom: 100, // Aumentado para separar la leyenda
                marginRight: 40,
                marginTop: 70,
                plotBorderWidth: 1,
                height: 400,
                alignTicks: false,
                backgroundColor: colors.background,
                style: {
                    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                },
                scrollablePlotArea: {
                    minWidth: 720
                },
                events: {
                    load: (e) => this.onChartLoad(e.target),
                    redraw: () => {
                        this.drawWeatherSymbols(this.chart);
                    }
                }
            },

            title: {
                text: titleText,
                align: 'left',
                style: {
                    whiteSpace: 'nowrap',
                    color: colors.text,
                    marginBottom: '15px'
                },
                margin: 30,
                y: 25
            },

            exporting: {
                enabled: false // Deshabilitar el menú de exportación
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
                    '<small>{point.x:%A, %e de %B, %H:%M} hora local</small><br>' +
                    '<img src="https://cdn.jsdelivr.net/gh/nrkno/yr-weather-symbols@8.0.1/dist/svg/{point.point.weatherSymbol}.svg" style="height: 24px; vertical-align: middle; margin-right: 5px;">' +
                    '<b>{point.point.weatherDescription}</b>' +
                    '</div>',
                pointFormat:
                    '<span style="color:{point.color}">●</span> {series.name}: <b>{point.y}</b><br/>'
            },

            xAxis: [{
                type: 'datetime',
                tickInterval: 3 * 36e5,
                minorTickInterval: null,
                minorGridLineWidth: 0,
                gridLineWidth: 1,
                gridLineColor: colors.gridLine,
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
            },
            {
                linkedTo: 0,
                type: 'datetime',
                tickInterval: 24 * 36e5,
                minorTickInterval: null,
                minorGridLineWidth: 0,
                gridLineWidth: 1,
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
                gridLineColor: colors.gridLine,
            }],

            yAxis: [
                // Temperature
                {
                     title: {
                        text: null
                    },
                    labels: {
                        format: '{value:.0f}°C',
                        style: {
                            fontSize: '10px',
                            color: colors.temperature
                        },
                        x: -3
                    },
                    plotLines: [{
                        value: 0,
                        color: colors.gridLine,
                        width: 1,
                        zIndex: 2
                    }],
                    maxPadding: 0.3,
                    minRange: 8,
                    tickInterval: 1,
                    gridLineColor: colors.gridLine,
                },

                // Precipitation
                {
                    title: {
                        text: null,
                        style: {
                            fontSize: '10px',
                            color: colors.precipitation,
                        }
                    },

                    labels: {
                        format: '{value:.0f}mm',
                        style: {
                            fontSize: '10px',
                            color: colors.precipitation
                        },
                        x: -3
                    },
                    opposite: false,
                    min: 0, // Forzar que empiece en 0
                    max: 10, // Establecer un máximo razonable
                    tickInterval: 2,
                    minorTickInterval: null,
                    minorGridLineWidth: 0,
                    gridLineWidth: 1,
                    gridLineColor: colors.gridLine,
                    lineWidth: 0,
                    startOnTick: true,
                    endOnTick: false
                },

                // Pressure
                {
                    allowDecimals: false,
                    title: {
                        text: 'hPa',
                        offset: 0,
                        align: 'high',
                        rotation: 0,
                        style: {
                            fontSize: '10px',
                            color: colors.pressure,
                        },
                        textAlign: 'left',
                        x: 3
                    },
                    opposite: true,
                    gridLineWidth: 0,
                    gridLineColor: colors.gridLine,
                    labels: {
                        style: {
                            fontSize: '10px',
                            color: colors.pressure
                        },
                        y: 2,
                        x: 3
                    },
                    showLastLabel: false
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
                margin: 20, // Reducido para dar más espacio
                itemDistance: 25,
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
                    },
                    events: {
                        // Cuando se oculta o muestra una serie, redibujar los símbolos
                        legendItemClick: function() {
                            const chart = this.chart;
                            setTimeout(() => {
                                if (chart.meteogram) {
                                    chart.meteogram.drawWeatherSymbols(chart);
                                }
                            }, 100);
                        }
                    }
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
                        enabled: false
                    }
                },
                {
                    name: 'Precipitación',
                    type: 'spline', // Mantenemos spline en lugar de column
                    data: this.precipitations,
                    color: colors.precipitation,
                    yAxis: 1,
                    zIndex: 1,
                    tooltip: {
                        valueSuffix: 'mm',
                        valueDecimals: 1
                    },
                    dataLabels: {
                        enabled: false
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
                        valueSuffix: 'hPa',
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

    parseData() {
        if (!this.json || !this.json.times) {
            throw new Error('Datos meteorológicos no disponibles');
        }

        const {times, T2, RAINC, PSFC, U10, V10, CLF, VIS} = this.json;

        const validateArray = (arr, name, defaultValue = 0) => {
            if (!arr || !arr.value || arr.value.length !== times.length) {
                return Array(times.length).fill(defaultValue);
            }
            return arr.value.map(val => val !== null && val !== undefined ? val : defaultValue);
        };

        const temps = validateArray(T2, 'T2');
        const rains = validateArray(RAINC, 'RAINC');
        const pressures = validateArray(PSFC, 'PSFC', 1013);
        const uWinds = validateArray(U10, 'U10');
        const vWinds = validateArray(V10, 'V10');
        const cloudiness = validateArray(CLF, 'CLF');
        const visibilities = VIS ? validateArray(VIS, 'VIS', 10) : Array(times.length).fill(10);

        // Limpiar arrays antes de llenarlos
        this.weatherData = [];
        this.temperatures = [];
        this.precipitations = [];
        this.pressures = [];
        this.winds = [];

        times.forEach((time, i) => {
            const timestamp = Date.parse(time + 'Z');
            const temp = temps[i];
            const rain = Math.max(0, rains[i]); // Asegurar que no sea negativo
            const windSpeed = Math.sqrt(Math.pow(uWinds[i], 2) + Math.pow(vWinds[i], 2)) * 3.6;
            const windDir = (270 - (Math.atan2(vWinds[i], uWinds[i]) * 180 / Math.PI)) % 360;
            const isDay = this.isDaytime(timestamp);
            const condition = this.getWeatherCondition({
                temp,
                rain,
                clf: cloudiness[i] / 100,
                windSpeed
            });

            // Obtener información del símbolo del clima
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
                pressure: pressures[i],
                visibility: visibilities[i],
                weatherSymbol,
                weatherDescription
            });

            this.temperatures.push({
                x: timestamp,
                y: temp,
                weatherSymbol,
                weatherDescription,
                color: temp > 0 ? '#ff4500' : '#00bfff',
            });

            this.precipitations.push({
                x: timestamp,
                y: rain,
            });

            this.pressures.push({
                x: timestamp,
                y: pressures[i],
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

            // Limpia el contenedor antes de crear el nuevo gráfico
            this.container.innerHTML = '';
            this.container.style.display = 'block';

            if (this.chart) {
                this.chart.destroy();
            }

            const options = this.getChartOptions();
            options.chart.renderTo = this.container;

            this.chart = new Highcharts.Chart(options);

        } catch (error) {
            // Limpia el contenedor en caso de error
            if (this.container) {
                this.container.innerHTML = '<div class="text-center text-muted p-4">Error al cargar el gráfico</div>';
            }
            throw new Error(`Error al crear el gráfico: ${error.message}`);
        }
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.weatherSymbolsGroup) {
            this.weatherSymbolsGroup.destroy();
        }
    }
}

// Clase MeteogramFormHandler
class MeteogramFormHandler {
    constructor() {
        this.meteogramInstance = null;
        this.autoHideTimeout = null;
        this.initElements();
        this.bindEvents();
        this.initLitepicker();
        this.setupDatetimeHandlers();
        this.setDefaultValues();
        // Carga inicial automática
        this.loadInitialData();
    }

    initLitepicker() {
        const datepickerElement = document.getElementById('datepicker');
        if (datepickerElement) {
            this.litepicker = new Litepicker({
                element: datepickerElement,
                format: 'YYYY-MM-DD',
                lang: 'es-ES',
                resetButton: false,
                buttonText: {
                    previousMonth: '<i class="ti ti-chevron-left" style="font-size:24px;line-height:1"></i>',
                    nextMonth: '<i class="ti ti-chevron-right" style="font-size:24px;line-height:1"></i>'
                },
                setup: (picker) => {
                    picker.on('selected', (date) => {
                        this.updateDatetimeInit();
                    });
                }
            });
        }
    }

    setupDatetimeHandlers() {
        document.getElementById('datepicker')?.addEventListener('change', () => this.updateDatetimeInit());
        document.getElementById('hour-select')?.addEventListener('change', () => this.updateDatetimeInit());
        document.getElementById('datepicker')?.addEventListener('input', () => this.updateDatetimeInit());
    }

    updateDatetimeInit() {
        const dateValue = document.getElementById('datepicker').value;
        const hourValue = document.getElementById('hour-select').value;

        if (dateValue && hourValue) {
            const formattedDate = dateValue.replace(/-/g, '') + hourValue;
            document.getElementById('datetime-init').value = formattedDate;
        }
    }

    initElements() {
        this.form = document.getElementById('meteogram-form');
        this.submitBtn = document.getElementById('submit-btn');
        this.errorContainer = document.getElementById('error-container');
        this.errorMessageElement = document.getElementById('error-message');
        this.chartContainer = document.getElementById('container');
        this.plotArea = document.getElementById('plot-area');
        this.datepicker = document.getElementById('datepicker');
        this.hourSelect = document.getElementById('hour-select');
        this.townSelect = document.getElementById('id_town');
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    setDefaultValues() {
        const today = new Date().toISOString().split('T')[0];
        if (this.datepicker) this.datepicker.value = today;
        if (this.hourSelect) this.hourSelect.value = '00';

        setTimeout(() => {
            this.updateDatetimeInit();
        }, 0);
    }

    loadInitialData() {
        setTimeout(() => {
            this.updateDatetimeInit();
            setTimeout(() => {
                this.handleSubmit(new Event('submit'));
            }, 100);
        }, 1000);
    }

    showError(message) {
        if (!this.errorContainer || !this.errorMessageElement) {
            console.error('Error: No se pudo encontrar el contenedor de error');
            return;
        }

        // Limpiar timeout anterior si existe
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }

        // Actualizar el mensaje de error
        this.errorMessageElement.textContent = message;

        // Mostrar el plot-area para que el error sea visible
        if (this.plotArea) {
            this.plotArea.style.display = 'block';
        }

        // Mostrar el contenedor de error
        this.errorContainer.style.display = 'block';

        // Ocultar el gráfico cuando hay error
        this.hideChart();

        // Auto-ocultar después de 8 segundos (solo el error, no el plot-area)
        this.autoHideTimeout = setTimeout(() => {
            this.hideError();
        }, 8000);
    }

    hideError() {
        if (this.errorContainer) {
            // Solo ocultamos el contenedor de error, no el plot-area
            this.errorContainer.style.display = 'none';
        }

        // Limpiar el timeout
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }
    }

    hidePlotArea() {
        // Ocultar el plot-area completo (solo se usa cuando hay éxito)
        if (this.plotArea) {
            this.plotArea.style.display = 'none';
        }
    }

    // Método para ocultar el gráfico
    hideChart() {
        if (this.meteogramInstance) {
            try {
                this.meteogramInstance.destroy();
                this.meteogramInstance = null;
            } catch (e) {
                console.warn('Error al destruir instancia del meteograma:', e);
            }
        }

        // También limpia el contenedor del gráfico
        if (this.chartContainer) {
            this.chartContainer.innerHTML = '';
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // Forzar actualización de datetime-init antes de enviar
        this.updateDatetimeInit();

        const datetimeInit = document.getElementById('datetime-init').value;

        if (!this.form.checkValidity()) {
            e.stopPropagation();
            this.form.classList.add('was-validated');
            return;
        }

        if (!/^\d{10}$/.test(datetimeInit)) {
            this.showError(`Formato de fecha/hora inválido: ${datetimeInit}`);
            return;
        }

        // Ocultar error previo (solo el error, no el plot-area)
        this.hideError();
        this.setSubmitButtonState(true);

        try {
            const formData = new FormData(this.form);
            const params = {
                datetime_init: formData.get('datetime_init'),
                town: formData.get('town')
            };

            const response = await fetch('', {
                method: 'POST',
                body: new URLSearchParams(params),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.message || `Error ${response.status}: ${response.statusText}`);
            }

            if (responseData.status !== 'success' || !responseData.data) {
                throw new Error(responseData.message || 'Respuesta inesperada del servidor');
            }

            // Verificar si hay datos realmente
            if (!responseData.data.times || responseData.data.times.length === 0) {
                this.showError('No hay datos disponibles para los criterios seleccionados');
                return;
            }

            // Obtener las coordenadas del municipio seleccionado
            const selectedOption = this.townSelect?.selectedOptions[0];
            const lat = selectedOption ? parseFloat(selectedOption.getAttribute('data-lat')) : 0;
            const long = selectedOption ? parseFloat(selectedOption.getAttribute('data-long')) : 0;

            this.updateMeteogram(responseData, lat, long);

        } catch (error) {
            console.error('Error en handleSubmit:', error);
            this.showError(error.message || 'Error al procesar la solicitud');
        } finally {
            this.setSubmitButtonState(false);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    updateMeteogram(formattedResponse, lat, long) {
        if (!formattedResponse || !formattedResponse.data || !formattedResponse.data.times) {
            this.showError('Datos meteorológicos no válidos o vacíos');
            return;
        }

        const datetimeInit = document.getElementById('datetime-init').value;

        const options = {
            lat: lat,
            long: long,
            municipio: this.townSelect?.selectedOptions[0]?.textContent || 'Municipio',
            datetimeInit: datetimeInit
        };

        // Limpia la instancia anterior
        this.hideChart();

        try {
            // Mostrar el plot-area
            if (this.plotArea) {
                this.plotArea.style.display = 'block';
            }

            // Ocultar error si existe
            this.hideError();

            // Crear el meteograma
            this.meteogramInstance = new Meteogram(formattedResponse.data, 'container', options);

        } catch (error) {
            console.error('Error al crear meteograma:', error);
            this.showError(`Error al crear gráfico: ${error.message}`);
        }
    }

    setSubmitButtonState(isLoading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = isLoading;
            this.submitBtn.textContent = isLoading ? 'Cargando...' : 'Generar';
        }
    }
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new MeteogramFormHandler();
});
