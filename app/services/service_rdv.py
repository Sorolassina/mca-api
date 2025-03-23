#from transformers import pipeline
from typing import List

#summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

async def generer_resume(contenu_liste: List[str]) -> str:
    texte = " ".join(contenu_liste)
    longueur = len(texte.split())

    # Adaptation dynamique
    max_len = min(150, longueur * 2)
    min_len = min(40, longueur)

    #resume = summarizer(texte, max_length=max_len, min_length=min_len, do_sample=False)
    return texte #resume[0]["summary_text"]

async def generer_conclusion(titre: str, objectif: str, resume: str) -> str:
    # Adaptation dynamique
    texte = " ".join([titre, objectif,resume])
    longueur = len(texte.split())
    max_len = min(100, longueur * 2)
    min_len = min(40, longueur)
    # Tu peux rendre cette fonction plus intelligente avec NLP
    #resume = summarizer(texte, max_length=max_len, min_length=min_len, do_sample=False)
    return texte #resume[0]["summary_text"]
