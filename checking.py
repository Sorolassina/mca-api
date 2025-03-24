import sys
import site

print("✅ Python utilisé :", sys.executable)
print("📦 Dossiers de packages :", site.getsitepackages())

try:
    import openpyxl
    print("✅ openpyxl est bien installé et accessible.")
except ImportError as e:
    print("❌ openpyxl introuvable :", e)