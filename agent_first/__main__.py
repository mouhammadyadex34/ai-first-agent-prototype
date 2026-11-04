"""Command line.

  python -m agent_first demander "Retiens l'offre full stack de Côte Web" [--modele llama3.1:8b]
  python -m agent_first evaluer [--modele llama3.1:8b] [--scenarios S01 S02]
  python -m agent_first parcours        # the UI journeys and their number of interactions
"""
import argparse
import json
from datetime import date
from pathlib import Path

from .agent import Agent
from .app import App
from .evaluation import evaluate, load, markdown
from .journeys import JOURNEYS
from .llm import OllamaChat

SCENARIOS = Path(__file__).resolve().parent.parent / "evaluation" / "scenarios.json"


def demander_confirmation(name: str, args: dict, description: str) -> bool:
    rep = input(f"\n  ⚠ L'agent veut faire : {description}. Confirmer ? [o/N] ")
    return rep.strip().lower() in ("o", "oui", "y", "yes")


def cmd_demander(a):
    app = App(date.fromisoformat(load(SCENARIOS)["aujourdhui"]))
    llm = OllamaChat(a.modele, num_ctx=a.num_ctx, num_thread=a.threads)
    trace = Agent(app, llm, confirmer=demander_confirmation).run(a.demande)
    print("\nÉtapes :")
    for name, args, effet, statut, _ in trace.etapes:
        print(f"  - [{effet}] {name}({json.dumps(args, ensure_ascii=False)}) → {statut}")
    print(f"\nAgent : {trace.reponse}\n({trace.appels_modele} appels au modèle, {trace.duree_s} s)")


def cmd_evaluer(a):
    journal = Path(f"evaluation/journal_{a.modele.replace(':', '_').replace('/', '_')}.jsonl")
    journal.write_text("", encoding="utf-8")

    def progress(r):
        print(f"{r['id']} {'réussi' if r['succes'] else 'ÉCHEC'} ({r['duree_s']} s)", flush=True)
        if not r["succes"]:
            print(f"    étapes : {[(e[0], e[1], e[3]) for e in r['etapes']]}")
            print(f"    réponse : {r['reponse'][:200]!r}", flush=True)
        with journal.open("a", encoding="utf-8") as f:  # written as we go: a stopped run is still readable
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    res = evaluate(SCENARIOS, lambda: OllamaChat(a.modele, num_ctx=a.num_ctx, num_thread=a.threads), a.scenarios,
                   jeu=a.jeu, pause_s=a.pause, progress=progress)
    out = Path(a.sortie or f"evaluation/resultats_{a.modele.replace(':', '_').replace('/', '_')}_v2.md")
    out.write_text(markdown(res, a.modele), encoding="utf-8")
    Path(out.with_suffix(".json")).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(markdown(res, a.modele))
    print(f"Écrit : {out}")


def cmd_parcours(a):
    for name, steps in JOURNEYS.items():
        print(f"{name} ({len(steps)}) : " + " → ".join(steps))


def main(argv=None):
    p = argparse.ArgumentParser(prog="agent_first", description="Prototype : des parcours utilisateurs aux agents.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("demander", help="une demande en langage naturel, avec confirmation des écritures")
    s.add_argument("demande")
    s.add_argument("--modele", default="llama3.1:8b")
    s.set_defaults(func=cmd_demander)
    s = sub.add_parser("evaluer", help="évalue l'agent sur les scénarios annotés")
    s.add_argument("--modele", default="llama3.1:8b")
    s.add_argument("--scenarios", nargs="*")
    s.add_argument("--jeu", choices=["dev", "test"], help="n'évalue qu'un jeu de scénarios")
    s.add_argument("--pause", type=float, default=0, help="secondes de pause entre deux scénarios (refroidissement)")
    s.add_argument("--sortie")
    s.set_defaults(func=cmd_evaluer)
    s = sub.add_parser("parcours", help="affiche les parcours de l'interface")
    s.set_defaults(func=cmd_parcours)
    for sp in sub.choices.values():
        if sp.prog.endswith(("demander", "evaluer")):
            sp.add_argument("--num-ctx", type=int, default=4096, help="taille de contexte du modèle (défaut 4096)")
            sp.add_argument("--threads", type=int, help="limite les cœurs utilisés par Ollama (moins de chauffe)")
    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
