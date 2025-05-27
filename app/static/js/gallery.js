/**
 * Funciones específicas para la galería de imágenes
 */

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
                     onclick="window.open('/uploads/${filename}', '_blank')">
                <div class="loading-spinner"></div>
            </div>
            <div class="image-name">${filename}</div>
            <div class="actions">
                <a href="/uploads/${filename}" target="_blank" class="view-btn">Ver</a>
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
