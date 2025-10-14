$(document).ready(function() {
    $('.retranscribe-audio').click(function() {
        var obj_id = $(this).data('id');
        var url = $(this).data('url');
        var button = $(this);
        button.prop('disabled', true);
        // Open sweetalert2 with "Processing..." message
        Swal.fire({
            title: 'Procesando...',
            text: 'Por favor, espere mientras se retranscribe el audio.',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        $.ajax({
            url: url,
            type: 'POST',
            data: {
                'obj_id': obj_id,
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                json_response = response;
                Swal.close();
                Swal.fire({
                    title: 'Éxito',
                    //text in html format
                    html: 'El audio ha sido retranscrito correctamente.<br>' + json_response.texto,
                    icon: 'success',
                    confirmButtonText: 'OK'
                }).then((result) => {
                    if (result.isConfirmed) {
                        location.reload();
                    }
                });
            },
            error: function(xhr, status, error) {
                Swal.close();
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al retranscribir el audio',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            },
            complete: function() {
                button.prop('disabled', false);
            }
        });

    });

    // Check if exists processed-False class in any button
    if ($('.retranscribe-audio.processed-False').length > 0) {
        setTimeout(function() {
            location.reload();
        }, 15000);
    }

});