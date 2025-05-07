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

// Obtener el área actual desde la URL o una variable fija
const areaActual = window.location.pathname.replace("/", "") || "default"; // Puedes asignar un área específica si no usas rutas

// Cargar datos específicos del área
const servicios = JSON.parse(localStorage.getItem(`servicios-${areaActual}`)) || [
    { titulo: "Descripción del servicio", contenido: "Atención médica básica, evaluaciones físicas, diagnóstico de enfermedades comunes, control de presión arterial y más." },
    { titulo: "Horarios de Atención", contenido: "Lunes a Viernes: 8:00 AM - 6:00 PM\nSábado: 9:00 AM - 2:00 PM\nSe requiere cita previa." },
    { titulo: "Personal Médico", contenido: "Dr. Juan Pérez - Médico General\nDra. Ana López - Especialista en Medicina Familiar" },
    { titulo: "Información Útil", contenido: "Traer credencial de estudiante y cartilla de vacunación si aplica." },
    { titulo: "Procedimientos Comunes", contenido: "<ul><li>Chequeo de presión arterial</li><li>Pruebas rápidas de glucosa</li><li>Revisión de síntomas generales</li></ul>" },
    { titulo: "Contacto", contenido: "📞 Teléfono: (33) 1234-5678<br>✉ Correo: psocucei@cucei.udg.mx<br><a href='/citas' class='boton-agendar'>Agendar Cita</a>" }
];

function guardarDatos() {
    localStorage.setItem(`servicios-${areaActual}`, JSON.stringify(servicios));
}

function renderTarjetas() {
    const container = document.getElementById("grid-container");
    container.innerHTML = ""; // Limpiar contenido anterior

    servicios.forEach((servicio, index) => {
        const tarjeta = document.createElement("div");
        tarjeta.classList.add("tarjeta");

        let contenidoHTML;

        if (servicio.contenido.includes("<li>")) {
            let items = servicio.contenido.replace(/<\/?ul>/g, "").split("</li>").filter(item => item.trim() !== "");
            contenidoHTML = `<ul>` + items.map(item => `<li>${item}</li>`).join("") + `</ul>`;
        } else {
            contenidoHTML = `<p>${servicio.contenido}</p>`;
        }

        tarjeta.innerHTML = `
            <h2>${servicio.titulo}</h2>
            <p>${contenidoHTML}</p>
            <button class="editar btn" onclick="mostrarFormulario(${index})">Editar</button>
            <button class="eliminar btn" onclick="eliminarTarjeta(${index})">Eliminar</button>
            <div id="formulario-${index}" class="formulario-edicion" style="display: none;">
                <input type="text" id="edit-titulo-${index}" value="${servicio.titulo}">
                <textarea id="edit-contenido-${index}"></textarea>
                <button onclick="guardarEdicion(${index})">Guardar</button>
                <button onclick="cancelarEdicion(${index})">Cancelar</button>
            </div>
        `;


        container.appendChild(tarjeta);
    });
}


function mostrarFormulario(index) {
    let formulario = document.getElementById(`formulario-${index}`);
    formulario.style.display = "block";
    formulario.style.opacity = "1";  // Hacerlo completamente visible
    formulario.style.transform = "translateY(0)"; // Ajustar animación

    let contenidoActual = servicios[index].contenido;
    
    // Convertir listas en texto editable
    if (contenidoActual.includes("<li>")) {
        contenidoActual = contenidoActual.replace(/<\/?ul>/g, "")
            .replace(/<\/?li>/g, "")
            .split("\n")
            .filter(item => item.trim() !== "")
            .join("\n");
    }

    document.getElementById(`edit-contenido-${index}`).value = contenidoActual;
}


function guardarEdicion(index) {
    const nuevoTitulo = document.getElementById(`edit-titulo-${index}`).value;
    let nuevoContenido = document.getElementById(`edit-contenido-${index}`).value;

    // Si el contenido tiene saltos de línea, conviértelo en una lista
    if (nuevoContenido.includes("\n")) {
        let items = nuevoContenido.split("\n").filter(item => item.trim() !== "");
        nuevoContenido = `<ul>` + items.map(item => `<li>${item}</li>`).join("") + `</ul>`;
    }

    servicios[index].titulo = nuevoTitulo;
    servicios[index].contenido = nuevoContenido;
    guardarDatos();
    renderTarjetas();
}

function cancelarEdicion(index) {
    document.getElementById(`formulario-${index}`).style.display = "none";
}

function eliminarTarjeta(index) {
    servicios.splice(index, 1);
    guardarDatos();
    renderTarjetas();
}

function agregarTarjeta() {
    document.getElementById("nuevo-formulario").style.display = "block";
}

function guardarNuevaTarjeta() {
    const titulo = document.getElementById("nuevo-titulo").value;
    const contenido = document.getElementById("nuevo-contenido").value;

    if (titulo && contenido) {
        servicios.push({ titulo, contenido });
        guardarDatos();
        renderTarjetas();
        document.getElementById("nuevo-formulario").style.display = "none";
    } else {
        alert("Debes ingresar ambos campos.");
    }
}

document.addEventListener("DOMContentLoaded", renderTarjetas);


