# Analista de Ações Multi-Agente - Google ADK & Gemini

Este projeto implementa uma arquitetura de sistemas multi-agentes assíncronos baseados em grafos de execução para análise quantitativa e qualitativa de ativos da B3 (bolsa de valores brasileira) em tempo real. O sistema é construído utilizando o **Google Agent Development Kit (ADK)** e o **Google GenAI SDK (Gemini)**, integrando dados reais via Yahoo Finance e pesquisas na web via Google Search, com um frontend interativo em **Streamlit**.

---

## 🏗️ Arquitetura de Sistemas & Roteamento Dinâmico

O core do projeto foi desenhado sob princípios de engenharia de software clássicos para garantir robustez, concorrência segura e separação rígida de responsabilidades.

```
                  ┌───────────────────────┐
                  │   User Input (Query)  │
                  └───────────┬───────────┘
                              │
                    [contem_contexto_b3?]
                              │
             ┌────────────────┴────────────────┐
            Sim                               Não
             ▼                                 ▼
   ┌───────────────────┐             ┌─────────────────────┐
   │ Pipeline Workflow │             │ ConversationalAgent │
   └─────────┬─────────┘             └──────────┬──────────┘
             ├──────────────────────┐           │ (Diálogo Direto)
             ▼                      ▼           ▼
      StockResearcher     QuantSpecialistAgent  │
      (Google Search)      (yfinance B3 API)    │
             │                      │           │
             └──────────┬───────────┘           │
                        ▼                       │
                     [JoinNode]                 │
                        ▼                       │
               AgenteConsolidador               │
                        │                       │
                        ▼                       ▼
                  ┌───────────────────────────────┐
                  │    Output Consolidated UI     │
                  └───────────────────────────────┘
```

### 1. Roteador de Intenções (Intent Router)
O ponto de entrada analisa a query do usuário antes de acionar o motor de grafos. Usando heurísticas de regex e análise léxica em `contem_contexto_b3`, a aplicação classifica se o input possui contexto de mercado financeiro ou ticker B3 (ex: `VALE3`, `PETR4`):
*   **Query de Ação:** Aciona o `pipeline_workflow` multi-agente complexo em paralelo.
*   **Conversa Geral / Saudação:** Aciona o `ConversationalAgent` (`AssistenteConversacional`) de turno único, evitando processamento desnecessário, eliminando expanders vazios na interface e mantendo o diálogo fluído e natural.

### 2. Paralelismo Concorrente e Sincronização (`Workflow` & `JoinNode`)
Em queries corporativas de ações, o ADK inicializa um fluxo concorrente a partir do gatilho `"START"`:
*   **`StockResearcher` (LlmAgent):** Varre a internet via ferramenta integrada `google_search` para extrair notícias recentes e tendências de mercado.
*   **`QuantSpecialistAgent` (LlmAgent):** Conecta-se à API do Yahoo Finance via conector `get_stock_market_data` para obter métricas de valuation precisas (Preço, P/L, Dividend Yield real).
*   **`SincronizacaoPesquisa` (JoinNode):** Atua como uma barreira síncrona. Ele bloqueia o pipeline e aguarda que ambos os especialistas finalizem, agregando o estado síncrono da sessão. Isso elimina condições de corrida e falhas por chaves ausentes.
*   **`AgenteConsolidador` (LlmAgent):** Sintetiza os indicadores numéricos e as tendências qualitativas gerando o relatório final Markdown livre de alucinações.

### 3. Engenharia de Validação Defensiva (Pydantic)
*   **Validação de Input:** O `MarketQueryInput` possui um `@model_validator(mode="before")` para capturar e traduzir payloads brutos de string ou objetos `types.Content` de forma transparente.
*   **Validação de Output:** O `FinalAnalysisOutput` declara os campos de métricas opcionais com `default=None`. Se algum dado não estiver disponível ou for omitido pelo LLM (como P/L indisponível de empresas em recuperação), a validação do Pydantic passa com sucesso, eliminando travamentos de sessão.

---

## 📂 Layout Técnico do Repositório

O projeto adota o padrão universal de pacotes Python (`src/`):

```
├── .gitignore               # Exclusões de ambiente, credenciais e caches
├── pyproject.toml           #PEP 621 declarando dependências explicitamente
├── requirements.txt         # Referências rápidas de pip
├── README.md                # Esta documentação
├── docs/
│   └── arquitetura_e_fluxo.md  # Diagrama de sequência avançado e posts
├── src/
│   ├── __init__.py          # Inicializador de pacote Python
│   ├── main.py              # Orquestrador, lógica CLI e roteamento
│   ├── sub_agents.py        # Definição dos agentes especialistas (PEP 8)
│   ├── personal_tools.py    # Conectores robustos de APIs de mercado
│   └── app.py               # Frontend Streamlit (Tracer de execução em real-time)
```

---

## 🛠️ Instalação e Execução

### 1. Sincronizar o Ambiente
O projeto utiliza o gerenciador **`uv`**:

```bash
uv sync
```

### 2. Variáveis de Ambiente
Configure o arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY="SUA_CHAVE_API"
```

### 3. Como Executar

#### Modo 1: Interface Web Interativa (Streamlit)
Oferece acompanhamento visual do workflow de agentes com diagramas e tabelas em tempo real:

```bash
uv run streamlit run src/app.py
```

#### Modo 2: CLI por Argumentos (Automação)
```bash
uv run python src/main.py "Como está a situação recente da VALE3?"
```

#### Modo 3: CLI Iterativo (Terminal)
```bash
uv run python src/main.py
```
