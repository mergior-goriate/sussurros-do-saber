# Sussurros do Saber

<p align="center"><strong>Portal internacional de ciência, investigação e divulgação do conhecimento</strong><br>
<em>International portal for science, research and scientific communication</em></p>

<p align="center">
  <a href="https://www.sussurrosdosaber.com/"><img alt="Portal oficial" src="https://img.shields.io/badge/Portal-oficial-184E77"></a>
  <a href="https://www.sussurrosdosaber.com/noticias"><img alt="Notícias de Ciência" src="https://img.shields.io/badge/Not%C3%ADcias-Ci%C3%AAncia-184E77"></a>
  <a href="SECURITY.md"><img alt="Política de segurança" src="https://img.shields.io/badge/Seguran%C3%A7a-Pol%C3%ADtica-555555"></a>
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-3776AB">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-Web-000000">
</p>

<p align="center"><a href="#sobre-o-projecto">Português</a> · <a href="#english-overview">English</a> · <a href="#índice">Documentação técnica</a></p>

## Sobre o projecto

A **Sussurros do Saber** é uma iniciativa científica fundada em Moçambique por Mergior Goriate, com alcance internacional. O portal procura aproximar a investigação científica dos leitores, estudantes, docentes e investigadores, promovendo a comunicação rigorosa do conhecimento em português e inglês.

O repositório reúne o código da plataforma web, os recursos de publicação editorial, os testes e a documentação técnica.

### Áreas do portal

