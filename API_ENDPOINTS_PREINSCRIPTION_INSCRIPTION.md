# API Endpoints - Préinscription et Inscription

## Nouveaux Endpoints API

### 1. Préinscription via API

**Endpoint:** `POST /api-mca/v1/preinscription/api/{programme_id}`

**Description:** Crée une préinscription directement via JSON sans passer par le formulaire HTML.

**URL:** `https://votre-domaine.com/api-mca/v1/preinscription/api/{programme_id}`

**Headers requis:**
```
Content-Type: application/json
```

**Body JSON:**
```json
{
  "programme_id": 1,
  "event_id": null,
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "telephone": "+33612345678",
  "date_naissance": "1990-01-15",
  "adresse": "123 Rue de la Paix",
  "code_postal": "75001",
  "ville": "Paris",
  "situation_professionnelle": "demandeur_emploi",
  "niveau_etude": "bac_plus_2",
  "projet_entrepreneurial": "Création d'une application mobile",
  "rgpd_consent": true,
  "source": "api_externe"
}
```

**Réponse de succès (200):**
```json
{
  "status": "success",
  "message": "Préinscription créée avec succès",
  "data": {
    "id": 123,
    "programme_id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "date_soumission": "2024-01-15"
  }
}
```

**Réponse d'erreur (422):**
```json
{
  "status": "error",
  "message": "Erreur de validation des données",
  "errors": [
    {
      "loc": ["email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 2. Inscription via API

**Endpoint:** `POST /api-mca/v1/inscription/api/{programme_id}`

**Description:** Crée une inscription directement via JSON sans passer par le formulaire HTML.

**URL:** `https://votre-domaine.com/api-mca/v1/inscription/api/{programme_id}`

**Headers requis:**
```
Content-Type: application/json
```

**Body JSON:**
```json
{
  "programme_id": 1,
  "event_id": null,
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "telephone": "+33612345678",
  "date_naissance": "1990-01-15",
  "adresse": "123 Rue de la Paix",
  "code_postal": "75001",
  "ville": "Paris",
  "situation_professionnelle": "demandeur_emploi",
  "niveau_etude": "bac_plus_2",
  "projet_entrepreneurial": "Création d'une application mobile",
  "rgpd_consent": true,
  "rgpd_consent_date": "2024-01-15",
  "source": "api_externe"
}
```

**Réponse de succès (200):**
```json
{
  "status": "success",
  "message": "Inscription créée avec succès",
  "data": {
    "id": 456,
    "programme_id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "date_inscription": "2024-01-15"
  }
}
```

## Explication du champ `event_id`

Le champ `event_id` est **optionnel** et permet de distinguer entre :

### Préinscription/Inscription générale au programme
```json
{
  "programme_id": 1,
  "event_id": null,  // Pas d'événement spécifique
  "nom": "Dupont",
  "prenom": "Jean"
}
```

### Préinscription/Inscription à un événement spécifique
```json
{
  "programme_id": 1,
  "event_id": 5,     // Session du 15 janvier 2024
  "nom": "Martin",
  "prenom": "Sophie"
}
```

**Valeurs acceptées pour `event_id` :**
- `null` : Préinscription/Inscription générale au programme
- `1, 2, 3...` : Préinscription/Inscription à un événement spécifique
- `0` : **Non autorisé** (doit être un entier positif)

## Valeurs possibles pour les champs enum

### SituationProfessionnelle
- `"demandeur_emploi"`
- `"salarie"`
- `"independant"`
- `"etudiant"`
- `"autre"`

### NiveauEtude
- `"sans_diplome"`
- `"cap_bep"`
- `"bac"`
- `"bac_plus_2"`
- `"bac_plus_3"`
- `"bac_plus_4"`
- `"bac_plus_5"`
- `"superieur"`

## Exemples d'utilisation

### Avec curl

**Préinscription:**
```bash
curl -X POST "https://votre-domaine.com/api-mca/v1/preinscription/api/1" \
  -H "Content-Type: application/json" \
  -d '{
    "programme_id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "telephone": "+33612345678",
    "date_naissance": "1990-01-15",
    "adresse": "123 Rue de la Paix",
    "code_postal": "75001",
    "ville": "Paris",
    "situation_professionnelle": "demandeur_emploi",
    "niveau_etude": "bac_plus_2",
    "rgpd_consent": true
  }'
```

**Inscription:**
```bash
curl -X POST "https://votre-domaine.com/api-mca/v1/inscription/api/1" \
  -H "Content-Type: application/json" \
  -d '{
    "programme_id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "telephone": "+33612345678",
    "date_naissance": "1990-01-15",
    "adresse": "123 Rue de la Paix",
    "code_postal": "75001",
    "ville": "Paris",
    "situation_professionnelle": "demandeur_emploi",
    "niveau_etude": "bac_plus_2",
    "rgpd_consent": true
  }'
```

### Avec JavaScript/Fetch

```javascript
// Préinscription
const preinscriptionData = {
  programme_id: 1,
  nom: "Dupont",
  prenom: "Jean",
  email: "jean.dupont@example.com",
  telephone: "+33612345678",
  date_naissance: "1990-01-15",
  adresse: "123 Rue de la Paix",
  code_postal: "75001",
  ville: "Paris",
  situation_professionnelle: "demandeur_emploi",
  niveau_etude: "bac_plus_2",
  rgpd_consent: true
};

fetch('https://votre-domaine.com/api-mca/v1/preinscription/api/1', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(preinscriptionData)
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## Codes d'erreur

- **400 Bad Request:** Données manquantes ou invalides
- **422 Unprocessable Entity:** Erreur de validation des données
- **500 Internal Server Error:** Erreur serveur

## Notes importantes

1. **RGPD:** Le champ `rgpd_consent` doit toujours être `true`
2. **Âge minimum:** La personne doit être majeure (18 ans minimum)
3. **Téléphone:** Format français requis (+33612345678 ou 0612345678)
4. **Code postal:** 5 chiffres requis
5. **Email:** Format email valide requis
6. **Programme ID:** Doit correspondre à l'ID dans l'URL
7. **Event ID:** Optionnel, peut être `null` ou un entier positif 