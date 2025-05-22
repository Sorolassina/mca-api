from datetime import datetime, date, timezone
from typing import Union, Optional

async def ensure_utc(dt: Optional[Union[datetime, date]]) -> Optional[datetime]:
    """
    Convertit une date ou datetime en datetime UTC.
    Si c'est une date simple, la convertit en datetime à minuit UTC.
    
    Args:
        dt: Date ou datetime à convertir, peut être None
        
    Returns:
        datetime en UTC ou None si dt est None
    """
    if dt is None:
        return None
        
    print(f"\n📅 Conversion de la date: {dt}")
    print(f"  - Type: {type(dt)}")
    
    # Si c'est une date simple (sans heure)
    if isinstance(dt, date) and not isinstance(dt, datetime):
        print("  - Conversion d'une date simple en datetime UTC")
        # Créer un datetime à minuit UTC
        dt = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
        print(f"  - Résultat: {dt} (UTC)")
        return dt
        
    # Si c'est déjà un datetime
    if isinstance(dt, datetime):
        print(f"  - TZ info: {dt.tzinfo}")
        
        # Si pas de fuseau horaire, supposer UTC
        if dt.tzinfo is None:
            print("  - Pas de fuseau horaire, conversion en UTC")
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Si déjà en UTC, retourner tel quel
            if dt.tzinfo == timezone.utc:
                print("  - Déjà en UTC")
                return dt
            # Sinon convertir en UTC
            print(f"  - Conversion de {dt.tzinfo} vers UTC")
            dt = dt.astimezone(timezone.utc)
            
        print(f"  - Résultat: {dt} (UTC)")
        return dt