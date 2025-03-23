function toggleHtmlInput() {
    const service = document.getElementById("service").value;
    const htmlContainer = document.getElementById("html_upload_container");
    const inputData = document.getElementById("input_data");
    const inputLabel = document.querySelector("label[for='input_data']");

    if (service === "pdf_from_html") {
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
    switch (service) {
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

document.addEventListener("DOMContentLoaded", () => {
    const htmlFile = document.getElementById("html_file");
    const htmlContent = document.getElementById("html_content");

    htmlFile.addEventListener("change", () => {
        htmlContent.disabled = htmlFile.files.length > 0;
    });

    htmlContent.addEventListener("input", () => {
        htmlFile.disabled = htmlContent.value.trim() !== "";
    });

    // ✅ Initialiser l'état selon la sélection
    toggleHtmlInput();

    // ✅ Masquer l'overlay s'il était affiché
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.style.display = "none";

    // ✅ Réactiver le bouton submit
    const btn = document.getElementById("submitBtn");
    if (btn) {
        btn.disabled = false;
        btn.innerText = "Envoyer";
    }
});

// ✅ Spinner on form submit
document.querySelector("form").addEventListener("submit", function () {
    document.getElementById("loading-overlay").style.display = "flex";
    const btn = document.getElementById("submitBtn");
    btn.disabled = true;
    btn.innerText = "Traitement...";
});
