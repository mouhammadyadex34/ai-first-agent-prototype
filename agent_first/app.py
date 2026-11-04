"""A small internship-tracking application (same spirit as StageTrack), backed by SQLite.

The services below are what the graphical interface calls when the user clicks through a journey.
The agent calls exactly the same services, through tools: there is no second implementation.
"""
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "data" / "seed.json"
RELANCE_APRES_JOURS = 7

SCHEMA = """
CREATE TABLE documents (id INTEGER PRIMARY KEY, titre TEXT NOT NULL, type TEXT NOT NULL);
CREATE TABLE offres (id INTEGER PRIMARY KEY, titre TEXT, entreprise TEXT, lieu TEXT, competences TEXT,
                     statut TEXT NOT NULL DEFAULT 'nouvelle');
CREATE TABLE candidatures (id INTEGER PRIMARY KEY, offre_id INTEGER, entreprise TEXT, poste TEXT, lieu TEXT,
                           statut TEXT NOT NULL DEFAULT 'a_postuler', cv_id INTEGER, envoyee_le TEXT, relance_le TEXT);
CREATE TABLE evenements (id INTEGER PRIMARY KEY, candidature_id INTEGER, type TEXT, texte TEXT, jour TEXT);
"""


class ErreurMetier(Exception):
    """Raised for an invalid request (unknown id, wrong state). The message is shown to the agent or the user."""


