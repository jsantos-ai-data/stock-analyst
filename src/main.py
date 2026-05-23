from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import Workflow, JoinNode
from google.genai import types

from src.sub_agents import StockResearcher, QuantSpecialistAgent

# Define o modelo padrão utilizado pelos agentes
GEMINI_MODEL = "gemini-2.5-flash"

# Instancia as classes dos sub-agentes utilizando o modelo centralizado
pesquisador = StockResearcher(model=GEMINI_MODEL)
analista_quant = QuantSpecialistAgent(model=GEMINI_MODEL)

# JoinNode para sincronizar a execução paralela dos agentes antes de chamar o merger
join_node = JoinNode(name="SincronizacaoPesquisa")

# --- 1. Agente Consolidador (Merger) ---
# Consolida os resultados gravados no estado em um relatório final integrado
merger_agent = LlmAgent(
    name="AgenteConsolidador",
    model=GEMINI_MODEL,
    instruction="""
    Você é um Assistente de IA responsável por consolidar análises financeiras e de mercado sobre ações em um relatório unificado.
    
    Sua tarefa principal é sintetizar as informações de pesquisa de mercado e a análise quantitativa fornecidas abaixo, gerando um relatório estruturado e coerente.
    
    **Importante: Toda a sua resposta DEVE ser baseada exclusivamente nas informações fornecidas nos 'Resumos de Entrada' abaixo. Não adicione qualquer conhecimento externo, suposição ou dados que não estejam presentes nesses textos.**
    
    **Resumos de Entrada:**
    
    *   **Análise de Mercado (Notícias e Tendências):**
        {stock_research_result}
    
    *   **Análise Quantitativa e Veredito Financeiro:**
        {final_financial_report}
    
    **Formato de Saída (Use exatamente esta estrutura em Markdown):**
    
    ## Relatório Consolidado de Análise de Ação
    
    ### 1. Visão de Mercado (Notícias e Tendências)
    (Baseado nos dados do PesquisadorDeAcoes)
    [Sintetize as informações obtidas pelo agente PesquisadorDeAcoes.]
    
    ### 2. Análise Quantitativa e Múltiplos
    (Baseado nos dados do Analista Quantitativo)
    [Sintetize as informações obtidas pelo Analista Quantitativo, incluindo os múltiplos de valuation.]
    
    ### 3. Veredito e Conclusão Geral
    [Forneça a recomendação ou conclusão final, conectando apenas os pontos descritos acima.]
    
    Gere apenas o relatório estruturado em português, seguindo estritamente o formato acima.
    """,
    description="Combina as análises dos agentes de pesquisa e quantitativo em um relatório financeiro integrado e fundamentado."
)

# --- 2. Workflow Orchestrator ---
# Este é o agente raiz. Ele executa a pesquisa paralela e depois consolida tudo via merger_agent.
pipeline_workflow = Workflow(
    name="PipelineDeAnaliseFinanceira",
    edges=[
        ("START", pesquisador),
        ("START", analista_quant),
        (pesquisador, join_node),
        (analista_quant, join_node),
        (join_node, merger_agent),
    ],
    description="Orquestra e coordena a pesquisa paralela e consolida a síntese financeira final."
)

def contem_contexto_b3(query: str) -> bool:
    """Verifica se a query do usuário contém algum ticker de ação ou palavra-chave de B3."""
    import re
    query_lower = query.lower().strip()
    
    # Busca por padrão clássico de ticker (4 letras + 1 ou 2 dígitos)
    has_ticker = bool(re.search(r'\b[a-zA-Z]{4}\d{1,2}\b', query_lower))
    
    # Palavras-chave corporativas comuns da B3
    keywords = ["vale", "petrobras", "petro", "itaú", "itau", "wege", "bradesco", "mglu", "magalu", "ações", "ação", "dividendos", "yield", "b3", "ticker"]
    has_keywords = any(kw in query_lower for kw in keywords)
    
    return has_ticker or has_keywords

root_agent = pipeline_workflow

if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    
    # Carrega o arquivo .env
    load_dotenv()
    
    # Garante que a chave da API está configurada
    if not os.environ.get("GEMINI_API_KEY"):
        print("AVISO: GEMINI_API_KEY não foi encontrada no ambiente ou no arquivo .env.")
    
    # Aceita query dinâmica via argumentos de terminal ou prompt iterativo
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        default_query = "Como está a situação recente da VALE3?"
        try:
            user_input = input(f"Digite a sua consulta sobre ações [{default_query}]: ").strip()
            query = user_input if user_input else default_query
        except (KeyboardInterrupt, EOFError):
            query = default_query
            print()
            
    # Seleção dinâmica do agente com base no contexto
    if contem_contexto_b3(query):
        agent_to_run = root_agent
        app_name = "AnaliseFinanceiraApp"
        print(f"Iniciando pipeline de análise integrada para a consulta: '{query}'\n")
    else:
        from src.sub_agents import ConversationalAgent
        agent_to_run = ConversationalAgent(model=GEMINI_MODEL)
        app_name = "AssistenteConversacionalApp"
        print(f"Iniciando diálogo geral para a consulta: '{query}'\n")
        
    # Inicializa o executor do ADK
    runner = Runner(
        agent=agent_to_run,
        app_name=app_name,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    
    try:
        events = runner.run(
            user_id="usuario_teste",
            session_id="sessao_teste",
            new_message=types.Content(
                parts=[types.Part.from_text(text=query)]
            )
        )
        
        # Exibe as saídas geradas por cada agente no terminal
        for event in events:
            if event.content and event.content.parts:
                conteudo = "".join(part.text for part in event.content.parts if part.text)
                if conteudo.strip():
                    print(f"\n--- [{event.author}] ---")
                    print(conteudo.strip())
                    print("-" * 30)
    except Exception as e:
        print(f"\nErro durante a execução do pipeline: {e}")