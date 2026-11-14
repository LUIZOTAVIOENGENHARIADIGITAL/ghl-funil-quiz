# Prompts prontos: crie o seu Funil de Quiz

Dois caminhos. Escolha um, troque o que está entre `[COLCHETES]` e cole.

| Caminho | Onde roda | Pra quem |
|---|---|---|
| **1. AI Studio do GHL** | dentro da sua conta GoHighLevel (menu lateral → **AI Studio**) | quem não quer mexer com terminal |
| **2. Claude Code, Codex ou outro agente local** | no seu computador | quem quer o quiz em HTML próprio, as páginas por avatar e os campos/tags criados no GHL pela API |

Antes de qualquer um dos dois, faça o passo que ninguém faz: **liste os seus avatares**. Pra cada um, escreva a dor, uma prova (depoimento/case) e a objeção principal. De 3 a 5 avatares bem feitos valem mais que 16 mal feitos.

---

## 1. AI Studio do GHL (vibecode, sem terminal)

1. No GHL, abra **AI Studio** no menu lateral.
2. Na caixa **"Descreva o que deseja construir…"**, cole o prompt abaixo.
3. Ajuste conversando: *"deixa a pergunta 2 mais curta"*, *"troca a cor do botão"*.
4. Publique e teste **uma vez por avatar**.
5. Abra **Contatos** e confira se o lead caiu com nome, WhatsApp e o avatar. Se não caiu, peça no chat pra ligar o formulário ao CRM. Se ainda assim não cair, monte o quiz nativo em **Sites → Questionários** e use o AI Studio só pra página de cada avatar.

```text
Crie uma página de QUIZ para a minha empresa [SEU NEGÓCIO], mobile-first,
uma pergunta por tela, com barra de progresso.

Pergunta 1 (roteadora): "Com quem você trabalha hoje?"
Opções (cada uma é um avatar): [AVATAR 1], [AVATAR 2], [AVATAR 3], [AVATAR 4].

Pergunta 2: "Qual o seu maior desafio hoje?" (4 opções curtas)
Pergunta 3: "Qual o faturamento mensal da empresa?" (faixas)

ANTES de mostrar o resultado, peça nome, WhatsApp e e-mail e envie
tudo para o CRM desta conta como contato, guardando a resposta da
pergunta 1 (o avatar).

Resultado: uma tela diferente para cada avatar, com headline falando
a dor daquele avatar e um botão "Falar no WhatsApp".

Visual: fundo escuro, cor de destaque [SUA COR], texto direto, sem
enrolação. Em português do Brasil.
```

Depois, no GHL: **Automações → Fluxos de trabalho**, um workflow que aplica a tag do avatar (`quiz:avatar-<nome>`) e dispara a régua de WhatsApp de cada um com **Se/Senão**.

---

## 2. Claude Code, Codex ou qualquer agente local

### Com a skill deste repositório (Claude Code)

```bash
git clone https://github.com/LUIZOTAVIOENGENHARIADIGITAL/ghl-funil-quiz
mkdir -p ~/.claude/skills && cp -r ghl-funil-quiz/skills/quiz-ghl ~/.claude/skills/
```

```text
/quiz-ghl
Quero um funil de quiz para [SEU NEGÓCIO]. Avatares: [AVATAR 1], [AVATAR 2],
[AVATAR 3], [AVATAR 4]. Gere o quiz.html, uma página por avatar e a régua
de WhatsApp de cada um. Crie os campos e as tags no GHL (rode o dry-run
antes) e me dê o checklist do que eu monto na interface.
```

### Codex, Cursor, Gemini CLI ou outro agente

Clone o repositório, abra o agente dentro da pasta e cole:

```text
Leia skills/quiz-ghl/SKILL.md e siga esse processo, usando os templates e
scripts da pasta skills/quiz-ghl.

Meu negócio: [SEU NEGÓCIO]. Vendo [PRODUTO/SERVIÇO].
Avatares (cada um com dor, prova e objeção):
- [AVATAR 1]: dor [..], prova [..], objeção [..]
- [AVATAR 2]: dor [..], prova [..], objeção [..]
- [AVATAR 3]: dor [..], prova [..], objeção [..]

Quero:
1. quiz.html mobile: 1 pergunta por tela, barra de progresso, a primeira
   pergunta separa o avatar, captura de nome + WhatsApp ANTES do resultado,
   UTM/fbclid/gclid em campos ocultos.
2. Uma página por avatar (dor, mecanismo, prova, objeção, oferta). Não é
   só trocar a headline.
3. Régua de WhatsApp por avatar: D0, D+1 quebrando a objeção, D+3.
4. Campos personalizados e tags no GHL pela API v2, com o token na
   variável GHL_TOKEN e a subconta em GHL_LOCATION_ID. Rode com --dry-run
   primeiro e me mostre antes de criar.
5. Checklist do que eu preciso montar na interface do GHL (workflow com
   gatilho, Se/Senão por avatar, publicação das páginas).

Nunca escreva token, telefone ou e-mail real em arquivo.
```

### O que a API do GHL faz e o que fica manual

- **API v2 cria:** contatos, oportunidades, campos personalizados, tags.
- **Só na interface:** quiz/formulário nativo, páginas/funis e fluxos de trabalho.
- Pra mandar o lead do HTML próprio pro GHL, use o gatilho **Webhook de entrada** no workflow (gatilho premium: em alguns planos cobra por execução). Alternativa: o quiz nativo do GHL.

---

Feito pra **Comunidade GHL Brasil**. Licença MIT.
