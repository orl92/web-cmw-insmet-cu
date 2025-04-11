// Datapicker Fecha
document.addEventListener("DOMContentLoaded", function () {
    // Configuración común para Litepicker
    const litepickerConfig = (elementId) => {
        const element = document.getElementById(elementId);
        if (element) {
            new Litepicker({
                element: element,
                buttonText: {
                    previousMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M15 6l-6 6l6 6" /></svg>`,
                    nextMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M9 6l6 6l-6 6" /></svg>`
                },
                format: 'YYYY-MM-DD'
            });
        }
    };

    // Inicializar todos los datepickers
    ['date', 'day1', 'day2', 'day3', 'day4', 'day5', 'nlpd'].forEach(litepickerConfig);
});

//  Cargar Datos Excel
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
                // Llama a la función para actualizar el formulario
                updateForm(data);
            },
            error: function () {
                console.log("it didn't work");
            }
        });
    });
});

// Actualiza los campos del formulario con los datos recibidos
function updateForm(data) {
    $('#id_ntm').val(data.ntm);
    $('#id_nta').val(data.nta);
    $('#id_ntn').val(data.ntn);
    $('#id_nwm').val(data.nwm);
    $('#id_nwa').val(data.nwa);
    $('#id_nwn').val(data.nwn);
    $('#id_nwddm').val(data.nwddm);
    $('#id_nwdda').val(data.nwdda);
    $('#id_nwddn').val(data.nwddn);
    $('#id_nwdfm').val(data.nwdfm);
    $('#id_nwdfa').val(data.nwdfa);
    $('#id_nwdfn').val(data.nwdfn);
    $('#id_nsm').val(data.nsm);
    $('#id_nsa').val(data.nsa);
    $('#id_nsn').val(data.nsn);
    $('#id_itm').val(data.itm);
    $('#id_ita').val(data.ita);
    $('#id_itn').val(data.itn);
    $('#id_iwm').val(data.iwm);
    $('#id_iwa').val(data.iwa);
    $('#id_iwn').val(data.iwn);
    $('#id_iwddm').val(data.iwddm);
    $('#id_iwdda').val(data.iwdda);
    $('#id_iwddn').val(data.iwddn);
    $('#id_iwdfm').val(data.iwdfm);
    $('#id_iwdfa').val(data.iwdfa);
    $('#id_iwdfn').val(data.iwdfn);
    $('#id_stm').val(data.stm);
    $('#id_sta').val(data.sta);
    $('#id_stn').val(data.stn);
    $('#id_swm').val(data.swm);
    $('#id_swa').val(data.swa);
    $('#id_swn').val(data.swn);
    $('#id_swddm').val(data.swddm);
    $('#id_swdda').val(data.swdda);
    $('#id_swddn').val(data.swddn);
    $('#id_swdfm').val(data.swdfm);
    $('#id_swdfa').val(data.swdfa);
    $('#id_swdfn').val(data.swdfn);
    $('#id_ssm').val(data.ssm);
    $('#id_ssa').val(data.ssa);
    $('#id_ssn').val(data.ssn);
    $('#id_day1_min_temp').val(data.day1_min_temp);
    $('#id_day1_max_temp').val(data.day1_max_temp);
    $('#id_day1_weather').val(data.day1_weather);
    $('#id_day2_min_temp').val(data.day2_min_temp);
    $('#id_day2_max_temp').val(data.day2_max_temp);
    $('#id_day2_weather').val(data.day2_weather);
    $('#id_day3_min_temp').val(data.day3_min_temp);
    $('#id_day3_max_temp').val(data.day3_max_temp);
    $('#id_day3_weather').val(data.day3_weather);
    $('#id_day4_min_temp').val(data.day4_min_temp);
    $('#id_day4_max_temp').val(data.day4_max_temp);
    $('#id_day4_weather').val(data.day4_weather);
    $('#id_day5_min_temp').val(data.day5_min_temp);
    $('#id_day5_max_temp').val(data.day5_max_temp);
    $('#id_day5_weather').val(data.day5_weather);
    $('#id_lp').val(data.lp);
    $('#id_nlp').val(data.nlp);
    $('#nlpd').val(data.nlpd);
    $('#id_sunrise').val(data.sunrise);
    $('#id_sunset').val(data.sunset);
    $('#id_uv_index').val(data.uv_index);
}