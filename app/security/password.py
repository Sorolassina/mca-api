from passlib.context import CryptContext

# ✅ Initialisation du contexte de hachage avec bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """ Hache un mot de passe en utilisant bcrypt """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Vérifie si le mot de passe en clair correspond au mot de passe haché """
    return pwd_context.verify(plain_password, hashed_password)
