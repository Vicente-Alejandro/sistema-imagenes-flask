/**
 * Funciones específicas para la galería de imágenes
 */

// Variables globales para el modal/lightbox
let currentImageIndex = 0;
let galleryImages = [];

/**
 * Abre el modal con la imagen seleccionada
 * @param {string} imageSrc - Ruta de la imagen
 * @param {string} caption - Descripción/título de la imagen
 */
function openImageModal(imageSrc, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    
    // Mostrar el modal
    modal.style.display = 'block';
    
    // Establecer imagen y texto
    modalImg.src = imageSrc;
    modalCaption.textContent = caption;
    
    // Recopilar todas las imágenes para navegación
    galleryImages = Array.from(document.querySelectorAll('.thumbnail'));
    
    // Encontrar el índice de la imagen actual
    const thumbnails = document.querySelectorAll('.thumbnail');
    for (let i = 0; i < thumbnails.length; i++) {
        const imgSrc = thumbnails[i].getAttribute('data-src');
        if (imgSrc === imageSrc) {
            currentImageIndex = i;
            break;
        }
    }
    
    // Mostrar/ocultar botones de navegación según sea necesario
    updateNavigationButtons();
}

/**
 * Actualiza la visibilidad de los botones de navegación
 */
function updateNavigationButtons() {
    const prevButton = document.getElementById('prevImage');
    const nextButton = document.getElementById('nextImage');
    
    // Ocultar botón 'Anterior' si estamos en la primera imagen
    prevButton.style.visibility = currentImageIndex > 0 ? 'visible' : 'hidden';
    
    // Ocultar botón 'Siguiente' si estamos en la última imagen
    nextButton.style.visibility = currentImageIndex < galleryImages.length - 1 ? 'visible' : 'hidden';
}

/**
 * Navega a la imagen anterior
 */
function showPreviousImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        const prevImage = galleryImages[currentImageIndex];
        const imageSrc = prevImage.getAttribute('data-src');
        const caption = prevImage.getAttribute('alt');
        
        document.getElementById('modalImage').src = imageSrc;
        document.getElementById('modalCaption').textContent = caption;
        
        updateNavigationButtons();
    }
}

/**
 * Navega a la imagen siguiente
 */
function showNextImage() {
    if (currentImageIndex < galleryImages.length - 1) {
        currentImageIndex++;
        const nextImage = galleryImages[currentImageIndex];
        const imageSrc = nextImage.getAttribute('data-src');
        const caption = nextImage.getAttribute('alt');
        
        document.getElementById('modalImage').src = imageSrc;
        document.getElementById('modalCaption').textContent = caption;
        
        updateNavigationButtons();
    }
}

/**
 * Cierra el modal de imagen
 */
function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// Manejo del formulario de subida
/**
 * Inicializa el lazy loading de imágenes usando Intersection Observer
 */
function initLazyLoading() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    // Si el navegador soporta IntersectionObserver
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    
                    // Crear una imagen oculta para precargar
                    const preloadImage = new Image();
                    preloadImage.src = src;
                    preloadImage.onload = function() {
                        // Una vez que la imagen se ha cargado, actualizar la imagen visible
                        img.src = src;
                        img.classList.add('loaded');
                        
                        // Ocultar el spinner
                        const spinner = img.parentNode.querySelector('.loading-spinner');
                        if (spinner) {
                            spinner.style.display = 'none';
                        }
                    };
                    
                    // Ya no necesitamos observar esta imagen
                    imageObserver.unobserve(img);
                }
            });
        }, {
            // Opciones del observador
            rootMargin: '50px 0px',  // Empieza a cargar cuando está a 50px de entrar en pantalla
            threshold: 0.01          // Trigger cuando al menos 1% de la imagen es visible
        });
        
        // Observar todas las imágenes con clase 'lazy'
        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    } else {
        // Fallback para navegadores que no soportan IntersectionObserver
        lazyImages.forEach(function(img) {
            img.src = img.dataset.src;
            img.classList.add('loaded');
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar lazy loading
    initLazyLoading();
    
    // Configurar eventos para el modal de imágenes
    const modal = document.getElementById('imageModal');
    const closeBtn = document.querySelector('.close-modal');
    const prevBtn = document.getElementById('prevImage');
    const nextBtn = document.getElementById('nextImage');
    
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
    
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const files = document.getElementById('fileInput').files;
            
            if (files.length === 0) {
                showNotification('Por favor selecciona al menos una imagen', 'error');
                return;
            }
            
            for (let file of files) {
                formData.append('files', file);
            }
            
            // Mostrar estado de carga
            const uploadBtn = document.querySelector('.upload-btn');
            const originalText = uploadBtn.textContent;
            uploadBtn.textContent = 'Subiendo...';
            uploadBtn.disabled = true;
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showNotification(result.message, 'success');
                    // Agregar nuevas imágenes a la galería
                    addNewImages(result.files);
                    // Limpiar formulario
                    document.getElementById('fileInput').value = '';
                } else {
                    showNotification(result.message, 'error');
                }
            } catch (error) {
                showNotification('Error al subir las imágenes', 'error');
                console.error('Error:', error);
            } finally {
                uploadBtn.textContent = originalText;
                uploadBtn.disabled = false;
            }
        });
    }
});

