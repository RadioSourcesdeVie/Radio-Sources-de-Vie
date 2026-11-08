#!/usr/bin/env python3
"""
essai_priere.py - Un exemple de priere du matin lu par VOTRE voix clonee.
Sert a decider avant de modifier quoi que ce soit au pipeline.
Usage : python essai_priere.py
        python essai_priere.py "tres lent et solennel"
Le style passe en argument remplace le style par defaut.
"""
import base64, sys
from pathlib import Path
from google import genai
import rsdv_voix as rv

MODELE = "gemini-3.8-flash-tts"
SORTIE = Path("essai_priere_matin.mp3")

# Consigne de jeu : courte, Google recommande de ne pas la surcharger.
STYLE_DEFAUT = "calme et recueilli, parlant lentement"

PRIERE = """Seigneur, en ce matin nouveau, je viens à toi avant toute chose.

Ta Parole dit : Éternel, le matin tu entends ma voix ; le matin je me tourne vers toi, et je regarde. Alors me voici. Je ne viens pas d'abord avec ma liste. Je viens avec mon cœur.

Seigneur, je me souviens d'Anne. Elle était à Silo, l'âme amère, et elle a prié. Elle priait si bas que le sacrificateur a cru qu'elle avait bu. Mais toi, tu l'as entendue. Et elle a pu dire : C'était pour cet enfant que je priais, et l'Éternel a exaucé la prière que je lui adressais. Une seule prière, Seigneur, et sa destinée a changé. Une seule prière, et tout un peuple a reçu Samuel.

Ce matin je te le demande simplement : change ce qui doit changer dans ma vie. Ce que je porte depuis trop longtemps. Ce que je n'arrive pas à dire à personne. Ce que personne ne voit. Toi, tu le vois.

Et je veux me rappeler une chose, Seigneur. Avant même que j'ouvre la bouche ce matin, Jésus avait déjà prié pour moi. Il a dit à Pierre : J'ai prié pour toi, afin que ta foi ne défaille point. Et dans sa grande prière au Père, il a dit : Ce n'est pas pour eux seulement que je prie, mais encore pour ceux qui croiront en moi par leur parole. C'est moi, Seigneur. Je suis dans cette prière-là.

Alors je pars dans cette journée sans crainte. Pas parce que je suis fort. Mais parce que mon Sauveur a déjà prié pour moi.

Au nom de Jésus, amen."""

def main():
    cle = rv.cle_gemini()
    if not cle:
        raise SystemExit("GEMINI_KEY introuvable dans .env")

    f = Path("ma_voix/voice_id.txt")
    if not f.exists():
        raise SystemExit("ma_voix/voice_id.txt introuvable.\n"
                         "Lancez d'abord : python cloner_ma_voix.py")
    voix = f.read_text(encoding="utf-8").strip()

    mots = len(PRIERE.split())
    print(f"\n  Voix   : {voix} (la votre)")
    print(f"  Texte  : {mots} mots, environ {mots/140:.1f} minutes")

    style = sys.argv[1] if len(sys.argv) > 1 else STYLE_DEFAUT
    print(f"  Style  : {style}")

    client = genai.Client(api_key=cle, http_options={"api_version": "v1beta"})
    # Une respiration entre chaque mouvement de la priere
    texte = rv.nettoyer(PRIERE).replace("\n\n", "\n\n<short pause>\n\n")

    morceaux = rv.decouper(texte)
    print(f"  Decoupe: {len(morceaux)} morceau(x)")
    bouts = []
    import time
    for i, m in enumerate(morceaux, 1):
        print(f"    morceau {i}/{len(morceaux)}...")
        r = client.interactions.create(
            model=MODELE,
            input=[{"type": "user_input",
                    "content": [{"type": "text", "text": m,
                                 "annotations": [{"type": "speech_metadata",
                                                  "style": style}]}]}],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": voix}]},
        )
        brut = base64.b64decode(r.output_audio.data)
        bouts.append(rv._fondu(rv._couper_parasite(rv._sans_entete(brut))))
        if i < len(morceaux):
            time.sleep(rv.PAUSE)

    pcm = rv._silence(180).join(bouts)
    pcm = rv._normaliser(pcm) + rv._silence(250)
    suffixe = "" if len(sys.argv) <= 1 else "_" + "".join(
        c if c.isalnum() else "_" for c in style)[:28]
    sortie = SORTIE.with_name(SORTIE.stem + suffixe + SORTIE.suffix)
    encodeur = rv.pcm_vers_mp3(pcm, sortie)
    cible = sortie if encodeur != "wav" else sortie.with_suffix(".wav")
    print(f"\n  Pret : {cible}  ({cible.stat().st_size//1024} Ko, "
          f"{len(pcm)/(rv.SR*2)/60:.1f} min)")
    print(f"  Ecoutez :  start {cible}")

if __name__ == "__main__":
    main()
