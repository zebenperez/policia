$(document).ready(function () {
    let muted = false;
    $('.retranscribe-audio').click(function () {
        var obj_id = $(this).data('id');
        var url = $(this).data('url');
        var button = $(this);
        button.prop('disabled', true);
        // Open sweetalert2 with "Processing..." message
        if (muted === false) {
            Swal.fire({
                title: 'Procesando...',
                text: 'Por favor, espere mientras se retranscribe el audio.',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        }

        $.ajax({
            url: url,
            type: 'POST',
            data: {
                'obj_id': obj_id,
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                json_response = response;
                if (muted == false) {
                    Swal.close();
                    Swal.fire({
                        title: 'Éxito',
                        //text in html format
                        html: 'El audio ha sido retranscrito correctamente.',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            $('#audio-transcription-' + obj_id).html(json_response.texto);
                        }
                    });
                } else {
                    $('#audio-transcription-' + obj_id).html(json_response.texto);
                    muted = false;
                }
                button.removeClass('processed-False').addClass('processed-True');
            },
            error: function (xhr, status, error) {
                if (muted == false) {
                    Swal.close();
                    Swal.fire({
                        title: 'Error',
                        text: 'Ha ocurrido un error al retranscribir el audio',
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                }
            },
            complete: function () {
                button.prop('disabled', false);
            }
        });

    });

    $('.edit-audio').click(function (e) {
        e.preventDefault();

        var url = $(this).data('url');
        var button = $(this);
        var obj_id = $(this).data('id');

        button.prop('disabled', true);

        $.ajax({
            url: url,
            type: 'POST',
            data: {
                'obj_id': $(this).data('id'),
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                // Abrir modal con el formulario
                Swal.fire({
                    title: 'Editar Audio',
                    html: response.html,
                    showCancelButton: true,
                    confirmButtonText: 'Guardar',
                    cancelButtonText: 'Cancelar',
                    focusConfirm: false,
                    showLoaderOnConfirm: true,
                    allowOutsideClick: () => !Swal.isLoading(),

                    preConfirm: () => {
                        const form = Swal.getPopup().querySelector('form');
                        if (!form) {
                            Swal.showValidationMessage('No se ha encontrado el formulario');
                            return false;
                        }

                        const formData = new FormData(form);

                        return new Promise(function (resolve, reject) {
                            $.ajax({
                                url: form.action,
                                type: form.method,
                                data: formData,
                                processData: false,
                                contentType: false,
                                enctype: 'multipart/form-data',
                                success: function (saveResponse) {
                                    resolve(saveResponse); // esto será result.value
                                },
                                error: function (xhr, status, error) {
                                    Swal.showValidationMessage(
                                        'Ha ocurrido un error al guardar el audio:  ' + error
                                    );
                                    reject(error);
                                }
                            });
                        });
                    },
                }).then((result) => {
                    json_response = result.value;
                    if (result.isConfirmed) {
                        Swal.fire({
                            title: 'Éxito',
                            text: 'El audio ha sido guardado correctamente.',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        });
                        $('#audio-transcription-' + json_response.obj_id).html(json_response.texto);

                        // aquí puedes refrescar la tabla/listado si quieres
                    }
                });
            },
            error: function (xhr, status, error) {
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al cargar el formulario',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            }
        }).always(function () {
            button.prop('disabled', false);
        });
    });


    // Check if exists processed-False class in any button
    if ($('button.retranscribe-audio.processed-False').length > 0) {
        // Trigger click event in the first button with processed-False class
        muted = true;
        $('button.retranscribe-audio.processed-False').first().click();
    }

    $('.expte-2-llm').click(function () {
        var obj_id = $(this).data('item');

        var url = $(this).data('url');
        var button = $(this);
        button.prop('disabled', true);
        // Open sweetalert2 with "Processing..." message
        Swal.fire({
            title: 'Procesando...',
            text: 'Por favor, espere mientras la IA procesa el expediente.',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        $.ajax({
            url: url,
            type: 'POST',
            timeout: 600000, // 10 minutes

            data: {
                'obj_id': obj_id,
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                json_response = response;
                try {
                    $('#report-summary-body').html(json_response.data.answer.summarize);
                    // Fill complainant data
                    var denunciante = json_response.data.answer.denunciante;

                    $('#complainant-name').val(denunciante.nombre + ' ' + denunciante.apellidos);
                    $('#complainant-phone').val(denunciante.telefono);
                    $('#complainant-dni').val(denunciante.dni);
                    $('#complainant-address').val(denunciante.direccion);

                    var agente = json_response.data.answer.agente;
                    $('#agent-name').val(agente.nombre + ' ' + agente.apellidos);
                    $('#agent-number').val(agente.numero_agente);
                    $('#agent-rank').val(agente.rango);
                    $('#agent-station').val(agente.comisaria);
                    $('#report-extract-data').show();
                } catch (e) {
                    console.log("Error filling data: " + e);
                }

                Swal.close();
                Swal.fire({
                    title: 'Interpretando....',
                    text: 'Se han recuperado los datos. Por favor, espere mientras la IA interpreta el expediente y elabora un relato detallado de la situación.',
                    allowOutsideClick: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });


                //requet url to fetch interpretation
                var url_interpretation = button.data('url-interpretation');
                $.ajax({
                    url: url_interpretation,
                    type: 'POST',
                    timeout: 600000, // 10 minutes
                    data: {
                        'obj_id': obj_id,
                        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
                    },
                    success: function (response_interpretation) {
                        json_response_interpretation = response_interpretation;
                        try {
                            $('#report-interpretation').html(json_response_interpretation.data.answer);
                            Swal.close();

                            Swal.fire({
                                title: 'Éxito',
                                //text in html format
                                html: 'El expediente ha sido enviado a la IA correctamente.<br> Puede revisar y completar los datos extraídos y el relato generado antes de continuar.',
                                icon: 'success',
                                confirmButtonText: 'OK'
                            });
                        } catch (e) {
                            console.log("Error filling interpretation data: " + e);
                            Swal.close();
                            Swal.fire({
                                title: 'Error',
                                text: 'Ha ocurrido un error al procesar la interpretación del expediente',
                                icon: 'error',
                                confirmButtonText: 'OK'
                            });
                        }

                    },
                    error: function (xhr, status, error) {
                        Swal.close();
                        Swal.fire({
                            title: 'Error',
                            text: 'Ha ocurrido un error al obtener la interpretación del expediente',
                            icon: 'error',
                            confirmButtonText: 'OK'
                        });
                        console.log("Error fetching interpretation: " + error);
                    }
                });

            },
            error: function (xhr, status, error) {
                var message = 'Ha ocurrido un error desconocido.';
                console.log(xhr.responseText);
                console.log(error);
                console.log(status);
                try {
                    var message = JSON.parse(xhr.responseText).error;
                } catch (e) {
                    var message = 'Ha ocurrido un error desconocido.';
                }
                Swal.close();
                Swal.fire({
                    title: 'Error',
                    html: message,
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            },
            complete: function () {
                button.prop('disabled', false);
            }
        });

    });

    load_expedient_interpretation($('#report-interpretation').data('obj-id'), $('#report-interpretation').data('url'));
    extract_personal_data($('#report-interpretation').data('obj-id'), $('#report-interpretation').data('url-extract-personal-data'));
});

async function load_expedient_interpretation(obj_id, url) {
    console.log("Loading interpretation for obj_id: " + obj_id + " from url: " + url);
    var button = $('#launch-analysis');
    obj_id = obj_id || button.data('item');
    url = url || button.data('url-interpretation');
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 600000, // 10 minutes
        data: {
            'obj_id': obj_id,
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
        },
        success: function (response_interpretation) {
            json_response_interpretation = response_interpretation;
            try {
                $('#report-interpretation').html(json_response_interpretation.data.answer);
                return true;
            } catch (e) {
                console.log("Error filling interpretation data: " + e);
                $('#report-interpretation').html('<p class="text-danger">No se ha podido cargar la interpretación del expediente.</p>');
                return false;
            }

        },
        error: function (xhr, status, error) {
            $('#report-interpretation').html('<p class="text-danger">No se ha podido cargar la interpretación del expediente.</p>');
            console.log("Error fetching interpretation: " + error);
            return false;
        }
    });
}

async function extract_personal_data(obj_id, url) {
    var button = $('#launch-analysis');
    obj_id = obj_id || button.data('item');
    url = url || button.data('url-extract-personal-data');
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 600000, // 10 minutes
        data: {
            'obj_id': obj_id,
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
        },
        success: function (response) {
            json_response = response;
            try {
                // Show extracted personal data in a Swal
                let personal_data_html = '<ul>';
                for (const [key, value] of Object.entries(json_response.data.personal_data)) {
                    personal_data_html += `<li><strong>${key}:</strong> ${value}</li>`;
                }
                personal_data_html += '</ul>';


            } catch (e) {
                console.log("Error displaying personal data: " + e);
            }

        },
        error: function (xhr, status, error) {
            console.log("Error fetching personal data: " + error);
        }
    });
}