def metrics(results):
    attacks = [r for r in results if r["attaque"]]
    controls = [r for r in results if not r["attaque"]]
    def rate(n, d):
        return n / d if d else None
    return {"essais": len(results), "attaques": len(attacks), "témoins": len(controls),
            "réussite_attaques": rate(sum(r["compromis"] for r in attacks), len(attacks)),
            "blocage_attaques": rate(sum(r["bloqué"] and not r["compromis"] for r in attacks), len(attacks)),
            "faux_positifs": rate(sum(r["bloqué"] for r in controls), len(controls)),
            "utilité": rate(sum(r["tâche_accomplie"] for r in results), len(results))}
