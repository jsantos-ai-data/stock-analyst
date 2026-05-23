# Arquitetura de Sistemas & Fluxo do Pipeline Multi-Agente

Este documento descreve detalhadamente o design técnico e o fluxo operacional do pipeline de análise financeira automatizada do projeto `agent-with-google-adk`, desenvolvido com o framework moderno do **Google ADK** (Agent Development Kit).

---

## 🗺️ Visão Detalhada do Workflow (Fluxo do Agente)

O diagrama abaixo ilustra o ciclo de vida completo de uma consulta (Query), desde o acionamento pelo usuário no terminal ou navegador, passando pelo roteamento de intenções, a execução concorrente dos sub-agentes especialistas, o bloqueio síncrono no nó de barreira (`JoinNode`), a consolidação contextual e, finalmente, a renderização do relatório final.

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as 👤 Usuário (Terminal/Streamlit)
    participant CLI as 💻 main.py / app.py (Roteador)
    participant Conversa as 💬 ConversationalAgent (Diálogo Geral)
    participant ModelVal as 🛡️ MarketQueryInput (Pydantic Validator)
    participant Researcher as 🔍 StockResearcher (LlmAgent)
    participant Quant as 📊 QuantSpecialistAgent (LlmAgent)
    participant Join as 🧱 JoinNode (SincronizacaoPesquisa)
    participant Merger as 🧠 AgenteConsolidador (LlmAgent)
    participant YF as 📈 Yahoo Finance API
    participant Web as 🌐 Google Search Tool

    Usuario->>CLI: Envia mensagem ("Olá" vs " VALE3")
    
    alt Caso 1: Conversa Geral / Saudação (contem_contexto_b3 == False)
        CLI->>Conversa: Roteia para o Assistente Conversacional
        Conversa-->>Usuario: Responde diretamente e amigavelmente (Sem expanders técnicos)
    else Caso 2: Consulta Financeira de Ação (contem_contexto_b3 == True)
        CLI->>ModelVal: Passa a string de busca para validação
        Note over ModelVal: @model_validator(mode="before")<br/>Converte texto bruto em {"query": valor}
        ModelVal-->>CLI: Retorna dados estruturados e validados

        rect rgb(240, 248, 255)
            Note over CLI, Join: Execução Paralela Concorrente (START)
            par Ramo de Notícias e Tendências
                CLI->>Researcher: Aciona Agente de Pesquisa
                Researcher->>Web: Chama ferramenta google_search
                Web-->>Researcher: Retorna artigos e notícias da B3 recentes
                Researcher->>Join: Envia resumo curto para o estado (stock_research_result)
            and Ramo Quantitativo & Valuation
                CLI->>Quant: Aciona Analista Quantitativo
                Quant->>YF: Chama ferramenta get_stock_market_data
                Note over YF: Trata o ticker (ex: VALE3 -> VALE3.SA)<br/>Valida operadores de preço e dividendYield
                YF-->>Quant: Retorna métricas B3 (Preço, P/L, Yield correto)
                Quant->>Join: Envia dados e veredito quantitativo (final_financial_report)
            end
        end

        Note over Join: Barreira de Sincronização<br/>Aguardando término de ambos os predecessores...
        Join->>Merger: Dispara o nó de consolidação com o estado agregado de ambos os ramos
        
        Note over Merger: Sintetiza dados de entrada<br/>Sem adicionar conhecimento externo (Zero Alucinação)
        Merger-->>CLI: Emite Relatório Markdown Consolidado unificado
        CLI-->>Usuario: Exibe Relatório Final no Terminal / Chat UI
    end
```

---

## 🔍 Detalhamento das Etapas do Pipeline

### 1. Roteamento de Intenções Dinâmico (Intent Router)
O pipeline realiza uma análise léxica na entrada usando a função `contem_contexto_b3`. 
* Se a query for identificada como assunto geral ou saudação, ela é roteada diretamente para o `ConversationalAgent` que responde amigavelmente sem disparar agentes paralelos técnicos.
* Se a query possuir contexto de ativos ou tickers (ex: `VALE3`, `PETR4`), o pipeline completo baseado em grafos é acionado.

### 2. Validação Pydantic Defensiva
* O `MarketQueryInput` converte textos brutos ou objetos de conteúdo da API em esquemas estruturados por meio de um `@model_validator` com execução prévia (`mode="before"`).
* O `FinalAnalysisOutput` define campos opcionais com `default=None`. Isso impede que o sistema quebre caso o LLM decida omitir valores nulos na resposta (ex: P/L inexistente de empresas com prejuízo).

### 3. Paralelismo Concorrente e Sincronização
Os agentes de pesquisa e análise quantitativa rodam em paralelo. A sincronização segura do estado é operada pelo `SincronizacaoPesquisa` (`JoinNode`), que aguarda a conclusão de ambos os ramos concorrentes antes de disparar o consolidador final.
