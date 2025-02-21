import smtplib
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.model_user import User
from app.schemas.schema_user import UserInDB
from app.database import get_db
from email.mime.multipart import MIMEMultipart
from app.security.tokens import *
from app.security.password import *
from fastapi import Depends, APIRouter
from sqlalchemy import select
from fastapi.security import OAuth2PasswordBearer
from app.config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD  # Assurez-vous d'avoir ces variables configurées

router = APIRouter()
# ✅ Définition du schéma OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api-mca/v1/token")

# ✅ Fonction pour envoyer un e-mail de bienvenue avec le token et l'URL de connexion
# ✅ URLs de Swagger et Redoc (Ajuste avec ton domaine après déploiement)
SWAGGER_URL = "http://127.0.0.1:8000/docs"
REDOC_URL = "http://127.0.0.1:8000/redoc"

async def send_welcome_email(email: str, username: str, token: str):
    """
    Envoie un e-mail de bienvenue à l'utilisateur avec son token et les liens de documentation.
    """
    subject = "Bienvenue sur MonAPI - Votre accès est prêt !"
    body = f"""
    Bonjour {username},<br><br>

    🎉 Félicitations ! Votre compte a été créé avec succès.<br>
    Voici votre token d'accès sécurisé : <b>{token}</b><br><br>

    📌 Accédez à la documentation API ici :<br>
    - <a href="{SWAGGER_URL}">Swagger UI</a> (Interface interactive)<br>
    - <a href="{REDOC_URL}">ReDoc</a> (Documentation détaillée)<br><br>

    🔒 Gardez votre token sécurisé et ne le partagez pas.<br>
    Bonne utilisation de notre API ! 🚀<br><br>

    Cordialement,<br>
    <b>L'équipe de MonAPI</b>
    """

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, email, msg.as_string())
        server.quit()
        print(f"✅ E-mail de bienvenue envoyé à {email}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'e-mail : {e}")


# ✅ Mise à jour de la fonction d'inscription
@router.post("/register", response_model=dict)
async def login_or_register(form_data: UserInDB, db: AsyncSession = Depends(get_db)):
    """
    - Inscrit un nouvel utilisateur s'il n'existe pas.
    - Vérifie la validité du token si l'utilisateur existe.
    - Envoie un e-mail de bienvenue avec le token et l'URL de Swagger.
    """

    # ✅ Vérifier si l'utilisateur existe déjà
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        token = create_access_token({"sub": user.username})
        return {"message": "Utilisateur déjà existant, connexion réussie", "token": token}

    # ✅ Créer un nouvel utilisateur
    new_user = User(
        username=form_data.username,
        email=form_data.email,
        hashed_password=hash_password(form_data.password),
        is_active=True,
        is_superuser=False
    )

    # ✅ Générer un token pour le nouvel utilisateur
    new_token = create_access_token({"sub": new_user.username})
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # ✅ Envoi de l'email avec le token et l'URL de Swagger
    await send_welcome_email(new_user.email, new_user.username, new_token)

    return {"message": "Utilisateur créé avec succès", "token": new_token}
