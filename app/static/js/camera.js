/**
 * Camera.js - Gestion sécurisée de la caméra
 * Compatible avec Content Security Policy (CSP)
 */

// Récupération des variables depuis les attributs data-* (CSP compliant)
function getConfigData() {
    const cardElement = document.querySelector('.card[data-mca-website-url]');
    if (cardElement) {
        return {
            MCA_WEBSITE_URL: cardElement.getAttribute('data-mca-website-url') || '',
            EMARGEMENT_ID: cardElement.getAttribute('data-emargement-id') || '',
            TOKEN: cardElement.getAttribute('data-token') || ''
        };
    }
    return {
        MCA_WEBSITE_URL: '',
        EMARGEMENT_ID: '',
        TOKEN: ''
    };
}

class CameraManager {
    constructor() {
        this.video = null;
        this.photoCanvas = null;
        this.photoPreview = null;
        this.startCameraBtn = null;
        this.takePhotoBtn = null;
        this.retakePhotoBtn = null;
        this.photoSection = null;
        this.signatureSection = null;
        this.stream = null;
        this.photoData = null;
        
        this.init();
    }

    init() {
        // Initialisation des éléments DOM
        this.video = document.getElementById('video');
        this.photoCanvas = document.getElementById('photoCanvas');
        this.photoPreview = document.getElementById('photoPreview');
        this.startCameraBtn = document.getElementById('startCameraBtn');
        this.takePhotoBtn = document.getElementById('takePhotoBtn');
        this.retakePhotoBtn = document.getElementById('retakePhotoBtn');
        this.photoSection = document.getElementById('photoSection');
        this.signatureSection = document.getElementById('signatureSection');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.startCameraBtn) {
            this.startCameraBtn.addEventListener('click', this.startCamera.bind(this));
        }
        
        if (this.takePhotoBtn) {
            this.takePhotoBtn.addEventListener('click', this.takePhoto.bind(this));
        }
        
        if (this.retakePhotoBtn) {
            this.retakePhotoBtn.addEventListener('click', this.retakePhoto.bind(this));
        }
    }

    async startCamera() {
        try {
            // Configuration vidéo optimisée pour Firefox
            const videoConstraints = {
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            };
            
            // Ajouter des contraintes spécifiques pour Firefox
            if (navigator.userAgent.includes('Firefox')) {
                videoConstraints.mozMediaSource = 'camera';
            }
            
            const mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: videoConstraints
            });
            
            this.stream = mediaStream;
            this.video.srcObject = this.stream;
            
            // Gestion spécifique pour Firefox et playsinline
            this.video.setAttribute('playsinline', 'true');
            this.video.setAttribute('webkit-playsinline', 'true');
            this.video.muted = true; // Nécessaire pour autoplay sur certains navigateurs
            
            this.video.style.display = 'block';
            this.takePhotoBtn.disabled = false;
            
            const placeholder = document.querySelector('.photo-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            // Attendre que la vidéo soit prête
            this.video.onloadedmetadata = () => {
                console.log('Vidéo prête à être utilisée');
            };
            
        } catch (err) {
            console.error('Erreur lors de l\'accès à la caméra:', err);
            this.showError('Impossible d\'accéder à la caméra. Veuillez vérifier les permissions.');
        }
    }

    takePhoto() {
        const context = this.photoCanvas.getContext('2d');
        this.photoCanvas.width = this.video.videoWidth;
        this.photoCanvas.height = this.video.videoHeight;
        context.drawImage(this.video, 0, 0, this.photoCanvas.width, this.photoCanvas.height);
        
        this.photoData = this.photoCanvas.toDataURL('image/jpeg', 0.8);
        
        this.photoPreview.src = this.photoData;
        this.photoPreview.style.display = 'block';
        this.video.style.display = 'none';
        this.photoCanvas.style.display = 'none';
        
        this.takePhotoBtn.style.display = 'none';
        this.retakePhotoBtn.style.display = 'block';
        this.startCameraBtn.disabled = true;
        
        this.updateSteps(1, 2);
        this.showSignatureSection();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        // Passer les données photo au gestionnaire de signature
        if (window.signatureManager) {
            window.signatureManager.setPhotoData(this.photoData);
        }
    }

    async retakePhoto() {
        this.photoPreview.style.display = 'none';
        this.video.style.display = 'block';
        this.takePhotoBtn.style.display = 'block';
        this.retakePhotoBtn.style.display = 'none';
        this.photoData = null;
        
        this.updateSteps(2, 1);
        this.showPhotoSection();
        
        try {
            // Configuration vidéo optimisée pour Firefox
            const videoConstraints = {
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            };
            
            // Ajouter des contraintes spécifiques pour Firefox
            if (navigator.userAgent.includes('Firefox')) {
                videoConstraints.mozMediaSource = 'camera';
            }
            
            const newStream = await navigator.mediaDevices.getUserMedia({ 
                video: videoConstraints
            });
            
            this.stream = newStream;
            this.video.srcObject = this.stream;
            
            // Gestion spécifique pour Firefox et playsinline
            this.video.setAttribute('playsinline', 'true');
            this.video.setAttribute('webkit-playsinline', 'true');
            this.video.muted = true;
            
        } catch (err) {
            console.error('Erreur lors du redémarrage de la caméra:', err);
            this.showError('Impossible de redémarrer la caméra.');
        }
    }

    updateSteps(fromStep, toStep) {
        const step1 = document.getElementById('step1');
        const step2 = document.getElementById('step2');
        
        if (fromStep === 1 && toStep === 2) {
            if (step1) {
                step1.classList.remove('active');
                step1.classList.add('completed');
            }
            if (step2) {
                step2.classList.add('active');
            }
        } else if (fromStep === 2 && toStep === 1) {
            if (step1) {
                step1.classList.add('active');
                step1.classList.remove('completed');
            }
            if (step2) {
                step2.classList.remove('active');
            }
        }
    }

    showSignatureSection() {
        if (this.photoSection) {
            this.photoSection.style.display = 'none';
        }
        if (this.signatureSection) {
            this.signatureSection.style.display = 'block';
        }
    }

    showPhotoSection() {
        if (this.photoSection) {
            this.photoSection.style.display = 'block';
        }
        if (this.signatureSection) {
            this.signatureSection.style.display = 'none';
        }
    }

    showError(message) {
        // Créer un élément d'alerte temporaire
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Supprimer l'alerte après 5 secondes
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    window.cameraManager = new CameraManager();
});

// Nettoyage lors de la fermeture de la page
window.addEventListener('beforeunload', function() {
    if (window.cameraManager) {
        window.cameraManager.stopCamera();
    }
}); 