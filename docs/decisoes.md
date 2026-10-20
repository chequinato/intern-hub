# Registro de decisões do InternHub

O grupo não fez reuniões formais: a organização acontece pelo grupo de
WhatsApp, onde cada integrante avisa quando termina a própria parte (isso foi
declarado na Entrega 2). Este arquivo junta as **decisões** tomadas ao longo
do projeto, com data, motivo e quem decidiu.

Até 15/10/2026 ele foi montado a partir do histórico do Git e dos documentos
das entregas (refinamento, Entrega 1 e Entrega 2). Daqui em diante, cada
decisão nova entra aqui no mesmo dia, com o motivo.

Formato: **o que foi decidido**, por quê e quem decidiu. Quando a decisão
mudou depois, a linha nova diz o que mudou e aponta para a anterior.

---

## Fase 1 — Refinamento e Entrega 1 (até 14/09)

| Data | Decisão | Motivo | Quem |
|---|---|---|---|
| 09/09 | Biblioteca principal: **SQLAlchemy**. Alternativa descartada: guardar em arquivos `.json`. | O sistema vive de registros que se acumulam e precisam ser somados e filtrados por pessoa e período. Com `.json`, toda soma e todo filtro teriam de ser feitos na mão. | Grupo |
| 09/09 | O que **não** entra: integração com ponto real, mais de um contrato por estagiário, documento com valor legal, login com senha por pessoa. | Manter o escopo do tamanho de dois meses. A distinção estagiário/gestor fica num seletor de perfil. | Grupo |
| 09/09 | **API própria (FastAPI) cobrindo todo o sistema**; a interface só fala com o banco por HTTP. | Um único ponto de acesso ao banco e prática de rotas, verbos, payloads e status code. | Grupo (Miguel, líder técnico) |
| 09/09 | **Desenvolvimento em sequência**: cada dev começa quando o anterior subiu a parte dele (fundação → ponto e saldo → relatório → solicitações → assistente e exportações → segurança). | Evitar conflito de código entre seis pessoas; cada parte começa de uma base pronta. | Grupo |
| 09/09 | Parâmetros: alerta em −5h, crédito vence em 2 meses, almoço mínimo de 1h, limite legal de 6h/dia e 30h/semana (configurável). | Regra do negócio e Lei 11.788/2008; o limite fica configurável porque a lei permite 8h/40h em período sem aula. | Grupo |
| 09/09 | Segurança (token e limite de requisições) como **última fase**, com o Miguel. | Ela protege as rotas que todos constroem; só faz sentido com a API inteira de pé. | Grupo |

## Fase 2 — Até a Entrega 2 (até 04/10)

| Data | Decisão | Motivo | Quem |
|---|---|---|---|
| 15/09 | Criar as rotas de **gestores** e a de **vincular gestor ao estagiário**, que não estavam no plano. | Sem cadastrar gestor e vincular, a fila de aprovações ficava sempre vazia. | Pedro Henrique |
| 15/09 | Relatório passa a usar a **meta de cada estagiário** no saldo do dia. | Estava fixa em 6h no código, errado para quem tem outra meta. | Pedro Henrique |
| 22/09 | **Trocar a lib `slowapi` por um middleware próprio** de limite de requisições. | A `slowapi` não funcionou com a versão atual do FastAPI: o limite nunca disparava. | Miguel |
| 22/09 | **Trocar a interface de Streamlit para React.** | A API já era o único acesso ao banco, então trocar o cliente não mexeu em nenhuma rota; o React permite navegar por endereço e controlar o layout de cada tela. | Miguel |
| 04/10 | **Remover o Streamlit do repositório.** | Manter as duas interfaces deixaria o código incoerente com a arquitetura descrita na Entrega 2. | Miguel |
| 04/10 | Faltas do relatório só contam **a partir do primeiro ponto** do estagiário. | Defeito: quem começou no dia 28 aparecia com 20 faltas no mês. Virou teste. | Miguel |
| 04/10 | Aviso de limite semanal considera **só os dias até o registro**. | Defeito: quando a semana estourava 30h, até a segunda-feira aparecia "acima do limite". Virou teste. | Miguel |
| 04/10 | Limite de requisições sobe de **30 para 120 por minuto**. | Com o React, cada tela faz de 2 a 4 chamadas ao abrir, e 30/min dava erro 429 no uso normal. | Miguel |
| 04/10 | **Antecipar os testes de API** (planejados para a Entrega 3). | Provar que o protótipo roda de ponta a ponta. O comando `pytest` do README falhava e ganhou um `pytest.ini`. | Miguel |
| 04/10 | Token comparado em **tempo constante** e **CORS só para o frontend**. | O `!=` responde mais devagar quando o começo do token está certo; o CORS estava liberado para qualquer site. | Miguel |

