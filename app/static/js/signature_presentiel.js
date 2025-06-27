/**
 * Signature Presentiel.js - Gestion sécurisée de la signature présentielle
 * Compatible avec Content Security Policy (CSP)
 */

document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('signaturePad');
    const container = document.getElementById('signatureContainer');
    const clearBtn = document.getElementById('clearBtn');
    const saveBtn = document.getElementById('saveBtn');
    
    // Configuration du canvas
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let selectedParticipant = null;
    
    // Fonction pour obtenir les coordonnées relatives au canvas
    function getCoordinates(e) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    // Démarrer le dessin
    function startDrawing(e) {
        isDrawing = true;
        container.classList.add('active');
        
        const coords = getCoordinates(e);
        lastX = coords.x;
        lastY = coords.y;
        
        // Dessiner un point initial
        ctx.beginPath();
        ctx.arc(lastX, lastY, 1, 0, 2 * Math.PI);
        ctx.fill();
    }
    
    // Dessiner
    function draw(e) {
        if (!isDrawing) return;
        
        const coords = getCoordinates(e);
        
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
        
        lastX = coords.x;
        lastY = coords.y;
    }
    
    // Arrêter le dessin
    function stopDrawing() {
        if (!isDrawing) return;
        isDrawing = false;
        container.classList.remove('active');
        
        // Vérifier si le canvas contient une signature
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const hasSignature = imageData.data.some(channel => channel !== 0);
        
        if (hasSignature) {
            container.classList.add('has-signature');
            saveBtn.disabled = false;
        }
    }
    
    // Événements de souris
    canvas.addEventListener('mousedown', function(e) {
        e.preventDefault();
        startDrawing(e);
    });
    
    canvas.addEventListener('mousemove', function(e) {
        e.preventDefault();
        draw(e);
    });
    
    canvas.addEventListener('mouseup', function(e) {
        e.preventDefault();
        stopDrawing();
    });
    
    canvas.addEventListener('mouseout', function(e) {
        e.preventDefault();
        stopDrawing();
    });
    
    // Événements tactiles
    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        startDrawing(mouseEvent);
    });
    
    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        draw(mouseEvent);
    });
    
    canvas.addEventListener('touchend', function(e) {
        e.preventDefault();
        stopDrawing();
    });
    
    // Gestionnaire de sélection des participants
    const participantItems = document.querySelectorAll('.participant-item');
    participantItems.forEach(item => {
        item.addEventListener('click', async function() {
            // Ne rien faire si le participant a déjà signé
            if (this.classList.contains('signed')) {
                return;
            }

            // Mettre à jour la sélection visuelle
            document.querySelectorAll('.participant-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');

            // Mettre à jour les informations du participant sélectionné
            selectedParticipant = {
                id: this.dataset.participantId,
                nom: this.dataset.participantNom,
                prenom: this.dataset.participantPrenom,
                email: this.dataset.participantEmail,
                emargement_id: this.dataset.emargementId,
                statut: this.dataset.statut
            };

            // Vérifier si l'émargement a déjà une signature
            if (selectedParticipant.statut !== 'non_signé') {
                saveBtn.disabled = true;
                document.getElementById('errorMessage').textContent = 'Une signature existe déjà pour ce participant.';
                document.getElementById('signatureError').style.display = 'block';
                return;
            }

            // Afficher les informations du participant
            const participantInfo = `${selectedParticipant.nom} ${selectedParticipant.prenom} (${selectedParticipant.email})`;
            document.getElementById('selectedParticipantInfo').textContent = participantInfo;
            document.getElementById('selectedParticipantInfo').classList.remove('text-muted');
            
            // Réinitialiser la signature
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            container.classList.remove('has-signature');
            saveBtn.disabled = true;
            document.getElementById('signatureSuccess').style.display = 'none';
            document.getElementById('signatureError').style.display = 'none';
        });
    });

    // Gestionnaire pour le bouton d'effacement
    clearBtn.addEventListener('click', function() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        container.classList.remove('has-signature');
        saveBtn.disabled = true;
    });

    // Gestionnaire pour le bouton de sauvegarde
    saveBtn.addEventListener('click', async function() {
        console.log('🔄 Début de la sauvegarde de la signature...');
        
        // Cacher les messages précédents
        document.getElementById('signatureSuccess').style.display = 'none';
        document.getElementById('signatureError').style.display = 'none';

        if (!selectedParticipant) {
            document.getElementById('errorMessage').textContent = 'Veuillez sélectionner un participant.';
            document.getElementById('signatureError').style.display = 'block';
            return;
        }

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const hasSignature = imageData.data.some(channel => channel !== 0);
        
        if (!hasSignature) {
            document.getElementById('errorMessage').textContent = 'Veuillez signer avant d\'enregistrer.';
            document.getElementById('signatureError').style.display = 'block';
            return;
        }

        // Désactiver le bouton pendant l'envoi
        saveBtn.disabled = true;
        const originalButtonText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enregistrement...';

        try {
            const signatureData = canvas.toDataURL('image/png');
            console.log('📝 Signature convertie en base64');
            
            const url = `/api-mca/v1/emargement/save/${selectedParticipant.emargement_id}/signature`;
            console.log('URL:', url);
            
            const requestBody = {
                signature_image: signatureData,
                ip_address: null,     // Sera rempli par le serveur
                user_agent: null      // Sera rempli par le serveur
            };
            console.log('📦 Corps de la requête:', { ...requestBody, signature_image: '...' });
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            console.log('📥 Réponse reçue:', response.status, response.statusText);

            let responseData;
            try {
                responseData = await response.json();
                console.log('📦 Données de réponse:', responseData);
            } catch (e) {
                console.error('❌ Erreur parsing JSON:', e);
                throw new Error('Erreur de communication avec le serveur');
            }

            if (!response.ok) {
                let errorMessage = 'Erreur lors de l\'enregistrement de la signature';
                if (responseData) {
                    if (typeof responseData === 'object') {
                        if (responseData.detail) {
                            errorMessage = responseData.detail;
                        } else if (responseData.error) {
                            errorMessage = responseData.error;
                        } else if (responseData.message) {
                            errorMessage = responseData.message;
                        } else {
                            errorMessage = JSON.stringify(responseData);
                        }
                    } else {
                        errorMessage = String(responseData);
                    }
                }
                console.error('❌ Erreur serveur:', errorMessage);
                throw new Error(errorMessage);
            }

            console.log('✅ Sauvegarde réussie:', responseData);

            // Mettre à jour l'interface
            const participantItem = document.querySelector('.participant-item.selected');
            if (participantItem) {
                participantItem.classList.add('signed', 'disabled');
                participantItem.classList.remove('selected');
                
                // Mettre à jour l'emoji et le statut
                const emojiSpan = participantItem.querySelector('.status-emoji');
                const statusBadge = participantItem.querySelector('.status-badge');
                
                emojiSpan.textContent = '⏳';  // Sablier pour en attente de validation
                statusBadge.className = 'badge status-badge en_attente';
                statusBadge.textContent = 'En attente de validation';
                
                // Ajouter la date de signature
                const now = new Date();
                const dateStr = now.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                participantItem.innerHTML += `<small class="text-muted">${dateStr}</small>`;
            }

            // Réinitialiser
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            container.classList.remove('has-signature');
            document.getElementById('signatureSuccess').style.display = 'block';
            selectedParticipant = null;

            // Rafraîchir la page après 2 secondes
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } catch (error) {
            console.error('❌ Erreur:', error);
            document.getElementById('errorMessage').textContent = error.message || 'Une erreur est survenue';
            document.getElementById('signatureError').style.display = 'block';
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalButtonText;
        }
    });

    // Redimensionnement
    window.addEventListener('resize', function() {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.putImageData(imageData, 0, 0);
    });
}); 