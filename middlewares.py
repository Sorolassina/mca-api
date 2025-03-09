import logging
import traceback
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT
from app.security.auth import verify_token
import os
from app.database import get_db
from app.models.model_user import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# ✅ Charger le mode DEBUG (activer ou désactiver l'envoi d'emails)
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

# ✅ Création des logs
os.makedirs("logs", exist_ok=True)

# ✅ Configuration du logging
logging.basicConfig(
    filename="logs/errors.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
async def get_user(db: AsyncSession,username:str):
    stmt=select(User).where(User.username==username)
    result = await db.execute(stmt)
    user=result.scalar_one_or_none()
    return user


def send_error_email(subject, message):
    """
    Envoie un email en cas d'erreur critique (`500`).
    L'envoi est **désactivé en mode DEBUG** pour éviter le spam.
    """
    if DEBUG_MODE:
        print("🚧 DEBUG MODE ACTIVÉ : Aucun email d'alerte envoyé.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        # Connexion au serveur SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Sécuriser la connexion
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        server.quit()

        print("✅ Email d'alerte envoyé avec succès !")
    except Exception as e:
        print(f"❌ Échec de l'envoi de l'email d'alerte : {e}")


async def request_logger_middleware(request: Request, call_next):
    """
    Middleware pour logger toutes les requêtes entrantes.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logging.info(f"🌍 {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response


async def error_handling_middleware(request: Request, call_next):
    """
    Middleware pour capturer et gérer toutes les erreurs HTTP et internes.
    """
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        logging.warning(f"⚠️ HTTPException : {request.method} {request.url} - {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status": exc.status_code},
        )
    except Exception as exc:
        error_trace = traceback.format_exc()
        logging.critical(f"🔥 CRITICAL ERROR: {request.method} {request.url} \n{error_trace}")

        print(f"\033[91m🔥 Erreur interne capturée : {error_trace}\033[0m")

        # ✅ Envoi d'un email d'alerte SEULEMENT si DEBUG_MODE est désactivé
        send_error_email(
            subject="🚨 Alerte : Erreur critique dans l'API",
            message=f"🔥 Une erreur critique a été détectée :\n\n{error_trace}"
        )

        return JSONResponse(
            status_code=500,
            content={"error": "Erreur interne du serveur. Veuillez réessayer plus tard."},
        )

async def auth_middleware(request: Request, call_next):
    """
    Middleware pour gérer l'authentification.
    """
    PUBLIC_ROUTES = [
        "/api-mca/v1/mycreo.json",
        "/api-mca/v1/recherche",
        "/api-mca/v1/documentation",
        "/api-mca/v1/register",
        "/api-mca/v1/qpv_check",
        "/api-mca/v1/siret",
        "/api-mca/v1/digiforma",
        "/api-mca/v1/generate-pdf",
        "/api-mca/v1/generate-pdf-from-file",
        "/",
        "",
        "/favicon.ico"
    ]

     # 🔥 Autoriser l'accès aux fichiers statiques sans authentification
    if request.url.path in PUBLIC_ROUTES or request.url.path.startswith("/static/") : 
        return await call_next(request)  # ✅ Autorisation sans authentification

    # ✅ Utilisation correcte du générateur `get_db()` avec `async for`
    async for db in get_db():
        try:
            # Vérification si l'utilisateur est admin et en local
            if request.client.host in ["127.0.0.1", "localhost"]:
                admin_user = await get_user(db, "admin")  # ✅ Appel correct de `get_user`
                if admin_user and admin_user.is_superuser:
                    request.state.user = admin_user
                    return await call_next(request)

            # ✅ Vérifier la présence du token dans les headers
            token = request.headers.get("Authorization")
            if not token:
                raise HTTPException(status_code=401, detail="Token manquant", headers={"WWW-Authenticate": "Bearer"})

            token = token.replace("Bearer ", "")
            payload = verify_token(token)
            print(payload)
            if not payload:
                raise HTTPException(status_code=401, detail="Token invalide ou expiré", headers={"WWW-Authenticate": "Bearer"})

            # ✅ Récupérer l'utilisateur associé au token
            username = payload.get("sub")
            user = await get_user(db, username)
            if not user:
                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

            request.state.user = user  # ✅ Ajout de l'utilisateur validé à la requête

            return await call_next(request)

        finally:
            await db.close()  # ✅ Fermeture propre de la session après la requête
