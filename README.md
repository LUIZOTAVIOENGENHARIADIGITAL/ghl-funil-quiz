# ghl-funil-quiz

**Funil de Quiz por avatar no GoHighLevel, montado com o Claude Code.**

Você não muda o anúncio nem a verba. Só coloca um quiz no meio que pergunta *"antes de continuar, só me diz: com quem você trabalha?"* e manda cada público pra **página dele** (ou direto pro **WhatsApp** com a régua dele).

A conta que motiva tudo:

| | Página generalista | Quiz → página do avatar |
|---|---|---|
| Investimento / CPC no link | R$ 1.000 / R$ 1 | R$ 1.000 / R$ 1 |
| Cliques | 1.000 | 1.000 (≈900 respondem o quiz) |
| Conversão | 0,5% | 5% |
| Vendas ou leads | **5** (CAC R$ 200) | **45** (CAC ≈ R$ 22) |

> Quem vende pra todo mundo não vende pra ninguém. E o quiz só funciona se **cada avatar tiver a sua página de verdade**: dor, depoimento e objeção próprios. Trocar só a headline não converte.

> 📋 **Só quer os prompts?** Veja [PROMPTS.md](PROMPTS.md): um pra vibecodar o quiz no **AI Studio do GHL** e outro pra **Claude Code, Codex** ou qualquer agente local.

## Pra quem é

Aluno da **Comunidade GHL Brasil** (e qualquer pessoa que usa GoHighLevel) que atende mais de um público, ou vende o mesmo produto por motivos diferentes: imobiliária (sair do aluguel, primeira casa, investidor), revenda de veículos (família cresceu, 13º, promoção), clínica, serviços, infoproduto, agência.

## O que tem aqui

```
skills/quiz-ghl/
├── SKILL.md                    o processo que o Claude segue
├── templates/
│   ├── quiz.html               quiz mobile (1 pergunta por tela, progresso, captura antes do resultado)
│   └── pagina-avatar.html      página por avatar (dor, mecanismo, prova, objeção, oferta)
├── exemplos/quiz.config.json   exemplo completo: imobiliária com 4 avatares
└── scripts/
    ├── gerar.py                gera quiz, páginas, réguas de WhatsApp e checklist
    └── ghl_setup.py            cria campos personalizados e tags no GHL pela API (--dry-run)
```

Tudo em HTML puro e Python 3 só com biblioteca padrão. Nada pra instalar.

## Instalar a skill no Claude Code

```bash
git clone https://github.com/LUIZOTAVIOENGENHARIADIGITAL/ghl-funil-quiz
mkdir -p ~/.claude/skills
cp -r ghl-funil-quiz/skills/quiz-ghl ~/.claude/skills/
```

Abra o Claude Code e digite `/quiz-ghl` (ou peça "monta um funil de quiz no GHL").

## Como usar (exemplo de pedido)

```
/quiz-ghl
Tenho uma revenda de seminovos. Meus públicos: família que cresceu, quem vai usar
o 13º de entrada, quem foi promovido e quem quer chegar de carro novo no Natal.
Quero que o quiz mande pro WhatsApp com follow-up quebrando a objeção de cada um.
```

O Claude vai: fazer uma entrevista curta → escrever o `quiz.config.json` (e te mostrar a tabela avatar × dor × prova × objeção pra aprovar) → gerar os arquivos → criar campos e tags no GHL (depois do dry-run) → te entregar o checklist do que montar na interface.

### Sem o Claude (manual)

```bash
cd ~/.claude/skills/quiz-ghl
cp exemplos/quiz.config.json ~/meu-quiz.json        # edite os avatares
python3 scripts/gerar.py --config ~/meu-quiz.json --out ~/meu-quiz/
cd ~/meu-quiz && python3 -m http.server 8080       # abra http://localhost:8080/quiz.html

export GHL_TOKEN="pit-..."            # Configurações → Integrações Privadas
export GHL_LOCATION_ID="..."          # ID da subconta
python3 ~/.claude/skills/quiz-ghl/scripts/ghl_setup.py --config ~/meu-quiz.json --dry-run
python3 ~/.claude/skills/quiz-ghl/scripts/ghl_setup.py --config ~/meu-quiz.json
```

## O que a skill faz no GHL e o que fica manual

| Pela API (automático) | Na interface (manual) |
|---|---|
| Campos personalizados: `quiz_avatar`, `quiz_respostas`, `quiz_pagina`, `quiz_<pergunta>`, `utm_*`, `fbclid`, `gclid` | Hospedar o quiz e as páginas (Funis com elemento Código, ou seu domínio) |
| Tags `quiz:<slug>` e `quiz:avatar-<id>` | Fluxo de trabalho com gatilho **Webhook de entrada** |
| Payload de teste pro webhook (`--webhook-teste`) | Criar/atualizar contato, tags, oportunidade, **Se/Senão** por avatar |
| | Réguas de WhatsApp por avatar (texto pronto em `mensagens-whatsapp.md`) |

A API v2 do GHL **não cria** quiz, formulário, página/funil nem fluxo de trabalho. Por isso o checklist.

### Importante sobre o Webhook de entrada

- É um **gatilho premium**: em alguns planos cobra por execução. Confira no seu plano.
- **Alternativa sem webhook:** monte o quiz nativo em **Sites → Questionários (Quizzes)**, mapeie as respostas nos campos `quiz_*` e use o gatilho de envio do questionário. As páginas e as réguas geradas aqui continuam valendo.
- Mande **um envio de teste antes** de mapear os campos no gatilho (`ghl_setup.py --webhook-teste URL`).
- Se o navegador bloquear o envio por CORS, use `"modo_envio": "no-cors"` no config ou um intermediário (ex.: n8n) na frente.

### WhatsApp

As réguas usam a ação de enviar WhatsApp do GHL. Pra WhatsApp com API e disparo/ligação, use um **provedor de API de WhatsApp** (ex.: o que indicamos na Comunidade GHL Brasil). Em linha oficial, fora da janela de 24h, use modelos aprovados.

## O payload que o quiz envia

```json
{
  "first_name": "Ana", "phone": "+5511999999999", "email": "",
  "quiz_nome": "imob", "quiz_avatar": "sair-aluguel", "quiz_avatar_nome": "Sair do aluguel",
  "quiz_respostas": "Por que você quer comprar…? → Quero sair do aluguel | Quanto cabe…? → Até R$ 2 mil",
  "quiz_faixa": "Até R$ 2 mil", "quiz_prazo": "Em até 6 meses",
  "quiz_pagina": "https://seudominio.com.br/quiz/sair-aluguel.html?nome=Ana",
  "tags": "quiz:imob,quiz:avatar-sair-aluguel",
  "utm_source": "facebook", "utm_campaign": "quiz-imob", "fbclid": "…",
  "page_url": "…", "referrer": "…", "submitted_at": "2026-01-01T12:00:00Z"
}
```
(dados fictícios)

## Segurança

- Token **só** por variável de ambiente. Nenhum arquivo do repositório guarda token, telefone ou e-mail real.
- Os depoimentos do exemplo são placeholders: use depoimentos reais. Em saúde, respeite as regras do conselho (sem antes/depois, sem promessa de resultado).

## Comunidade

Feito pra **Comunidade GHL Brasil**, a comunidade de quem usa GoHighLevel no Brasil: aula teórica + aula prática deste funil, tutoria e templates.

## Licença

MIT © Luiz Otávio. Veja [LICENSE](LICENSE).
