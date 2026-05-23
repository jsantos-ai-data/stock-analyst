# app.py
import streamlit as st
import os
import sys
import json
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Garante que a pasta raiz do projeto está no path para imports absolutos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import root_agent, contem_contexto_b3
from src.sub_agents import ConversationalAgent

# Carrega o arquivo .env
load_dotenv()

# Configuração da página Streamlit
st.set_page_config(
    page_title="📈 Analista de Ações Multi-Agente - Google ADK",
    page_icon="🤖",
    layout="centered"
)

# Estilo visual moderno com Vanilla CSS injetado
st.markdown("""
<style>
    .reportview-container {
        background: #111;
    }
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    .stMarkdown h2 {
        color: #1E88E5;
        font-weight: 700;
        border-bottom: 2px solid #E0E0E0;
        padding-bottom: 8px;
        margin-top: 24px;
    }
    .stMarkdown h3 {
        color: #0D47A1;
        font-weight: 600;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Título da Aplicação
st.title("🤖 Analista de Ações Multi-Agente")
st.caption("Desenvolvido com Google ADK, Gemini 2.5 Flash e APIs reais de mercado da B3")

# Inicialização do Runner do Google ADK com o agente selecionado dinamicamente
def get_runner(agent):
    # Garante que a API key está presente
    if not os.environ.get("GEMINI_API_KEY"):
        st.warning("⚠️ GEMINI_API_KEY não foi encontrada no ambiente ou no arquivo .env!")
    
    app_name = "AnaliseFinanceiraApp" if agent == root_agent else "AssistenteConversacionalApp"
    return Runner(
        agent=agent,
        app_name=app_name,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações da IA")
    st.write("**Orquestrador:** `google.adk.workflow.Workflow`")
    st.write("**Modelo Base:** `gemini-2.5-flash` (Gemini Pro multimodal engine)")
    st.write("**Conector de Mercado:** `Yahoo Finance (yfinance)`")
    st.write("**Chave de API:** Configurada no `.env` ✅" if os.environ.get("GEMINI_API_KEY") else "Faltando chave ❌")
    st.markdown("---")
    
    st.subheader("💡 Dicas de Consulta")
    st.write("Digite o nome ou ticker de qualquer empresa listada na B3, como:")
    st.write("- *'Como está a situação recente da VALE3?'*")
    st.write("- *'Quero um resumo e múltiplos de valuation da PETR4.'*")
    st.write("- *'Análise quantitativa completa da WEGE3.'*")
    
    st.markdown("---")
    st.caption(
        "A arquitetura do workflow utiliza JoinNode para sincronizar as consultas concorrentes de mercado e sentimento."
    )

# 1. Inicializar o Histórico de Chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Olá! Eu sou o seu Analista Financeiro Multi-Agente. Digite o ticker ou a sua dúvida sobre alguma ação da B3 para iniciarmos a análise de mercado e múltiplos quantitativos em tempo real!",
        }
    ]

# 2. Exibir o Histórico de Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Atalhos rápidos de Consulta
st.write("") # Espaçador
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Análise VALE3 ⛏️"):
        st.session_state.temp_prompt = "Como está a situação recente da VALE3?"
with col2:
    if st.button("Análise PETR4 🛢️"):
        st.session_state.temp_prompt = "Quero um resumo e múltiplos de valuation da PETR4."
with col3:
    if st.button("Análise WEGE3 ⚡"):
        st.session_state.temp_prompt = "Faça uma análise quantitativa completa da WEGE3."

# Captura de input por clique nos botões de atalho
prompt = None
if "temp_prompt" in st.session_state and st.session_state.temp_prompt:
    prompt = st.session_state.temp_prompt
    del st.session_state.temp_prompt

# 4. Capturar a Entrada do Usuário via campo de Chat
if not prompt:
    prompt = st.chat_input("Insira sua dúvida sobre ações da B3...")

# Processamento do Prompt
if prompt:
    # Adicionar a mensagem do usuário ao histórico e exibi-la
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Execução do pipeline de acordo com a presença de contexto financeiro/ações
    is_market_query = contem_contexto_b3(prompt)
    if is_market_query:
        agent_to_run = root_agent
        spinner_msg = "🤖 Os agentes de inteligência estão trabalhando... Consultando B3 e Web..."
    else:
        agent_to_run = ConversationalAgent()
        spinner_msg = "🤖 Pensando..."
        
    runner = get_runner(agent_to_run)

    # Execução do pipeline multi-agente
    with st.chat_message("assistant"):
        # Contêineres reservados para renderizar os agentes intermediários em tempo real (apenas se for query de mercado)
        research_expander_placeholder = st.empty()
        quant_expander_placeholder = st.empty()
        
        with st.spinner(spinner_msg):
            try:
                import uuid
                unique_session_id = f"session_{uuid.uuid4().hex}"
                events = runner.run(
                    user_id="streamlit_user",
                    session_id=unique_session_id,
                    new_message=types.Content(
                        parts=[types.Part.from_text(text=prompt)]
                    )
                )
                
                final_report = ""
                
                for event in events:
                    if event.content and event.content.parts:
                        conteudo = "".join(part.text for part in event.content.parts if part.text)
                        if not conteudo.strip():
                            continue
                        
                        # Direciona os retornos dos sub-agentes intermediários para expanders interativos
                        if is_market_query:
                            if event.author == "PesquisadorDeAcoes":
                                with research_expander_placeholder.expander("🔍 Pesquisa de Notícias & Sentimento (StockResearcher)", expanded=False):
                                    st.markdown(conteudo)
                            elif event.author == "analista_quantitativo":
                                with quant_expander_placeholder.expander("📊 Métricas de Valuation B3 (QuantSpecialistAgent)", expanded=False):
                                    try:
                                        # Formata os dados de métricas como árvore interativa de JSON se válido
                                        metrics_data = json.loads(conteudo)
                                        st.json(metrics_data)
                                    except Exception:
                                        st.markdown(conteudo)
                            elif event.author == "AgenteConsolidador":
                                final_report += conteudo
                        else:
                            # Se for diálogo conversacional, captura diretamente o retorno do Assistente
                            if event.author == "AssistenteConversacional":
                                final_report += conteudo
                
                if final_report:
                    st.markdown(final_report)
                    st.session_state.messages.append({"role": "assistant", "content": final_report})
                else:
                    st.error("Desculpe, ocorreu um erro ao tentar processar a sua mensagem.")
            except Exception as e:
                st.error(f"Erro na execução do pipeline de agentes: {e}")
