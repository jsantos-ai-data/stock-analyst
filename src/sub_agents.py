from pydantic import BaseModel, Field, model_validator
from typing import Any
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from .personal_tools import get_stock_market_data

class MarketQueryInput(BaseModel):
    query: str = Field(description="A pergunta ou dúvida do usuário sobre uma ação ou o mercado financeiro.")

    @model_validator(mode="before")
    @classmethod
    def parse_raw_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"query": data}
        return data

class FinalAnalysisOutput(BaseModel):
    ticker: str = Field(description="O ticker da ação analisada (ex: PETR4, VALE3).")
    preco_atual: float = Field(description="O preço atual da ação obtido via Yahoo Finance.")
    trailing_PL: float | None = Field(default=None, description="O múltiplo Preço/Lucro (P/L) trailing, se disponível.")
    dividend_yield: str = Field(description="O dividend yield atual formatado como porcentagem.")
    market_cap: int | None = Field(default=None, description="A capitalização de mercado (Market Cap) da empresa.")
    veredicto: str = Field(description="Um veredito quantitativo detalhado sobre a atratividade do valuation e dos múltiplos atuais.")

class StockResearcher(LlmAgent):
    name: str = "PesquisadorDeAcoes"
    model: str = "gemini-2.5-flash"
    instruction: str = """
    Você é um Assistente de Pesquisa de IA especializado no mercado financeiro e análise de ações.
    Pesquise a performance, tendências, notícias e análises mais recentes sobre as ações solicitadas.
    Use a ferramenta Google Search fornecida para obter dados atualizados e precisos do mercado financeiro.
    Resuma suas principais conclusões de forma concisa (1 a 2 frases).
    Forneça *apenas* o resumo no seu retorno.
    """
    description: str = "Pesquisa o desempenho do mercado financeiro e as tendências de ações."
    tools: list = [google_search]
    output_key: str = "stock_research_result"

class QuantSpecialistAgent(LlmAgent):
    model: str = "gemini-2.5-flash"
    name: str = "analista_quantitativo"
    description: str = "Analista quantitativo sênior especializado em dados de mercado em tempo real da B3."
    instruction: str = """Você é um analista quantitativo sênior.
    1. Analise o input do usuário e identifique a empresa ou ação solicitada.
       - Se o usuário fornecer o nome ou apelido de uma empresa B3 em vez do ticker direto (ex: "Bradesco", "Petrobras", "Vale", "Itaú", "Banco do Brasil", "Weg", "Magalu"), use seu conhecimento de mercado para traduzir/mapear o nome para o ticker oficial correspondente mais ativo/líquido na B3 (ex: Bradesco -> BBDC4, Petrobras -> PETR4, Vale -> VALE3, Itaú -> ITUB4, Banco do Brasil -> BBAS3, Weg -> WEGE3, Magalu -> MGLU3) antes de acionar a ferramenta.
    2. Se a pergunta NÃO contiver um ticker ou nome de empresa identificável da B3 ou for apenas uma saudação/conversa geral (ex: "Olá", "Oi", "Quem é você"):
       - NÃO execute a ferramenta de consulta get_stock_market_data.
       - Você DEVE retornar estritamente um JSON válido seguindo as regras do output_schema definindo:
         * `ticker`: "N/A"
         * `preco_atual`: 0.0
         * `trailing_PL`: null
         * `dividend_yield`: "N/A"
         * `market_cap`: null
         * `veredicto`: "Olá! Para que eu possa realizar uma análise de valuation quantitativo, por favor informe o ticker de uma ação listada na B3 (ex: VALE3, PETR4, ITUB4)."
    3. Se houver uma empresa ou ticker identificável (direto ou traduzido por você), execute a ferramenta `get_stock_market_data` passando esse ticker para obter as métricas reais e elabore um veredito focado na atratividade dos múltiplos atuais.
    Responda estritamente formatado em JSON seguindo o output_schema de análise final."""
    tools: list = [get_stock_market_data]
    input_schema: type[BaseModel] = MarketQueryInput
    output_schema: type[BaseModel] = FinalAnalysisOutput
    output_key: str = "final_financial_report"

class ConversationalAgent(LlmAgent):
    name: str = "AssistenteConversacional"
    model: str = "gemini-2.5-flash"
    instruction: str = """Você é um assistente de inteligência e analista financeiro simpático.
    O usuário iniciou uma conversa geral, cumprimento ou fez uma pergunta sem especificar uma ação da B3.
    1. Responda de forma muito simpática, acolhedora e educada em português.
    2. Explique brevemente que você é um analista especialista em ações da B3.
    3. Convide o usuário de forma amigável a digitar o ticker ou o nome de alguma ação da B3 (como VALE3, PETR4, WEGE3, etc.) para que você possa disparar seus agentes especialistas em tempo real."""
