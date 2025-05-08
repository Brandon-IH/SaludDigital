// Conexión WebSocket al servidor
const socket = new WebSocket('ws://localhost:8765'); // Asegura que la URL sea la correcta

socket.onopen = function () {
    console.log('Conectado al servidor WebSocket');
};

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log('Datos recibidos del servidor:', data);
};

socket.onclose = function () {
    console.log('Desconectado del servidor WebSocket');
};

// Manejo del formulario de comentarios
const comentarioForm = document.querySelector('.comentarios__formulario');
comentarioForm.addEventListener('submit', function (event) {
    event.preventDefault();

    const comentarioInput = document.querySelector('.formulario__comentarios');
    const comentario = comentarioInput.value;

    if (comentario) {
        fetch('/api/comentarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comentario })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Comentario enviado correctamente');
                comentarioInput.value = '';
                mostrarNotificacion('Comentario enviado correctamente', 'success');
            })
            .catch(error => {
                console.error('Error al enviar el comentario:', error);
                mostrarNotificacion('Error al enviar el comentario', 'error');
            });
    }
});

// Función para mostrar una notificación en pantalla
function mostrarNotificacion(mensaje, tipo) {
    const notificacion = document.createElement('div');
    notificacion.textContent = mensaje;
    notificacion.classList.add('notificacion', tipo);

    document.body.appendChild(notificacion);
    setTimeout(() => {
        notificacion.remove();
    }, 3000);
}

// Manejo del formulario de citas
document.getElementById('citasForm').addEventListener('submit', function (event) {
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
            mostrarNotificacion('Cita registrada correctamente', 'success');
            console.log("Cita enviada:", data);
        })
        .catch(error => {
            console.error('Error al registrar cita:', error);
            mostrarNotificacion('Error al registrar cita', 'error');
        });

    // Resetear el formulario después de enviarlo
    event.target.reset();
});

// Función para desplazarse a la sección de agendar cita
function desplazar() {
    document.getElementById('agendar-cita').scrollIntoView({ behavior: 'smooth' });
}

