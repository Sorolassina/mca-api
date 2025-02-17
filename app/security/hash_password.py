from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Générer un nouveau hash pour "password"
hashed_password = pwd_context.hash("password")
print("Mot de passe haché :", hashed_password)

# Vérifier que le mot de passe "password" correspond bien au hash
is_valid = pwd_context.verify("password", hashed_password)
print("Vérification du mot de passe :", is_valid)
