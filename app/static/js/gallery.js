/**
 * Funciones específicas para la galería de imágenes
 */

// Variables globales - definidas como window.variables para garantizar alcance global
window.currentIndex = 0;
window.images = [];
window.currentFilters = {
    search: '',
    sortBy: 'default',
    order: 'asc'
};

/**
 * Inicializa la carga diferida de imágenes
 */
function initLazyLoading() {
    const lazyImages = document.querySelectorAll('.lazy');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    
                    // Ocultar spinner cuando la imagen está cargada
                    img.onload = function() {
                        const spinner = img.nextElementSibling;
                        if (spinner && spinner.classList.contains('loading-spinner')) {
                            spinner.style.display = 'none';
                        }
                    };
                }
            });
        });
        
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback para navegadores que no soportan IntersectionObserver
        let lazyLoadThrottleTimeout;
        
        function lazyLoad() {
            if (lazyLoadThrottleTimeout) {
                clearTimeout(lazyLoadThrottleTimeout);
            }
            
            lazyLoadThrottleTimeout = setTimeout(function() {
                const scrollTop = window.pageYOffset;
                lazyImages.forEach(img => {
                    if (img.offsetTop < (window.innerHeight + scrollTop)) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        
                        // Ocultar spinner cuando la imagen está cargada
                        img.onload = function() {
                            const spinner = img.nextElementSibling;
                            if (spinner && spinner.classList.contains('loading-spinner')) {
                                spinner.style.display = 'none';
                            }
                        };
                    }
                });
                
                if (lazyImages.length == 0) { 
                    document.removeEventListener("scroll", lazyLoad);
                    window.removeEventListener("resize", lazyLoad);
                    window.removeEventListener("orientationChange", lazyLoad);
                }
            }, 20);
        }
        
        document.addEventListener("scroll", lazyLoad);
        window.addEventListener("resize", lazyLoad);
        window.addEventListener("orientationChange", lazyLoad);
        
        // Llamar a lazyLoad inmediatamente
        lazyLoad();
    }
}

/**
 * Abre el modal con la imagen seleccionada
 * @param {string} imageSrc - Ruta de la imagen
 * @param {string} caption - Descripción/título de la imagen
 */
function openImageModal(imageSrc, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    const downloadBtn = document.getElementById('downloadImage');
    
    // Mostrar el modal
    modal.style.display = 'block';
    
    // Establecer imagen y texto
    modalImg.src = imageSrc;
    modalCaption.textContent = caption;
    
    // Configurar botón de descarga
    if (downloadBtn) {
        downloadBtn.onclick = function() {
            downloadImage(imageSrc, caption);
        };
    }
    
    // Recopilar todas las imágenes para navegación (solo las visibles)
    window.images = Array.from(document.querySelectorAll('.thumbnail:not(.hidden)'));
    
    // Encontrar el índice de la imagen actual
    window.currentIndex = 0;
    for (let i = 0; i < window.images.length; i++) {
        const imgSrc = window.images[i].getAttribute('data-src');
        if (imgSrc === imageSrc) {
            window.currentIndex = i;
            break;
        }
    }
    
    // Mostrar/ocultar botones de navegación según sea necesario
    updateNavigationButtons();
}

/**
 * Cierra el modal de imagen
 */
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.style.display = 'none';
}

/**
 * Descarga la imagen actual
 * @param {string} src - Ruta de la imagen
 * @param {string} filename - Nombre de la imagen
 */
