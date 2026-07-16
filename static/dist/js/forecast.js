$(document).ready(function () {
    $('#excelFile').on('change', function (e) {
        var formData = new FormData($('#uploadForm')[0]);
        $.ajax({
            url: '/dashboard/excel/json/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (data) {
                updateForm(data);
            },
            error: function () {
                console.log("it didn't work");
            }
        });
    });
});

function updateForm(data) {
    const setVal = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.value = value;
            if (el.litepicker) {
                el.litepicker.setDate(value);
            }
        }
    };

    setVal('id_date', data.date);

    data.regions.forEach(function (r) {
        var prefix = 'forecastregions';
        var forms = document.querySelectorAll('[name^="' + prefix + '-"][name$="-region"]');
        for (var i = 0; i < forms.length; i++) {
            if (forms[i].value === r.region) {
                var periodField = document.querySelector('[name="' + prefix + '-' + i + '-period"]');
                if (periodField && periodField.value === r.period) {
                    setVal(prefix + '-' + i + '-temp', r.temp);
                    setVal(prefix + '-' + i + '-weather', r.weather);
                    setVal(prefix + '-' + i + '-wind_dir', r.wind_dir);
                    setVal(prefix + '-' + i + '-wind_speed', r.wind_speed);
                    setVal(prefix + '-' + i + '-sea_note', r.sea_note);
                }
            }
        }
    });

    data.extended.forEach(function (d) {
        var prefix = 'forecastextendedday';
        var forms = document.querySelectorAll('[name^="' + prefix + '-"][name$="-day_number"]');
        for (var i = 0; i < forms.length; i++) {
            if (parseInt(forms[i].value) === d.day_number) {
                setVal(prefix + '-' + i + '-date', d.date);
                setVal(prefix + '-' + i + '-min_temp', d.min_temp);
                setVal(prefix + '-' + i + '-max_temp', d.max_temp);
                setVal(prefix + '-' + i + '-weather', d.weather);
            }
        }
    });

    setVal('id_lp', data.lp);
    setVal('id_nlp', data.nlp);
    setVal('id_nlpd', data.nlpd);
    setVal('id_sunrise', data.sunrise);
    setVal('id_sunset', data.sunset);
    setVal('id_uv_index', data.uv_index);
}