class App:
    def __init__(self, aujourdhui: date, seed: Path | None = SEED):
        self.aujourdhui = aujourdhui
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.ecritures: list[str] = []  # journal of state changes, used by the evaluation
        if seed:
            self._charger(json.loads(Path(seed).read_text(encoding="utf-8")))

    def _charger(self, d):
        for x in d["documents"]:
            self.db.execute("INSERT INTO documents VALUES (?,?,?)", (x["id"], x["titre"], x["type"]))
        for x in d["offres"]:
            self.db.execute("INSERT INTO offres VALUES (?,?,?,?,?,?)", (x["id"], x["titre"], x["entreprise"], x["lieu"],
                            json.dumps(x["competences"], ensure_ascii=False), x.get("statut", "nouvelle")))
        for x in d["candidatures"]:
            self.db.execute("INSERT INTO candidatures VALUES (?,?,?,?,?,?,?,?,?)",
                            (x["id"], x.get("offre_id"), x["entreprise"], x["poste"], x.get("lieu", ""), x["statut"],
                             x.get("cv_id"), x.get("envoyee_le"), x.get("relance_le")))
        self.db.commit()

    # ---------- helpers ----------
    def _ligne(self, table, id_):
        row = self.db.execute(f"SELECT * FROM {table} WHERE id = ?", (id_,)).fetchone()
        if not row:
            raise ErreurMetier(f"Aucun élément {id_} dans {table}.")
        return dict(row)

    def _offre(self, row):
        row = dict(row)
        row["competences"] = json.loads(row["competences"] or "[]")
        return row

    def _jour(self, valeur: str | None) -> date:
        if not valeur:
            return self.aujourdhui
        try:
            return date.fromisoformat(valeur)
        except ValueError:
            raise ErreurMetier(f"Date invalide : {valeur} (format attendu AAAA-MM-JJ).")

    def _ecrit(self, quoi):
        self.ecritures.append(quoi)
        self.db.commit()

    # ---------- reads ----------
    def chercher_offres(self, mots_cles: str = "", lieu: str = "", entreprise: str = "", statut: str = "nouvelle"):
        rows = self.db.execute("SELECT * FROM offres WHERE statut = ? ORDER BY id", (statut,)).fetchall()
        out = []
        for r in map(self._offre, rows):
            texte = f"{r['titre']} {' '.join(r['competences'])}".lower()
            if mots_cles and not all(m in texte for m in mots_cles.lower().split()):
                continue
            if lieu and lieu.lower() not in r["lieu"].lower():
                continue
            if entreprise and entreprise.lower() not in r["entreprise"].lower():
                continue
            out.append(r)
        return out

    def lister_cv(self):
        return [dict(r) for r in self.db.execute("SELECT id, titre FROM documents WHERE type = 'cv' ORDER BY id")]

    def lister_candidatures(self, statut: str = "", entreprise: str = ""):
        rows = [dict(r) for r in self.db.execute("SELECT * FROM candidatures ORDER BY id")]
        return [r for r in rows if (not statut or r["statut"] == statut)
                and (not entreprise or entreprise.lower() in r["entreprise"].lower())]

    def relances_a_faire(self, jusqu_au: str = ""):
        limite = self._jour(jusqu_au) if jusqu_au else self.aujourdhui + timedelta(days=6 - self.aujourdhui.weekday())
        return [c for c in self.lister_candidatures(statut="envoyee")
                if c["relance_le"] and date.fromisoformat(c["relance_le"]) <= limite]

    def rediger_relance(self, candidature_id: int):
        c = self._ligne("candidatures", candidature_id)
        if c["statut"] not in ("envoyee", "relancee"):
            raise ErreurMetier("On ne relance qu'une candidature envoyée.")
        envoi = date.fromisoformat(c["envoyee_le"]).strftime("%d/%m/%Y") if c["envoyee_le"] else "récemment"
        return {"objet": f"Relance – candidature {c['poste']}",
                "corps": (f"Bonjour,\n\nJe me permets de revenir vers vous au sujet de ma candidature au poste de "
                          f"{c['poste']} chez {c['entreprise']}, envoyée le {envoi}. Ce stage m'intéresse toujours "
                          "vivement et je reste disponible pour un échange.\n\nBien cordialement,")}

    # ---------- writes ----------
    def retenir_offre(self, offre_id: int):
        o = self._offre(self._ligne("offres", offre_id))
        if o["statut"] != "nouvelle":
            raise ErreurMetier(f"L'offre {offre_id} est déjà « {o['statut']} ».")
        cur = self.db.execute("INSERT INTO candidatures (offre_id, entreprise, poste, lieu) VALUES (?,?,?,?)",
                              (offre_id, o["entreprise"], o["titre"], o["lieu"]))
        self.db.execute("UPDATE offres SET statut = 'retenue' WHERE id = ?", (offre_id,))
        self._ecrit(f"retenir_offre {offre_id}")
        return self._ligne("candidatures", cur.lastrowid)

    def ignorer_offre(self, offre_id: int):
        o = self._ligne("offres", offre_id)
        if o["statut"] != "nouvelle":
            raise ErreurMetier(f"L'offre {offre_id} est déjà « {o['statut']} ».")
        self.db.execute("UPDATE offres SET statut = 'ignoree' WHERE id = ?", (offre_id,))
        self._ecrit(f"ignorer_offre {offre_id}")
        return {"offre_id": offre_id, "statut": "ignoree"}

    def associer_cv(self, candidature_id: int, cv_id: int):
        self._ligne("candidatures", candidature_id)
        doc = self._ligne("documents", cv_id)
        if doc["type"] != "cv":
            raise ErreurMetier(f"Le document {cv_id} n'est pas un CV.")
        self.db.execute("UPDATE candidatures SET cv_id = ? WHERE id = ?", (cv_id, candidature_id))
        self._ecrit(f"associer_cv {candidature_id} {cv_id}")
        return self._ligne("candidatures", candidature_id)

    def marquer_envoyee(self, candidature_id: int, jour: str = ""):
        c = self._ligne("candidatures", candidature_id)
        if c["statut"] != "a_postuler":
            raise ErreurMetier(f"La candidature {candidature_id} est déjà « {c['statut']} ».")
        j = self._jour(jour)
        self.db.execute("UPDATE candidatures SET statut = 'envoyee', envoyee_le = ?, relance_le = ? WHERE id = ?",
                        (j.isoformat(), (j + timedelta(days=RELANCE_APRES_JOURS)).isoformat(), candidature_id))
        self._evenement(candidature_id, "envoi", "", j)
        self._ecrit(f"marquer_envoyee {candidature_id}")
        return self._ligne("candidatures", candidature_id)

    def planifier_relance(self, candidature_id: int, jour: str):
        self._ligne("candidatures", candidature_id)
        j = self._jour(jour)
        self.db.execute("UPDATE candidatures SET relance_le = ? WHERE id = ?", (j.isoformat(), candidature_id))
        self._ecrit(f"planifier_relance {candidature_id}")
        return self._ligne("candidatures", candidature_id)

    def ajouter_note(self, candidature_id: int, texte: str):
        self._ligne("candidatures", candidature_id)
        if not texte.strip():
            raise ErreurMetier("La note est vide.")
        self._evenement(candidature_id, "note", texte.strip()[:500], self.aujourdhui)
        self._ecrit(f"ajouter_note {candidature_id}")
        return {"candidature_id": candidature_id, "note": texte.strip()[:500]}

    def _evenement(self, candidature_id, type_, texte, jour):
        self.db.execute("INSERT INTO evenements (candidature_id, type, texte, jour) VALUES (?,?,?,?)",
                        (candidature_id, type_, texte, jour.isoformat()))

    def evenements(self, candidature_id: int):
        return [dict(r) for r in self.db.execute("SELECT * FROM evenements WHERE candidature_id = ?", (candidature_id,))]
