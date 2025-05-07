function showMessage(message, isError = false) {
    const messageBox = document.getElementById('message-box');
    messageBox.textContent = message;
    messageBox.style.display = 'block';
    
    // Aplicar clases para mostrar el mensaje con opacidad
    setTimeout(() => {
        messageBox.classList.add('visible');
    }, 10);

    if (isError) {
        messageBox.classList.add('error');
    } else {
        messageBox.classList.remove('error');
    }

    setTimeout(() => {
        messageBox.classList.remove('visible');
        setTimeout(() => {
            messageBox.style.display = 'none';
        }, 500);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('citas.js cargado correctamente');

    const citasForm = document.getElementById('citasForm');
    const citasTableBody = document.getElementById('citasTable').querySelector('tbody');
    let citas = [];

    function fetchCitas() {
        console.log('Fetching citas...');
        fetch('/api/citas')
            .then(response => response.json())
            .then(data => {
                console.log('Citas fetched:', data);
                citas = data;
                renderCitas();
            })
            .catch(error => {
                console.error('Error al cargar citas:', error);
                showMessage('Error al cargar citas', true);
            });
    }

    function renderCitas() {
        console.log('Rendering citas...');
    
        // Ordenar las citas por estatus y fecha
        citas.sort((a, b) => {
            const estatusOrder = { pendiente: 1, completada: 2, cancelada: 3 }; // Orden de estatus
            const estatusA = estatusOrder[a.estatus] || 4; // Si el estatus no está definido, asignar un orden alto
            const estatusB = estatusOrder[b.estatus] || 4;
    
            // Primero por estatus, luego por fecha (más cercana primero)
            if (estatusA === estatusB) {
                return new Date(`${a.dia}T${a.hora}:00`) - new Date(`${b.dia}T${b.hora}:00`);
            }
            return estatusA - estatusB;
        });
    
        // Limpiar la tabla antes de renderizar
        citasTableBody.innerHTML = '';
    
        citas.forEach(cita => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${cita.nombre_alumno}</td>
                <td>${cita.apellidos}</td>
                <td>${cita.correo_alumno}</td>
                <td>${cita.codigo}</td>
                <td>${cita.departamento}</td>
                <td>${cita.hora}</td>
                <td>${cita.dia}</td>
                <td>${cita.estatus}</td>
                <td>
                    <div class="button-container">
                        <button class="button edit" data-id="${cita.id}">Editar</button>
                        <button class="button delete" data-id="${cita.id}">Eliminar</button>
                    </div>
                </td>
            `;
            citasTableBody.appendChild(row);
        });
    
        console.log('Citas rendered in sorted order.');
    }
    

    document.getElementById('citasForm').addEventListener('submit', function(event) {
        event.preventDefault();
    
        const cita = {
            id: document.getElementById('id').value,
            nombre_alumno: document.getElementById('nombre_alumno').value,
            apellidos: document.getElementById('apellidos').value,
            correo_alumno: document.getElementById('correo_alumno').value,
            codigo: document.getElementById('codigo').value,
            departamento: document.getElementById('departamento').value,
            hora: document.getElementById('hora').value,
            dia: document.getElementById('dia').value,
            estatus: document.getElementById('estatus').value
        };
        // Convertir el formato dd-mm-yyyy a yyyy-mm-dd
        function convertirFormatoFecha(fecha) {
            const [day, month, year] = fecha.split('-'); // Dividir la fecha en partes
            return `${year}-${month}-${day}`; // Reorganizar al formato yyyy-mm-dd
        }

        // Obtener fecha y hora actuales
        const now = new Date();
        const diaFormateado = convertirFormatoFecha(cita.dia); // Convertir fecha ingresada
        const diaIngresado = new Date(diaFormateado); // Crear instancia válida de fecha
        const [hourIngresada, minuteIngresada] = cita.hora.split(':').map(Number);

        // Crear instancias específicas para comparación de fechas y horas
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const fechaHoraIngresada = new Date(diaIngresado);
        fechaHoraIngresada.setHours(hourIngresada, minuteIngresada, 0, 0);

        // Validación 1: La hora debe estar entre las 08:00 y las 20:00
        if (hourIngresada < 8 || hourIngresada >= 20) {
            showMessage('La hora debe estar entre las 08:00 y las 20:00.', true);
            return;
        }

        // Validación 2: No se pueden programar citas en fines de semana
        const dayOfWeek = diaIngresado.getDay();
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            showMessage('No se pueden programar citas en fines de semana.', true);
            return;
        }

        // Validación 3: No se pueden agendar citas en días anteriores a hoy
        if (diaIngresado < today) {
            showMessage('No se pueden agendar citas en días anteriores a hoy.', true);
            return;
        }

        // Validación 4: No se pueden agendar citas en horas pasadas del día actual
        if (diaIngresado.getTime() === today.getTime() && fechaHoraIngresada < now) {
            showMessage('No se pueden agendar citas en horas anteriores a la hora actual.', true);
            return;
        }

        // Si pasa todas las validaciones
        showMessage('Cita validada correctamente.', false);


    
        // Procesar la cita si todas las validaciones son exitosas
        if (cita.id) {
            fetch(`/api/citas/${cita.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cita)
            }).then(response => {
                if (response.ok) {
                    showMessage('Cita actualizada correctamente');
                } else {
                    showMessage('Error al actualizar la cita', true);
                }
                fetchCitas();
            }).catch(error => {
                console.error('Error al editar cita:', error);
                showMessage('Error al editar cita', true);
            });
        } else {
            fetch('/api/citas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cita)
            }).then(response => {
                if (response.ok) {
                    showMessage('Cita agregada correctamente');
                } else {
                    showMessage('Error al agregar la cita', true);
                }
                fetchCitas();
            }).catch(error => {
                console.error('Error al añadir cita:', error);
                showMessage('Error al añadir cita', true);
            });
        }
    
        citasForm.reset();
        document.getElementById('id').value = '';
    });
    
    

    citasTableBody.addEventListener('click', function(event) {
        if (event.target.classList.contains('edit')) {
            const citaId = event.target.dataset.id;
            const cita = citas.find(c => c.id == citaId);
            document.getElementById('id').value = cita.id;
            document.getElementById('nombre_alumno').value = cita.nombre_alumno;
            document.getElementById('apellidos').value = cita.apellidos;
            document.getElementById('correo_alumno').value = cita.correo_alumno;
            document.getElementById('codigo').value = cita.codigo;
            document.getElementById('departamento').value = cita.departamento;
            document.getElementById('hora').value = cita.hora;
            document.getElementById('dia').value = cita.dia;
            document.getElementById('estatus').value = cita.estatus;
        } else if (event.target.classList.contains('delete')) {
            const citaId = event.target.dataset.id;
            fetch(`/api/citas/${citaId}`, {
                method: 'DELETE'
            }).then(response => {
                if (response.ok) {
                    showMessage('Cita eliminada correctamente');
                } else {
                    showMessage('Error al eliminar la cita', true);
                }
                fetchCitas();
            }).catch(error => {
                console.error('Error al eliminar cita:', error);
                showMessage('Error al eliminar cita', true);
            });
        }
    });

    function loadCitas() {
        fetchCitas();
    }

    loadCitas();
});

window.addEventListener('load', function() {
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.side-menu a');
    menuItems.forEach(function(item) {
        if (currentPath === item.getAttribute('href')) {
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