function downloadImage(src, filename) {
    const link = document.createElement('a');
    link.href = src;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Navega a la imagen anterior
 */
function showPreviousImage() {
    if (window.images.length <= 1) return;
    
    window.currentIndex = (window.currentIndex - 1 + window.images.length) % window.images.length;
    const prevImg = window.images[window.currentIndex];
    const src = prevImg.getAttribute('data-src');
    const caption = prevImg.getAttribute('alt');
    
    const modalImg = document.getElementById('modalImage');
    const captionText = document.getElementById('modalCaption');
    const downloadBtn = document.getElementById('downloadImage');
    
    modalImg.src = src;
    captionText.textContent = caption;
    
    if (downloadBtn) {
        downloadBtn.onclick = function() {
            downloadImage(src, caption);
        };
    }
    
    updateNavigationButtons();
}

/**
 * Navega a la imagen siguiente
 */
function showNextImage() {
    if (window.images.length <= 1) return;
    
    window.currentIndex = (window.currentIndex + 1) % window.images.length;
    const nextImg = window.images[window.currentIndex];
    const src = nextImg.getAttribute('data-src');
    const caption = nextImg.getAttribute('alt');
    
    const modalImg = document.getElementById('modalImage');
    const captionText = document.getElementById('modalCaption');
    const downloadBtn = document.getElementById('downloadImage');
    
    modalImg.src = src;
    captionText.textContent = caption;
    
    if (downloadBtn) {
        downloadBtn.onclick = function() {
            downloadImage(src, caption);
        };
    }
    
    updateNavigationButtons();
}

/**
 * Actualiza la visibilidad de los botones de navegación
 */
function updateNavigationButtons() {
    const prevButton = document.getElementById('prevImage');
    const nextButton = document.getElementById('nextImage');
    
    if (!prevButton || !nextButton) return;
    
    // Ocultar botón 'Anterior' si estamos en la primera imagen
    prevButton.style.visibility = window.currentIndex > 0 ? 'visible' : 'hidden';
    
    // Ocultar botón 'Siguiente' si estamos en la última imagen
    nextButton.style.visibility = window.currentIndex < window.images.length - 1 ? 'visible' : 'hidden';
}

/**
 * Edita el nombre de la imagen
 * @param {string} filename - Nombre del archivo de la imagen
 * @param {string} currentName - Nombre actual de la imagen
 */
function editImageName(filename, currentName) {
    // Mostrar el modal de edición
    const modal = document.getElementById('editNameModal');
    const nameInput = document.getElementById('newImageName');
    const filenameInput = document.getElementById('editImageFilename');
    
    if (!modal || !nameInput || !filenameInput) return;
    
    // Establecer valores actuales
    nameInput.value = currentName;
    filenameInput.value = filename;
    
    // Mostrar modal
    modal.style.display = "block";
    nameInput.focus();
}

/**
 * Cierra el modal de edición de nombre
 */
function closeEditNameModal() {
    const modal = document.getElementById('editNameModal');
    if (modal) {
        modal.style.display = "none";
    }
}

/**
 * Guarda el nuevo nombre de la imagen
 */
function saveImageName() {
    const filename = document.getElementById('editImageFilename').value;
    const newName = document.getElementById('newImageName').value;
    
    if (!filename || !newName || newName.trim() === '') {
        alert('Por favor ingresa un nombre válido');
        return false;
    }
    
    // Realizar petición para actualizar el nombre
    fetch(`/update-name/${filename}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_name: newName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la UI
            const imageItem = document.querySelector(`.image-item[data-filename="${filename}"]`);
            if (imageItem) {
                const viewBtn = imageItem.querySelector('.view-btn');
                const editBtn = imageItem.querySelector('.edit-btn');
                
                // Actualizar botones con el nuevo nombre
                if (viewBtn) {
                    viewBtn.setAttribute('onclick', `openImageModal('/uploads/${filename}', '${newName}')`);
                }
                
                if (editBtn) {
                    editBtn.setAttribute('onclick', `editImageName('${filename}', '${newName}')`);
                }
                
                // Cerrar modal
                closeEditNameModal();
                
                // Mostrar mensaje de éxito
                showNotification('Nombre actualizado correctamente', 'success');
            }
        } else {
            showNotification(data.message || 'Error al actualizar el nombre', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al actualizar el nombre', 'error');
    });
    
    return false;
}

/**
 * Muestra una notificación al usuario
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Verificar si ya existe un contenedor de notificaciones
    let notificationContainer = document.getElementById('notificationContainer');
    
    if (!notificationContainer) {
        // Crear el contenedor si no existe
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notificationContainer';
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    // Crear la notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">${message}</div>
        <span class="notification-close">&times;</span>
    `;
    
    // Añadir al contenedor
    notificationContainer.appendChild(notification);
    
    // Configurar cierre de notificación
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            if (notification.parentNode) {
                notificationContainer.removeChild(notification);
            }
        }, 300);
    });
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notificationContainer.removeChild(notification);
                }
            }, 300);
        }
    }, 5000);
}

/**
 * Elimina una imagen
 * @param {string} filename - Nombre del archivo a eliminar
 */
