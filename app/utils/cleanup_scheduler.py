import os
import time
from apscheduler.schedulers.background import BackgroundScheduler

# Récupère le chemin du dossier projet (racine)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR_FILE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Paramètres === 10080=Une semaine
CLEANUP_CONFIG = [
    {
        "folder": os.path.join(BASE_DIR, "static", "images"),
        "extensions": (".png", ".jpg", ".jpeg"),
        "age_limit_minutes": 1440
    },
    {
        "folder": os.path.join(BASE_DIR, "static", "fichiers"),
        "extensions": (".png", ".jpg", ".jpeg",".zip"),
        "age_limit_minutes": 1440
    },
    {
        "folder": os.path.join(BASE_DIR,  "static", "maps"),
        "extensions": (".html",),
        "age_limit_minutes": 1440
    },
    {
        "folder": os.path.join(BASE_DIR_FILE,  "fichiers"),
        "extensions": (".html", ".pdf", ".csv", ".zip"),
        "age_limit_minutes": 1440
    }
]

scheduler = BackgroundScheduler()

def cleanup_temp_files():
    now = time.time()
    for config in CLEANUP_CONFIG:
        folder = config["folder"]
        extensions = config["extensions"]
        age_limit = config["age_limit_minutes"]

        if not os.path.exists(folder):
            print(f"📁 Dossier introuvable : {folder}")
            continue

        deleted_files = []

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) and file_path.lower().endswith(extensions):
                file_age = now - os.path.getmtime(file_path)
                if file_age > age_limit * 60:
                    try:
                        os.remove(file_path)
                        deleted_files.append(filename)
                    except Exception as e:
                        print(f"⚠️ Erreur suppression {filename} : {e}")

        if deleted_files:
            print(f"🧹 {len(deleted_files)} fichiers supprimés de {folder} :", deleted_files)

def start_cleanup_scheduler():
    scheduler.add_job(cleanup_temp_files, "interval", minutes=2)
    scheduler.start()
    print("✅ Scheduler de nettoyage lancé.")

def stop_cleanup_scheduler():
    scheduler.shutdown()
    print("🛑 Scheduler arrêté proprement.")
