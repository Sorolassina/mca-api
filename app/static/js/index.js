
document.addEventListener("DOMContentLoaded", () => {
    const service = document.getElementById("service");
    const htmlContainer = document.getElementById("html_upload_container");
    const inputData = document.getElementById("input_data");
    const inputLabel = document.querySelector("label[for='input_data']");
    const htmlFile = document.getElementById("html_file");
    const htmlContent = document.getElementById("html_content");
    const overlay = document.getElementById("loading-overlay");
    const btn = document.getElementById("submitBtn");
    const form = document.querySelector("form");

    // 🔁 Fonction pour adapter les champs selon le service choisi
    function toggleHtmlInput() {
        const selectedService = service.value;

        if (selectedService === "pdf_from_html") {
            htmlContainer.style.display = "block";
            inputData.style.display = "none";
            inputLabel.style.display = "none";
            inputData.removeAttribute("required");
        } else {
            htmlContainer.style.display = "none";
            inputData.style.display = "block";
            inputLabel.style.display = "block";
            inputData.setAttribute("required", "true");
        }

        // Adapter le label et le placeholder
        switch (selectedService) {
            case "company_info":
                inputLabel.innerText = "SIRET ou SIREN";
                inputData.placeholder = "Insérez votre SIRET ou SIREN ici...";
                break;
            case "check_qpv":
                inputLabel.innerText = "Adresse à vérifier";
                inputData.placeholder = "Ex : 12 rue de Paris, 75000 Paris";
                break;
            case "digiformat_data":
                inputLabel.innerText = "Mot de passe Digiformat";
                inputData.placeholder = "Insérez votre mot de passe ici...";
                break;
            default:
                inputLabel.innerText = "Données";
                inputData.placeholder = "Entrez les informations...";
        }
    }

    // Initialiser les champs à l'ouverture
    toggleHtmlInput();

    // Mettre à jour le formulaire lors du changement de service
    service.addEventListener("change", toggleHtmlInput);

    // Activer/désactiver les champs HTML selon contenu
    htmlFile.addEventListener("change", () => {
        htmlContent.disabled = htmlFile.files.length > 0;
    });

    htmlContent.addEventListener("input", () => {
        htmlFile.disabled = htmlContent.value.trim() !== "";
    });

    // Réinitialiser l'état du bouton et de l'overlay au chargement
    if (overlay) overlay.style.display = "none";
    if (btn) {
        btn.disabled = false;
        btn.innerText = "Envoyer";
    }

    // ✅ Affichage overlay + timeout lors du submit
    if (form) {
        form.addEventListener("submit", () => {
            if (overlay) overlay.style.display = "flex";
            if (btn) {
                btn.disabled = true;
                btn.innerText = "Traitement en cours...";
            }

            // ⏱️ Timeout automatique de 30s
            setTimeout(() => {
                if (overlay && overlay.style.display === "flex") {
                    overlay.style.display = "none";
                    if (btn) {
                        btn.disabled = false;
                        btn.innerText = "Temps dépassé. Réessayez.";
                    }
                    alert("⏱️ Le traitement a pris trop de temps. Veuillez réessayer.");
                }
            }, 60000); // 30 000 ms = 30 secondes
        });
    }
});

