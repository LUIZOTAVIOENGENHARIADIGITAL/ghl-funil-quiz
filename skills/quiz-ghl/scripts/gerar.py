#!/usr/bin/env python3
"""Gera o Funil de Quiz a partir de um quiz.config.json (só biblioteca padrão).

Saída (pasta --out):
  quiz.html                 o quiz (config embutida, pronto pra subir ou incorporar)
  <avatar-id>.html          uma página por avatar (template pagina-avatar.html)
  mensagens-whatsapp.md     D0 / D+1 / D+3 por avatar, já com as variáveis do GHL
  payload-exemplo.json      o JSON que o quiz manda pro Webhook de entrada
  CHECKLIST.md              o que montar na interface do GHL

Uso:
  python3 gerar.py --config quiz.config.json --out saida/
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

AQUI = Path(__file__).resolve().parent
TEMPLATES = AQUI.parent / "templates"

CAMPOS_AVATAR = ["id", "opcao", "nome", "headline", "sub", "dores", "mecanismo", "prova", "objecao", "oferta", "cta", "whatsapp"]


def erro(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def validar(c):
    for k in ["marca", "slug", "pergunta_avatar", "perguntas", "avatares"]:
        if k not in c:
            erro(f"config sem o campo '{k}'")
    if not re.fullmatch(r"[a-z0-9-]+", c["slug"]):
        erro("slug deve ter só letras minúsculas, números e hífen")
    if len(c["avatares"]) < 2:
        erro("um quiz de roteamento precisa de pelo menos 2 avatares")
    ids = set()
    avisos = []
    for a in c["avatares"]:
        for k in CAMPOS_AVATAR:
            if k not in a:
                erro(f"avatar {a.get('id', '?')} sem o campo '{k}'")
        if not re.fullmatch(r"[a-z0-9-]+", a["id"]):
            erro(f"id de avatar inválido: {a['id']} (use minúsculas e hífen)")
        if a["id"] in ids:
            erro(f"id de avatar repetido: {a['id']}")
        ids.add(a["id"])
        if len(a["dores"]) < 2:
            avisos.append(f"{a['id']}: menos de 2 dores. Cada avatar precisa das dores DELE.")
        if "[" in a["prova"]["texto"]:
            avisos.append(f"{a['id']}: depoimento ainda é placeholder. Use um depoimento REAL desse avatar.")
    # o erro clássico: páginas iguais com headline trocada
    corpos = {}
    for a in c["avatares"]:
        corpo = json.dumps([a["dores"], a["mecanismo"], a["objecao"]], ensure_ascii=False)
        if corpo in corpos:
            avisos.append(f"{a['id']} e {corpos[corpo]} têm dor/mecanismo/objeção IGUAIS. Só trocar a headline não converte.")
        corpos[corpo] = a["id"]
    for p in c["perguntas"]:
        if not re.fullmatch(r"[a-z0-9_]+", p["chave"]):
            erro(f"chave de pergunta inválida: {p['chave']} (use minúsculas e _)")
    return avisos


def marcar(texto):
    """Escapa HTML e transforma *trecho* em <mark>trecho</mark>."""
    t = html.escape(texto)
    return re.sub(r"\*(.+?)\*", r"<mark>\1</mark>", t)


def url_pagina(c, a):
    base = c.get("paginas_base_url") or "./"
    if not base.endswith("/"):
        base += "/"
    return f"{base}{a['id']}.html"


def cta_url(c, a):
    if a.get("cta_url"):
        return a["cta_url"]
    num = re.sub(r"\D", "", c.get("whatsapp_numero", ""))
    if num:
        txt = f"Oi! Vi a página de {a['nome']} e quero saber mais."
        return f"https://wa.me/{num}?text={quote(txt)}"
    return "#"


def gerar_quiz(c, out):
    tpl = (TEMPLATES / "quiz.html").read_text(encoding="utf-8")
    leve = {k: v for k, v in c.items() if k != "avatares"}
    leve["avatares"] = [{k: a.get(k, "") for k in ("id", "emoji", "opcao", "nome")} for a in c["avatares"]]
    js = json.dumps(leve, ensure_ascii=False, indent=1).replace("</", "<\\/")
    novo, n = re.subn(r'(<script id="quiz-config" type="application/json">)(.*?)(</script>)',
                      lambda m: m.group(1) + "\n" + js + "\n" + m.group(3), tpl, count=1, flags=re.S)
    if n != 1:
        erro("bloco quiz-config não encontrado no template")
    (out / "quiz.html").write_text(novo, encoding="utf-8")


def gerar_paginas(c, out):
    tpl = (TEMPLATES / "pagina-avatar.html").read_text(encoding="utf-8")
    for a in c["avatares"]:
        rep = {
            "MARCA": html.escape(c["marca"]),
            "COR": html.escape(c.get("cor", "#6d28d9")),
            "AVATAR_NOME": html.escape(a["nome"]),
            "HEADLINE": marcar(a["headline"]),
            "SUB": html.escape(a["sub"]),
            "DORES": "".join(f'<div class="dor"><span>✕</span>{html.escape(d)}</div>' for d in a["dores"]),
            "MECANISMO": html.escape(a["mecanismo"]),
            "PROVA_TEXTO": html.escape(a["prova"]["texto"]),
            "PROVA_AUTOR": html.escape(a["prova"]["autor"]),
            "OBJ_PERGUNTA": html.escape(a["objecao"]["pergunta"]),
            "OBJ_RESPOSTA": html.escape(a["objecao"]["resposta"]),
            "OFERTA": html.escape(a["oferta"]),
            "CTA": html.escape(a["cta"]),
            "CTA_URL": html.escape(cta_url(c, a), quote=True),
        }
        pg = tpl
        for k, v in rep.items():
            pg = pg.replace("{{" + k + "}}", v)
        (out / f"{a['id']}.html").write_text(pg, encoding="utf-8")


def var_ghl(texto, c, a):
    """Troca {nome}, {link} e {chave_da_pergunta} pelas variáveis do GHL."""
    t = texto.replace("{nome}", "{{contact.first_name}}")
    link = url_pagina(c, a)
    if not link.startswith("http"):  # link relativo não funciona no WhatsApp
        link = "https://SEU_DOMINIO/" + link.lstrip("./")
    t = t.replace("{link}", link + "?nome={{contact.first_name}}")
    for p in c["perguntas"]:
        t = t.replace("{" + p["chave"] + "}", "{{contact.quiz_" + p["chave"] + "}}")
    return t


def gerar_mensagens(c, out):
    linhas = [f"# Réguas de WhatsApp por avatar · {c['marca']}", "",
              "Cole cada mensagem na ação **Enviar WhatsApp** do ramo do avatar no fluxo de trabalho.",
              "Entre as mensagens: **Aguardar** 1 dia (D+1) e 2 dias (D+3), saindo da régua se o contato responder.",
              "Linha oficial (API do WhatsApp): fora da janela de 24h use modelos (templates) aprovados.", ""]
    for a in c["avatares"]:
        w = a["whatsapp"]
        linhas += [f"## {a.get('emoji', '')} {a['nome']}  ·  tag `quiz:avatar-{a['id']}`", "",
                   f"Objeção que a régua quebra: {a['objecao']['pergunta']}", "",
                   "**D0 (logo após o quiz)**", "", "```", var_ghl(w["d0"], c, a), "```", "",
                   "**D+1 (quebra a objeção)**", "", "```", var_ghl(w["d1"], c, a), "```", "",
                   "**D+3 (convite final)**", "", "```", var_ghl(w["d3"], c, a), "```", ""]
    (out / "mensagens-whatsapp.md").write_text("\n".join(linhas), encoding="utf-8")


def exemplo_payload(c):
    a = c["avatares"][0]
    p = {
        "first_name": "Teste", "phone": "+5500000000000", "email": "",
        "quiz_nome": c["slug"], "quiz_avatar": a["id"], "quiz_avatar_nome": a["nome"],
        "quiz_respostas": " | ".join([c["pergunta_avatar"]["texto"] + " → " + a["opcao"]] +
                                     [q["texto"] + " → " + q["opcoes"][0] for q in c["perguntas"]]),
        "quiz_pagina": url_pagina(c, a) + "?nome=Teste",
        "tags": f"quiz:{c['slug']},quiz:avatar-{a['id']}",
        "utm_source": "facebook", "utm_medium": "cpc", "utm_campaign": f"quiz-{c['slug']}",
        "utm_content": "criativo-01", "utm_term": "", "fbclid": "teste", "gclid": "",
        "page_url": "https://seudominio.com.br/quiz", "referrer": "", "submitted_at": "2026-01-01T12:00:00Z",
    }
    for q in c["perguntas"]:
        p["quiz_" + q["chave"]] = q["opcoes"][0]
    return p


def gerar_checklist(c, out):
    av = c["avatares"]
    linhas = [f"# Checklist na interface do GHL · {c['marca']}", "",
              "A API do GHL cria campos e tags (rode `ghl_setup.py`). O resto é na interface:", "",
              "- [ ] **Hospedar** `quiz.html` e as páginas (`" + "`, `".join(a['id'] + '.html' for a in av) + "`)",
              "      - opção A: Sites → Funis → etapa com elemento **Código/HTML** (um por página)",
              "      - opção B: qualquer hospedagem estática no seu domínio",
              "- [ ] Ajustar `paginas_base_url` no config se as páginas ficarem em outro endereço e rodar `gerar.py` de novo",
              "- [ ] **Automação → Fluxos de trabalho → + Criar fluxo**, gatilho **Webhook de entrada** (premium: pode cobrar por execução)",
              "- [ ] Copiar a URL do webhook pro `webhook_url` do config e rodar `gerar.py` de novo",
              "- [ ] `ghl_setup.py --webhook-teste URL` pra mandar 1 payload de exemplo e mapear os campos no gatilho",
              "- [ ] Ação **Criar/atualizar contato**: first_name, phone, email + campos quiz_* e utm_*",
              "- [ ] Ação **Adicionar tag**: `quiz:" + c['slug'] + "` e `quiz:avatar-{{quiz_avatar}}` (ou uma ação por ramo)",
              "- [ ] Ação **Criar oportunidade**: pipeline do quiz, etapa *Novo lead*",
              "- [ ] **Se/Senão** por `quiz_avatar` com um ramo por avatar:"]
    linhas += [f"      - [ ] `{a['id']}` → régua de WhatsApp de *{a['nome']}* (ver mensagens-whatsapp.md)" for a in av]
    linhas += ["- [ ] Em cada ramo: **Aguardar** com saída se o contato responder → tarefa pro vendedor",
               "- [ ] Pixel/Tag do Google no quiz e nas páginas (evento Lead já é disparado se o `fbq` existir)",
               "- [ ] Testar o quiz **uma vez por avatar** e conferir tag, campos, oportunidade, página e mensagem",
               "- [ ] Medir por avatar (filtro por tag `quiz:avatar-*`) e reescrever a página do avatar que não converte", "",
               "Alternativa sem webhook: monte o quiz nativo em **Sites → Questionários (Quizzes)**, mapeie as respostas",
               "nos campos `quiz_*` e use o gatilho de envio do questionário no fluxo. As páginas e as réguas continuam as mesmas."]
    (out / "CHECKLIST.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Gera quiz.html, páginas por avatar e réguas de WhatsApp.")
    ap.add_argument("--config", required=True, help="caminho do quiz.config.json")
    ap.add_argument("--out", default="saida", help="pasta de saída (padrão: saida/)")
    args = ap.parse_args()

    try:
        c = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        erro(f"não consegui ler o config: {e}")
    avisos = validar(c)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    gerar_quiz(c, out)
    gerar_paginas(c, out)
    gerar_mensagens(c, out)
    (out / "payload-exemplo.json").write_text(json.dumps(exemplo_payload(c), ensure_ascii=False, indent=2), encoding="utf-8")
    gerar_checklist(c, out)

    print(f"OK: {len(c['avatares'])} avatares → {out.resolve()}")
    for f in sorted(out.iterdir()):
        print("  ", f.name)
    if c.get("webhook_url", "").startswith("SEU_WEBHOOK"):
        print("\nAVISO: webhook_url ainda é placeholder. O quiz funciona, mas não envia o lead pro GHL.")
    for a in avisos:
        print("AVISO:", a)
    print(f"\nTeste local: cd {out} && python3 -m http.server 8080  →  http://localhost:8080/quiz.html")


if __name__ == "__main__":
    main()
