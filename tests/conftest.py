import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH pour que les imports fonctionnent
sys.path.append(str(Path(__file__).parent.parent)) 