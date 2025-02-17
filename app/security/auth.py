from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import timedelta
from app.security.tokens import create_access_token, verify_token

router = APIRouter()

# Simuler une base de données d'utilisateurs (à remplacer par une vraie BDD)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$KYZHFa0dTg9t0puMxhXaXOuaeXPnXHxjxbFB68Xcuf.BDJAkKazA.",  # Mot de passe: "password"
        "disabled": False
    }
}

# Gestion du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Password Bearer (utilisé pour récupérer le token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    print(f"Mot de passe entré : {plain_password}")
    print(f"Mot de passe stocké (haché) : {hashed_password}")
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    user = fake_users_db.get(username)
    if user:
        return user
    return None

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    
    # Génération du token JWT
    access_token = create_access_token({"sub": user["username"]}, timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    
    username = payload.get("sub")
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    return {"username": user["username"], "email": user["email"], "full_name": user["full_name"]}
