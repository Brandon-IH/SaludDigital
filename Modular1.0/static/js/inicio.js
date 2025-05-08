// INDEX

    // Conexión WebSocket al servidor
    const socket = new WebSocket('ws://localhost:8765'); // Asegúrate de que la URL sea la correcta

    socket.onopen = function() {
        console.log('Conectado al servidor WebSocket');
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Datos recibidos del servidor:', data);
        // Aquí puedes actualizar el frontend con los nuevos datos que lleguen, si es necesario
    };

    socket.onclose = function() {
        console.log('Desconectado del servidor WebSocket');
    };

    // Manejo del formulario de comentarios
    const comentarioForm = document.querySelector('.comentarios__formulario');
    comentarioForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const comentarioInput = document.querySelector('.formulario__comentarios');
        const comentario = comentarioInput.value;

        if (comentario) {
            // Envía el comentario al servidor Flask (backend)
            fetch('/api/comentarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    comentario: comentario
                })
            })
            .then(response => {
                if (response.ok) {
                    console.log('Comentario enviado correctamente');

                    // Limpiar el cuadro de texto
                    comentarioInput.value = '';

                    // Mostrar notificación de éxito
                    mostrarNotificacion('Comentario enviado correctamente', 'success');
                } else {
                    console.error('Error al enviar el comentario');
                    mostrarNotificacion('Error al enviar el comentario', 'error');
                }
            })
            .catch(error => {
                console.error('Error al enviar el comentario:', error);
                mostrarNotificacion('Error al enviar el comentario', 'error');
            });
        }
    });

// Función para mostrar una notificación
function mostrarNotificacion(mensaje, tipo) {
    const notificacion = document.createElement('div');
    notificacion.textContent = mensaje;
    notificacion.classList.add('notificacion', tipo);
    
    document.body.appendChild(notificacion);

    setTimeout(() => {
        notificacion.remove();
    }, 3000); // La notificación desaparece después de 3 segundos
}

document.getElementById('citasForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Evita la recarga de la página

    const cita = {
        nombre_alumno: document.getElementById('nombre_alumno').value,
        apellidos: document.getElementById('apellidos').value,
        correo_alumno: document.getElementById('correo_alumno').value,
        codigo: document.getElementById('codigo').value,
        departamento: document.getElementById('departamento').value,
        hora: document.getElementById('hora').value,
        dia: document.getElementById('dia').value,
        celular: document.getElementById('celular').value,
        estatus: 'pendiente'
    };

    fetch('/agendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cita)
    })
    .then(response => response.json())
    .then(data => {
        showMessage('Cita registrada correctamente');
        console.log("Cita enviada:", data);
    })
    .catch(error => {
        console.error('Error al registrar cita:', error);
        showMessage('Error al registrar cita', true);
    });

    // Resetear el formulario después de enviarlo
    event.target.reset();
});


// FUNCTION: DESPLAZAR
function desplazar() {
    document.getElementById('agendar-cita').scrollIntoView({ behavior: 'smooth' });
}
