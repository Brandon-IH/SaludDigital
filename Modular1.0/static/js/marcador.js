// Espera a que la ventana se cargue completamente antes de ejecutar la función
window.addEventListener('load', function() {
    // Obtiene la ruta actual de la URL
    var currentPath = window.location.pathname;
    // Selecciona todos los elementos de enlace dentro del menú lateral
    var menuItems = document.querySelectorAll('.side-menu a');

    // Itera sobre cada elemento del menú
    menuItems.forEach(function(item) {
        // Si la ruta actual coincide con el atributo href del enlace
        if (currentPath === item.getAttribute('href')) {
            // Añade la clase 'active' al enlace
            item.classList.add('active');
        }
    });
});

// Función para alternar la visibilidad del menú lateral
function toggleSideMenu() {
    // Selecciona el menú lateral
    const sideMenu = document.querySelector('.side-menu');
    // Selecciona el contenido principal
    const mainContent = document.querySelector('main');

    // Alterna la clase 'hidden' en el menú lateral
    sideMenu.classList.toggle('hidden');
    // Alterna la clase 'main-full' en el contenido principal
    mainContent.classList.toggle('main-full');
}
