document.addEventListener('DOMContentLoaded', function () {
    var excelFile = document.getElementById('excelFile');
    if (excelFile) {
        var uploadUrl = excelFile.getAttribute('data-upload-url');
        excelFile.addEventListener('change', function () {
            var formData = new FormData(document.getElementById('uploadForm'));
            fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
            })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.error) {
                    showExcelError(data.error);
                    return;
                }
                updateForm(data);
            })
            .catch(function () {
                showExcelError('No se pudo procesar el archivo Excel.');
            });
        });
    }

    var dateInput = document.getElementById('id_date');
    if (dateInput) {
        dateInput.addEventListener('change', function () {
            var iso = window.pickerDateToIso ? window.pickerDateToIso(dateInput.value) : '';
            if (iso) {
                syncExtendedDates(iso);
            }
        });
        var picker = window.tempusDominus && window.tempusDominus._instances['id_date'];
        if (picker && picker.subscribe) {
            picker.subscribe(window.tempusDominus.Namespace.events.change, function (e) {
                var iso = e.date && window.formatPickerDate
                    ? window.pickerDateToIso(window.formatPickerDate(e.date))
                    : '';
                if (iso) {
                    syncExtendedDates(iso);
                }
            });
        }
    }
});

function showExcelError(message) {
    var alert = document.getElementById('excelError');
    if (!alert) {
        return;
    }
    alert.textContent = message;
    alert.classList.remove('d-none');
}

function toPickerDate(iso) {
    if (!iso) {
        return '';
    }
    var parts = iso.split('-');
    if (parts.length !== 3) {
        return iso;
    }
    return parts[2] + '/' + parts[1] + '/' + parts[0];
}

function toPickerTime(time) {
    if (!time || typeof time !== 'string') {
        return '';
    }
    var hasMeridiem = /am|pm/i.test(time);
    var parts = time.split(':');
    var hour = parseInt(parts[0], 10);
    var minute = (parts[1] || '').replace(/[^0-9]/g, '') || '00';
    if (isNaN(hour)) {
        return time;
    }
    if (hasMeridiem) {
        return time.trim().replace(/\s+/g, ' ');
    }
    var meridiem = hour >= 12 ? 'PM' : 'AM';
    var hour12 = hour % 12;
    if (hour12 === 0) {
        hour12 = 12;
    }
    return hour12 + ':' + minute + ' ' + meridiem;
}

function formsetPrefix(totalFormsId, fallback) {
    var el = document.getElementById(totalFormsId);
    if (el) {
        var match = el.name.match(/^(.*)-TOTAL_FORMS$/);
        if (match) {
            return match[1];
        }
    }
    return fallback;
}

function pad2(value) {
    return String(value).padStart(2, '0');
}

function isoToDate(iso) {
    if (!iso || typeof iso !== 'string') {
        return null;
    }
    var res = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!res) {
        return null;
    }
    return new Date(parseInt(res[1], 10), parseInt(res[2], 10) - 1, parseInt(res[3], 10));
}

function timeToDate(time) {
    if (!time || typeof time !== 'string') {
        return null;
    }
    var parts = time.split(':');
    var hour = parseInt(parts[0], 10);
    var minute = parseInt(parts[1] || '0', 10);
    if (isNaN(hour)) {
        return null;
    }
    var date = new Date();
    date.setHours(hour, minute, 0, 0);
    return date;
}

function addDaysToIsoDate(iso, days) {
    var date = isoToDate(iso);
    if (!date) {
        return '';
    }
    date.setDate(date.getDate() + days);
    return date.getFullYear() + '-' + pad2(date.getMonth() + 1) + '-' + pad2(date.getDate());
}

function syncExtendedDates(baseIso) {
    var extendedPrefix = formsetPrefix('id_extended_days-TOTAL_FORMS', 'extended_days');
    var dayInputs = document.querySelectorAll('[name^="' + extendedPrefix + '-"][name$="-day_number"]');
    Array.prototype.forEach.call(dayInputs, function (input) {
        var dayNum = parseInt(input.value, 10);
        if (isNaN(dayNum) || dayNum < 1) {
            return;
        }
        var dateName = input.name.replace('-day_number', '-date');
        if (!baseIso) {
            return;
        }
        var targetIso = addDaysToIsoDate(baseIso, dayNum);
        setExcelValue(dateName, toPickerDate(targetIso), isoToDate(targetIso));
    });
}

function setExcelValue(id, value, pickerValue) {
    var el = document.getElementById(id);
    if (!el) {
        el = document.querySelector('[name="' + id + '"]');
    }
    if (!el) {
        return;
    }
    el.value = value === null || value === undefined ? '' : value;
    var picker = window.tempusDominus && window.tempusDominus._instances[el.id];
    if (picker && pickerValue) {
        try {
            picker.dates.setValue(pickerValue);
        } catch (e) {
            // mantiene el valor del input aunque el picker no pueda parsear
        }
    }
}

function updateForm(data) {
    var regionsPrefix = formsetPrefix('id_regions-TOTAL_FORMS', 'regions');
    var extendedPrefix = formsetPrefix('id_extended_days-TOTAL_FORMS', 'extended_days');

    setExcelValue('id_date', toPickerDate(data.date), isoToDate(data.date));

    var baseIso = data.date || '';

    if (data.regions) {
        data.regions.forEach(function (r) {
            var prefix = regionsPrefix;
            var forms = document.querySelectorAll('[name^="' + prefix + '-"][name$="-region"]');
            for (var i = 0; i < forms.length; i++) {
                if (forms[i].value === r.region) {
                    var periodField = document.querySelector('[name="' + prefix + '-' + i + '-period"]');
                    if (periodField && periodField.value === r.period) {
                        setExcelValue(prefix + '-' + i + '-temp', r.temp);
                        setExcelValue(prefix + '-' + i + '-weather', r.weather);
                        setExcelValue(prefix + '-' + i + '-wind_dir', r.wind_dir);
                        setExcelValue(prefix + '-' + i + '-wind_speed', r.wind_speed);
                        setExcelValue(prefix + '-' + i + '-sea_note', r.sea_note);
                    }
                }
            }
        });
    }

    if (data.extended) {
        data.extended.forEach(function (d) {
            var prefix = extendedPrefix;
            var forms = document.querySelectorAll('[name^="' + prefix + '-"][name$="-day_number"]');
            for (var i = 0; i < forms.length; i++) {
                if (parseInt(forms[i].value, 10) === d.day_number) {
                    setExcelValue(prefix + '-' + i + '-min_temp', d.min_temp);
                    setExcelValue(prefix + '-' + i + '-max_temp', d.max_temp);
                    setExcelValue(prefix + '-' + i + '-weather', d.weather);
                }
            }
        });
    }
    syncExtendedDates(baseIso);

    setExcelValue('id_lp', data.lp);
    setExcelValue('id_nlp', data.nlp);
    setExcelValue('id_nlpd', toPickerDate(data.nlpd), isoToDate(data.nlpd));
    setExcelValue(
        'id_sunrise',
        data.sunrise ? toPickerTime(data.sunrise) : '',
        data.sunrise ? timeToDate(data.sunrise) : null
    );
    setExcelValue(
        'id_sunset',
        data.sunset ? toPickerTime(data.sunset) : '',
        data.sunset ? timeToDate(data.sunset) : null
    );
    setExcelValue('id_uv_index', data.uv_index);
}
