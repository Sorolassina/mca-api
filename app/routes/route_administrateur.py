'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.schemas.user import User
from app.models.model_user import UserInDB
from app.security.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/create", response_model=UserInDB)
async def create_user(user_data: UserInDB, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    🚀 **Créer un nouvel utilisateur (Admin uniquement)**
    """
    existing_user = await db.execute(select(User).where(User.username == user_data.username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà pris")
    
    new_user = User(**user_data.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    🔍 **Récupérer un utilisateur par ID**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@router.get("/", response_model=list[UserInDB])
async def list_users(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    📋 **Liste tous les utilisateurs**
    """
    result = await db.execute(select(User))
    return result.scalars().all()


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(user_id: int, user_data: UserInDB, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    🔄 **Mettre à jour un utilisateur**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    ❌ **Supprimer un utilisateur**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    await db.delete(user)
    await db.commit()
    return {"message": "Utilisateur supprimé avec succès"}


@router.put("/{user_id}/activate")
async def activate_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    ✅ **Activer un utilisateur**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user.is_active = True
    await db.commit()
    return {"message": "Utilisateur activé avec succès"}


@router.put("/{user_id}/deactivate")
async def deactivate_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    🚫 **Désactiver un utilisateur**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user.is_active = False
    await db.commit()
    return {"message": "Utilisateur désactivé avec succès"}


@router.put("/{user_id}/promote")
async def promote_to_admin(user_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    🎩 **Promouvoir un utilisateur en administrateur**
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user.is_superuser = True
    await db.commit()
    return {"message": "Utilisateur promu administrateur"}
'''