// Función para agregar nuevas imágenes a la galería
function addNewImages(filenames) {
    const gallery = document.getElementById('gallery');
    const noImages = document.getElementById('noImages');
    
    // Ocultar mensaje de "no hay imágenes"
    if (noImages) {
        noImages.style.display = 'none';
    }
    
    // Crear galería si no existe
    if (!gallery) {
        const newGallery = document.createElement('div');
        newGallery.className = 'gallery';
        newGallery.id = 'gallery';
        document.querySelector('main').appendChild(newGallery);
    }
    
    filenames.forEach(filename => {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.setAttribute('data-filename', filename);
        imageItem.innerHTML = `
            <div class="thumbnail-container">
                <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D'http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg' viewBox%3D'0 0 200 200'%2F%3E" 
                     data-src="/uploads/${filename}" 
                     alt="${filename}" 
                     class="thumbnail lazy" 
                     onclick="openImageModal('/uploads/${filename}', '${filename}')">
                <div class="loading-spinner"></div>
            </div>
            <div class="image-name">${filename}</div>
            <div class="actions">
                <button onclick="openImageModal('/uploads/${filename}', '${filename}')" class="view-btn">Ver</button>
                <button onclick="deleteImage('${filename}')" class="delete-btn">Eliminar</button>
            </div>
        `;
        
        // Insertar al principio (más recientes primero)
        const currentGallery = document.getElementById('gallery');
        currentGallery.insertBefore(imageItem, currentGallery.firstChild);
        
        // Inicializar lazy loading para las nuevas imágenes
        const newLazyImages = imageItem.querySelectorAll('img.lazy');
        if ('IntersectionObserver' in window && newLazyImages.length > 0) {
            const imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.dataset.src;
                        
                        // Crear una imagen oculta para precargar
                        const preloadImage = new Image();
                        preloadImage.src = src;
                        preloadImage.onload = function() {
                            img.src = src;
                            img.classList.add('loaded');
                            
                            // Ocultar el spinner
                            const spinner = img.parentNode.querySelector('.loading-spinner');
                            if (spinner) {
                                spinner.style.display = 'none';
                            }
                        };
                        
                        imageObserver.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });
            
            newLazyImages.forEach(function(img) {
                imageObserver.observe(img);
            });
        } else if (newLazyImages.length > 0) {
            newLazyImages.forEach(function(img) {
                img.src = img.dataset.src;
                img.classList.add('loaded');
            });
        }
    });
    
    updateImageCount();
}

// Función para eliminar imágenes
async function deleteImage(filename) {
    try {
        const response = await fetch(`/delete/${filename}`);
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            // Remover del DOM
            const imageItem = document.querySelector(`[data-filename="${filename}"]`);
            if (imageItem) {
                imageItem.remove();
            }
            updateImageCount();
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error al eliminar la imagen', 'error');
        console.error('Error:', error);
    }
}

// Función para actualizar el contador de imágenes
function updateImageCount() {
    const gallery = document.getElementById('gallery');
    const imageStats = document.getElementById('imageStats');
    const noImages = document.getElementById('noImages');
    
    if (gallery) {
        const count = gallery.children.length;
        
        if (count === 0) {
            if (gallery.parentNode) {
                gallery.parentNode.removeChild(gallery);
            }
            if (imageStats && imageStats.parentNode) {
                imageStats.parentNode.removeChild(imageStats);
            }
            if (noImages) {
                noImages.style.display = 'block';
            } else {
                const newNoImages = document.createElement('div');
                newNoImages.className = 'no-images';
                newNoImages.id = 'noImages';
                newNoImages.textContent = 'No hay imágenes subidas. ¡Sube la primera!';
                document.querySelector('main').appendChild(newNoImages);
            }
        } else {
            if (imageStats) {
                imageStats.textContent = `Total de imágenes: ${count}`;
            } else {
                const newStats = document.createElement('div');
                newStats.className = 'stats';
                newStats.id = 'imageStats';
                newStats.textContent = `Total de imágenes: ${count}`;
                gallery.parentNode.insertBefore(newStats, gallery);
            }
        }
    }
}
