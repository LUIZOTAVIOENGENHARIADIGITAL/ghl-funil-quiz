---
name: quiz-ghl
description: Monta um Funil de Quiz de roteamento por avatar no GoHighLevel (GHL) — quiz mobile "com quem você trabalha?" que captura nome/WhatsApp antes do resultado, manda cada avatar pra uma página própria (dor, prova, objeção, oferta) ou direto pro WhatsApp com régua própria, e cria no GHL os campos personalizados e tags via API v2. Use quando o usuário pedir "/quiz-ghl", "funil de quiz", "quiz no GHL", "quiz por avatar", "segmentar público com quiz", "página por avatar", "quiz que manda pro WhatsApp" ou quiser parar de usar uma página generalista pra vários públicos.
---

# Funil de Quiz no GHL (roteamento por avatar)

Princípio: **quem vende pra todo mundo não vende pra ninguém.** O anúncio e a verba não mudam; entra um quiz no meio que identifica o avatar e manda cada um pra comunicação dele. O que faz converter NÃO é a pergunta: é a **página e a régua de cada avatar** (dor, prova, objeção próprias). Trocar só a headline não converte.

## Arquivos desta skill
- `templates/quiz.html` — quiz mobile, 1 pergunta por tela, barra de progresso, captura antes do resultado, UTM/fbclid/gclid ocultos, POST pro Webhook de entrada, redirect por avatar ou tela de WhatsApp.
- `templates/pagina-avatar.html` — template da página por avatar.
- `exemplos/quiz.config.json` — exemplo completo (imobiliária, 4 avatares). Use como molde do config.
- `scripts/gerar.py` — gera quiz.html, páginas, mensagens-whatsapp.md, payload-exemplo.json e CHECKLIST.md.
- `scripts/ghl_setup.py` — cria campos personalizados e tags pela API (`--dry-run`, `--webhook-teste`).

## Processo (siga na ordem)

### 1. Entrevista curta (no máximo 6 perguntas, numa mensagem só)
1. Qual o negócio e o produto/serviço?
2. Quem são os públicos que compram? (sugira 3 a 5; se vierem mais de 6, recomende começar com os 5 maiores)
3. Por que cada um compra? Qual a objeção nº 1 de cada um?
4. Tem depoimentos reais por público? (se não tiver, deixe placeholder `[DEPOIMENTO REAL ...]` — NUNCA invente depoimento)
5. Destino: página por avatar ou direto pro WhatsApp?
6. Já existe o fluxo com gatilho Webhook de entrada? (se sim, peça a URL; se não, use `SEU_WEBHOOK_AQUI`)

### 2. Escreva o `quiz.config.json`
- Copie a estrutura de `exemplos/quiz.config.json`.
- `pergunta_avatar`: a pergunta-roteador ("Antes de continuar, só me diz: com quem você trabalha?" / "Por que você quer comprar agora?").
- 2 `perguntas` extras no máximo: uma que revele a objeção/dor, uma de prazo ou capacidade. Quiz longo mata a conclusão.
- Para CADA avatar: headline com `{nome}` e `*destaque*`, 3 dores DELE, mecanismo, prova de alguém IGUAL a ele, objeção + resposta, oferta, CTA e régua `whatsapp.d0/d1/d3`. A d1 quebra a objeção. Variáveis: `{nome}`, `{link}` e `{chave_da_pergunta}`.
- Nichos regulados: saúde/medicina sem antes/depois e sem promessa de resultado; financeiro sem promessa de retorno.
- Mostre ao usuário a tabela avatar → dor → prova → objeção → CTA e peça OK antes de gerar.

### 3. Gere os arquivos
```bash
python3 ~/.claude/skills/quiz-ghl/scripts/gerar.py --config quiz.config.json --out saida/
```
Leia os AVISOS (placeholder de depoimento, avatares com corpo igual) e corrija. Depois sirva e teste cada avatar:
```bash
cd saida && python3 -m http.server 8080   # http://localhost:8080/quiz.html
```

### 4. Crie no GHL o que a API permite
Token só por variável de ambiente (`GHL_TOKEN` = Private Integration Token `pit-...`, `GHL_LOCATION_ID`). Nunca grave token em arquivo nem cole no chat de volta.
```bash
python3 ~/.claude/skills/quiz-ghl/scripts/ghl_setup.py --config quiz.config.json --dry-run
python3 ~/.claude/skills/quiz-ghl/scripts/ghl_setup.py --config quiz.config.json
```
Rode o real só depois de mostrar o dry-run e o usuário concordar. Cria: `quiz_nome`, `quiz_avatar`, `quiz_avatar_nome`, `quiz_respostas`, `quiz_pagina`, `quiz_<chave>` por pergunta, `utm_*`, `fbclid`, `gclid` e as tags `quiz:<slug>` + `quiz:avatar-<id>`. É idempotente.

API v2: `services.leadconnectorhq.com`, header `Version: 2021-07-28`. A API cria contatos, oportunidades, campos, tags, notas e tarefas, e LÊ pipelines/formulários/pesquisas. **Não cria** quiz, formulário, funil/página nem fluxo de trabalho: isso é na interface.

### 5. Entregue o checklist da interface
Mostre o `saida/CHECKLIST.md` e explique:
- Fluxo com gatilho **Webhook de entrada** (premium: pode cobrar por execução em alguns planos). Depois de colar a URL no config, rode `gerar.py` de novo e mande `ghl_setup.py --webhook-teste URL` pra mapear os campos.
- Criar/atualizar contato → tags → oportunidade → **Se/Senão** por `quiz_avatar` → régua de cada avatar (`mensagens-whatsapp.md`).
- Alternativa sem webhook: quiz nativo em Sites → Questionários (Quizzes), mapeando respostas nos campos `quiz_*`.
- Se o navegador bloquear o POST por CORS, mude `"modo_envio": "no-cors"` no config (envia como text/plain) ou ponha um intermediário (ex.: n8n) na frente.

### 6. Feche com o teste por avatar
Fazer o quiz uma vez por avatar e conferir: tag, campos, oportunidade, página certa, mensagem certa. Depois medir por tag `quiz:avatar-*` e reescrever a página do avatar que não converte (antes de desligar).

## Regras
- Nunca invente depoimento, número de resultado ou dado de cliente.
- Nunca grave token, telefone ou e-mail real nos arquivos gerados.
- Não chame a API sem dry-run aprovado.
- Avatares com página igual e headline trocada = falha. O `gerar.py` avisa; corrija antes de entregar.
