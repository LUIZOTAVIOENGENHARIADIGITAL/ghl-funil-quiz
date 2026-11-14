#!/usr/bin/env python3
"""Cria no GHL (API v2) os campos personalizados e as tags do Funil de Quiz. Só biblioteca padrão.

O que a API FAZ aqui:  campos personalizados de contato + tags (idempotente: pula o que já existe).
O que a API NÃO faz:   quiz, páginas e fluxos de trabalho (monte na interface: veja CHECKLIST.md).

Variáveis de ambiente (nunca coloque o token em arquivo):
  GHL_TOKEN        Private Integration Token (pit-...) com escopos de custom fields e tags
  GHL_LOCATION_ID  ID da subconta

Uso:
  python3 ghl_setup.py --config quiz.config.json --dry-run      # mostra o que faria, sem chamar a API
  python3 ghl_setup.py --config quiz.config.json                # cria campos e tags
  python3 ghl_setup.py --config quiz.config.json --webhook-teste "URL_DO_WEBHOOK_DE_ENTRADA"
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://services.leadconnectorhq.com"
VERSION = "2021-07-28"

UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid", "gclid"]


def campos(c):
    f = [("quiz_nome", "TEXT"), ("quiz_avatar", "TEXT"), ("quiz_avatar_nome", "TEXT"),
         ("quiz_respostas", "LARGE_TEXT"), ("quiz_pagina", "TEXT")]
    f += [("quiz_" + p["chave"], "TEXT") for p in c["perguntas"]]
    f += [(u, "TEXT") for u in UTM]
    return f


def tags(c):
    return ["quiz:" + c["slug"]] + ["quiz:avatar-" + a["id"] for a in c["avatares"]]


class GHL:
    def __init__(self, token, loc):
        self.token, self.loc = token, loc

    def req(self, method, path, body=None, tentativas=3):
        url = API + path
        data = json.dumps(body).encode() if body is not None else None
        for i in range(tentativas):
            r = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": "Bearer " + self.token, "Version": VERSION,
                "Accept": "application/json", "Content-Type": "application/json",
                "User-Agent": "ghl-funil-quiz/1.0"})
            try:
                with urllib.request.urlopen(r, timeout=30) as resp:
                    txt = resp.read().decode() or "{}"
                    return json.loads(txt)
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:300]
                if e.code == 429 and i < tentativas - 1:
                    time.sleep(2 * (i + 1))
                    continue
                if e.code in (401, 403):
                    sys.exit(f"ERRO {e.code}: token sem permissão (confira os escopos da Integração Privada). {msg}")
                raise RuntimeError(f"{method} {path} → HTTP {e.code}: {msg}")
            except urllib.error.URLError as e:
                if i < tentativas - 1:
                    time.sleep(2)
                    continue
                raise RuntimeError(f"{method} {path} → rede: {e.reason}")

    def campos_existentes(self):
        d = self.req("GET", f"/locations/{self.loc}/customFields?model=contact")
        nomes = set()
        for f in d.get("customFields", []):
            nomes.add((f.get("name") or "").strip().lower())
            fk = (f.get("fieldKey") or "").split(".")[-1].lower()
            if fk:
                nomes.add(fk)
        return nomes

    def tags_existentes(self):
        d = self.req("GET", f"/locations/{self.loc}/tags")
        return {(t.get("name") or "").strip().lower() for t in d.get("tags", [])}

    def criar_campo(self, nome, tipo):
        return self.req("POST", f"/locations/{self.loc}/customFields",
                        {"name": nome, "dataType": tipo, "model": "contact"})

    def criar_tag(self, nome):
        return self.req("POST", f"/locations/{self.loc}/tags", {"name": nome})


def payload_teste(c):
    a = c["avatares"][0]
    p = {"first_name": "Teste Quiz", "phone": "+5500000000000", "email": "",
         "quiz_nome": c["slug"], "quiz_avatar": a["id"], "quiz_avatar_nome": a["nome"],
         "quiz_respostas": c["pergunta_avatar"]["texto"] + " → " + a["opcao"],
         "quiz_pagina": "https://seudominio.com.br/" + a["id"] + ".html?nome=Teste",
         "tags": f"quiz:{c['slug']},quiz:avatar-{a['id']}",
         "utm_source": "teste", "utm_medium": "teste", "utm_campaign": f"quiz-{c['slug']}",
         "utm_content": "", "utm_term": "", "fbclid": "", "gclid": "",
         "page_url": "https://seudominio.com.br/quiz", "referrer": "", "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for q in c["perguntas"]:
        p["quiz_" + q["chave"]] = q["opcoes"][0]
    return p


def main():
    ap = argparse.ArgumentParser(description="Cria campos personalizados e tags do Funil de Quiz no GHL.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true", help="não chama a API, só mostra o plano")
    ap.add_argument("--sem-campos", action="store_true")
    ap.add_argument("--sem-tags", action="store_true")
    ap.add_argument("--webhook-teste", metavar="URL", help="envia 1 payload de exemplo pro Webhook de entrada (pra mapear campos)")
    a = ap.parse_args()

    c = json.loads(Path(a.config).read_text(encoding="utf-8"))
    plano_campos = [] if a.sem_campos else campos(c)
    plano_tags = [] if a.sem_tags else tags(c)

    if a.dry_run:
        loc = os.environ.get("GHL_LOCATION_ID", "<GHL_LOCATION_ID>")
        print("DRY-RUN: nenhuma chamada será feita.\n")
        for n, t in plano_campos:
            print(f"POST {API}/locations/{loc}/customFields  {json.dumps({'name': n, 'dataType': t, 'model': 'contact'})}")
        for t in plano_tags:
            print(f"POST {API}/locations/{loc}/tags  {json.dumps({'name': t}, ensure_ascii=False)}")
        if a.webhook_teste:
            print(f"\nPOST {a.webhook_teste}\n{json.dumps(payload_teste(c), ensure_ascii=False, indent=2)}")
        print(f"\n{len(plano_campos)} campos, {len(plano_tags)} tags (os que já existirem serão pulados na execução real).")
        print("Headers: Authorization: Bearer $GHL_TOKEN · Version: " + VERSION)
        return

    if plano_campos or plano_tags:
        token, loc = os.environ.get("GHL_TOKEN"), os.environ.get("GHL_LOCATION_ID")
        if not token or not loc:
            sys.exit("Defina GHL_TOKEN e GHL_LOCATION_ID no ambiente (export GHL_TOKEN=pit-... ; export GHL_LOCATION_ID=...).")
        g = GHL(token, loc)
        criados, pulados, falhas = [], [], []
        if plano_campos:
            existentes = g.campos_existentes()
            for n, t in plano_campos:
                if n.lower() in existentes:
                    pulados.append("campo " + n)
                    continue
                try:
                    g.criar_campo(n, t)
                    criados.append("campo " + n)
                except RuntimeError as e:
                    falhas.append(str(e))
        if plano_tags:
            existentes = g.tags_existentes()
            for t in plano_tags:
                if t.lower() in existentes:
                    pulados.append("tag " + t)
                    continue
                try:
                    g.criar_tag(t)
                    criados.append("tag " + t)
                except RuntimeError as e:
                    falhas.append(str(e))
        print(f"Criados ({len(criados)}): " + (", ".join(criados) or "-"))
        print(f"Já existiam ({len(pulados)}): " + (", ".join(pulados) or "-"))
        if falhas:
            print("FALHAS:")
            for f in falhas:
                print("  ", f)

    if a.webhook_teste:
        body = json.dumps(payload_teste(c)).encode()
        r = urllib.request.Request(a.webhook_teste, data=body, method="POST",
                                   headers={"Content-Type": "application/json", "User-Agent": "ghl-funil-quiz/1.0"})
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                print(f"Webhook de teste enviado: HTTP {resp.status}. Agora mapeie os campos no gatilho do fluxo.")
        except urllib.error.HTTPError as e:
            print(f"Webhook respondeu HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
        except urllib.error.URLError as e:
            print(f"Falha de rede no webhook: {e.reason}")

    print("\nPróximo passo: monte quiz/páginas/fluxo na interface (CHECKLIST.md gerado pelo gerar.py).")


if __name__ == "__main__":
    main()
