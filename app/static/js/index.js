
document.addEventListener("DOMContentLoaded", () => {
    const service = document.getElementById("service");
    const htmlContainer = document.getElementById("html_upload_container"); 
    const qpvGroupContainer = document.getElementById("qpvblock_upload_container")
    const inputData = document.getElementById("input_data");
    const inputLabel = document.querySelector("label[for='input_data']");
    const htmlFile = document.getElementById("html_file");
    const htmlContent = document.getElementById("html_content");
    const overlay = document.getElementById("loading-overlay");
    const Labelhtmlfile = document.querySelector("label[for='html_file']");
    const htmlContentContainer = document.getElementById("html_content_container");
    const btn = document.getElementById("submitBtn");
    const form = document.querySelector("form"); 

    // 🔁 Fonction pour adapter les champs selon le service choisi
    function toggleHtmlInput() {
        const selectedService = service.value;
        const customizeContainer = document.getElementById("customize_container");

        // Par défaut, cacher tous les blocs
        htmlContainer.style.display = "none";
        inputData.style.display = "none";
        inputLabel.style.display = "none";
        customizeContainer.style.display = "none";

        // Désactiver tous les "required" par défaut
        inputData.removeAttribute("required");
        document.getElementById("custom_file").removeAttribute("required");
        document.getElementById("new_word").removeAttribute("required");

        if (selectedService === "pdf_from_html") {
            htmlContainer.style.display = "block";
            htmlContentContainer.style.display="block";
            inputData.style.display = "none";
            inputLabel.style.display = "none";
            inputData.removeAttribute("required");
            
        } else if (selectedService === "customize_folder") {
            customizeContainer.style.display = "block";
            document.getElementById("custom_file").setAttribute("required", "true");
            document.getElementById("new_word").setAttribute("required", "true");
        }
        else if (selectedService === "check_groupeqpv") {
            htmlContainer.style.display = "block";  // <--- manquant ! 
            htmlContentContainer.style.display = "None";
            document.getElementById("html_file").setAttribute("required", "true");
        }
        else {
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
            case "check_groupeqpv":
                Labelhtmlfile.innerText = "Sélectionner un fichier (.csv, .xlsx)";
                break;
            case "pdf_from_html":
                Labelhtmlfile.innerText = "Sélectionner un fichier (.html)";
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

        });
    }
});

