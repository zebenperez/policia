$(document).ready(function() {
    let muted = false;
    $('.retranscribe-audio').click(function() {
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
            success: function(response) {
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
            error: function(xhr, status, error) {
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
            complete: function() {
                button.prop('disabled', false);
            }
        });

    });

    // Check if exists processed-False class in any button
    if ($('button.retranscribe-audio.processed-False').length > 0) {
        // Trigger click event in the first button with processed-False class
        muted = true;
        $('button.retranscribe-audio.processed-False').first().click();
    }

    $('.expte-2-llm').click(function() {
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
            success: function(response) {
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
                    title: 'Éxito',
                    //text in html format
                    html: 'El expediente ha sido enviado a la IA correctamente.<br>Resumen: ' + json_response.data.answer.summarize,
                    icon: 'success',
                    confirmButtonText: 'OK'
                });
            },
            error: function(xhr, status, error) {
                var message = 'Ha ocurrido un error desconocido.';
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
            complete: function() {
                button.prop('disabled', false);
            }
        });

    });
});

