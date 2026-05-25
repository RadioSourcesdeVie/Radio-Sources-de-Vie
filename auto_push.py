#!/usr/bin/env python3
"""
auto_push.py — Script maître tout-en-un
Usage: python auto_push.py --owm-key OWM_KEY --anthropic-key CLAUDE_KEY
"""
import sys, subprocess, argparse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
NOW_FR    = datetime.now().strftime("%d/%m/%Y à %Hh%M")

def run(cmd, check=True):
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=REPO_ROOT, text=True)
    if check and result.returncode != 0:
        print(f"⚠️  Code retour: {result.returncode}")
    return result.returncode == 0

def step(msg):
    print(f"\n{'─'*50}\n  {msg}\n{'─'*50}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owm-key",       required=True)
    parser.add_argument("--anthropic-key", default=None)
    parser.add_argument("--skip-content",  action="store_true")
    parser.add_argument("--skip-push",     action="store_true")
    args = parser.parse_args()

    print(f"\n📻  Radio Sources de Vie — {NOW_FR}\n")

    step("🌡️  1/4 — Météo")
    run(f'python fetch_weather.py --api-key "{args.owm_key}"')

    step("📰  2/4 — Nouvelles RSS")
    run("python fetch_news.py")

    if not args.skip_content and args.anthropic_key:
        step("🙏  3/4 — Contenu spirituel")
        run(f'python generate_content.py --api-key "{args.anthropic_key}" --type all')
    else:
        print("\n⏭️  Étape 3/4 ignorée")

    if not args.skip_push:
        step("🚀  4/4 — GitHub Push")
        if (REPO_ROOT / ".git").exists():
            run("git add -A")
            run(f'git commit -m "📻 Mise à jour — {NOW_FR}"')
            if not run("git push origin main", check=False):
                run("git push origin master", check=False)
        else:
            print("⚠️  Pas de dépôt git trouvé")
    else:
        print("\n⏭️  Push ignoré (--skip-push)")

    print(f"\n✅  Terminé! Site: radiosourcesdevie.github.io/Radio-Sources-de-Vie\n")

if __name__ == "__main__":
    main()
