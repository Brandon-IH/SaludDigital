// Conexión al servidor WebSocket
const socket = new WebSocket("ws://localhost:8765");
    
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Datos recibidos:', data);

    // Actualizar datos de comentarios
    if (data.comentarios) {
        updateChart(data.comentarios);
        updateTotalComments(data.comentarios.TotalComentarios);
    } else {
        console.error("Datos de comentarios no disponibles.");
    }

    // Actualizar datos de citas
    if (data.citas && data.citas.length > 0) {
        updateAppointments(data.citas);
        updateTotalAppointments(data.citas.length);
    } else {
        updateAppointments([]);
        updateTotalAppointments(0);
        console.log("No hay citas disponibles.");
    }

    // Actualizar total de alumnos
    if (data.total_alumnos !== undefined) {
        updateTotalAlumnos(data.total_alumnos);
    } else {
        console.error("Datos de total de alumnos no disponibles.");
    }
};

socket.onerror = function(error) {
    console.error("Error de WebSocket: ", error);
};

socket.onopen = function() {
    console.log("Conexión WebSocket establecida.");
};

socket.onclose = function() {
    console.log("Conexión WebSocket cerrada.");
};

// Función para actualizar la gráfica
function updateChart(data) {
    if (data && data.Positivos !== undefined && data.Neutrales !== undefined && data.Negativos !== undefined) {
        commentsChart.data.datasets[0].data = [
            data.Positivos,
            data.Neutrales,
            data.Negativos
        ];
        commentsChart.update();
    } else {
        console.error("Datos de comentarios inválidos: ", data);
    }
}

// Función para actualizar el total de comentarios
function updateTotalComments(total) {
    const totalCommentsElement = document.getElementById('total-comments');
    if (total !== undefined) {
        totalCommentsElement.textContent = total;
    } else {
        console.error("Total de comentarios inválido: ", total);
    }
}

// Función para actualizar el total de citas
function updateTotalAppointments(total) {
    const totalAppointmentsElement = document.getElementById('total-appointments');
    if (total !== undefined) {
        totalAppointmentsElement.textContent = total;
    } else {
        console.error("Total de citas inválido: ", total);
    }
}

// Función para actualizar el total de alumnos
function updateTotalAlumnos(total) {
    const totalAlumnosElement = document.getElementById('total-alumnos');
    if (total !== undefined) {
        totalAlumnosElement.textContent = total;
    } else {
        console.error("Total de alumnos inválido: ", total);
    }
}

function updateAppointments(citas) {
    const listaCitas = document.getElementById('lista-citas');
    listaCitas.innerHTML = ""; // Limpia la lista antes de llenarla

    if (citas.length === 0) {
        listaCitas.innerHTML = "<li>No hay citas disponibles</li>";
    } else {
        citas.forEach(cita => {
            const li = document.createElement('li');
            li.textContent = `${cita.hora} - ${cita.nombre_alumno} (${cita.departamento})`;
            listaCitas.appendChild(li);
        });
    }
}

window.addEventListener('load', function() {
    var currentPath = window.location.pathname;
    var menuItems = document.querySelectorAll('.side-menu a');

    menuItems.forEach(function(item) {
        if (currentPath.includes(item.getAttribute('href'))) {
            item.classList.add('active');
        }
    });
});

function toggleSideMenu() {
    const sideMenu = document.querySelector('.side-menu');
    const mainContent = document.querySelector('main');

    sideMenu.classList.toggle('hidden');
    mainContent.classList.toggle('main-full');
}



// Configuración del horario de la enfermería
const openingHour = 8; // Hora de apertura (8:00 AM)
const closingHour = 20; // Hora de cierre (7:00 PM)

function updateNursingStatus() {
    const now = new Date();
    const currentHour = now.getHours();
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    if (currentHour >= openingHour && currentHour < closingHour) {
        statusIndicator.style.backgroundColor = 'green';
        statusText.textContent = 'Abierto';
    } else {
        statusIndicator.style.backgroundColor = 'red';
        statusText.textContent = 'Cerrado';
    }
}

const ctx = document.getElementById('commentsGraph').getContext('2d');
const commentsChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Buenos', 'Regulares', 'Malos'],
        datasets: [{
            label: 'Comentarios Analizados',
            data: [1, 1, 1],
            backgroundColor: [
                'rgba(75, 192, 192, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(255, 99, 132, 0.6)'
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'bottom', // Cambia la posición a la parte inferior
                labels: {
                    font: {
                        size: 16 // Ajusta el tamaño de las etiquetas
                    },
                    color: 'black' // Cambia el color si lo deseas
                }
            },
            title: {
                display: true,
                text: 'Distribución de Comentarios',
                font: {
                    size: 24,
                    weight: 'bold' // Puedes ajustar el grosor del texto
                },
                color: 'black'
            },
        }
    }
});

updateNursingStatus();
setInterval(updateNursingStatus, 60000); // Actualiza cada minuto