function deleteImage(filename) {
    if (confirm('¿Estás seguro de que quieres eliminar esta imagen?')) {
        fetch(`/delete/${filename}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Eliminar elemento del DOM
                    const imageItem = document.querySelector(`.image-item[data-filename="${filename}"]`);
                    if (imageItem) {
                        imageItem.remove();
                        
                        // Actualizar contador de imágenes
                        updateImageCount();
                        
                        // Mostrar mensaje de éxito
                        showNotification('Imagen eliminada correctamente', 'success');
                    }
                } else {
                    showNotification(data.message || 'Error al eliminar la imagen', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error al eliminar la imagen', 'error');
            });
    }
}

/**
 * Actualiza el contador de imágenes
 */
function updateImageCount() {
    const gallery = document.getElementById('gallery');
    if (gallery) {
        const count = gallery.querySelectorAll('.image-item').length;
        let stats = document.getElementById('imageStats');
        
        if (count === 0) {
            // Si no hay imágenes, mostrar mensaje "No hay imágenes"
            let noImages = document.getElementById('noImages');
            if (!noImages) {
                noImages = document.createElement('div');
                noImages.id = 'noImages';
                noImages.className = 'no-images';
                noImages.textContent = 'No hay imágenes subidas. ¡Sube la primera!';
                gallery.parentNode.insertBefore(noImages, gallery.nextSibling);
            }
            
            // Ocultar galería
            gallery.style.display = 'none';
            
            // Eliminar stats si existe
            if (stats) stats.remove();
        } else {
            // Mostrar galería
            gallery.style.display = 'grid';
            
            // Ocultar mensaje "No hay imágenes"
            const noImages = document.getElementById('noImages');
            if (noImages) noImages.style.display = 'none';
            
            // Actualizar o crear stats
            if (!stats) {
                stats = document.createElement('div');
                stats.id = 'imageStats';
                stats.className = 'stats';
                gallery.parentNode.insertBefore(stats, gallery);
            }
            
            stats.textContent = `Total de imágenes: ${count}`;
        }
    }
}

/**
 * Aplica los filtros y búsqueda a las imágenes
 */
function applyFilters() {
    const searchTerm = window.currentFilters.search.toLowerCase();
    const imageItems = document.querySelectorAll('.image-item');
    let visibleCount = 0;
    
    // Filtrar imágenes
    imageItems.forEach(item => {
        const filename = item.getAttribute('data-filename').toLowerCase();
        const nameElement = item.querySelector('.image-name');
        const name = nameElement ? nameElement.textContent.toLowerCase() : '';
        
        // Aplicar filtro de búsqueda
        const matchesSearch = searchTerm === '' || 
                              filename.includes(searchTerm) || 
                              name.includes(searchTerm);
        
        // Mostrar/ocultar según filtros
        if (matchesSearch) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });
    
    // Mostrar mensaje si no hay resultados
    const noResults = document.getElementById('noSearchResults');
    if (noResults) {
        if (visibleCount === 0 && imageItems.length > 0) {
            noResults.style.display = 'block';
        } else {
            noResults.style.display = 'none';
        }
    }
    
    // Aplicar ordenamiento
    if (window.currentFilters.sortBy !== 'default') {
        sortImages(window.currentFilters.sortBy, window.currentFilters.order);
    }
    
    // Actualizar contador de imágenes visibles
    const stats = document.getElementById('imageStats');
    if (stats) {
        stats.textContent = `Imágenes visibles: ${visibleCount} de ${imageItems.length}`;
    }
    
    // Guardar filtros en localStorage
    saveFiltersToLocalStorage();
}

/**
 * Ordena las imágenes según criterio seleccionado
 * @param {string} sortBy - Criterio de ordenación
 * @param {string} order - Dirección del ordenamiento (asc/desc)
 */
function sortImages(sortBy, order) {
    const gallery = document.getElementById('gallery');
    const items = Array.from(gallery.querySelectorAll('.image-item:not(.hidden)'));
    
    items.sort((a, b) => {
        let valueA, valueB;
        
        // Determinar valores a comparar según criterio de ordenamiento
        if (sortBy === 'name') {
            valueA = a.querySelector('.image-name').textContent.toLowerCase();
            valueB = b.querySelector('.image-name').textContent.toLowerCase();
        } 
        else if (sortBy === 'date') {
            // Extraer fecha del nombre (formato esperado: xxx-HHMM_DDMMAAAA.xxx)
            const filenameA = a.getAttribute('data-filename');
            const filenameB = b.getAttribute('data-filename');
            
            const datePartA = filenameA.split('-')[1]?.split('.')[0] || '';
            const datePartB = filenameB.split('-')[1]?.split('.')[0] || '';
            
            valueA = datePartA;
            valueB = datePartB;
        }
        else {
            // Default: orden original
            return 0;
        }
        
        // Aplicar dirección del ordenamiento
        let result = valueA.localeCompare(valueB);
        return order === 'desc' ? -result : result;
    });
    
    // Reordenar elementos en el DOM
    items.forEach(item => gallery.appendChild(item));
}

/**
 * Guarda los filtros actuales en localStorage
 */
function saveFiltersToLocalStorage() {
    localStorage.setItem('galleryFilters', JSON.stringify(window.currentFilters));
}

/**
 * Carga los filtros guardados desde localStorage
 */
function loadFiltersFromLocalStorage() {
    const savedFilters = localStorage.getItem('galleryFilters');
    if (savedFilters) {
        try {
            window.currentFilters = JSON.parse(savedFilters);
            
            // Aplicar filtros guardados a la interfaz
            const searchInput = document.getElementById('imageSearch');
            const sortSelect = document.getElementById('sortBy');
            const orderToggle = document.getElementById('orderToggle');
            
            if (searchInput) searchInput.value = window.currentFilters.search;
            if (sortSelect) sortSelect.value = window.currentFilters.sortBy;
            if (orderToggle) {
                orderToggle.innerHTML = window.currentFilters.order === 'asc' ? '&#8593;' : '&#8595;';
            }
            
            // Aplicar filtros a las imágenes
            applyFilters();
        } catch (e) {
            console.error('Error al cargar filtros:', e);
            localStorage.removeItem('galleryFilters');
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar lazy loading
    initLazyLoading();
    
    // Configurar eventos para el modal de imágenes
    const modal = document.getElementById('imageModal');
    const closeBtn = document.querySelector('.close-modal');
    const prevBtn = document.getElementById('prevImage');
    const nextBtn = document.getElementById('nextImage');
    const downloadBtn = document.getElementById('downloadImage');
    
    if (modal && closeBtn) {
        // Cerrar modal al hacer clic en X
        closeBtn.addEventListener('click', closeImageModal);
        
        // Cerrar modal al hacer clic fuera de la imagen
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeImageModal();
            }
        });
        
        // Navegación con teclado
        document.addEventListener('keydown', function(e) {
            if (modal.style.display === 'block') {
                if (e.key === 'Escape') {
                    closeImageModal();
                } else if (e.key === 'ArrowLeft') {
                    showPreviousImage();
                } else if (e.key === 'ArrowRight') {
                    showNextImage();
                }
            }
        });
        
        // Botones de navegación
        if (prevBtn) prevBtn.addEventListener('click', showPreviousImage);
        if (nextBtn) nextBtn.addEventListener('click', showNextImage);
    }
    
    // Configurar formulario de edición de nombre
    const editForm = document.getElementById('editNameForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveImageName();
        });
    }
    
    // Configurar cierre del modal de edición
    const closeEditBtn = document.querySelector('.close-edit-modal');
    if (closeEditBtn) {
        closeEditBtn.addEventListener('click', closeEditNameModal);
    }
    
    // Configurar búsqueda y filtros
    const searchInput = document.getElementById('imageSearch');
    const searchButton = document.getElementById('searchButton');
    const sortSelect = document.getElementById('sortBy');
    const orderToggle = document.getElementById('orderToggle');
    
    if (searchInput) {
        // Búsqueda en tiempo real al escribir
        // searchInput.addEventListener('input', function() {
        //     window.currentFilters.search = this.value;
        //     applyFilters();
        // });
        
        // Búsqueda al hacer clic en el botón
        if (searchButton) {
            searchButton.addEventListener('click', function() {
                window.currentFilters.search = searchInput.value;
                applyFilters();
            });
        }
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            window.currentFilters.sortBy = this.value;
            applyFilters();
        });
    }
    
    if (orderToggle) {
        orderToggle.addEventListener('click', function() {
            window.currentFilters.order = window.currentFilters.order === 'asc' ? 'desc' : 'asc';
            this.innerHTML = window.currentFilters.order === 'asc' ? '&#8593;' : '&#8595;';
            applyFilters();
        });
    }
    
    // Cargar filtros guardados
    loadFiltersFromLocalStorage();
    
    // Configurar formulario de subida de imágenes
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('fileInput');
            const files = fileInput.files;
            
            if (files.length === 0) {
                showNotification('Por favor selecciona al menos una imagen', 'error');
                return;
            }
            
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    
                    // Recargar la página para mostrar las nuevas imágenes
                    // (En una versión futura, se podrían añadir dinámicamente)
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showNotification(data.message || 'Error al subir imágenes', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Error al subir imágenes', 'error');
            }
            
            // Limpiar el input de archivos
            fileInput.value = '';
        });
        
        // Mostrar nombres de archivos seleccionados
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                const fileCount = this.files.length;
                const selectedFiles = document.getElementById('selectedFiles');
                
                if (selectedFiles) {
                    if (fileCount > 0) {
                        selectedFiles.textContent = fileCount === 1 
                            ? `1 archivo seleccionado: ${this.files[0].name}`
                            : `${fileCount} archivos seleccionados`;
                    } else {
                        selectedFiles.textContent = 'No hay archivos seleccionados';
                    }
                }
            });
        }
    }
});
