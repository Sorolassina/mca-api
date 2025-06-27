/**
 * Signature.js - Gestion sécurisée de la signature électronique
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

class SignatureManager {
    constructor() {
        this.isDrawing = false;
        this.lastX = 0;
        this.lastY = 0;
        this.ctx = null;
        this.canvas = null;
        this.container = null;
        this.saveBtn = null;
        this.clearBtn = null;
        this.photoData = null;
        
        this.init();
    }

    init() {
        // Initialisation des éléments DOM
        this.canvas = document.getElementById('signatureCanvas');
        this.container = document.getElementById('signatureContainer');
        this.saveBtn = document.getElementById('saveBtn');
        this.clearBtn = document.getElementById('clearBtn');
        
        if (this.canvas) {
            this.ctx = this.initCanvas();
            this.setupEventListeners();
        }
    }

    initCanvas() {
        const ctx = this.canvas.getContext('2d');
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
        
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        return ctx;
    }

    setupEventListeners() {
        // Événements de souris
        this.canvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.canvas.addEventListener('mousemove', this.draw.bind(this));
        this.canvas.addEventListener('mouseup', this.stopDrawing.bind(this));
        this.canvas.addEventListener('mouseout', this.stopDrawing.bind(this));
        
        // Événements tactiles
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Boutons
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', this.clearSignature.bind(this));
        }
        
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', this.saveSignature.bind(this));
        }
        
        // Bouton "Réessayer"
        const retryBtn = document.getElementById('retryBtn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                window.location.reload();
            });
        }
        
        // Redimensionnement
        window.addEventListener('resize', this.handleResize.bind(this));
    }

    getCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    startDrawing(e) {
        e.preventDefault();
        this.isDrawing = true;
        this.container.classList.add('active');
        
        const coords = this.getCoordinates(e);
        this.lastX = coords.x;
        this.lastY = coords.y;
        
        // Dessiner un point initial
        this.ctx.beginPath();
        this.ctx.arc(this.lastX, this.lastY, 1, 0, 2 * Math.PI);
        this.ctx.fill();
    }

    draw(e) {
        if (!this.isDrawing) return;
        
        const coords = this.getCoordinates(e);
        
        this.ctx.beginPath();
        this.ctx.moveTo(this.lastX, this.lastY);
        this.ctx.lineTo(coords.x, coords.y);
        this.ctx.stroke();
        
        this.lastX = coords.x;
        this.lastY = coords.y;
    }

    stopDrawing() {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        this.container.classList.remove('active');
        
        // Vérifier que le canvas a des dimensions valides
        if (this.canvas.width === 0 || this.canvas.height === 0) {
            this.ctx = this.initCanvas();
        }
        
        try {
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            const hasSignature = imageData.data.some(channel => channel !== 0);
            
            if (hasSignature) {
                this.container.classList.add('has-signature');
                if (this.saveBtn) {
                    this.saveBtn.disabled = false;
                }
            }
        } catch (error) {
            console.error('Erreur lors de la vérification de la signature:', error);
        }
    }

    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.startDrawing(mouseEvent);
    }

    handleTouchMove(e) {
        if (this.isDrawing) {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            this.draw(mouseEvent);
        }
    }

    handleTouchEnd(e) {
        e.preventDefault();
        this.stopDrawing();
    }

    clearSignature() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.container.classList.remove('has-signature');
        if (this.saveBtn) {
            this.saveBtn.disabled = true;
        }
    }

    async saveSignature() {
        if (!this.photoData) {
            this.showError('Veuillez d\'abord prendre votre photo.');
            return;
        }

        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const hasSignature = imageData.data.some(channel => channel !== 0);
        
        if (!hasSignature) {
            this.showError('Veuillez signer avant d\'enregistrer.');
            return;
        }

        const signatureData = this.canvas.toDataURL('image/png');
        
        if (this.saveBtn) {
            this.saveBtn.disabled = true;
            this.saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enregistrement...';
        }
        
        try {
            const url = window.location.origin + '/api-mca/v1/emargement/save/' + this.getEmargementId() + '/signature';
            
            const requestBody = {
                signature_image: signatureData,
                photo_profil: this.photoData,
                token: this.getToken(),
                ip_address: null,
                user_agent: null
            };
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showSuccess();
                this.redirectAfterSuccess();
            } else {
                let errorMessage;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || 'Erreur lors de l\'enregistrement de la signature';
                } catch (e) {
                    errorMessage = 'Erreur lors de l\'enregistrement de la signature';
                }
                throw new Error(errorMessage);
            }
        } catch (error) {
            this.showError(error.message);
            if (this.saveBtn) {
                this.saveBtn.disabled = false;
                this.saveBtn.innerHTML = '<i class="fas fa-check"></i> Valider la signature';
            }
        }
    }

    handleResize() {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.putImageData(imageData, 0, 0);
    }

    getEmargementId() {
        const config = getConfigData();
        return config.EMARGEMENT_ID;
    }

    getToken() {
        const config = getConfigData();
        return config.TOKEN;
    }

    showError(message) {
        const errorElement = document.getElementById('errorMessage');
        const errorContainer = document.getElementById('signatureError');
        
        if (errorElement) {
            errorElement.textContent = message;
        }
        if (errorContainer) {
            errorContainer.style.display = 'block';
        }
    }

    showSuccess() {
        const step2 = document.getElementById('step2');
        const step3 = document.getElementById('step3');
        const signatureSection = document.getElementById('signatureSection');
        const signatureSuccess = document.getElementById('signatureSuccess');
        
        if (step2) {
            step2.classList.remove('active');
            step2.classList.add('completed');
        }
        if (step3) {
            step3.classList.add('active');
        }
        if (signatureSection) {
            signatureSection.style.display = 'none';
        }
        if (signatureSuccess) {
            signatureSuccess.style.display = 'block';
        }
    }

    redirectAfterSuccess() {
        // Redirection après 3 secondes
        setTimeout(() => {
            window.location.href = this.getRedirectUrl();
        }, 3000);
    }

    getRedirectUrl() {
        const config = getConfigData();
        return config.MCA_WEBSITE_URL || '/';
    }

    setPhotoData(photoData) {
        this.photoData = photoData;
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    window.signatureManager = new SignatureManager();
}); 