| Área | Finalidade |
| --- | --- |
| [Portal científico](https://www.sussurrosdosaber.com/) | Artigos de divulgação, investigação e comunicação científica |
| [SS News — Notícias de Ciência](https://www.sussurrosdosaber.com/noticias) · [English](https://www.sussurrosdosaber.com/en/news) | Notícias e reportagens sobre investigação científica |
| [Revistas e publicações científicas](https://www.sussurrosdosaber.com/revistas) | Publicações científicas, metadados bibliográficos e consulta de artigos |
| [Recursos educativos](https://www.sussurrosdosaber.com/recursos) | Ferramentas e materiais de apoio à aprendizagem |

### Princípios editoriais

- Rigor científico, transparência das fontes e distinção entre evidência e interpretação.
- Difusão internacional do conhecimento, com atenção à investigação realizada em África.
- Acesso gratuito aos artigos científicos e de divulgação, distinto dos conteúdos adicionais Premium.
- Respeito pela autoria, pela privacidade, pelos direitos de utilização de conteúdos e pela correcção de erros.

## English overview

**Sussurros do Saber** is a scientific initiative founded in Mozambique by Mergior Goriate, with an international outlook. It connects scientific research with readers, students, educators and researchers through science communication in Portuguese and English.

The platform includes science articles, [science news](https://www.sussurrosdosaber.com/en/news), scientific journals and publications, educational resources, author profiles, reader accounts and editorial submission and review workflows.

This repository contains the web application, tests and technical documentation. The application uses Python, Flask, SQLAlchemy, Jinja, Tailwind CSS and JavaScript. PostgreSQL, Redis and Docker support production deployment.

For development, consult the [setup guide](#instalação-e-desenvolvimento), [configuration](#configuração) and [testing guide](#testes-e-validação). Contributions can be proposed through [GitHub Issues](https://github.com/mergior-goriate/sussurros-do-saber/issues) or pull requests. Potential security vulnerabilities should be reported privately in accordance with the [security policy](SECURITY.md).

## Colaboração e segurança

- Para sugerir uma melhoria ou comunicar um problema não sensível, utilizar as [Issues do GitHub](https://github.com/mergior-goriate/sussurros-do-saber/issues).
- Para propor alterações ao código ou à documentação, preparar um pull request com a descrição da alteração e os testes realizados.
- Para comunicar vulnerabilidades, seguir a [política de segurança bilingue](SECURITY.md); não publicar credenciais, dados pessoais ou detalhes sensíveis numa issue pública.
- A visibilidade pública do repositório não constitui, por si só, uma licença de reutilização do código, dos logótipos ou dos conteúdos editoriais.

## Documentação técnica

As notas seguintes conservam o histórico técnico do projecto. As versões efectivas das dependências devem ser consultadas em [requirements.txt](requirements.txt), [package.json](package.json) e no ficheiro de lock correspondente. A situação dos serviços em produção depende da respectiva implantação e configuração.

**Notícias de Ciência:** secção bilingue em `/noticias` e `/en/news`, publicações independentes por idioma e fluxo editorial no painel. [Operação e implantação](docs/SCIENCE_NEWS.md).

**Métricas científicas:** recolha interna, painéis públicos/administrativos e adaptadores bibliográficos na migração `20261023_13`. [Implementação, operação, testes e limitações](docs/SCIENTIFIC_METRICS.md).

**Premium — pagamentos:** a migração `20261023_11` acrescenta ClicPay (M-Pesa, e-Mola e checkout de cartões), Stripe recorrente condicionado à elegibilidade, histórico privado, cancelamento, reconciliação e diário financeiro. As cobranças ficam desactivadas por omissão; os artigos científicos e informativos continuam gratuitos. Configuração, limites, testes e operação: [Pagamentos Premium](docs/PREMIUM_PAYMENTS.md). Os registos de alterações anteriores abaixo descrevem fases históricas.

Plataforma de divulgação científica e publicação editorial, com recursos bilingues, construída com Flask, SQLAlchemy, Jinja, Tailwind CSS e JavaScript. Reúne artigos, publicações científicas na área de revistas, perfis de autores, recursos educativos, contas de leitores e um fluxo privado de submissões.

**Entrega SMTP:** a revisão de limites usa o head `20261021_08`, aprovação e autorização separadas e contadores globais persistentes. Parar os trabalhadores antigos antes de actualizar. O procedimento actual está em [Limites e entrega](docs/NEWSLETTER_DELIVERY.md); as secções históricas abaixo descrevem também as revisões anteriores.

A documentação técnica histórica abaixo descreve a implementação revista em **20 de outubro de 2026**, com base no código do repositório. Documentar uma integração não comprova que as suas credenciais, serviços externos ou tarefas agendadas estejam activos no servidor. O README deve ser actualizado junto com alterações às funcionalidades.

## Capturas de ecrã

Imagens do [portal Sussurros do Saber](https://www.sussurrosdosaber.com/), captadas em 28 de Novembro de 2026.

### Página inicial

[![Página inicial em português — modo claro](docs/screenshots/home-pt.jpg)](https://www.sussurrosdosaber.com/)

| Versão em inglês | Modo escuro |
| --- | --- |
| [![Página inicial em inglês](docs/screenshots/home-en.jpg)](https://www.sussurrosdosaber.com/en/) | ![Página inicial em modo escuro](docs/screenshots/home-dark.jpg) |

### Outras páginas do portal

| SS News — Notícias de Ciência | Revistas científicas |
| --- | --- |
| [![Notícias de Ciência](docs/screenshots/news.jpg)](https://www.sussurrosdosaber.com/noticias) | [![Revistas científicas](docs/screenshots/journals.jpg)](https://www.sussurrosdosaber.com/revistas) |

## Índice

- [Capturas de ecrã](#capturas-de-ecrã)

- [Actualizações recentes](#actualizações-recentes)
- [Visão geral e arquitectura](#visão-geral-e-arquitectura)
- [Site público](#site-público)
- [Contas, favoritos e notificações](#contas-favoritos-e-notificações)
- [Revistas e artigos científicos](#revistas-e-artigos-científicos)
- [Painel administrativo](#painel-administrativo)
- [Equipa, funções e trabalho editorial](#equipa-funções-e-trabalho-editorial)
- [Remoções e histórico do fundador](#remoções-e-histórico-do-fundador)
- [Notificações internas unificadas](#notificações-internas-unificadas)
- [Submissões e produção editorial](#submissões-e-produção-editorial)
- [Conteúdo, imagens e vídeos](#conteúdo-imagens-e-vídeos)
- [Integrações](#integrações)
- [Dados e persistência](#dados-e-persistência)
- [Instalação e desenvolvimento](#instalação-e-desenvolvimento)
- [Configuração](#configuração)
- [Produção, manutenção e recuperação](#produção-manutenção-e-recuperação)
- [Segurança, privacidade e desempenho](#segurança-privacidade-e-desempenho)
- [Auditoria de 20/10/2026](#auditoria-de-20102026)
- [Testes e validação](#testes-e-validação)
- [Limites da implementação](#limites-da-implementação)
- [Inventário completo de rotas](#inventário-completo-de-rotas)

## Actualizações recentes

- **Premium — primeira fase (histórico):** página `/premium`, planos mensal/anual configuráveis, biblioteca de conteúdos adicionais e acessos de oferta com validade, geridos pelo administrador principal. Todos os artigos da revista e do portal continuam gratuitos. Pagamentos reais e renovação automática ainda não estão implementados. Migração `20261023_10`; [relatório, operação e plano de pagamentos](docs/PREMIUM.md).

- **Pesquisa científica e DOI:** a pesquisa existente inclui identificadores e palavras-chave; o catálogo de revistas pesquisa também títulos científicos e autores, com formulário GET na mesma barra. As ligações DOI usam um normalizador comum, sem alterar dados nem comprovar registo externo. Ver [âmbito, testes e limitações](docs/SCIENTIFIC_SEARCH.md).

As funcionalidades abaixo estão integradas na `main`; a sua disponibilidade em produção depende de um deploy bem-sucedido e da configuração dos serviços externos.

- **Compilação CSS:** Tailwind 4.3.3 com CLI própria, configuração em CSS e fontes de classes explícitas; Playwright 1.64.1. [Migração, compatibilidade de navegadores e limitações da validação](docs/TAILWIND4_MIGRATION_20261017.md).
- **Ícones de leitura:** ORCID, partilhas Bluesky/Reddit e seta da conta com representação local, utilizável mesmo quando a fonte externa de ícones falha.
- **Fila de revisão do portal:** a Área de trabalho mostra artigos atribuídos com parecer por entregar; reatribuição, revogação de permissão e fim do mandato retiram o acesso correspondente.

- **Equipa e governação:** colaboradores, contactos, convites registados, mandatos gerais ou de revista, 11 funções padrão e 24 permissões independentes; configurações personalizadas preservadas.
- **Trabalho editorial:** tarefas e comentários, documentos privados com aceite, revisão independente de artigos, atribuição de revisores científicos por versão e relatórios de actividade.
- **Remoções do fundador:** arquivo lógico de submissões, colaboradores, documentos e relatórios, confirmação, auditoria, histórico privado e reatribuição de responsabilidades.
- **Notificações unificadas:** sino e página com a mesma caixa por destinatário, contador, leitura individual/global, eliminação própria, persistência e deduplicação.
- **Interface administrativa:** Área de trabalho adaptada aos acessos; Equipa e convites, Funções e permissões, Histórico de remoções e Notificações internas em cartões responsivos; tipografia compacta, sino no topo, logótipo branco e barra lateral recolhível com ícones, preferência persistente e deslocamento interno. No telemóvel, cabeçalho de largura completa e menu horizontal com os últimos itens alcançáveis.
- **Correcções editoriais:** reatribuição de revisor exige nova revisão e cancela aprovação/agendamento; publicação programada gera auditoria e avisos; repetição do mesmo parecer não duplica a entrega.
- **Login administrativo:** recuperação de token CSRF expirado no login e no desafio de 2FA, preservando a verificação de credenciais e o segundo factor.
- **Segurança administrativa:** sessões associadas às credenciais e permissões atuais; alterações invalidam sessões anteriores. Desafios de 2FA expiram em cinco minutos, incluindo acesso às pré-visualizações.
- **PDF científico:** cabeçalho «Revista Científica Sussurros do Saber», nomes e ORCID sem descrições de autores no PDF, cache privado limitado, limites de pedidos e controlo de geração concorrente.
- **Operação e recuperação:** healthcheck com resposta 503 em falhas da base de dados, verificação de saúde no Docker, baseline Alembic histórica e ensaio de restauração PostgreSQL numa base isolada.
- **Fluxo de artigos:** estados «Em revisão» e «Aprovado para publicação», que permanecem privados até publicação; interface com cinco etapas, responsáveis, conteúdo recolhível, acções autorizadas e histórico de pareceres.
- **Formulários móveis:** criação/edição de artigos e revistas e políticas editoriais com grelhas que respeitam a largura disponível; ferramentas e tabelas deslocam-se nos seus próprios contentores, sem alargar a página.
- **GitHub Packages:** publicação de imagens Docker no GHCR a partir de Releases ou execução manual para uma tag existente.
- **Leitura e dispositivos móveis:** favoritos/notificações por conta em cartões responsivos, índice recolhível no telemóvel e aberto no computador, carregamento diferido de publicidade e fontes sem bloquear a apresentação.
- **Presença digital:** perfis Bluesky e Reddit no rodapé, botões de partilha nas páginas de artigos de divulgação e no cabeçalho dos artigos científicos, e meta tags de verificação Bing/Yandex.
- **Manutenção:** remoção de quatro ficheiros legados sem referências de runtime. A compilação actual usa Tailwind 4.3.3 e a CLI própria, conforme package-lock.json e a documentação da migração.

### Últimas alterações integradas

A revisão anterior do README já documentava equipa, funções, remoções e notificações até ao [PR #168](https://github.com/MergiorGoriate/sussurros-do-saber/pull/168). As alterações seguintes também estão integradas na `main`, conforme o estado dos PRs consultado em 8 de outubro de 2026:

| PR | Alteração |
| --- | --- |
| [#169](https://github.com/MergiorGoriate/sussurros-do-saber/pull/169) | Barra lateral móvel de largura completa, controlos separados e navegação horizontal nos estados expandido/recolhido |
| [#170](https://github.com/MergiorGoriate/sussurros-do-saber/pull/170) | Interface do Fluxo editorial com etapas, responsáveis, cartões, conteúdo recolhível e histórico |
| [#171](https://github.com/MergiorGoriate/sussurros-do-saber/pull/171) | Partilha de artigos de divulgação no Bluesky e Reddit, incluindo alternativa sem JavaScript |
| [#172](https://github.com/MergiorGoriate/sussurros-do-saber/pull/172) | Partilha no Bluesky e Reddit no cabeçalho dos artigos científicos, com grupo adaptado ao telemóvel |
| [#173](https://github.com/MergiorGoriate/sussurros-do-saber/pull/173) | Correcção da largura dos formulários de criação/edição de artigos, revistas e políticas editoriais |

Estes cinco PRs não exigem migrações adicionais. A integração no GitHub não confirma automaticamente que a mesma versão esteja em execução no Coolify.

## Visão geral e arquitectura

A aplicação renderiza páginas no servidor e acrescenta interacções no navegador. A base de dados guarda conteúdo, utilizadores e processos editoriais; Cloudinary guarda imagens e vídeos enviados pelo painel. Os anexos originais de submissões ficam privados na própria base de dados. Redis mantém os limites de utilização em produção. O assistente usa um Worker do Cloudflare através do backend Flask.

| Componente | Responsabilidade |
| --- | --- |
| `app.py` | Configuração Flask, páginas públicas, Markdown, SEO, APIs, PDF, cabeçalhos, inicialização e alterações leves do esquema |
| `governance.py` / `governance_models.py` | Equipa, funções, mandatos, tarefas, documentos, pareceres, fluxo de artigos, auditoria e remoções |
| `internal_notices.py` | Destinatários, eventos, deduplicação e revalidação de acesso aos avisos internos |
| `admin.py` | Autenticação administrativa, 2FA, gestão editorial, utilizadores, comentários e exportações |
| `models.py` | Artigos, autores, categorias, revistas, políticas, administradores, comentários, contactos e subscritores |
| `reader_accounts.py` | Sessão do leitor, favoritos por conta, biblioteca, acompanhamento e notificações |
| `google_auth.py` | Validação do login Google, associação de identidade e comando de migração |
| `submissions.py` / `submission_models.py` | Contas de investigadores, submissões, versões, decisões, produção e fila de e-mails |
| `submission_uploads.py` | Validação de anexos e conversão limitada de DOCX para Markdown |
| `journal_article.py` / `journal_metadata.py` | Campos científicos, ordem de apresentação e autores estruturados/ORCID |
| `journal_pdf.py` | Composição editorial de PDF, tabelas, imagens e gráficos |
| `pdf_cache.py` | Cache privado limitado e trava de geração PDF entre workers do mesmo contentor |
| `gunicorn.conf.py` | Pools de base de dados independentes após fork dos workers |
| `migrations/` / `alembic.ini` | Baseline histórica de esquema, criação ou validação da base |
| `scripts/restore_drill.py` | Ensaio de recuperação PostgreSQL numa base nova e isolada |
| `storage.py` | Validação e envio de imagens/vídeos para Cloudinary |
| `extensions.py` | Instância e armazenamento do limitador de pedidos |
| `editorial_content.py` | Conteúdo editorial inicial e compatibilidade com texto existente |
| `templates/` | Páginas públicas, painel, diálogos e submissões em Jinja |
| `static/js/` | Editores, contas, pesquisa, consentimento, partilha, ferramentas educativas e interfaces responsivas |
| `static/css/` | Estilos próprios e Tailwind compilado |
| `cloudflare-worker/worker.js` | Endpoint privado do assistente e chamada ao Workers AI |
| `tests/` | Testes Python e testes de navegador Playwright |
| `Dockerfile` | Compilação CSS e imagem de execução Python/Gunicorn |
| `.github/workflows/` | Testes, auditorias, recuperação PostgreSQL, construção Docker e publicação GHCR |

A execução de referência usa Python 3.11 e Node 22. As dependências efectivas estão em [requirements.txt](requirements.txt), [package.json](package.json) e `package-lock.json`; esses ficheiros são a fonte dos números de versão.

## Site público

### Início, artigos e autores

- A página inicial apresenta até 10 artigos publicados, ordenados por destaque e data, e até três revistas/publicações públicas recentes.
- O catálogo de artigos aceita `q`, `categoria` e `page`, com 12 resultados por página. A pesquisa consulta título, resumo, corpo, palavras-chave, DOI e nome/ORCID do autor; a categoria usa o nome normalizado.
- O artigo apresenta título, resumo, autor, categoria, data, tempo de leitura, capa/imagem ou vídeo, corpo Markdown, referências e metadados editoriais disponíveis.
- Os três artigos sugeridos dão prioridade à categoria do artigo aberto, ordenados por data e ID; quando faltam artigos do mesmo tema, completam com publicações recentes de outras categorias. O artigo aberto e conteúdos privados são excluídos; não existe motor de recomendação semântica.
- Ligações antigas por ID, incluindo `artigo-N`, redireccionam para o slug quando a publicação existe. Rascunhos e artigos programados ainda não publicados ficam fora das consultas públicas.
- Perfis de autores incluem os campos preenchidos: função, apresentação, formação, instituição, biografia, interesses, projectos, publicações, experiência editorial, fotografia e ligações académicas. A lista respeita activação/ordenação; o perfil reúne artigos publicados do autor.
- Ferramentas de leitura e partilha incluem guardar por conta, partilhar por WhatsApp, Facebook, X, LinkedIn, Telegram, Bluesky, Reddit ou e-mail e copiar a ligação. Alguns recursos usam APIs do navegador, como a área de transferência, com alternativa manual em caso de falha.

### Comentários, contacto e newsletter

Comentários exigem nome, e-mail e texto válido, token CSRF e campo anti-robô. São guardados para moderação; apenas aprovados aparecem publicamente, até 100 por artigo. O envio tem limite específico de cinco pedidos por hora. O nome admite 2–80 caracteres e o comentário 10–2000.

O formulário de contacto envia para `/api/contacto` e guarda a mensagem na base de dados. A equipa consulta e gere essas mensagens no painel. Guardar uma mensagem não equivale a encaminhá-la automaticamente por e-mail.

A página inicial apresenta «Artigos recentes» em vez de atribuir popularidade sem métricas. A área do boletim permite subscrever e apresenta a disponibilidade de envio segundo a configuração SMTP.

A newsletter reutiliza o cadastro de subscritores e a fila SMTP. O painel permite rever e preparar uma selecção de até cinco artigos da última semana completa; o comando preparar-boletim permite automatizar essa preparação. Cada edição é preparada uma vez por destinatário e inclui cancelamento de inscrição. A entrega usa enviar-notificacoes e exige SMTP seguro e tarefas agendadas no servidor. Ver [activação e operação do boletim](docs/NEWSLETTER.md). Os novos boletins incluem uma versão HTML responsiva com capas dos artigos, títulos, resumos e ligações de leitura, além da versão em texto simples. O conteúdo é guardado na preparação e o envio reutiliza o mesmo SMTP. A coluna opcional `EditorialNotification.html_body` é adicionada pela migração `20261020_05` ou pelo arranque com actualização automática activa; mensagens anteriores e a deduplicação são preservadas.

### Recursos educativos

- `/recursos`: ferramentas de estatística descritiva (N, média, mediana e intervalo mínimo–máximo), pequeno quiz de ciência, exploração de organelos, cálculo de diluição pela relação C₁V₁=C₂V₂, frequências de Hardy–Weinberg e cartões de estudo. Também há glossário pesquisável e gerador simples de referência a partir de autor, ano, título e revista; não é um gestor bibliográfico nem validador completo de normas.
- `/aprender`: catálogo educativo definido em `LEARNING_RESOURCES`, com pesquisa, filtros por tipo/tema e contador de resultados. `tipo` e `tema` também podem vir na URL.
- A colecção de recursos educativos e os cartões marcados como dominados usam `localStorage` do navegador; não são os favoritos editoriais por conta.
- `/laboratorio/osmose`: simulação ilustrativa com concentração externa, volume visual da célula, estados hipotónico/isotónico/hipertónico e botão de reinício. Não é um modelo quantitativo validado de transporte celular.
- `/api/recursos` expõe o catálogo educativo; não existe CRUD administrativo desse catálogo.

### Páginas institucionais e descoberta

O site contém Sobre, Contacto, Serviços, Edição científica, Termos e condições, Privacidade, Acessibilidade, Política de correcções, Políticas editoriais e Diretrizes para autores. As políticas editoriais e diretrizes aceitam conteúdo do painel; as restantes páginas usam os seus templates.

Há canonical, metadados de partilha, dados estruturados nas páginas aplicáveis, sitemap, robots, RSS de artigos e `ads.txt`. O RSS não é um feed completo de submissões/revistas. O sitemap reúne as páginas públicas previstas no código, artigos, autores e revistas publicados. O domínio canónico padrão é `https://www.sussurrosdosaber.com`; o domínio sem `www` recebe redireccionamento permanente 308, preservando caminho e parâmetros.

A existência de `ads.txt`, tags de verificação ou integração GTM não comprova aprovação comercial, indexação ou tráfego medido.

## Contas, favoritos e notificações

As contas públicas reutilizam `Researcher`, também usado nas submissões; são independentes das contas de administrador e dos perfis públicos de `Author`.

| Operação | Comportamento |
| --- | --- |
| Criar conta | Nome, e-mail e palavra-passe de 12–128 caracteres; e-mail de confirmação entra na fila SMTP |
| Entrar | E-mail/palavra-passe no diálogo do leitor ou página de submissões; sessão autenticada no servidor |
| Confirmar/recuperar | Ligações temporárias assinadas; confirmação e recuperação através das páginas de submissões |
| Guardar artigo | Relação `ReaderArticle` por conta e artigo publicado |
| Guardar revista/publicação | Preferência `saved` em `ReaderJournal` |
| Biblioteca | `/conta/biblioteca` mostra favoritos ainda públicos |
| Acompanhar | Preferência `following`; requer e-mail confirmado para activar |
| Notificações | Caixa persistente por destinatário, actualizações de artigos acompanhados, contador de avisos activos não lidos e cartões de acompanhamento |
| Marcar actualização lida | Reconhece a revisão efectivamente apresentada, sem reconhecer uma edição posterior |
| Importar favoritos antigos | Até 100 IDs/slugs por lote; navegador remove a cópia antiga só após confirmação de todos os lotes |
| Sair | POST de logout das submissões, com protecção CSRF |

A página de notificações reúne avisos internos e cartões de publicações acompanhadas. As actualizações de artigos acompanhados são materializadas por conta e revisão, sem duplicação; o utilizador pode ler ou eliminar o aviso sem apagar a publicação ou desactivar o acompanhamento. Estas notificações são internas ao site. Não há push nem e-mails de acompanhamento implementados. Os favoritos editoriais actuais não dependem apenas do armazenamento local.

### Login Google opcional

`GOOGLE_CLIENT_ID` activa Google Identity Services, botão de login e tentativa automática de apresentação do One Tap. O browser/FedCM pode suprimir a apresentação automática; o botão manual continua disponível.

O backend verifica assinatura, emissor, audiência, validade e nonce do ID token. A identidade é associada pelo identificador Google (`sub`); a associação por e-mail respeita as regras de autoridade/verificação e evita associar automaticamente contas antigas não verificadas ou e-mails externos sem confirmação adequada. A fotografia válida é usada na sessão, não como ficheiro permanente. Não se guarda o ID token, nem se pede palavra-passe do Google ou client secret.

Configuração e cenários de associação estão em [docs/google-login.md](docs/google-login.md). Registar as origens JavaScript exactas utilizadas no Google Cloud, incluindo a origem canónica. Sem client ID, continua disponível o login por palavra-passe.

## Revistas e artigos científicos

### Catálogo e leitura

`/revistas` mostra apenas registos publicados, com filtro imediato no navegador e pesquisa GET por título, área, resumo, autores, DOI, ORCID, palavras-chave e edição. Cada `/revistas/<slug>` apresenta a identidade da revista e o conteúdo científico disponível. Um registo `Journal` combina dados da revista com uma página de publicação; não há, neste momento, entidades relacionais independentes de volume, edição e artigo científico.

Os campos incluem nome/abreviatura, área, descrição, ISSN, periodicidade, edição actual, capa e texto alternativo, DOI, data de publicação, título científico, autores e ORCID, correspondente, resumo, palavras-chave, abstract e keywords.

O título científico explícito tem prioridade. Na compatibilidade com registos antigos, pode ser derivado do primeiro H1 do conteúdo ou do título da revista. Resumo e palavras-chave bilingues precedem o corpo; contribuição dos autores, agradecimentos, financiamento, conflitos, ética, consentimento e dados são apresentados quando preenchidos. Referências, notas, direitos, licença e histórico editorial são apresentados nas áreas correspondentes.

Autores estruturados admitem até 30 entradas, com nome/ORCID e descrição individual. O formato antigo `authors_orcid` continua a ser lido. No formulário de revista, o ORCID é normalizado e validado por formato; na submissão, também é verificado o dígito de controlo. Não existe consulta automática de perfis ORCID.

O índice é construído a partir das secções do conteúdo. No computador, o painel fica aberto por padrão; em ecrãs até 899 px, mantém o comportamento recolhível. O comportamento adapta-se ao redimensionamento, e no telemóvel há fecho ao seleccionar uma secção, clicar fora ou usar Escape. O diálogo de detalhes permite alternar informações e autores com teclado e devolve o foco ao fechar.

O botão de citação abre uma referência construída com autores, ano, título, revista, edição e DOI ou URL, com opção de copiar. É uma referência de apoio; conferir a norma bibliográfica exigida antes de a usar. A acção de proposta no cabeçalho encaminha ao contacto com assunto; o portal privado de submissões constitui um fluxo separado.

O cabeçalho científico inclui botões de partilha no Bluesky e Reddit. As ligações usam o título científico e a URL pública, codificados para o destino, com rótulos acessíveis e abertura em nova aba protegida por `noopener noreferrer`. No telemóvel, o grupo permite quebra de linha e alvos de toque de pelo menos 44 px. Os links funcionam sem JavaScript e abrem a composição no serviço externo; a publicação depende da confirmação do utilizador nesse serviço.

### PDF

O cabeçalho usa **Revista Científica Sussurros do Saber**. No bloco de autores, o PDF apresenta nomes e ligações ORCID; as descrições individuais continuam disponíveis na página do site.

O cache de geração é privado no servidor, com validade de 300 segundos, limite de 16 MiB por PDF e 64 MiB no conjunto. As respostas mantêm `Cache-Control: private, no-store`. Uma trava entre workers do mesmo contentor limita a geração concorrente: indisponibilidade temporária devolve 503 e `Retry-After: 5`; PDF acima do limite devolve 413. A chave inclui os dados da publicação, base de dados e versão de formato.

- Download público em `/revistas/<slug>/baixar.pdf`, apenas para publicações visíveis.
- Pré-visualização e PDF privados para administradores, incluindo rascunhos.
- Composição em A4 pelo ReportLab, com identidade editorial, metadados, autores, corpo, referências e numeração de páginas; não é simplesmente uma captura do HTML.
- O corpo começa em nova página na composição editorial prevista. Há suporte a parágrafos, cabeçalhos, listas, tabelas, imagens e gráficos SVG gerados pelo renderer, dentro das limitações de conversão.
- Imagens locais são limitadas à pasta estática; figuras de publicação respeitam visibilidade. Downloads externos limitam tamanho/tempo, validam redireccionamentos, portas e endereços públicos, para impedir acesso a redes privadas.
- Vídeos não se tornam vídeos reproduzíveis dentro do PDF. O resultado deve ser revisto editorialmente, sobretudo com tabelas extensas, fontes externas indisponíveis ou conteúdo muito longo.

## Painel administrativo

Entrada em `/admin/login`. O painel tem autenticação central, CSRF, verificação de sessão, ausência de cache privado e autenticação de dois factores. O resumo apresenta número de artigos, rascunhos, programados, contactos não lidos, subscritores activos e artigos actualizados recentemente.

| Área | Funções |
| --- | --- |
| Artigos | Criar, editar, eliminar, gerir slug, autor/categoria, resumo, corpo, referências, palavras-chave, DOI, capa/vídeo, destaque, tempo de leitura, estado e datas |
| Autores | Criar/editar perfis, ordem, activação, fotografia, biografia, formação, investigação e ligações académicas; eliminação sujeita às relações existentes |
| Categorias | Criar/editar nomes/slugs e eliminar respeitando artigos associados |
| Revistas | Criar/editar conteúdo e metadados, autores, capa, rascunho/publicação, pré-visualização HTML/PDF, ocultar e eliminar quando permitido |
| Políticas editoriais | Título/descrição, texto geral, diretrizes de autores/revisores, ética, uso de IA, dados, taxas e acesso aberto; pré-visualização Markdown |
| Comentários | Listar, aprovar/desaprovar e eliminar |
| Contactos | Consultar, marcar leitura no fluxo de consulta, eliminar e exportar CSV |
| Subscritores | Consultar, activar/desactivar e exportar CSV |
| Submissões | Filtrar processos, consultar versões/anexos, atribuir editor, decisões e notas, configurar revistas abertas e preparar publicação |
| Administradores | Superadministrador cria/edita/desactiva/elimina contas; salvaguardas de acesso e da própria conta |
| Segurança | Configuração TOTP para contas da base de dados e códigos de recuperação |
| Documentação | Instruções internas em `/admin/docs` |

### Estados e edição

Artigos de divulgação têm `draft`, `review`, `approved`, `published` e `scheduled`. «Em revisão» e «Aprovado para publicação» permanecem privados e não aparecem no sitemap nem no feed. A aprovação exige corpo suficiente, mas não publica automaticamente o artigo. Um artigo programado torna-se publicado ao chegar a data e ocorrer um pedido que execute a verificação, excepto pedidos excluídos como estáticos/health/robots/ads. **Não existe um agendador autónomo de publicação**. As datas internas usam UTC sem timezone; não assumir conversão automática do campo `datetime-local` para a hora local.

O editor fornece ferramentas Markdown, imagem/vídeo, gráficos, citações e pré-visualização. O HTML sanitizado no servidor é a referência final; a pré-visualização JavaScript não substitui a validação do servidor. Nas revistas, o botão de rascunho e a opção de publicação controlam visibilidade; não há programação temporal de revistas.

Limites relevantes: corpo de artigo/revista até 400000 caracteres, referências até 100000; campos científicos opcionais normalmente até 20000, palavras-chave científicas até 2000; políticas até 100000 por campo. O formulário de artigo valida título 5–240, resumo 10–2000, tempo de leitura 1–120 e exige autor/categoria e corpo suficiente para publicar/programar.

A eliminação de uma revista ligada a submissões ou configuração editorial é bloqueada; ocultar é a alternativa para retirar acesso público sem destruir o histórico. DOI e ISSN são metadados preenchidos pela equipa, não identificadores emitidos pelo site.

### Responsividade dos formulários

As páginas de criar/editar artigos, criar/editar revistas e editar políticas editoriais partilham o dimensionamento responsivo dos formulários. Os elementos das grelhas, campos nativos, cartões de autores e pré-visualizações podem encolher até à largura disponível. Em ecrãs até 850 px, o formulário e o espaço de edição de artigos usam uma coluna com `minmax(0,1fr)`.

A correcção evita que o tamanho mínimo intrínseco do conteúdo alargue o documento: o teste anterior reproduziu 605 px de página numa área útil de 375 px. A navegação, ferramentas, tabelas e blocos de código mantêm o deslocamento local quando necessário; o documento não deve ganhar deslocamento horizontal por causa do editor. CSS versionado no template permite carregar a versão alterada após deploy.

### Administradores e 2FA

O administrador principal pode ser definido por variáveis de ambiente; contas adicionais ficam em `AdminUser`. Em produção, a autenticação por ambiente exige hash da palavra-passe e segredo TOTP. `ADMIN_PASSWORD` em texto simples só é aceite no modo de desenvolvimento.

Contas administrativas na base de dados precisam concluir a configuração de 2FA antes de usar as áreas protegidas. A interface produz oito códigos de recuperação, guardados como hashes. A conta gerida por ambiente usa `ADMIN_TOTP_SECRET`; a configuração não é feita nesse formulário. A inactividade administrativa expira por padrão após 15 minutos, ajustável entre 1 e 120. Sessões e desafios são associados às credenciais/permissões atuais; alterações invalidam o acesso anterior. O desafio de 2FA expira em cinco minutos. Pré-visualizações HTML, Markdown e PDF exigem as mesmas protecções do painel. Ver [docs/security-hardening-20261006.md](docs/security-hardening-20261006.md).

## Equipa, funções e trabalho editorial

### Colaboradores e mandatos

**Equipa e convites** regista perfil, áreas, instituição, disponibilidade, estado, contactos e histórico de abordagem. O convite é um estado do membro; não há envio automático de convite externo. O fundador associa a conta administrativa e o perfil de autor, regista o aceite e cria/termina mandatos com função, datas e âmbito geral ou revista. O substituto indicado não herda acesso automaticamente.

As permissões efectivas são consultadas na próxima requisição: conta e membro activos, aceite, mandato vigente, revista, autoria/atribuição, conflitos e fase editorial. Múltiplos mandatos somam poderes **por permissão e dentro do seu âmbito**; atribuir na revista A e decidir na B não permite decidir na A. Recursos institucionais sem revista exigem mandato geral. Menus, formulários, rotas e APIs aplicam essas verificações. Conta inactiva ou remoção bloqueia sessões abertas. As funções personalizadas e os identificadores guardados são preservados; um identificador sem implementação não cria um poder novo.

### Catálogo de funções padrão

Os padrões abaixo vêm de `DEFAULT_ROLES`; as escolhas guardadas pelo fundador prevalecem. A base de produção pode conter outras funções personalizadas.

| Código | Nome | Permissões padrão |
| --- | --- | --- |
| `direction` | Direcção institucional | `team.manage`, `tasks.manage`, `reports.read`, `contacts.manage`, `subscribers.manage` |
| `coordination` | Coordenação do portal | `tasks.manage`, `reports.read`, `article.edit`, `authors.manage`, `categories.manage`, `comments.manage` |
| `chief_editor` | Editor científico principal | `manuscript.read`, `manuscript.edit`, `manuscript.assign`, `manuscript.decide`, `manuscript.production`, `submissions.configure`, `journal.manage`, `journal.publish`, `policies.manage`, `reports.read` |
| `associate_editor` | Editor associado | `manuscript.edit` |
| `reviewer` | Revisor científico | `manuscript.review` |
| `author` | Autor do portal | `article.write` |
| `portal_reviewer` | Revisor do portal | `article.review` |
| `portal_editor` | Editor do portal | `article.edit`, `article.approve` |
| `publisher` | Responsável de publicação | `article.publish` |
| `secretariat` | Secretariado editorial | `tasks.manage`, `manuscript.read` |
| `production` | Produção científica | `manuscript.production` |

### Catálogo das 24 permissões

| Identificador | Rótulo | Âmbito |
| --- | --- | --- |
| `team.manage` | Gerir equipa, convites e mandatos | Geral |
| `tasks.manage` | Distribuir tarefas | Geral |
| `reports.read` | Consultar relatórios e auditoria | Geral |
| `article.write` | Escrever artigos próprios | Geral |
| `article.edit` | Editar todos os artigos | Geral |
| `article.review` | Rever artigos atribuídos | Geral |
| `article.approve` | Aprovar artigos revistos | Geral |
| `article.publish` | Publicar artigos aprovados | Geral |
| `article.delete` | Eliminar artigos | Geral |
| `authors.manage` | Gerir autores | Geral |
| `categories.manage` | Gerir categorias | Geral |
| `journal.manage` | Gerir revistas | Revista ou geral |
| `journal.publish` | Publicar revistas | Revista ou geral |
| `manuscript.read` | Consultar submissões da revista | Revista ou geral |
| `manuscript.edit` | Tratar submissões atribuídas | Revista ou geral |
| `manuscript.assign` | Atribuir editores e revisores | Revista ou geral |
| `manuscript.decide` | Emitir decisões científicas | Revista ou geral |
| `manuscript.production` | Preparar artigos científicos | Revista ou geral |
| `manuscript.review` | Emitir pareceres atribuídos | Revista ou geral |
| `submissions.configure` | Configurar submissões | Revista ou geral |
| `policies.manage` | Gerir políticas editoriais | Geral |
| `comments.manage` | Moderar comentários | Geral |
| `contacts.manage` | Gerir contactos | Geral |
| `subscribers.manage` | Gerir subscritores | Geral |

Consultar [a matriz completa de interfaces, rotas e acções](docs/PERMISSIONS_AUDIT.md). Consultar, editar, rever, aprovar, publicar e eliminar continuam poderes separados. «Gerir subscritores» não significa gerir submissões; não existe `submissions.manage`. Alterar funções, ligar contas, atribuir/terminar mandatos e as remoções especiais continuam reservados ao fundador.

### Área de trabalho, tarefas e documentos

- **Área de trabalho:** mostra responsabilidades, tarefas, prazos, documentos e acessos efectivos. «Distribuir tarefas» leva ao formulário de atribuição para quem tem `tasks.manage`.
- **Tarefas:** responsável, título, descrição e prazo; estados Pendente, Em curso, Bloqueada, Concluída e Cancelada; comentários e reatribuição. O colaborador conserva a actualização das próprias tarefas com mandato válido; o gestor acompanha as tarefas autorizadas.
- **Documentos da equipa:** texto e anexos PDF/DOCX/TXT validados, até 8 MB; acesso privado ao destinatário/gestor autorizado. O aceite guarda utilizador e data da versão documental; não é assinatura digital certificada.
- **Relatórios e auditoria:** actividade, tarefas concluídas/atrasadas e pareceres por membro; últimos 200 eventos apresentados. Relatórios guardados preservam uma fotografia de até 1.000 eventos, separada dos eventos originais.
- **Lembretes:** agendar `flask --app app notificar-prazos-equipa` diariamente num único worker para tarefas, pareceres e fim de mandato. É idempotente e interno; não funciona como cron autónomo nem envia e-mails.

### Revisão independente e avaliação científica

O **Fluxo editorial** do artigo de divulgação distingue rascunho, submissão, revisão, correcções, aprovação, programação e publicação. Exige perfil de autor associado, revisor diferente do autor e aprovador diferente do autor/revisor. A aprovação não publica. Publicar ou programar exige aprovação registada; o responsável de publicação não ganha edição do texto. Alterar conteúdo aprovado exige reabertura e nova revisão. Reatribuir o revisor cancela aprovação/programação e preserva o parecer anterior. Artigos legados sem fluxo mantêm compatibilidade; artigos com pareceres não podem ser simplesmente eliminados.

Na submissão científica, o detalhe contém atribuição de editor e acesso à atribuição de revisores. **Meus pareceres** apresenta os convites próprios por versão: aceitar, recusar, declarar conflito e entregar recomendação fundamentada. Ficheiros só ficam acessíveis após aceite, com mandato válido, versão corrente e fase autorizada. O parecer não decide automaticamente o manuscrito. Decidir, preparar o rascunho científico e publicar continuam operações distintas, limitadas à revista de origem. Esta revisão permite autoria identificável; não promete avaliação cega.

### Interface administrativa

Cartões e indicadores em Equipa e convites, Funções e permissões, Histórico de remoções e Notificações internas; formulários agrupados, foco visível e disposição adaptada a computador/telemóvel. A barra lateral recolhe e expande pelo botão, mantém apenas os ícones quando recolhida e guarda a preferência no navegador. A navegação usa deslocamento interno, com espaço para os ícones e sem barra exterior duplicada. A tipografia foi reduzida e o sino reposicionado no topo. A aparência da barra de deslocamento depende também do sistema/navegador. O logótipo administrativo aparece em branco sobre o fundo azul, preservando o símbolo e a transparência, também com a barra recolhida e no telemóvel.

No telemóvel (até 850 px), o cabeçalho administrativo ocupa a largura útil disponível. A marca reserva espaço para Recolher/Expandir e Sair; a linha do menu desloca-se horizontalmente. No estado recolhido, os links ficam representados por ícones em alvos de 48 px, com nomes acessíveis. A mudança de largura entre computador e telemóvel preserva a escolha guardada. A scrollbar fina não deve cortar os ícones nem impedir o acesso ao último item.

### Fluxo editorial do portal

A página `/admin/fluxo-artigos/<ident>` apresenta o processo dos artigos de divulgação em cinco etapas visuais: **Preparação, Submissão, Revisão, Aprovação e Publicação**. A etapa actual usa `aria-current="step"`; os estados internos continuam a distinguir rascunho, submissão, correcções, revisão, aprovação, programação e publicação.

- Cartão inicial com título, estado, autor, revisor independente e responsável pela aprovação; atribuições em falta aparecem como «Por atribuir».
- Mensagens específicas para correcções solicitadas, revisão concluída à espera de aprovação e publicação programada com data UTC.
- Resumo visível e corpo do artigo recolhível em «Ler conteúdo».
- Área «Acções disponíveis» com formulários segundo a etapa, atribuição e permissões: submeter, atribuir revisor, emitir parecer, solicitar correcções, aprovar e publicar/programar quando autorizados.
- Histórico de pareceres com identificação do responsável, data e rótulos de estado.
- Conteúdo/acções em duas colunas no computador e uma em ecrãs até 1000 px; etapas e responsáveis reorganizam-se em ecrãs menores, com foco visível e alvos de toque.

A alteração da interface preserva as rotas, condições de autorização e tokens CSRF. Revisão, aprovação e publicação continuam operações independentes. O indicador de etapas não concede acesso nem substitui a autorização no servidor. Este processo é distinto das sete etapas de preparação das submissões científicas descritas adiante.

## Remoções e histórico do fundador

As quatro operações abaixo exigem o mecanismo existente de identificação do fundador, sessão válida, 2FA e POST com CSRF. Permissões gerais de gestão não as concedem. A confirmação identifica o item e consequências; Cancelar/GET não altera dados. A operação lógica e a auditoria são persistidas juntas; repetir a mesma remoção não duplica o evento.

| Operação | Acesso | Preservação |
| --- | --- | --- |
| Eliminar submissão | Lista e detalhe | Retira dos fluxos activos e bloqueia novas acções; conserva versões, anexos, pareceres, decisões, publicação e DOI |
| Remover colaborador | Equipa e convites | Termina acesso e mandatos, encerra convite associado e invalida sessão na próxima requisição; conserva conta pública independente, autoria, artigos e pareceres; bloqueia remoção do fundador |
| Eliminar documento | Documentos da equipa, com ou sem anexo | Impede novos aceites e retira das listas activas; conserva texto, versão, anexo, datas e aceites anteriores |
| Eliminar relatório | Relatórios guardados | Arquiva só a fotografia individual; conserva todos os eventos de auditoria de origem |

**Histórico de remoções** é exclusivo do fundador, com consulta e downloads preservados quando aplicável. **Responsabilidades** identifica tarefas, submissões, pareceres em curso e artigos pendentes do colaborador. A reatribuição valida mandato, revista e conflitos, preserva autoria e histórico; parecer em curso é cancelado e substituído por nova atribuição. Parecer já entregue e artigo publicado não são reatribuídos por esse fluxo. Não há eliminação automática de ficheiros partilhados ou artigos publicados. Ver [o guia de remoções](docs/LIFECYCLE_NOTIFICATIONS.md).

## Notificações internas unificadas

`StaffNotice` é a caixa persistente por destinatário; não é a fila SMTP `EditorialNotification`. O sino e a página administrativa consultam os mesmos dados. Investigadores têm caixa própria; leitores recebem também actualizações dos artigos acompanhados. Não há novos canais de e-mail, WhatsApp ou push.

| Eventos | Destinatários, conforme acesso vigente |
| --- | --- |
| Convites, estado, funções e mandatos | Membro associado e responsáveis institucionais relevantes |
| Atribuição/reatribuição, comentário e estado de tarefa | Responsável e gestores autorizados; anterior responsável quando elegível |
| Documento disponibilizado, aceite e remoção | Destinatário e responsáveis autorizados conforme evento |
| Submissão/versão, editor, parecer, decisão e produção | Intervenientes científicos no âmbito da revista, sem expor notas/pareceres ao autor |
| Submissão, revisão, aprovação, programação/publicação de artigo | Responsáveis do fluxo com mandato e destinatários da fase |
| Relatório e remoções | Fundador e intervenientes autorizados conforme recurso |
| Actualização de artigo acompanhado | Leitor verificado que acompanha publicação pública |

Avisos são criados na transacção da operação e só persistem após sucesso, com chave única por evento/destinatário. Não há recriação retroactiva de avisos antigos nem ressurreição de avisos eliminados. Múltiplos mandatos não duplicam o destinatário. Descrição e ligação respeitam o acesso; abrir revalida autorização e apresenta indisponibilidade quando o recurso foi removido ou o acesso revogado.

- Ordem recente primeiro; título, descrição, data e ligação quando disponível.
- Sino com cinco avisos recentes; página paginada com 30; contador de todos os avisos activos não lidos.
- Ler individualmente, ler todos e eliminar aviso próprio pela barra/página, por POST com CSRF. Eliminação lógica afecta só o destinatário, persiste após voltar a entrar e não apaga o recurso ou avisos alheios; repetição é idempotente.
- Actualização ao abrir e a cada 60 segundos numa aba visível, sem pedidos sobrepostos; barra/página sincronizam o resumo.
- Estados vazio/carregamento/erro, indicação acessível do contador, foco e adaptação móvel; formulários funcionam sem JavaScript.
- Avisos de artigos ocultados/acompanhamentos desactivados ficam fora da caixa pública. Apagar aviso não desactiva acompanhamento; nova revisão pode gerar outro aviso.

Regras completas de destinatários e limites: [docs/LIFECYCLE_NOTIFICATIONS.md](docs/LIFECYCLE_NOTIFICATIONS.md).

## Submissões e produção editorial

### Acesso e configuração

O portal `/submissoes` é privado. O autor entra com a conta pública/investigador e confirma o e-mail para as operações que o exigem. Um utilizador não ganha acesso administrativo por ser autor ou por ter uma associação de revisão na base.

Em `/admin/submissoes/configuracao`, a equipa abre/fecha submissões por revista, define tipos de artigo, formatos principais e e-mail editorial. Só revistas habilitadas aceitam novos processos. As directrizes e políticas usadas no formulário são as páginas editoriais do site.

### As sete etapas

1. Revista e tipo: seleccionar revista aberta, tipo autorizado, área e idioma.
2. Autores: 1–30 autores, nome/e-mail, ORCID, afiliação, departamento, instituição, cidade/país e exactamente um correspondente.
3. Informações: título, resumo/palavras-chave, abstract/keywords, comentários ao editor e detalhes científicos opcionais.
4. Ficheiros: exactamente um manuscrito principal por versão; figuras, tabelas, suplementos, dados e outros documentos em categorias separadas.
5. Declarações: originalidade, exclusividade, acordo de autores, aceitação de políticas e diretrizes; conflitos, financiamento, ética, consentimento e dados com aplicabilidade/justificação.
6. Revisão: conferir informação e anexos antes da finalização.
7. Submissão: validação completa, código do processo, versão finalizada e confirmação na fila de e-mails.

Pode guardar rascunhos, retomar o processo e consultar o histórico. Há no máximo 20 rascunhos por conta. A confirmação usa bloqueio/validação no servidor e preserva um snapshot da versão; repetir o envio não deve criar uma nova submissão independente. Versões finalizadas não são editadas como rascunhos. Quando a equipa pede revisão, o autor envia uma nova versão e resposta ao editor, conservando as anteriores.

### Estados editoriais

| Estado | Próximas operações editoriais previstas |
| --- | --- |
| Rascunho (`draft`) | Autor completa/confirma; não aparece como processo editorial submetido |
| Submetido (`submitted`) | Triagem ou rejeição |
| Triagem (`screening`) | Revisão, pedido de revisões, aceitação ou rejeição |
| Em revisão (`review`) | Pedido de revisões, aceitação ou rejeição |
| Revisões solicitadas (`revision_requested`) | Autor envia versão revista; equipa pode rejeitar |
| Manuscrito revisto (`revised`) | Reavaliação, revisão, aceitação ou rejeição |
| Reavaliação (`reevaluation`) | Revisão, pedido de revisões, aceitação ou rejeição |
| Aceite (`accepted`) | Preparar publicação, criando rascunho separado |
| Produção (`production`) | Conferir/editar rascunho e publicar |
| Publicado (`published`) | Ocultar publicação regressa o processo à produção |
| Rejeitado (`rejected`) | Sem transição normal de reabertura na interface |

Decisões exigem observação e respeitam a tabela de transições no servidor. Existem atribuição de editor e notas internas. Eventos guardam actor, acção, estado anterior/novo, nota, data e visibilidade para o autor. Notas internas não são expostas ao autor. Confirmações e decisões são notificações transaccionais, distintas das notificações de acompanhamento do leitor.

A avaliação científica usa `StaffPeerReview`, com convite por versão, aceite, conflitos e parecer fundamentado. `ReviewAssignment` permanece como estrutura legada; não é o mecanismo activo de pareceres. Os originais podem identificar os autores: não existe garantia de anonimização nem revisão duplamente cega.

### Anexos privados

| Limite | Valor |
| --- | --- |
| Ficheiro individual | 8 MiB |
| Ficheiros por versão | 25 |
| Total de anexos por conta | 100 MiB |
| Formatos suportados | DOCX, XLSX, PDF, PNG, JPG/JPEG, CSV e TXT; principal sujeito à configuração da revista |
| PDF | Não cifrado, 1–500 páginas, sem conteúdo activo detectado |
| Arquivo Office | Até 1500 entradas e 32 MiB descomprimidos |
| Imagem de submissão | Até 20 milhões de pixels, formato real verificado |

São verificados extensão, MIME, assinatura/estrutura, limites e conteúdo inválido. Office com macros, ActiveX, objectos incorporados executáveis, entidades XML ou relações externas não permitidas é rejeitado; hyperlinks normais HTTP/HTTPS/mailto podem ser aceites. PDF com JavaScript/acções proibidas, cifrado ou corrompido é rejeitado. Texto usa UTF-8 e rejeita caracteres de controlo proibidos. Estas verificações não são um antivírus.

Os payloads ficam em `ManuscriptFile` com nome interno, MIME, tamanho e SHA-256, fora de `/static` e do Cloudinary. Download exige propriedade da submissão ou acesso editorial. O backup da base deve incluir esses binários.

### Da aceitação à publicação

“Preparar publicação” cria um **novo registo Journal em rascunho** e mantém a revista de origem. Copia metadados, autores, declarações e histórico; não torna os anexos originais públicos.

DOCX permite importação limitada de texto, tabelas e imagens bitmap; TXT permite importação de texto. PDF não é convertido automaticamente para artigo: a equipa insere/revê o conteúdo. Conteúdo científico fornecido nos campos próprios pode completar/substituir a importação. Figuras são copiadas e sanitizadas para `PublicationAsset`; só ficam públicas quando a publicação está visível. Ao ocultar, voltam a exigir acesso editorial. Rever sempre o resultado antes de publicar.

## Conteúdo, imagens e vídeos

### Markdown e directivas

O servidor usa Python Markdown com extensões `extra`/`sane_lists`, sanitização Bleach e ligações automáticas de URLs em texto apropriado. Links, imagens, tabelas, listas, referências e formatação devem respeitar o conjunto permitido; scripts e HTML perigoso não são conteúdo editorial aceite.

```markdown
## Secção do artigo

Texto com **ênfase**, [fonte](https://example.org) e uma imagem:

![Descrição acessível](https://example.org/figura.jpg)

[video: Título do vídeo](https://www.youtube.com/watch?v=IDENTIFICADOR)

[chart: bar|Comparação|Grupo A=10;Grupo B=20]

[portrait: Texto alternativo|Legenda|Crédito](https://example.org/retrato.jpg)

[destaque: Texto da citação|Autor]

[capitular] Primeiro parágrafo com capitular.
```

Gráficos admitem `bar`, `line` e `pie`, até 12 pontos numéricos finitos não negativos e dados com valor positivo. São gerados como SVG; não consultam dados externos. Vídeos aceitam YouTube (incorporação com domínio de privacidade), Vimeo e ligações directas HTTP/HTTPS MP4, WebM ou OGG reconhecidas. As directivas têm sintaxe própria; testar a apresentação final no artigo e, se aplicável, no PDF. A capitular usa o marcador `[capitular]` no início do parágrafo, também nas traduções: o serviço preserva-o automaticamente. Versões antigas que contêm `[drop cap]`, `[drop_cap]`, `[dropcap]`, `[drop-cap]` ou `[letra capitular]` são apresentadas com a mesma tipografia em todo o portal, sem alterar o texto guardado. A mesma lista de variantes é usada pelo renderizador, pelo tradutor e pelos editores.

### Uploads do painel

Imagens públicas passam por Pillow: até 8 MiB e 40 milhões de pixels, validação do formato, redimensionamento e conversão WebP. Limites de enquadramento: artigos 2000×2000, fotografias 800×800 e capas de revista 1600×2200. O URL seguro devolvido pelo Cloudinary é guardado na base. Há optimização de URLs Cloudinary e fallback visual para imagens indisponíveis.

Vídeos enviados pelo painel admitem até 50 MiB, extensões MP4/WebM/OGG e assinatura inicial correspondente. Cloudinary recebe recurso de vídeo e devolve URL seguro, com pedido de saída MP4. A validação local de assinatura não confirma todo o codec/conteúdo do vídeo; verificar reprodução após upload. O limite global do pedido Flask é 60 MiB, incluindo o formulário multipart.

URLs já alojados podem ser usados nos campos compatíveis sem novo upload. Imagens externas continuam dependentes do servidor de origem. Os nomes de pasta Cloudinary são configuráveis; nunca colocar API secret no JavaScript ou no README.

## Integrações

### Assistente científico

O navegador envia pergunta a `POST /api/assistente`; Flask valida 1–800 caracteres, aplica limites de cinco pedidos/minuto e vinte/hora e chama o Worker com `X-Assistant-Key`. O Worker só aceita POST e o segredo correcto, usa binding `AI` e o modelo configurado no código `@cf/meta/llama-3.1-8b-instruct-fast`, com resposta em português e limite de 500 tokens de saída.

Configurar `ASSISTANT_WORKER_URL` e o mesmo `ASSISTANT_SHARED_KEY` na aplicação e nos Secrets do Worker; disponibilizar binding Workers AI chamado `AI` e publicar `cloudflare-worker/worker.js`. O browser não recebe o segredo. Falhas do modelo/Worker são devolvidas como indisponibilidade; não há pesquisa automática de fontes, memória persistente de conversa ou RAG implementados. O ficheiro [cloudflare-worker/README.md](cloudflare-worker/README.md) ainda contém referências históricas ao Render; usar o ambiente actual da aplicação no Coolify para essas variáveis.

### SMTP e e-mails transaccionais

Registo, recuperação, confirmação de submissão e decisões colocam mensagens em `EditorialNotification`. Para entrega, configurar SMTP e executar periodicamente **um único worker**:

```bash
flask --app app enviar-notificacoes --limit 50
```

Agendar, por exemplo, a cada minuto, no ambiente com a mesma base e segredos. O comando aceita limite 1–500, conserva mensagens pendentes, regista tentativas e usa Message-ID estável. TLS ou SSL é obrigatório fora dos testes, com validação do certificado e do nome do servidor. As mensagens aceites são confirmadas na base antes de fechar a ligação SMTP, para uma falha no QUIT não as colocar novamente na fila. Uma falha entre entrega SMTP e commit pode causar duplicação na tentativa seguinte; o Message-ID não garante entrega exactamente uma vez. Sem a tarefa SMTP, as mensagens ficam na fila.

### Analytics, consentimento e redes sociais

A interface gere escolhas de cookies necessários, analytics e publicidade, persiste consentimento `cookie_consent_v3` durante 180 dias e actualiza consentimento Google. Scripts opcionais seguem as escolhas previstas no código. GTM e verificação Search Console são configuráveis; atribuir os IDs da instalação efectiva. O tema claro/escuro usa `sessionStorage`, enquanto a colecção educativa usa `localStorage`.

As ligações de Facebook, Instagram, YouTube, LinkedIn, X e WhatsApp podem ser definidas por ambiente. O rodapé inclui também [Bluesky](https://bsky.app/profile/sussurrosdosaber.com) e [Reddit](https://www.reddit.com/user/sussurrosdosaber/), definidos no template partilhado. A configuração de consentimento não substitui a revisão das políticas publicadas e dos scripts configurados no GTM.

Os botões de partilha do Bluesky e Reddit são independentes dos links de perfil do rodapé: os primeiros preparam uma publicação com título/URL; os segundos abrem os perfis do portal. O script de partilha dos artigos mantém esses destinos e o template oferece links nativos como alternativa sem JavaScript. Não há publicação automática, integração com credenciais destas redes ou envio de conteúdo sem confirmação no destino.

## Dados e persistência

| Modelo | Conteúdo principal |
| --- | --- |
| `AdminUser` | Identidade administrativa, hash, actividade, privilégios, segredo TOTP e hashes de recuperação |
| `Author`, `Category` | Perfis públicos, metadados académicos e classificação de artigos |
| `Article` | Conteúdo de divulgação, slug, autor/categoria, estado, datas, media e referências |
| `Journal` | Identidade de revista e conteúdo científico público/rascunho, autores e metadados |
| `EditorialPolicy` | Textos editáveis de políticas e diretrizes |
| `Comment` | Texto, identificação do comentador, artigo e aprovação |
| `ContactMessage`, `Subscriber` | Contactos recebidos/estado de leitura e inscrições/activação |
| `Researcher`, `GoogleIdentity` | Conta pública/investigador, confirmação, nonce e identidade Google |
| `ReaderArticle`, `ReaderJournal` | Favoritos e acompanhamento por conta, revisão reconhecida |
| `SubmissionSetting` | Abertura, tipos, formatos e e-mail editorial por revista |
| `Manuscript`, `ManuscriptAuthor` | Processo editorial, metadados/declaracões e autores ordenados |
| `ManuscriptVersion`, `ManuscriptFile` | Snapshots, versões e anexos privados com payload/hash |
| `EditorialEvent` | Histórico de acções, decisões e notas com visibilidade |
| `ReviewAssignment` | Estrutura legada, distinta dos pareceres activos em `StaffPeerReview` |
| `TeamRole`, `TeamMember`, `TeamAppointment`, `StaffContactLog` | Funções/permissões, colaboradores, mandatos e histórico de contactos |
| `StaffTask`, `TaskComment` | Responsável, prazo, estado e comentários de tarefas |
| `StaffDocument` | Documento privado, anexo, versão, aceite e arquivo lógico |
| `StaffPeerReview` | Atribuição científica por versão, conflito, aceite e parecer entregue |
| `ArticleWorkflow`, `PortalReview` | Revisão, aprovação e publicação de artigos com histórico |
| `StaffNotice` | Aviso por destinatário, leitura, eliminação lógica e chave de deduplicação |
| `GovernanceAudit`, `AuditReport` | Eventos preservados e fotografias individuais de relatórios |
| `EditorialNotification` | Fila transaccional de e-mail e estado de entrega |
| `PublicationAsset` | Cópias sanitizadas de figuras ligadas à publicação |

SQLite é o padrão local (`sqlite:///sussurros.db`, normalmente na pasta `instance/`). Para produção, configurar PostgreSQL persistente por `DATABASE_URL`; o código normaliza `postgres://` para `postgresql://`. A versão exacta do servidor PostgreSQL é definida pela infraestrutura, não pelo repositório.

Com `BOOTSTRAP_ON_STARTUP=true` (valor por omissão), o arranque mantém a preparação de dados e, se `AUTO_SCHEMA_UPGRADE=true`, as actualizações de esquema legadas. Os exemplos de revistas e artigos são criados apenas fora do modo de produção. Em produção, pode preparar a base explicitamente e arrancar com `BOOTSTRAP_ON_STARTUP=false`.

As revisões Alembic partem da baseline histórica e chegam a `20261127_23` (Automation Engine). A baseline valida o esquema histórico existente. Investigue incompatibilidades antes de prosseguir. O downgrade destrutivo é recusado.

No **terminal do serviço da aplicação no Coolify**, com a versão nova disponível, o ambiente apontado à base correcta e backup previamente verificado, aplicar antes de iniciar os novos processos:

```bash
python -m alembic current
python -m alembic upgrade head
python -m alembic current
FLASK_ENV=production BOOTSTRAP_ON_STARTUP=false python -m flask --app app preparar-dados
```

O último `alembic current` deve apresentar `20261127_23 (head)`. Ensaiar primeiro numa cópia isolada. Executar `preparar-dados` uma vez por implantação, com o ambiente de produção configurado. O comando prepara as funções padrão, a categoria editorial e os slugs legados. Após validar estes passos, definir `BOOTSTRAP_ON_STARTUP=false` no serviço web do Coolify e verificar `/healthz`, a listagem pública e o acesso administrativo.

O [Sussurros Automation Engine](docs/AUTOMATION_ENGINE.md) acrescenta cinco operadores, painel e comando de tarefas periódico; os operadores começam desactivados.

Consulte [Vídeos de Ciência](docs/SCIENCE_VIDEOS.md) para o fluxo editorial, a implantação e a submissão do sitemap de vídeos.

Comando específico para as tabelas Google/favoritos:

```bash
flask --app app migrar-login-google
```

O comando deve ser executado no ambiente correcto e não substitui a estratégia de migração das outras tabelas. Ver detalhes em [docs/google-login.md](docs/google-login.md).

## Instalação e desenvolvimento

### Linux/macOS

```bash
git clone https://github.com/mergior-goriate/sussurros-do-saber.git
cd sussurros-do-saber
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
npm run build:css
```

Definir as variáveis no ambiente do processo, usando valores locais próprios. O código não carrega automaticamente um `.env` por `python app.py`; não presumir esse carregamento. Gerar segredo e hash sem os guardar no repositório:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Palavra-passe: ')))"
```

Depois configurar `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` e, para a conta administrativa, `ADMIN_TOTP_SECRET` de um autenticador. Para ambiente local, manter `FLASK_ENV` fora de produção; Redis pode ser omitido, usando contador em memória. Executar:

```bash
python app.py
```

Abrir `http://127.0.0.1:5000` e `/admin/login`. O servidor de desenvolvimento não deve ser usado para servir produção. `FLASK_DEBUG=true` só activa debug fora de produção.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm ci
npm run build:css
$env:SECRET_KEY = 'SUBSTITUIR_POR_SEGREDO_LOCAL'
$env:ADMIN_USERNAME = 'editor-local'
$env:ADMIN_PASSWORD_HASH = 'SUBSTITUIR_POR_HASH_GERADO'
python app.py
```

Configurar também TOTP para a conta usada. Se a política do PowerShell impedir activação, pode executar directamente `.\.venv\Scripts\python.exe` em vez de mudar a política global.

### CSS e execução Docker

`npm run build:css` compila Tailwind; executar após alterações a classes/templates. Node não é necessário para servir a aplicação Python depois do build.

```bash
docker build -t sussurros-do-saber:local .
docker run --rm -p 8000:8000 --env-file /caminho/seguro/config.local sussurros-do-saber:local
```

O ficheiro de ambiente é fornecido pelo Docker, não carregado pela aplicação. Para persistência, usar PostgreSQL externo; não confiar no SQLite dentro de um contentor efémero. A imagem constrói CSS com Node 22, instala Python 3.11, usa utilizador sem privilégios e inicia Gunicorn com dois workers por padrão (`WEB_CONCURRENCY`), preload, timeout de 120 segundos e porta `PORT` (padrão 8000). `gunicorn.conf.py` reinicia o pool de ligação em cada worker após fork. O Docker verifica `/healthz` a cada 30 segundos, com timeout de 5 segundos e período inicial de 60 segundos; falhas de base de dados devolvem 503 sem detalhes privados.

## Configuração

Segredos pertencem às variáveis protegidas do serviço/Worker. Os valores abaixo descrevem nomes e comportamento; não são credenciais reais.

### Aplicação, administração e infraestrutura

| Variável | Uso e requisito |
| --- | --- |
| `FLASK_ENV` | `production` activa regras de produção; definir explicitamente no servidor |
| `RENDER` | `true` também activa modo produção, por compatibilidade histórica; não é requisito do Coolify |
| `SECRET_KEY` | Assinatura de sessão/tokens; obrigatório e não padrão em produção |
| `DATABASE_URL` | PostgreSQL de produção; SQLite por padrão local |
| `SITE_URL` | Origem pública usada em links e metadados; padrão canónico com `www` |
| `RATELIMIT_STORAGE_URI` | Redis para limites; tem prioridade sobre `REDIS_URL`; obrigatório um dos dois em produção |
| `REDIS_URL` | Alternativa de configuração Redis; memória só no desenvolvimento |
| `ADMIN_USERNAME` | Administrador principal por ambiente; define também a precedência dos privilégios |
| `ADMIN_PASSWORD_HASH` | Hash Werkzeug da palavra-passe administrativa, exigido para conta por ambiente em produção |
| `ADMIN_PASSWORD` | Alternativa em texto apenas no desenvolvimento; não usar em produção |
| `ADMIN_TOTP_SECRET` | Segredo TOTP da conta gerida por ambiente; exigido para esse acesso em produção |
| `ADMIN_IDLE_TIMEOUT_MINUTES` | Inactividade administrativa; padrão 15, intervalo 1–120 |
| `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` | Chaves pública/privada do Turnstile para o login administrativo |
| `REQUIRE_TURNSTILE` | Obrigatório por padrão em produção; manter `true` e configurar as duas chaves |
| `SESSION_COOKIE_SECURE` | Pode forçar cookie Secure fora de produção; em produção fica activo |
| `FLASK_DEBUG` | Debug local explícito, ignorado em produção |
| `PORT` | Porta do comando Gunicorn no Docker; padrão 8000 |
| `WEB_CONCURRENCY` | Workers Gunicorn no Docker; padrão 2 |
| `BOOTSTRAP_ON_STARTUP` | Preparação legada ao arrancar, activa por omissão. Usar `false` após configurar Alembic e `preparar-dados` na implantação. |
| `AUTO_SCHEMA_UPGRADE` | Actualização legada do esquema, activa por omissão quando a preparação ao arrancar está activa. |
| `PUBLISH_SCHEDULED_ON_REQUEST` | Processamento de publicações ao receber pedidos HTTP, activo por omissão. Usar `false` após validar a tarefa periódica. |
| `PROXY_FIX_X_FOR`, `PROXY_FIX_X_PROTO` | Saltos de proxy confiáveis para IP/protocolo; padrão 1 |
| `PROXY_FIX_X_HOST` | Saltos confiáveis para host encaminhado; padrão 0 |

### Media, identidade e assistente

| Variável | Uso |
| --- | --- |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | As três credenciais exigidas pelos uploads |
| `CLOUDINARY_FOLDER` | Pasta de imagens de artigos; padrão `sussurros-do-saber/artigos` |
| `CLOUDINARY_AUTHOR_FOLDER` | Fotografias; padrão `sussurros-do-saber/autores` |
| `CLOUDINARY_JOURNAL_FOLDER` | Capas; padrão `sussurros-do-saber/revistas` |
| `CLOUDINARY_VIDEO_FOLDER` | Vídeos; padrão `sussurros-do-saber/videos` |
| `CLOUDINARY_URL` | Lida para identificação do cloud em optimização; não substitui as três credenciais exigidas pelo upload |
| `GOOGLE_CLIENT_ID` | Login Google opcional; ID público da aplicação Web |
| `GOOGLE_SITE_VERIFICATION` | Token de verificação do site nos metadados |
| `GTM_CONTAINER_ID` | Container GTM; configurar para a instalação efectiva |
| `ASSISTANT_WORKER_URL` | Endpoint do Worker; há URL padrão no código |
| `ASSISTANT_SHARED_KEY` | Mesmo segredo privado na aplicação e no Worker |
| `SOCIAL_FACEBOOK_URL`, `SOCIAL_INSTAGRAM_URL`, `SOCIAL_YOUTUBE_URL` | Ligações institucionais; existem padrões no código |
| `SOCIAL_LINKEDIN_URL`, `SOCIAL_X_URL`, `SOCIAL_WHATSAPP_URL` | Ligações institucionais restantes |

### SMTP

| Variável | Uso |
| --- | --- |
| `SMTP_HOST` | Servidor obrigatório para entrega |
| `SMTP_FROM` | Endereço remetente válido obrigatório |
| `SMTP_PORT` | Padrão 587 com TLS, 465 com SSL |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Autenticação quando o provedor a exige |
| `SMTP_TLS` | Padrão `true`, usa STARTTLS se SSL não estiver activo |
| `SMTP_SSL` | Padrão `false`, ligação SSL directa quando `true` |
| `NEWSLETTER_ENABLED` | Padrão `true`; `false` pausa preparação e entrega de boletins, preservando e-mails transaccionais |

Estas variáveis configuram envio, não DNS do domínio. MX, SPF, DKIM e DMARC são configurados no DNS conforme o provedor de e-mail contratado; os seus valores não devem ser inventados ou copiados de exemplos de outro serviço.

## Produção, manutenção e recuperação

O projecto é compatível com execução Docker no Coolify e PostgreSQL/Redis externos. A infraestrutura usada pelo projecto foi descrita como VPS OVHcloud com Coolify, domínio na Spaceship, DNS no Cloudflare e backups externos. A versão PostgreSQL, destino R2, agenda de backup, ramo de deployment e estado actual dos serviços devem ser confirmados no painel; o código não comprova essas configurações.

### Deployment no Coolify

1. Seleccionar o repositório e o ramo que contém as alterações aprovadas. A configuração antiga pode apontar para `deploy/coolify-vps`; conferir explicitamente o ramo e o commit, sem assumir que segue `main`.
2. Construir pelo `Dockerfile`, definir porta interna 8000 (ou `PORT`) e domínio HTTPS canónico.
3. Configurar produção, segredo, PostgreSQL persistente, Redis e credenciais administrativas/2FA/Turnstile. Acrescentar integrações realmente utilizadas.
4. Fazer backup antes de mudança de versão que altere esquema; testar alteração numa cópia quando aplicável.
5. Executar deploy/redeploy e confirmar o commit servido, logs e `GET /healthz`.
6. Configurar separadamente a tarefa de entrega SMTP. Confirmar envio real de teste e fila; deploy do Flask não cria a tarefa automaticamente.
7. Verificar página inicial, artigo, revista/índice em computador e telefone, PDF, login, submissões e integrações activas.

`/healthz` executa uma consulta simples à base e devolve estado apropriado. Não verifica entrega SMTP, Redis, Cloudinary, Worker AI, Google, DNS ou qualidade do conteúdo. Usar monitorização externa e alertas separados para esses componentes e para disco/memória/processo.

### Imagens versionadas no GitHub Packages

O workflow [publish-package.yml](.github/workflows/publish-package.yml) constrói a imagem do código da tag de lançamento e publica em `ghcr.io/mergiorgoriate/sussurros-do-saber`. Executa ao publicar uma Release ou manualmente, com uma tag existente como `v2.0.0`. Usa `GITHUB_TOKEN` com `contents: read` e `packages: write`.

Uma versão `v2.0.0` gera as tags `2.0.0` e `v2.0.0`; versões sem sufixo também actualizam `latest`. Preferir versão explícita ou digest para deployments reproduzíveis. O workflow verifica a construção e importação de Flask/Gunicorn; isso não comprova reprodução de vídeos, SMTP ou funcionamento completo em produção. Publicar a imagem não configura nem executa deploy no Coolify. O acesso ao pacote depende das permissões/visibilidade no GHCR.

### Ensaio de recuperação PostgreSQL

[scripts/restore_drill.py](scripts/restore_drill.py) verifica o arquivo e restaura numa base nova e isolada, com contagens, relações e relatório privado. Recusa usar a base da aplicação como destino administrativo. O teste CI usa uma cópia sintética; backups reais no R2 e revisão editorial dos conteúdos restaurados continuam a exigir um ensaio próprio. O relatório distingue restauração concluída de revisão de conteúdo concluída.

### DNS e e-mail

O registo do domínio e a autoridade DNS são funções diferentes. Se Cloudflare for a autoridade, os nameservers no registador devem coincidir exactamente com os atribuídos à zona. Os registos DNS do site/e-mail devem ser mantidos no provedor autoritativo. O estado visual de propagação num painel não basta para comprovar resolução mundial ou entrega de e-mail.

Coolify executa a aplicação; não é o local de delegação de nameservers. Não tratar correcção de DNS como alteração ao código nem mudar registos de e-mail para resolver um erro de interface.

### Backups e rollback

- Guardar backups consistentes de PostgreSQL, incluindo payloads de anexos/figuras, utilizadores, favoritos e histórico editorial; proteger acesso porque contêm dados privados.
- Manter media Cloudinary, configuração do serviço, versões do código e configuração do Worker segundo a estratégia operacional. Redis armazena contadores, não substitui backup da base.
- Confirmar retenção, cópia externa e ensaiar restauração. Um job configurado sem restauração validada não comprova recuperação.
- No rollback de código, preservar tabelas e dados novos; não executar `db.drop_all()`, apagar volume ou restaurar uma base antiga sobre produção sem plano explícito.
- Mudanças do esquema são aditivas e leves, mas não têm downgrade automático; testar compatibilidade com o código anterior antes de voltar a uma versão.
- Depois de restaurar, verificar contas, conteúdo, anexos, versões, favoritos, acesso privado, fila SMTP e ficheiros externos.

## Segurança, privacidade e desempenho

- Sessões assinadas com cookies HttpOnly/SameSite=Lax e Secure em produção; duração de sessão pública de duas horas. Administração tem controlo adicional de inactividade e 2FA.
- CSRF para mutações, validação de campos e permissões no servidor, hashes de palavras-passe, tokens temporários de confirmação/recuperação e nonce de conta.
- Flask-Limiter aplica limites gerais (300/dia, 100/hora) e específicos por operação. Usar Redis partilhado evita contadores independentes por worker em produção.
- CSP com nonce/scripts autorizados, `nosniff`, política de referência, restrições de permissões e HSTS quando HTTPS. A política mantém estilos inline permitidos para a interface existente; não declarar uma CSP sem qualquer inline.
- `ProxyFix` tem confiança configurável em cabeçalhos encaminhados: por padrão, um salto para IP/protocolo e nenhum para host. Ajustar apenas à topologia real de Cloudflare/Coolify; não aceitar cabeçalhos arbitrários directamente na aplicação.
- Respostas administrativas, contas, Google e submissões usam cache privado/no-store; áreas privadas também recebem restrições de indexação quando previstas.
- Gzip para texto elegível, respeitando negociação; cache curto nas páginas públicas elegíveis e cache longo apenas de estáticos com a impressão digital actual do conteúdo. `url_for('static', ...)` acrescenta automaticamente `v=<sha256>`; recursos sem a impressão digital actual exigem revalidação. Não aplicar cache público ao HTML com sessão/formulário privado.
- Imagens responsivas/lazy loading, optimização Cloudinary e listas que evitam carregar corpos desnecessários. CSS Tailwind é compilado no build.
- Navegação responsiva, labels, foco de teclado, diálogos e página de acessibilidade existem; isso não é certificação WCAG nem auditoria completa por leitores de ecrã.
- CSV administrativo aplica tratamento de valores para reduzir interpretação como fórmulas. Exportações contêm dados pessoais e são restritas ao painel.

Evitar publicar dumps, tokens, segredos TOTP, anexos privados e credenciais em issues, logs ou ficheiros versionados. As validações existentes não equivalem a auditoria de segurança independente.

## Auditoria de 20/10/2026

Base revista: `main` no commit `03831d527752718db7ec78057fa15a44aab51db2`, incluindo os PRs #235 e #236. Não havia PRs abertos no início da auditoria. Foram analisados código, recursos estáticos, cabeçalhos, navegação, persistência do navegador, consentimento e entrega pela fila existente. Os testes funcionais usaram SQLite e identidades sintéticas; não alteraram a base de produção nem enviaram e-mails reais.

### Problemas corrigidos

| Área | Falha confirmada e correcção |
| --- | --- |
| Cache após deploy | Recursos sem versão recebiam um ano de cache imutável. As URLs estáticas geradas por Flask passam a incluir a impressão digital do conteúdo; URLs sem a versão actual exigem revalidação. Erros de recursos não recebem cache imutável. |
| SMTP seguro | STARTTLS e SMTP_SSL passam a receber um contexto que valida o certificado e o nome do servidor. Um certificado inválido impede autenticação e envio. |
| Estado da fila SMTP | Uma falha ao fechar a ligação podia desfazer o registo de mensagens já aceites. O estado é agora confirmado antes de QUIT, e erros de rede durante o envio ficam registados por mensagem, preservando os envios já aceites no lote. Continua possível haver duplicação se o processo falhar entre a aceitação SMTP e o commit; não existe garantia de entrega exactamente uma vez. |
| Contraste | Corrigidos textos secundários dos cartões, metadados e ligações de revistas, convite a autores, ligações educativas e directrizes no modo escuro. Os exemplos dos campos de pesquisa e a ajuda do login administrativo também mantêm contraste nos respectivos temas. |
| Ordem dos estilos | Os estilos de revistas e aprendizagem eram injectados pelo JavaScript depois dos estilos comuns, sobrepondo cores e tipografia. Passaram para CSS local carregado pelos respectivos templates, antes das regras comuns de leitura. |
| Colecção educativa | JSON inválido, um valor que não fosse uma lista ou armazenamento bloqueado podiam interromper o JavaScript. A leitura passa a validar os dados; falhas de escrita apresentam uma mensagem sem impedir os filtros. |
| Acessibilidade do glossário | Acrescentado um rótulo explícito ao campo de pesquisa, preservando a apresentação. |
| Documentação | Actualizadas a data da revisão e a versão do Playwright; removida a afirmação contraditória de que a compilação ainda usava Tailwind 3. |

### Verificações efectuadas

- A suite inicial executou **308 testes Python sem falhas**. Os testes de regressão novos verificam certificados SMTP, desconexão em QUIT e invalidação de cache por conteúdo. Os cinco novos testes de navegador passaram. O teste de download compara agora os bytes com o ficheiro efectivamente guardado, evitando a instabilidade causada pela data interna de um ZIP recriado. Os resultados da suite final constam dos checks do PR.
- O percurso local por **16 páginas e 76 destinos internos distintos** não encontrou respostas de erro. Foram incluídos os recursos estáticos e as ligações públicas apresentadas nessas páginas; isto não equivale a percorrer todos os registos da base real.
- As páginas públicas observadas no Chromium não apresentaram erros JavaScript nem transbordo horizontal a 360 e 1280 píxeis. Os testes de contraste cobrem elementos concretos em ambos os temas; os testes de aprendizagem incluem dados locais inválidos e armazenamento bloqueado. Esta amostragem não certifica conformidade integral com WCAG.
- Os **6 testes JavaScript de consentimento passaram**; a compilação Tailwind foi concluída. `npm audit --omit=dev --audit-level=high` e `pip-audit -r requirements.txt` não encontraram vulnerabilidades conhecidas nas dependências abrangidas, na data da execução. O resultado não cobre vulnerabilidades ainda não publicadas nem constitui uma análise de todo o código por si só.
- Foram feitos apenas pedidos GET públicos a `/`, `/contacto`, `/equipa`, `/healthz`, `/robots.txt` e `/sitemap.xml` no domínio oficial; os seis responderam com HTTP 200. Não foram ensaiados envios de formulários ou autenticação real em produção.

### Validação no Coolify após integrar

1. Integrar o PR depois de os checks passarem e executar Redeploy da revisão integrada. Confirmar a revisão nos logs e a resposta HTTP 200 de `/healthz`.
2. Abrir uma janela nova e confirmar que as URLs de CSS/JS incluem `v=`. Verificar artigos, revistas, aprendizagem, rodapé e formulários num telemóvel e nos dois temas disponíveis.
3. Confirmar SMTP_HOST, SMTP_PORT, SMTP_FROM e o modo TLS/SSL no ambiente. `flask --app app preparar-boletim --dry-run` verifica a selecção e a presença da configuração; **não comprova ligação, autenticação SMTP ou recepção**. Usar um destinatário de teste controlado para validar entrega e inspeccionar também spam e os registos do fornecedor.
4. Confirmar a tarefa que prepara o boletim e **um único worker** periódico de `enviar-notificacoes`, incluindo fuso horário e última execução. Seguir [a operação do boletim](docs/NEWSLETTER.md), sem criar outro sistema de newsletter ou recomendação.
5. Verificar backups com recuperação numa base isolada, credenciais Google/Cloudinary/Turnstile, DNS de e-mail e monitorização no ambiente efectivo. A auditoria local não confirma estas configurações nem substitui revisão científica das fontes de cada artigo.

## Testes e validação

A revisão de 17/10/2026 passou em **214 testes Python e 61 testes de navegador** locais, com auditorias npm e Python sem vulnerabilidades reportadas. O [registo de resolução dos PRs](docs/PR_RESOLUTION_20261017.md) identifica as versões, o navegador alternativo usado e os limites: a CI do GitHub continua bloqueada antes de executar etapas, e Docker completo, PostgreSQL e produção não foram confirmados nesta revisão.

Testes Python:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Incluem plataforma, regressões do site, submissões, contas, login Google, conteúdo editorial, metadados, PDF, matriz das 24 permissões, contas inactivas, mandatos expirados/múltiplos, âmbito de revista, concessão/revogação, recursos próprios/atribuídos, tarefas, aceites, transições editoriais, remoções e notificações (propriedade, deduplicação, rollback, leitura e persistência). Usar uma base de teste isolada: importar `app` inicializa o esquema e pode criar dados iniciais.

Testes de navegador:

```bash
npm ci
npm run build:css
npx playwright install chromium
npm run test:e2e
```

O Playwright espera aplicação em `http://127.0.0.1:5000`, com fixtures/configuração próprias. Consultar [playwright.config.js](playwright.config.js), `tests/browser/` e a sequência completa de preparação em [.github/workflows/ci.yml](.github/workflows/ci.yml); executar apenas o comando não inicia nem prepara automaticamente o servidor.

A CI de `main`/pull requests executa testes Python, auditoria pip, build CSS, auditoria npm de dependências de produção, navegador Chromium e upload de diagnóstico. O workflow separado constrói Docker. A CI inclui ensaios de baseline e restauração PostgreSQL 18 com dados sintéticos, verificando preservação do conteúdo e isolamento da base restaurada. Dependabot está configurado para dependências do projecto. Ver o resultado do commit específico no GitHub Actions; a presença de testes não significa que passaram num deployment diferente.

[docs/site-audit-20261005.md](docs/site-audit-20261005.md) guarda uma auditoria histórica com escopo/commit e limitações próprias. Não usar as contagens ou observações daquele documento como prova automática do estado actual. Consultar também [a auditoria funcional de 08/10](docs/PORTAL_AUDIT_20261008.md), [a matriz de permissões](docs/PERMISSIONS_AUDIT.md) e [a recuperação do login](docs/ADMIN_LOGIN_RECOVERY_20261008.md). Testes de navegador usam contas/dados sintéticos, incluindo computador e telemóvel, tarefas, aceites, remoções, notificações e barra lateral. A evidência histórica deste parágrafo refere-se à revisão documental anterior; os novos ensaios locais estão registados na auditoria de 20/10/2026, acima. Google real, uploads Cloudinary reais, contas de homologação, SMTP, backups e configuração efectiva do Coolify continuam a exigir validação no ambiente correspondente.

### Evidência recente e verificações pendentes

A [CI do PR #173](https://github.com/MergiorGoriate/sussurros-do-saber/actions/runs/37837579711), no commit `36571261504019bc41259c0b2f06fb33e4d68700`, concluiu **212 testes Python e 61 testes de navegador** com sucesso. Também passaram os ensaios PostgreSQL, a auditoria de dependências e o build Docker. Estas contagens referem-se àquela execução; a actualização documental deste README não constitui nova validação funcional.

| Alteração | Cobertura automática recente |
| --- | --- |
| Barra lateral móvel | [staff.spec.js](tests/browser/staff.spec.js): 320, 390 e 768 px, expandir/recolher, limites úteis, último ícone alcançável e mudança para computador |
| Fluxo editorial | [workflow.spec.js](tests/browser/workflow.spec.js): 1440, 390 e 320 px, etapas, leitura, submissão real/persistência e ausência de aprovação/publicação prematura |
| Partilha Bluesky/Reddit | [site.spec.js](tests/browser/site.spec.js): título/URL, destinos, atributos, visibilidade e dimensões móveis/computador; alternativa sem JavaScript nos artigos de divulgação |
| Formulários administrativos | [editors.spec.js](tests/browser/editors.spec.js): cinco páginas a 320, 390, 768 e 1440 px, ambos estados da barra, edição de campos e ferramentas de imagem/gráfico |

A regressão dos formulários foi executada antes da correcção: falhou a 320 e 390 px. Depois da correcção, passou nas quatro larguras. As capturas de editar artigo e editar revista foram inspeccionadas visualmente. Os testes usam bases isoladas e fixtures de artigos/revistas não publicados, como [editor_fixture.py](tests/browser/editor_fixture.py) e [workflow_fixture.py](tests/browser/workflow_fixture.py); não usar esses scripts contra a base de produção.

Continuam pendentes a confirmação no aparelho físico e no deployment efectivo do Coolify, outras famílias de navegador (por exemplo Safari/WebKit), a aparência da scrollbar nativa em Windows/Edge e login/publicação em contas reais das redes sociais. Na captura de 320 px da validação do PR #172, o botão flutuante do índice sobrepunha parte da linha de partilha na posição de deslocamento usada; os testes não comprovam ausência de todas as sobreposições com elementos flutuantes. Isso deve ser revisto no teste prático de leitura.

## Limites da implementação

- Publicação científica usa `Journal` como registo combinado; template ou campo legado sem rota activa não comprova um módulo completo de edições.
- DOI/ISSN, licenças e histórico são metadados editoriais. Não há emissão Crossref, depósito DOI, registo ISSN, indexação automática ou verificação externa implementados.
- Há portal de pareceres atribuídos, com controlo de versão e conflito; não há anonimização garantida nem revisão duplamente cega.
- O boletim tem preparação semanal e entrega pela fila SMTP existente; activar e validar SMTP e agendamentos no servidor é uma etapa operacional separada. Não há editor de campanhas arbitrárias. O contacto continua a guardar mensagens, sem encaminhamento automático.
- Notificações de acompanhamento são internas; e-mails editoriais dependem de SMTP e do comando agendado.
- PDF é uma composição própria e a conversão DOCX é limitada. Publicar exige revisão humana do conteúdo e das figuras.
- O catálogo educativo é definido no código; as preferências educativas locais não sincronizam entre dispositivos.
- O assistente chama um modelo com uma pergunta, sem pesquisa de fontes ou contexto completo da base editorial.
- Programação de artigos é verificada em pedidos, não por cron autónomo. Revistas não têm agendamento de publicação equivalente.
- A baseline histórica e as revisões posteriores devem ser aplicadas e verificadas para o esquema desta versão. Não há downgrade automático destrutivo, antivírus de anexos ou prova de configuração/backup real de infraestrutura apenas pela leitura deste repositório.

## Inventário completo de rotas

Inventário dos decoradores de rotas do código revisto. `GET` inclui o tratamento automático de HEAD quando aplicável; OPTIONS é gerido pelo Flask. Os parâmetros entre `<...>` são variáveis, não texto literal. O prefixo do blueprint já está incluído. Rotas administrativas, de conta e submissão mantêm as permissões descritas acima; uma rota listada não significa acesso público.

### Páginas públicas, APIs e pré-visualizações

| Método | Rota | Handler em `app.py` |
| --- | --- | --- |
| GET | `/diretrizes-para-autores` | `author_guidelines` |
| GET | `/ads.txt` | `ads_txt` |
| GET | `/` | `home` |
| GET | `/artigos` | `articles` |
| GET | `/artigo/<slug>` | `article` |
| POST | `/artigo/<slug>/comentarios` | `submit_comment` |
| GET | `/artigo/<int:article_id>` | `article_legacy` |
| GET | `/sobre` | `about` |
| GET | `/autores` | `authors` |
| GET | `/autor/<slug>` | `author_detail` |
| GET | `/autor/<int:author_id>` | `legacy_author` |
| GET | `/contacto` | `contact` |
| GET | `/termos-e-condicoes` | `terms` |
| GET | `/politica-de-privacidade` | `privacy` |
| GET | `/politica-editorial` | `editorial_policy` |
| GET | `/politicas-editoriais` | `editorial_policy` |
| GET | `/politica-de-correcoes` | `corrections_policy` |
| GET | `/acessibilidade` | `accessibility` |
| GET | `/servicos` | `services` |
| GET | `/servicos/edicao-cientifica` | `scientific_editing` |
| GET | `/revistas` | `journals` |
| GET | `/revistas/<slug>` | `journal_detail` |
| POST | `/admin/revistas/previsualizar-markdown` | `journal_markdown_preview` |
| GET | `/admin/revistas/<int:journal_id>/previsualizar` | `journal_preview` |
| GET | `/revistas/<slug>/baixar.pdf` | `journal_download_pdf` |
| GET | `/admin/revistas/<int:journal_id>/baixar.pdf` | `journal_preview_pdf` |
| GET | `/recursos` | `resources` |
| GET | `/aprender` | `learn` |
| GET | `/laboratorio/osmose` | `osmosis_lab` |
| GET | `/api/recursos` | `api_resources` |
| GET | `/favoritos` | `favorites` |
| GET | `/api/artigos` | `api_articles` |
| GET | `/feed.xml` | `feed` |
| GET | `/sitemap.xml` | `sitemap` |
| GET | `/robots.txt` | `robots` |
| GET | `/healthz` | `healthcheck` |
| POST | `/api/newsletter` | `newsletter` |
| GET, POST | `/boletim/cancelar/<token>` | `newsletter_public.unsubscribe` |
| POST | `/api/assistente` | `assistant` |
| POST | `/api/contacto` | `submit_contact` |

### Administração

| Método | Rota | Handler em `admin.py` |
| --- | --- | --- |
| GET, POST | `/admin/login` | `login` |
| GET, POST | `/admin/verificar-2fa` | `verify_two_factor` |
| GET, POST | `/admin/seguranca/2fa` | `two_factor_settings` |
| POST | `/admin/logout` | `logout` |
| GET, POST | `/admin/politicas-editoriais` | `editorial_policies` |
| POST | `/admin/politicas-editoriais/previsualizar` | `preview_author_guidelines` |
| GET | `/admin/docs` | `docs` |
| GET | `/admin` | `dashboard` |
| GET, POST | `/admin/administradores` | `administrators` |
| POST | `/admin/administradores/<int:administrator_id>/editar` | `edit_administrator` |
| POST | `/admin/administradores/<int:administrator_id>/eliminar` | `delete_administrator` |
| GET | `/admin/artigos` | `articles` |
| POST | `/admin/api/videos` | `upload_inline_video` |
| POST | `/admin/api/imagens` | `upload_inline_image` |
| GET, POST | `/admin/artigos/novo` | `article_form` |
| GET, POST | `/admin/artigos/<int:article_id>/editar` | `article_form` |
| POST | `/admin/artigos/<int:article_id>/eliminar` | `delete_article` |
| GET, POST | `/admin/autores` | `authors` |
| POST | `/admin/autores/<int:author_id>/eliminar` | `delete_author` |
| GET, POST | `/admin/categorias` | `categories` |
| POST | `/admin/categorias/<int:category_id>/eliminar` | `delete_category` |
| GET | `/admin/revistas` | `journals` |
| GET, POST | `/admin/revistas/nova` | `journal_form` |
| GET, POST | `/admin/revistas/<int:journal_id>/editar` | `journal_form` |
| POST | `/admin/revistas/<int:journal_id>/publicacao` | `toggle_journal` |
| POST | `/admin/revistas/<int:journal_id>/eliminar` | `delete_journal` |
| GET | `/admin/comentarios` | `comments` |
| POST | `/admin/comentarios/<int:comment_id>/estado` | `update_comment_status` |
| POST | `/admin/comentarios/<int:comment_id>/eliminar` | `delete_comment` |
| GET | `/admin/contactos` | `contacts` |
| GET, POST | `/admin/subscritores` | `subscribers` |
| POST | `/admin/contactos/<int:message_id>/eliminar` | `delete_contact` |
| POST | `/admin/subscritores/<int:subscriber_id>/estado` | `toggle_subscriber` |
| GET | `/admin/contactos/exportar.csv` | `export_contacts` |
| GET | `/admin/subscritores/exportar.csv` | `export_subscribers` |

### Equipa, governação e notificações administrativas

| Método | Rota | Handler em `governance.py` |
| --- | --- | --- |
| GET, POST | `/admin/equipa` | `team` |
| POST | `/admin/equipa/<int:ident>/mandatos` | `appointment` |
| POST | `/admin/mandatos/<int:ident>/terminar` | `end_appointment` |
| GET, POST | `/admin/funcoes` | `roles` |
| GET, POST | `/admin/trabalho` | `workspace` |
| GET, POST | `/admin/documentos-equipa` | `documents` |
| GET | `/admin/documentos-equipa/<int:ident>/ficheiro` | `document_file` |
| POST | `/admin/documentos-equipa/<int:ident>/aceitar` | `accept_document` |
| GET, POST | `/admin/notificacoes` | `notifications` |
| GET | `/admin/notificacoes/<int:ident>/abrir` | `open_notice` |
| GET | `/admin/api/notificacoes` | `notice_summary` |
| GET | `/admin/relatorios-equipa` | `reports` |
| GET, POST | `/admin/pareceres` | `reviews` |
| GET, POST | `/admin/pareceres/<int:ident>` | `review_detail` |
| GET | `/admin/pareceres/<int:ident>/ficheiros/<int:file_id>` | `review_file` |
| GET, POST | `/admin/fluxo-artigos/<int:ident>` | `article_workflow` |
| GET, POST | `/admin/remover/<kind>/<int:ident>` | `remove_record` |
| GET | `/admin/historico-remocoes` | `removed_history` |
| GET | `/admin/historico-submissoes/<int:ident>` | `archived_manuscript` |
| POST | `/admin/relatorios-equipa/guardar` | `save_report` |
| GET | `/admin/relatorios-equipa/<int:ident>` | `report_detail` |
| GET, POST | `/admin/equipa/<int:ident>/responsabilidades` | `responsibilities` |

### Contas e biblioteca

| Método | Rota | Handler em `reader_accounts.py` |
| --- | --- | --- |
| GET | `/conta/sessao` | `state` |
| POST | `/conta/entrar` | `login` |
| POST | `/conta/criar-conta` | `register` |
| POST | `/conta/artigos/<int:ident>` | `article_preference` |
| POST | `/conta/importar-favoritos` | `import_favorites` |
| GET, POST | `/conta/revistas/<slug>` | `preference` |
| GET | `/conta/biblioteca` | `library` |
| GET, POST | `/conta/notificacoes` | `notifications` |

### Login Google

| Método | Rota | Handler em `google_auth.py` |
| --- | --- | --- |
| POST | `/conta/google/preparar` | `prepare` |
| POST | `/conta/google/entrar` | `login` |

### Submissões e gestão editorial

| Método | Rota | Handler em `submissions.py` |
| --- | --- | --- |
| GET, POST | `/submissoes/criar-conta` | `register` |
| GET, POST | `/submissoes/entrar` | `login` |
| POST | `/submissoes/sair` | `logout` |
| GET, POST | `/submissoes/confirmacao` | `verify_notice` |
| GET, POST | `/submissoes/confirmar/<token>` | `verify` |
| GET, POST | `/submissoes/recuperar` | `forgot_password` |
| GET, POST | `/submissoes/recuperar/<token>` | `reset_password` |
| GET | `/submissoes` | `mine` |
| GET | `/submissoes/` | `mine` |
| GET, POST | `/submissoes/nova` | `new` |
| GET, POST | `/submissoes/<int:ident>/etapa/<int:step>` | `edit` |
| POST | `/submissoes/<int:ident>/ficheiros` | `upload` |
| POST | `/submissoes/ficheiros/<int:file_id>/remover` | `remove_file` |
| GET | `/submissoes/ficheiros/<int:file_id>` | `download` |
| POST | `/submissoes/<int:ident>/confirmar` | `submit` |
| GET | `/submissoes/<int:ident>` | `detail` |
| POST | `/submissoes/<int:ident>/nova-versao` | `revised` |
| GET | `/admin/submissoes` | `submissions_list` |
| GET, POST | `/admin/submissoes/configuracao` | `submission_settings` |
| GET, POST | `/admin/submissoes/<int:ident>` | `submission_detail` |
| POST | `/admin/submissoes/<int:ident>/preparar` | `prepare_publication` |
| GET | `/submissoes/figuras/<int:asset_id>` | `publication_figure` |
| GET, POST | `/submissoes/notificacoes` | `internal_notifications` |
| GET | `/submissoes/notificacoes/<int:ident>/abrir` | `open_internal_notice` |
| GET | `/submissoes/api/notificacoes` | `internal_notice_summary` |

### Protocolo das APIs principais

| Endpoint | Entrada/resposta principal |
| --- | --- |
| `GET /api/artigos` | `q`, `ids` (até 50 IDs), `limit` (1–50, padrão 24); metadados/cartões de artigos publicados, sem corpos completos |
| `GET /api/recursos` | Catálogo educativo JSON; cache específico de 600 segundos e stale-while-revalidate |
| `POST /api/newsletter` | Inscrição validada; grava/reativa subscritor |
| `POST /api/contacto` | Dados de contacto validados; grava mensagem |
| `POST /api/assistente` | Pergunta `message`; JSON com estado/resposta; erro de integração quando indisponível |
| `GET /conta/sessao` | Autenticação, confirmação, CSRF, nome/fotografia, artigos guardados, contador de notificações e supressão Google |
| `POST /conta/artigos/<ident>` | `enabled=true/false`, CSRF; guarda/remove artigo público |
| `GET/POST /conta/revistas/<slug>` | Preferências; POST com `action=saved/following/read`, `enabled` e revisão quando reconhece leitura |
| `POST /conta/importar-favoritos` | Listas `article_ids`/`journal_slugs`, no máximo 100 itens no total por lote |
| `POST /conta/google/preparar` e `/entrar` | Preparação nonce/CSRF e validação de credencial Google; detalhes em `google_auth.py` |
| `POST /admin/api/imagens` e `/videos` | Multipart autenticado com CSRF; validação, upload e URL de recurso |
| Pré-visualizações Markdown | POST administrativo autenticado/CSRF; conteúdo sanitizado, limites próprios |

Os formulários e JavaScript do repositório definem os nomes exactos dos campos e mensagens. As APIs são internas ao site, sem promessa de contrato externo versionado, CORS público ou autenticação por chave para terceiros. Para manutenção, conferir handlers antes de criar clientes independentes.

## Como manter esta documentação

Ao alterar rotas, permissões, estados, campos, limites, variáveis, templates ou tarefas de operação, actualizar esta documentação e os guias relacionados no mesmo trabalho. Separar claramente o que está implementado, o que é configuração do deployment e o que ainda é futuro. Não marcar uma integração como validada só porque há um botão ou uma variável.

### Painéis administrativos: documentos, contactos e relatórios (20/10/2026)

Os documentos privados da equipa, as mensagens de contacto e os relatórios de auditoria usam cartões, formulários responsivos e acções com contraste nos temas claro e escuro. Os relatórios incluem atalhos para as secções e tabelas com deslocamento horizontal por teclado em ecrãs pequenos; os tipos de documento são apresentados em português. A página de detalhe dos relatórios segue o mesmo layout.

Mantêm-se as permissões, o aceite pela própria conta do membro, os downloads privados, a exportação CSV e os fluxos de eliminação existentes. «Responder por e-mail» abre o programa de correio do utilizador; não envia mensagens automaticamente. Estas alterações de apresentação não exigem migrações nem configuração SMTP.

### Confirmação de remoção de registos

A página partilhada de confirmação de remoção de documentos, membros, submissões e relatórios identifica o registo em português, explica as consequências e separa visualmente «Cancelar» de «Confirmar remoção». O layout adapta-se ao telemóvel e aos temas claro e escuro. Mantêm-se a autorização exclusiva do fundador, a validação CSRF, a remoção lógica e a preservação do histórico; abrir a página ou cancelar não remove o registo. Não exige migração de dados.

### Interface móvel (20/10/2026)

A navegação pública usa o menu recolhido abaixo de 1024 px, evitando que ligações fiquem fora do ecrã em tablets. Menu e pesquisa fecham-se mutuamente; Escape devolve o foco ao botão de origem. Em orientação horizontal, o menu tem deslocamento próprio e altura limitada ao ecrã.

O cabeçalho suporta a campainha e a conta autenticada a 320 px, com ou sem fotografia. Os controlos principais e a navegação das submissões têm áreas de toque de pelo menos 44 px. Os formulários de contacto, a pesquisa, os diálogos e os espaçamentos de leitura adaptam-se ao telemóvel. As secções públicas em ecrãs pequenos deixam de usar alturas estimadas de `content-visibility`; as imagens mantêm o carregamento diferido. Não há alterações de permissões, dados ou SMTP.

As regressões de navegação, foco, conta autenticada e formulários estão em `tests/browser/mobile-layout.spec.js`. Executar com `npx playwright test tests/browser/mobile-layout.spec.js` no ambiente de testes isolado descrito acima. A validação local usa dados sintéticos; envio de mensagens e boletins em produção não faz parte destes testes.

### Introdução dos artigos no telemóvel

Até 767 px, o resumo usa 16 px e entrelinha de 1,6; o nome do autor e a fotografia ocupam menos altura. A publicação fica à esquerda, a actualização ao centro e o tempo de leitura com o botão de guardar à direita, mantendo uma área de toque de 44 px. A data de actualização é sempre apresentada, mesmo quando coincide com a publicação. Os elementos `time` mantêm os valores ISO. O texto continua alinhado à esquerda e adapta-se aos dois temas. Não altera o conteúdo editorial, as datas guardadas nem o fluxo de favoritos.

### Espaçamento do rodapé no telemóvel

Até 767 px, o rodapé usa opções de navegação com pelo menos 36 px de altura, texto de 14 px e entrelinha de 1,35. Os grupos ficam separados por 16 px e os títulos por 2 px das opções. Os ícones sociais mantêm 44 px. A linha decorativa da navegação principal não é aplicada às ligações do rodapé. O layout de computador mantém a sua escala.

### Meus pareceres e gestão de atribuições (21/10/2026)

O painel `/admin/pareceres` separa a vista pessoal de «Gerir atribuições». O fundador e os editores com permissões de gestão podem seleccionar uma submissão em avaliação e convidar revisores elegíveis. A lista respeita o âmbito da revista, a atribuição do editor, a disponibilidade, os mandatos activos e os conflitos de autoria; revisores já convidados para a mesma versão deixam de aparecer na selecção. A conta do fundador sem membro pessoal pode acompanhar as atribuições sem receber uma lista pessoal vazia como única opção.

Na vista pessoal, o revisor responde ao convite, confirma a ausência de conflito, consulta os ficheiros da versão atribuída e entrega uma recomendação fundamentada. Pode declarar conflito depois de aceitar, interrompendo o acesso aos ficheiros. Versões anteriores ou submissões fora de avaliação apresentam uma vista fechada para alterações; os pareceres já entregues continuam consultáveis. A validação de uma entrega inválida não altera o relatório nem a recomendação guardados. A decisão científica continua a pertencer ao editor.

As revisões de artigos de divulgação aparecem numa secção distinta, com acesso ao fluxo editorial existente; não são apresentadas como revisão por pares de investigação original. Não se criam atribuições automaticamente: o editor escolhe o manuscrito, o revisor e o prazo. As notificações internas continuam a usar o mecanismo existente.

O layout inclui filtros de estado, contadores da vista, prazos, estados em português e formulários responsivos nos temas claro e escuro. Os testes de permissões e transições estão em `tests/test_review_workspace.py`; o percurso no navegador e a apresentação estão em `tests/browser/reviews.spec.js`, com dados sintéticos de `reviews_fixture.py`. Não exige migração de dados nem configuração SMTP adicional.

A validação de segurança deste deployment exige Pillow 13.0.0, actualizado a partir de 12.3.0. A compatibilidade é verificada pelos testes de submissões, imagens e PDF. Notas oficiais da versão: https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html.

### Fundo dos artigos de divulgação (21/10/2026)

O formulário existente de criação/edição inclui «Fundo do artigo», junto dos controlos de apresentação. Os cartões usam botões de opção nativos, seleccionáveis pelo teclado, com indicação textual da escolha. «Fundo padrão» mantém os estilos públicos actuais; «Papel antigo» usa uma textura criada em CSS, sem imagens externas nem novas dependências, com paletas próprias para os temas claro e escuro.

A escolha altera imediatamente a pré-visualização existente, incluindo título e resumo, sem publicar nem gravar a opção. É necessário usar **Guardar artigo**. A alteração desta opção pausa a gravação automática de texto pelo mecanismo existente de protecção das opções do formulário. O renderizador de Markdown e a pré-visualização de notas continuam a funcionar; as tabelas da pré-visualização ficam em regiões com deslocamento horizontal e foco por teclado.

A coluna `article.background` guarda apenas `default` ou `aged_paper`; valores ausentes, nulos ou desconhecidos são apresentados como `default`. A validação no servidor não converte valores recebidos em classes CSS ou estilos arbitrários. A mesma autorização de edição, CSRF e protecção contra alterações concorrentes continuam aplicáveis. A opção é guardada no histórico; recuperar uma versão anterior à funcionalidade usa o fundo padrão. O autosave de texto não altera o fundo guardado. A publicação e o agendamento existentes preservam a escolha.

Na página individual, o contentor `.article-paper` só existe quando foi escolhido papel antigo e inclui título, capa e conteúdo editorial, incluindo referências. A partilha, os comentários, artigos relacionados, cabeçalho, navegação, publicidade e rodapé ficam fora desse contentor. Os cartões de artigos, pesquisa e a Revista Científica não usam o novo fundo. A preferência do visitante por tema claro/escuro não modifica a escolha editorial.

**Implantação:** a migração aditiva `20261021_06`, após `20261020_05`, acrescenta apenas `article.background VARCHAR(20) NOT NULL DEFAULT 'default'`. Artigos anteriores recebem o fundo padrão; não é necessário regravar nem republicar conteúdo. Faça backup e ensaie a migração numa cópia da base. No ambiente da nova versão, com o `DATABASE_URL` já configurado, execute:

```bash
python -m alembic upgrade head
python -m alembic current
```

O resultado esperado é `20261021_06 (head)`. Aplique a migração com o código da nova versão antes de servir tráfego, sobretudo se `AUTO_SCHEMA_UPGRADE` estiver desactivado. O mecanismo de compatibilidade de arranque já existente, `ensure_article_columns()`, reconhece também esta coluna; a migração é idempotente se a coluna já tiver sido acrescentada por esse mecanismo. Não altere `AUTO_SCHEMA_UPGRADE` para esta funcionalidade. No Coolify, publique a nova versão com a migração aplicada e confirme `/healthz`, a edição e a página pública de um artigo. Não há novas variáveis de ambiente nem alterações ao SMTP, Cloudflare ou agendamentos.

Testes específicos:

```bash
PYTHONPATH=tests:. python -m unittest test_article_backgrounds test_migrations test_article_history test_article_autosave -v
npx playwright test article-backgrounds.spec.js
```

A suite Python cobre criação, valores inválidos/ausentes, migração de artigos anteriores, persistência, isolamento entre artigos, âmbito do contentor público, permissões, CSRF, concorrência, histórico, autosave e publicação agendada. Os testes de navegador usam dados sintéticos numa base SQLite isolada e verificam selecção pelo teclado, pré-visualização sem gravação, gravação explícita, reabertura, largura de 320/768/1440 px, ambos os temas, contraste de leitura e preservação das superfícies globais. A implantação e a aparência na base de produção devem ser confirmadas após a publicação; os testes não acedem à produção.

### Vídeos como capas dos artigos (21/10/2026)

O editor existente inclui **Formato da capa**: «Imagem estática», «Vídeo animado» e «Vídeo com controlos». Reutiliza `article.image` como capa estática, reserva do vídeo e imagem para cartões, Open Graph, Twitter e dados estruturados. Reutiliza `article.cover_video` para o recurso de vídeo. Só acrescenta `article.cover_mode`; não cria biblioteca de recursos, armazenamento, publicação ou agendamento paralelos.

A opção interna `auto`, por omissão no modelo e na migração, conserva a interpretação histórica: artigos sem vídeo apresentam imagem; artigos com um vídeo anterior conservam a apresentação com controlos. O formulário só apresenta as três escolhas editoriais. Mudar para imagem mantém o vídeo associado; **Remover vídeo da capa** limpa a associação ao guardar, sem eliminar o recurso no Cloudinary. As escolhas ficam no histórico e são recuperadas como rascunho; versões anteriores sem `cover_mode` recuperam o comportamento histórico. O autosave continua limitado ao texto e não altera as opções da capa. Alterar a capa de conteúdo já aprovado continua sujeito à protecção editorial existente e pode exigir guardar como rascunho para nova revisão.

A pré-visualização reutiliza a imagem do formulário e o leitor usado na página pública. Ficheiros seleccionados são apresentados através de URLs `blob:` locais, sem upload ou gravação automática. As directivas `img-src` e `media-src` da CSP permitem esses recursos; a política de scripts, os nonces, CSRF e as permissões continuam aplicáveis. A gravação manual utiliza o carregamento existente no Cloudinary, com limite de **50 MB**, extensões MP4/WebM/OGG, verificação de MIME e assinatura, e confirmação de um recurso de vídeo descodificado com dimensões e duração positivas na resposta do serviço. Mantém a entrega MP4 já utilizada pelo carregamento; vídeos WebM previamente disponíveis também podem ser apresentados.

As ligações novas a ficheiros nativos devem corresponder à conta Cloudinary configurada, em `https://res.cloudinary.com/<conta>/video/upload/...`. Não são procuradas nem descarregadas pelo servidor URLs remotos arbitrários. Recursos nativos anteriores já associados continuam permitidos no modo com controlos. YouTube e Vimeo mantêm o suporte existente nesse modo, com carregamento do leitor só depois de interacção e uma opção para regressar à imagem de reserva. O modo animado exige um ficheiro nativo da conta Cloudinary. O projecto não possui um selector de biblioteca de vídeos; pode carregar um ficheiro ou usar uma ligação de um recurso da conta.

O vídeo nativo animado usa reprodução sem som, `loop` e `playsinline`, com botão de pausa/retoma por teclado. A imagem de reserva é prioritária e tem proporção definida. O vídeo só recebe o endereço ao iniciar a reprodução, quando está visível, e não inicia automaticamente com movimento reduzido, poupança de dados ou ligação 2G indicada pelo navegador. Sai do ecrã ou muda de separador: a animação pausa. Bloqueio de autoplay, erro de rede ou demora no arranque mantêm a imagem e permitem nova tentativa. O modo com controlos só inicia por acção do visitante, apresenta controlos nativos e conserva o enquadramento completo; a animação preenche o espaço da capa sem distorção. Os cartões/listagens continuam a usar apenas imagens e não descarregam vídeos de capa.

URLs Cloudinary da conta utilizam transformações de entrega `q_auto:good,w_1280,c_limit`; animações acrescentam `ac_none`, preservando o recurso original. A reprodução e a compatibilidade de codecs dependem do navegador e do ficheiro. Não se geram legendas, transcrições ou `VideoObject` fictícios: o editor deve manter explicações essenciais no artigo e fornecer as alternativas necessárias para vídeos informativos. As legendas/transcrições e o conteúdo audiovisual exigem revisão humana; testes automáticos de interface não certificam todo o conteúdo.

**Configuração:** usa as variáveis já existentes `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` e, opcionalmente, `CLOUDINARY_VIDEO_FOLDER`. Não introduz credenciais no frontend nem exige novas dependências, serviços, tarefas agendadas ou alterações ao Cloudflare. Sem armazenamento configurado, o carregamento apresenta erro e não substitui a capa guardada; imagens estáticas continuam disponíveis. Os testes do navegador configuram apenas um nome de conta sintético e interceptam a entrega dos vídeos; não usam credenciais reais.

**Migração e Coolify:** a revisão aditiva `20261021_07`, após `20261021_06`, acrescenta `cover_mode VARCHAR(24) NOT NULL DEFAULT 'auto'`, sem alterar imagens, URLs ou outros dados. Faça backup e ensaie numa cópia. Execute com o código da nova versão antes de servir tráfego:

```bash
python -m alembic upgrade head
python -m alembic current
```

Resultado esperado: `20261021_07 (head)`. O mecanismo de compatibilidade de arranque existente também reconhece a coluna; não altere `AUTO_SCHEMA_UPGRADE`. Publique a nova imagem no Coolify e confirme `/healthz`, um artigo antigo, um rascunho, uma capa animada e a imagem de partilha. Não há migrações destrutivas nem implantação automática em produção por esta alteração.

Testes: `tests/test_article_covers.py`, o cenário de actualização em `tests/test_migrations.py` e `tests/browser/article-covers.spec.js`, com registos sintéticos de `cover_fixture.py` e clips sem som gerados em `tests/fixtures/article-cover.mp4` e `.webm`. Os testes de carregamento simulam respostas/erros do SDK Cloudinary; os testes de reprodução usam um vídeo WebM real entregue por uma rota interceptada no navegador. A confirmação com a conta Cloudinary real e nos dispositivos finais deve ser feita após a implantação. O teste browser da moldura YouTube valida a integração com uma resposta simulada, não a disponibilidade do serviço externo.

### Capa animada no destaque da página inicial (21/10/2026)

O artigo principal de **Em destaque** também reproduz a capa quando o editor escolhe **Vídeo animado**. Reutiliza o vídeo, a imagem de reserva e o leitor acessível do artigo, sem novos campos ou migrações. A imagem e o título continuam a abrir o artigo; o botão de pausa é independente da ligação. Os modos de imagem e vídeo com controlos conservam a imagem estática na página inicial. Os outros cartões e listagens não carregam vídeos. Movimento reduzido, poupança de dados, falhas de reprodução e pausa fora do ecrã seguem as mesmas regras do leitor existente. Não há configurações adicionais no Coolify: publicar esta versão após a migração `20261021_07` já exigida pelas capas de vídeo.

O controlo sobreposto da capa usa agora um botão circular de 48 px com ícones de reproduzir/pausar. O nome acessível acompanha o estado, o foco permanece visível e o texto descritivo surge também na dica do botão. Aplica-se ao artigo, destaque e pré-visualização do editor, reutilizando o mesmo leitor.

### Limites e entrega da newsletter

A fila EditorialNotification passa a ter campanhas aprovadas/agendadas, estados persistentes e histórico de tentativas. A secção **Limites e entrega** em /admin/subscritores usa a permissão existente subscribers.manage e CSRF. Preparar não envia; aprovar e autorizar/agendar são passos separados. Os valores iniciais são 2500 destinatários por edição, 100 tentativas/hora UTC, 500/dia UTC, intervalo de 36 segundos e até três tentativas adicionais. O orçamento é partilhado por toda a fila SMTP, incluindo correio transaccional; quotas externas manuais mais restritivas prevalecem. Não são quotas confirmadas do fornecedor.

Reutiliza enviar-notificacoes periódico no Coolify, com bloqueio coordenado PostgreSQL. Aceitações são guardadas antes de QUIT; resultados incertos e claims abandonados não são reenviados automaticamente. A reconciliação exige evidência registada pelo responsável. Não existe garantia distribuída de entrega exactamente uma vez.

**Migração:** parar trabalhadores antigos, fazer backup e ensaiar a migração antes de executar `python -m alembic upgrade head` com a nova versão. O head desta revisão é 20261021_08. A migração preserva a fila e coloca campanhas legadas em preparação sem autorização de envio. Não executar o worker antigo sobre o esquema novo. Não há novas variáveis de ambiente, serviço pago ou mudança ao Dockerfile. Procedimento, limites, recuperação e testes: [docs/NEWSLETTER_DELIVERY.md](docs/NEWSLETTER_DELIVERY.md).

