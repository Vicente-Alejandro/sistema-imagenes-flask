/**
 * Funciones específicas para el panel de administración
 */

// Variables globales
window.currentFilters = {
    search: '',
    sortBy: 'default',
    order: 'asc'
};

/**
 * Inicializa la funcionalidad de búsqueda y filtrado en la página de admin
 */
function initAdminImageSearch() {
    const searchInput = document.getElementById('imageSearch');
    const searchButton = document.getElementById('searchButton');
    const sortSelect = document.getElementById('sortBy');
    const orderToggle = document.getElementById('orderToggle');
    
    if (!searchInput || !searchButton) return;
    
    // Manejar la búsqueda
    searchButton.addEventListener('click', function() {
        window.currentFilters.search = searchInput.value.toLowerCase();
        applyFilters();
    });
    
    // Búsqueda al presionar Enter
    searchInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            window.currentFilters.search = this.value.toLowerCase();
            applyFilters();
        }
    });
    
    // Manejar el cambio de criterio de ordenación
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            window.currentFilters.sortBy = this.value;
            applyFilters();
        });
    }
    
    // Manejar el cambio de dirección de ordenación
    if (orderToggle) {
        orderToggle.addEventListener('click', function() {
            window.currentFilters.order = window.currentFilters.order === 'asc' ? 'desc' : 'asc';
            this.innerHTML = window.currentFilters.order === 'asc' ? '&#8593;' : '&#8595;';
            applyFilters();
        });
    }
}

/**
 * Aplica los filtros a las imágenes
 */
function applyFilters() {
    const searchTerm = window.currentFilters.search.toLowerCase();
    const sortBy = window.currentFilters.sortBy;
    const order = window.currentFilters.order;
    
    const gallery = document.querySelector('.image-detail-grid');
    const noResults = document.getElementById('noSearchResults');
    
    if (!gallery) return;
    
    const images = Array.from(gallery.querySelectorAll('.image-detail-card'));
    let visibleCount = 0;
    
    // Filtrar por término de búsqueda
    images.forEach(image => {
        const title = image.querySelector('.image-detail-title')?.textContent.toLowerCase() || '';
        const username = image.querySelector('.image-detail-meta')?.textContent.toLowerCase() || '';
        
        if (searchTerm === '' || title.includes(searchTerm) || username.includes(searchTerm)) {
            image.style.display = '';
            visibleCount++;
        } else {
            image.style.display = 'none';
        }
    });
    
    // Mostrar mensaje si no hay resultados
    if (noResults) {
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
    
    // Ordenar imágenes visibles
    if (sortBy !== 'default' && visibleCount > 0) {
        sortImages(sortBy, order);
    }
}

/**
 * Ordena las imágenes según el criterio seleccionado
 */
function sortImages(sortBy, order) {
    const gallery = document.querySelector('.image-detail-grid');
    if (!gallery) return;
    
    const images = Array.from(gallery.querySelectorAll('.image-detail-card:not([style*="display: none"])'));
    
    images.sort((a, b) => {
        let valueA, valueB;
        
        if (sortBy === 'name') {
            valueA = a.querySelector('.image-detail-title')?.textContent || '';
            valueB = b.querySelector('.image-detail-title')?.textContent || '';
        } else if (sortBy === 'user') {
            // Buscar el nombre de usuario en el texto de metadatos
            const metaA = a.querySelector('.image-detail-meta')?.textContent || '';
            const metaB = b.querySelector('.image-detail-meta')?.textContent || '';
            
            // Extraer el nombre de usuario (después de "Subida por:")
            const userRegex = /Subida por:\s*([^\n]+)/;
            const matchA = metaA.match(userRegex);
            const matchB = metaB.match(userRegex);
            
            valueA = matchA ? matchA[1] : '';
            valueB = matchB ? matchB[1] : '';
        } else if (sortBy === 'date') {
            // Buscar la fecha en el texto de metadatos
            const metaA = a.querySelector('.image-detail-meta')?.textContent || '';
            const metaB = b.querySelector('.image-detail-meta')?.textContent || '';
            
            // Extraer la fecha (después de "Fecha:")
            const dateRegex = /Fecha:\s*([^\n]+)/;
            const matchA = metaA.match(dateRegex);
            const matchB = metaB.match(dateRegex);
            
            valueA = matchA ? matchA[1] : '';
            valueB = matchB ? matchB[1] : '';
        }
        
        // Invertir orden si es descendente
        const orderMultiplier = order === 'asc' ? 1 : -1;
        
        return orderMultiplier * valueA.localeCompare(valueB);
    });
    
    // Reordenar elementos en el DOM
    images.forEach(image => gallery.appendChild(image));
}

/**
 * Confirma y elimina una imagen desde la vista de administración
 */
function adminDeleteImage(imageId, button) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
        return;
    }
    
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    fetch(`/admin/images/${imageId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-TOKEN': csrfToken || ''
        }
    })
    .then(response => {
        if (response.ok) {
            // Encontrar y eliminar la tarjeta de imagen
            const card = button.closest('.image-detail-card');
            if (card) {
                card.remove();
                
                // Verificar si no quedan imágenes
                const remainingImages = document.querySelectorAll('.image-detail-card').length;
                if (remainingImages === 0) {
                    const gallery = document.querySelector('.image-detail-grid');
                    const noImagesMsg = document.createElement('div');
                    noImagesMsg.className = 'no-images-message';
                    noImagesMsg.innerHTML = '<p>No hay imágenes que mostrar.</p>';
                    
                    if (gallery) {
                        gallery.after(noImagesMsg);
                        gallery.style.display = 'none';
                    }
                }
                
                // Mostrar notificación
                showNotification('Imagen eliminada correctamente', 'success');
            }
        } else {
            showNotification('Error al eliminar la imagen', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al eliminar la imagen', 'error');
    });
}

/**
 * Muestra una notificación
 */
function showNotification(message, type = 'info', duration = 3500) {
    // Verificar si ya existe un contenedor de notificaciones
    let notifContainer = document.querySelector('.notification-container');
    
    if (!notifContainer) {
        notifContainer = document.createElement('div');
        notifContainer.className = 'notification-container';
        document.body.appendChild(notifContainer);
    }
    
    // Crear la notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-message">${message}</div>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    // Añadir la notificación al contenedor
    notifContainer.appendChild(notification);
    
    // Mostrar la notificación con un efecto
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Configurar cierre de notificación
    const closeBtn = notification.querySelector('.notification-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }
    
    // Auto-cerrar después del tiempo especificado
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, duration);
    
    return notification;
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar búsqueda y filtros
    initAdminImageSearch();
    
    // Aplicar filtros iniciales
    applyFilters();
});