## Fase 3 — Entrega 3 (a partir de 14/10)

| Data | Decisão | Motivo | Quem |
|---|---|---|---|
| 14/10 | Plano da Entrega 3 (seção 10 da Entrega 2): painéis do estagiário e do gestor, tendência do semestre, telas para o que a API já fazia (feriados, comprovante em PDF, editar meta), interface mais clara. | Boa parte do que o sistema calcula ficava escondida, e algumas rotas não tinham tela. Prioridade: melhorar o que existe antes de criar coisa nova. | Grupo (plano), Miguel (execução) |
| 14/10 | **Ponto em um clique**: cada marcação na hora em que acontece. | O modelo já previa preencher os horários ao longo do dia, mas só dava para lançar o dia inteiro de uma vez. | Miguel |
| 15/10 | **Assistente: de OpenAI para provedor configurável, com o Groq como padrão.** | A API da OpenAI não tem cota gratuita (precisa de cartão e crédito mínimo), então ninguém do grupo testava. O Groq é gratuito e usa a mesma biblioteca. | Miguel |
| 15/10 | Modelo padrão no Groq: **`openai/gpt-oss-120b`**. | O Llama que estava configurado saiu da lista do Groq (erro 404). Entre os disponíveis, foi o que respondeu melhor em português nos testes. | Miguel |
| 15/10 | **Visual grafite e laranja** e fonte SF Pro (Inter no Windows), com tela de entrada animada. Substitui o visual verde-petróleo de 14/10. | O visual anterior ainda parecia genérico. Foram comparadas três propostas e escolhida a "C". | Miguel |
| 15/10 | **Login com senha avaliado e mantido fora.** | Foi declarado fora do escopo na Entrega 1; mudar agora aumentaria o que cada um precisa explicar. A limitação está registrada no README. | Miguel |
| 15/10 | **Compensação de horas** (folga usando o crédito do banco) **avaliada e adiada.** | Não estava prometida; o foco ficou em fechar o que existe. | Miguel |
| 15/10 | **Modo demonstração do assistente**: sem chave, ele responde com os números do banco. | O enunciado pede um modo de demonstração para quem avaliar sem a chave da API. | Miguel |
| 15/10 | **Padronizar os módulos de feriado e relatório** (cabeçalho com dono, comentários, estilo). | Era o único trecho com estilo diferente do resto do código; prometido na Entrega 2. | Miguel |

## Fase 3b — Funcionalidades novas da Entrega 3 (17/10)

O sistema atendia as 23 funcionalidades do refinamento, mas o lado do
estagiário ficou pequeno (bater ponto, ver saldo, pedir ajuste). O grupo
decidiu enriquecer o sistema mantendo o foco no controle do estágio. Cada
item novo precisava de um motivo ligado a esse foco.

| Data | Decisão | Motivo | Quem |
|---|---|---|---|
| 17/10 | **Login com e-mail e senha.** Revoga a decisão de 09/09 ("sem login com senha") e a de 15/10 (login mantido fora). | Testando a Entrega 3, vimos que sem login qualquer pessoa entrava como gestor e aprovava os próprios ajustes, o que anula a regra principal do sistema. O token da API protegia as rotas, mas não dizia quem estava usando. | Miguel (com o grupo) |
| 17/10 | Senha guardada em **hash PBKDF2-SHA256 com sal** (biblioteca padrão `hashlib`), e o token do login também guardado só em hash. Mesma mensagem para e-mail inexistente e senha errada. Limite de 10 tentativas de login por minuto. | Nunca guardar senha em texto. Quem copiar o banco não consegue entrar; a tela de login não serve para descobrir quem tem conta; adivinhar senha fica impraticável. Sem lib nova para instalar. | Miguel |
| 17/10 | A chave da API (`API_TOKEN`) muda do header `Authorization` para **`X-API-Key`**. | O `Authorization` passou a levar o token do login. A chave identifica o aplicativo; o login identifica a pessoa. É a separação que a Entrega 1 já descrevia. | Miguel |
| 17/10 | **Regras de acesso:** o estagiário vê e altera só o que é dele; o gestor vê a própria equipe, mas não bate ponto nem abre pedido no lugar do estagiário; só o gestor responsável decide pedidos, muda a meta e desativa crachá. | Sem isso o login seria só uma tela: qualquer pessoa logada ainda acessaria os dados de todo mundo pela API. Há um teste que percorre todas as rotas e confere que exigem login. | Miguel |
| 17/10 | **A meta passa a ser alterada só pelo gestor.** A tela de Configurações do estagiário vira só leitura. | A meta é contratual. O estagiário que pudesse baixar a própria meta ganharia saldo sem trabalhar. | Miguel |
| 17/10 | **Só um gestor cadastra outro gestor** (o primeiro de um banco vazio se cadastra sozinho). | Se o cadastro de gestor fosse aberto, um estagiário criaria um "gestor" para aprovar os próprios ajustes. | Miguel |
| 17/10 | **Chamados ao gestor**, com conversa, prioridade e andamento que só vai para a frente. | Problemas que não são ponto (acesso bloqueado, equipamento, sistema fora do ar, documentos) não tinham canal. Segue o mesmo desenho das solicitações de ajuste (serviço levanta exceção, rota traduz em status). | Miguel |
| 17/10 | **Agenda com dia de prova: a meta e o limite do dia caem pela metade.** | Lei 11.788/2008, art. 10, § 2º: nos períodos de avaliação a carga horária do estágio é reduzida pelo menos à metade. O sistema cobrava a meta cheia em dia de prova. A agenda deixa de ser enfeite e passa a entrar no cálculo do saldo. | Miguel |
| 17/10 | **Google Agenda sem a API do Google:** link "adicionar ao Google Agenda" por compromisso e exportação `.ics`. Ler a agenda do Google fica de fora. | A integração completa exigiria OAuth com conta Google e uma chave de projeto: o professor não conseguiria testar numa máquina limpa e a apresentação dependeria de internet e de login no Google. O link e o `.ics` são formatos abertos que o próprio Google aceita. | Miguel |
| 17/10 | **Crachá virtual com QR code** e página pública de verificação. A página mostra só nome, gestor e situação; o crachá pode ser reemitido (o código antigo para de valer) e desativado pelo gestor. | Comprovar o vínculo de estágio na portaria, no RH ou na faculdade sem expor o banco de horas. O código é aleatório, então não dá para descobrir o crachá de outra pessoa trocando um número no endereço. QR em SVG com a lib `qrcode`, sem Pillow. | Miguel |
| 17/10 | As tabelas novas (conta, sessão, chamado, mensagem, compromisso, crachá) ficam **separadas**, sem coluna nova nas tabelas antigas. | O `create_all` cria tabelas que faltam, mas não acrescenta colunas. Assim quem já tem o banco não perde nada: `popular_demo.py` só cria as contas que faltam. | Miguel |

## Fase 3c — Contrato de estágio (20/10)

Até aqui o sistema controlava as **horas**. Faltava controlar o **estágio**
naquilo que a Lei 11.788/2008 exige da empresa. Os três itens abaixo foram
escolhidos justamente por terem a lei como motivo.

| Data | Decisão | Motivo | Quem |
|---|---|---|---|
| 20/10 | **Termo de compromisso** com início e fim, cadastrado pelo gestor; no máximo 2 anos, salvo pessoa com deficiência; aviso a 30 dias do fim. | Art. 11: o estágio na mesma empresa não pode passar de 2 anos. Sem a data de fim, ninguém percebia o contrato acabando. | Miguel (com o grupo) |
| 20/10 | **Recesso remunerado:** 2,5 dias por mês completo (30 por ano), pedido pelo estagiário e aprovado pelo gestor. Dia de recesso aprovado não conta como falta. | Art. 13: 30 dias de recesso por ano, proporcional quando o estágio tem menos de um ano. O relatório contava esses dias como falta. | Miguel |
| 20/10 | **Relatório de atividades semestral:** o estagiário registra, o gestor avalia e valida (o semestre fecha), o estagiário dá ciência; sai em PDF. | Art. 9º, VII: a empresa envia à faculdade, no mínimo a cada 6 meses, um relatório de atividades "com vista obrigatória ao estagiário". | Miguel |
| 20/10 | Tabelas novas (`termos_compromisso`, `pedidos_recesso`, `atividades_estagio`, `relatorios_atividades`), sem coluna nova nas antigas. | Mesmo motivo do crachá: o `create_all` não acrescenta colunas, e quem já tem o banco não perde nada. | Miguel |
| 20/10 | **Central de notificações** avaliada e deixada para depois. | Não tem base legal como os outros três; o grupo priorizou o que a lei exige. | Grupo |

## Pendente

- **Roteiro da apresentação** (15 minutos divididos por papel) e **documento
  da Entrega 3**: ficam para depois que o código estiver fechado, para não
  precisar refazer se algo mudar.
