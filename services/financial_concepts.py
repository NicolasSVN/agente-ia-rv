"""
Glossário de Conceitos Financeiros de Renda Variável.

Este módulo fornece:
1. Um dicionário abrangente de conceitos financeiros organizados em categorias
2. Expansão de query: converte termos do usuário em termos de busca mais amplos
3. Contexto para o agente: fornece descrições que ajudam o GPT a entender o que procurar

Usado pelo pipeline de busca (VectorStore) e pelo agente (OpenAIAgent) para
melhorar a recuperação semântica e a qualidade das respostas.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


FINANCIAL_CONCEPTS = [
    # =========================================================================
    # CATEGORIA 1: ESTRUTURA E ESTRATÉGIA DE FUNDOS
    # =========================================================================
    {
        "id": "estrategia_investimento",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "tese", "estratégia", "filosofia", "posicionamento", "como investe",
            "o que faz", "como funciona o fundo", "qual a tese", "tipo de investimento",
            "abordagem", "mandato", "foco do fundo"
        ],
        "termos_busca": [
            "estratégia", "posicionamento", "investimento", "alocação",
            "objetivo do fundo", "hedge fund", "incorporação", "tese",
            "filosofia de investimento", "mandato", "foco"
        ],
        "descricao": "A estratégia ou tese de investimento define como o fundo aloca seus recursos, quais tipos de ativos prioriza, em quais setores atua e qual sua filosofia de gestão. Inclui posicionamento de mercado, tipos de operações e objetivos de retorno.",
        "temas_relacionados": ["composicao_carteira", "gestao_fundo", "alocacao"]
    },
    {
        "id": "gestao_fundo",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "gestão", "gestora", "gestor", "quem gere", "quem administra",
            "gestão ativa", "gestão passiva", "equipe de gestão"
        ],
        "termos_busca": [
            "gestão", "gestor", "gestora", "administrador", "gestão ativa",
            "gestão passiva", "equipe", "management"
        ],
        "descricao": "A gestão do fundo refere-se a quem toma as decisões de investimento. Gestão ativa permite comprar e vender ativos sem aprovação dos cotistas. Gestão passiva segue o regulamento e requer aprovação em assembleia para mudanças.",
        "temas_relacionados": ["estrategia_investimento", "administrador"]
    },
    {
        "id": "objetivo_fundo",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "objetivo", "pra que serve", "qual o objetivo", "finalidade",
            "propósito", "meta do fundo"
        ],
        "termos_busca": [
            "objetivo", "auferir rendimentos", "aplicação de recursos",
            "finalidade", "propósito", "meta"
        ],
        "descricao": "O objetivo do fundo define sua finalidade principal, como auferir rendimentos, valorização de capital ou geração de renda recorrente.",
        "temas_relacionados": ["estrategia_investimento", "regulamento"]
    },
    {
        "id": "regulamento",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "regulamento", "regras", "prazo do fundo", "público alvo",
            "classificação", "anbima"
        ],
        "termos_busca": [
            "regulamento", "prazo do fundo", "público alvo", "classificação",
            "anbima", "condomínio fechado"
        ],
        "descricao": "O regulamento define as regras do fundo: prazo de duração, público-alvo, classificação ANBIMA, política de investimento e direitos dos cotistas.",
        "temas_relacionados": ["objetivo_fundo", "gestao_fundo"]
    },
    {
        "id": "benchmark",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "benchmark", "referência", "índice de referência", "comparação",
            "contra o que compara", "IFIX", "CDI", "Ibovespa"
        ],
        "termos_busca": [
            "benchmark", "IFIX", "CDI", "Ibovespa", "referência",
            "comparação", "índice"
        ],
        "descricao": "Benchmark é o índice de referência usado para avaliar o desempenho de um fundo. Para FIIs, normalmente é o IFIX. Para ações, o Ibovespa. Para renda fixa, o CDI.",
        "temas_relacionados": ["rentabilidade", "performance"]
    },
    {
        "id": "tipo_fii",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "tipo de fundo", "fundo de tijolo", "fundo de papel", "fundo de fundos",
            "FoF", "híbrido", "multiestratégia"
        ],
        "termos_busca": [
            "tijolo", "papel", "fundo de fundos", "FoF", "híbrido",
            "multiestratégia", "hedge fund", "recebíveis"
        ],
        "descricao": "FIIs podem ser de tijolo (imóveis físicos), papel (CRIs, LCIs), fundo de fundos (investe em outros FIIs) ou multiestratégia/híbrido (combina vários tipos).",
        "temas_relacionados": ["estrategia_investimento", "composicao_carteira"]
    },
    {
        "id": "dados_cadastrais",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "CNPJ", "código", "ticker", "início", "data de início",
            "quando começou", "código de negociação"
        ],
        "termos_busca": [
            "CNPJ", "código de negociação", "início do fundo", "ticker",
            "data de início"
        ],
        "descricao": "Dados cadastrais do fundo incluem CNPJ, código de negociação (ticker), data de início, administrador e gestor.",
        "temas_relacionados": ["gestao_fundo", "regulamento"]
    },
    {
        "id": "administrador",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "administrador", "quem administra", "administração do fundo",
            "escriturador", "custodiante"
        ],
        "termos_busca": [
            "administrador", "administração", "escriturador", "custodiante"
        ],
        "descricao": "O administrador é a instituição responsável pela parte burocrática e regulatória do fundo, diferente do gestor que toma decisões de investimento.",
        "temas_relacionados": ["gestao_fundo", "dados_cadastrais"]
    },
    # =========================================================================
    # CATEGORIA 2: PERFORMANCE E INDICADORES
    # =========================================================================
    {
        "id": "rentabilidade",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "rentabilidade", "retorno", "rendimento", "performance",
            "quanto rendeu", "quanto deu", "valorização", "resultado",
            "desempenho", "ganho"
        ],
        "termos_busca": [
            "rentabilidade", "retorno", "valorização", "performance",
            "desempenho", "resultado", "rendimento", "cota patrimonial ajustada",
            "cota de mercado ajustada"
        ],
        "descricao": "Rentabilidade mede o retorno total do investimento, incluindo valorização da cota e dividendos distribuídos. Pode ser expressa em termos absolutos ou relativos a um benchmark.",
        "temas_relacionados": ["benchmark", "dividend_yield", "cota"]
    },
    {
        "id": "dividend_yield",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "dividend yield", "DY", "yield", "rendimento percentual",
            "quanto paga", "quanto rende por mês", "retorno em dividendos"
        ],
        "termos_busca": [
            "dividend yield", "DY", "rendimento", "dividendo",
            "distribuição", "payout"
        ],
        "descricao": "Dividend Yield (DY) é a relação percentual entre os dividendos pagos e o preço da cota. DY = (Dividendos / Preço da cota) × 100. Usado para comparar retorno passivo entre fundos.",
        "temas_relacionados": ["dividendo", "cota", "rentabilidade"]
    },
    {
        "id": "cota",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "cota", "valor da cota", "preço da cota", "cota patrimonial",
            "valor patrimonial", "VP", "cota de mercado", "P/VP",
            "quanto vale", "preço"
        ],
        "termos_busca": [
            "cota", "cota patrimonial", "cota de mercado", "valor patrimonial",
            "P/VP", "preço", "valor", "patrimônio líquido"
        ],
        "descricao": "A cota é a fração do patrimônio do fundo. Cota patrimonial = patrimônio líquido / número de cotas. Cota de mercado = preço negociado na bolsa. P/VP compara as duas: abaixo de 1 = desconto.",
        "temas_relacionados": ["rentabilidade", "patrimonio"]
    },
    {
        "id": "patrimonio",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "patrimônio", "patrimônio líquido", "PL", "tamanho do fundo",
            "quanto tem", "valor de mercado", "market cap"
        ],
        "termos_busca": [
            "patrimônio líquido", "PL", "valor de mercado", "market cap",
            "patrimônio"
        ],
        "descricao": "Patrimônio líquido (PL) é o valor total dos ativos do fundo menos suas obrigações. O valor de mercado é o preço da cota × número de cotas.",
        "temas_relacionados": ["cota", "rentabilidade"]
    },
    {
        "id": "cap_rate",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "cap rate", "taxa de capitalização", "retorno do imóvel",
            "capitalization rate"
        ],
        "termos_busca": [
            "cap rate", "taxa de capitalização", "NOI", "aluguel",
            "valor do imóvel"
        ],
        "descricao": "Cap Rate = (Receita operacional líquida anual / Valor do imóvel) × 100. Mede o retorno anual de um imóvel baseado na receita de aluguel.",
        "temas_relacionados": ["noi", "rentabilidade", "vacancia"]
    },
    {
        "id": "noi",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "NOI", "resultado operacional", "receita líquida",
            "net operating income", "lucro operacional"
        ],
        "termos_busca": [
            "NOI", "resultado operacional", "receita", "despesa",
            "lucro operacional"
        ],
        "descricao": "NOI (Net Operating Income) é a receita bruta de aluguel menos despesas operacionais. É a base para calcular o Cap Rate.",
        "temas_relacionados": ["cap_rate", "resultado_operacional"]
    },
    {
        "id": "pvp",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "P/VP", "preço sobre valor patrimonial", "está caro",
            "está barato", "desconto", "ágio", "deságio"
        ],
        "termos_busca": [
            "P/VP", "valor patrimonial", "deságio", "ágio", "desconto",
            "prêmio"
        ],
        "descricao": "P/VP = Preço de mercado / Valor patrimonial. Abaixo de 1,0 = cota negociada com desconto (deságio). Acima de 1,0 = ágio (prêmio).",
        "temas_relacionados": ["cota", "patrimonio"]
    },
    {
        "id": "pl_ratio",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "P/L", "preço sobre lucro", "múltiplo", "valuation",
            "está caro ou barato"
        ],
        "termos_busca": [
            "P/L", "preço sobre lucro", "múltiplo", "valuation",
            "lucro por ação"
        ],
        "descricao": "P/L (Preço/Lucro) indica quantos anos de lucro são necessários para recuperar o investimento. P/L baixo pode indicar ação barata.",
        "temas_relacionados": ["roe", "rentabilidade"]
    },
    {
        "id": "roe",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "ROE", "retorno sobre patrimônio", "return on equity",
            "eficiência da empresa"
        ],
        "termos_busca": [
            "ROE", "retorno sobre patrimônio", "return on equity",
            "eficiência"
        ],
        "descricao": "ROE (Return on Equity) mede a rentabilidade do patrimônio líquido da empresa. ROE alto indica boa capacidade de gerar lucro com o capital dos sócios.",
        "temas_relacionados": ["pl_ratio", "rentabilidade"]
    },
    # =========================================================================
    # CATEGORIA 3: DISTRIBUIÇÃO E PROVENTOS
    # =========================================================================
    {
        "id": "dividendo",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "dividendo", "dividendos", "provento", "proventos",
            "quanto paga", "quanto distribui", "rendimento mensal",
            "quanto recebo", "pagamento", "distribuição"
        ],
        "termos_busca": [
            "dividendo", "distribuição", "rendimento", "provento",
            "por cota", "pagamento", "R$"
        ],
        "descricao": "Dividendos são a parcela dos lucros distribuída aos cotistas/acionistas. Em FIIs, a distribuição é geralmente mensal e isenta de IR para pessoa física.",
        "temas_relacionados": ["dividend_yield", "guidance", "payout"]
    },
    {
        "id": "guidance",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "guidance", "projeção", "estimativa de dividendo",
            "quanto vai pagar", "previsão", "expectativa de dividendo"
        ],
        "termos_busca": [
            "guidance", "projeção", "estimativa", "expectativa",
            "previsão", "dividendo futuro"
        ],
        "descricao": "Guidance é a projeção de dividendos futuros divulgada pela gestão do fundo. Indica quanto o fundo espera distribuir nos próximos meses.",
        "temas_relacionados": ["dividendo", "perspectivas"]
    },
    {
        "id": "payout",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "payout", "taxa de distribuição", "quanto do lucro distribui",
            "percentual distribuído"
        ],
        "termos_busca": [
            "payout", "distribuição", "percentual", "lucro distribuído"
        ],
        "descricao": "Payout é o percentual dos lucros que o fundo distribui como dividendos. FIIs são obrigados a distribuir pelo menos 95% dos lucros.",
        "temas_relacionados": ["dividendo", "resultado_operacional"]
    },
    {
        "id": "amortizacao",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "amortização", "devolução de capital", "redução de cota",
            "amortizar"
        ],
        "termos_busca": [
            "amortização", "devolução de capital", "redução", "resgate"
        ],
        "descricao": "Amortização é a devolução de parte do capital investido aos cotistas, além dos dividendos. Geralmente ocorre após venda de ativos.",
        "temas_relacionados": ["dividendo", "cota"]
    },
    {
        "id": "jcp",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "JCP", "juros sobre capital próprio", "juros sobre capital",
            "JSCP"
        ],
        "termos_busca": [
            "JCP", "juros sobre capital próprio", "JSCP"
        ],
        "descricao": "Juros sobre Capital Próprio (JCP) é uma forma de remuneração dos acionistas similar aos dividendos, mas com tratamento fiscal diferente (dedutível como despesa para a empresa).",
        "temas_relacionados": ["dividendo"]
    },
    # =========================================================================
    # CATEGORIA 4: COMPOSIÇÃO E CARTEIRA
    # =========================================================================
    {
        "id": "composicao_carteira",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "carteira", "composição", "alocação", "em que investe",
            "onde está investido", "portfólio", "ativos do fundo",
            "o que tem na carteira", "exposição"
        ],
        "termos_busca": [
            "carteira", "composição", "alocação", "exposição", "portfólio",
            "ativos", "investimento", "percentual", "% PL", "setor"
        ],
        "descricao": "A composição da carteira mostra em quais ativos o fundo está investido e em qual proporção. Inclui tipo de ativo, setor, indexador, prazo e concentração.",
        "temas_relacionados": ["estrategia_investimento", "cri", "diversificacao"]
    },
    {
        "id": "cri",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "CRI", "certificado de recebíveis", "recebíveis imobiliários",
            "papel", "crédito imobiliário", "operação estruturada"
        ],
        "termos_busca": [
            "CRI", "certificado de recebíveis", "operação estruturada",
            "recebíveis", "securitização", "emissor"
        ],
        "descricao": "CRI (Certificado de Recebíveis Imobiliários) é um título de crédito lastreado em recebíveis do mercado imobiliário. Usado por FIIs de papel como principal investimento.",
        "temas_relacionados": ["composicao_carteira", "ltv", "duration_conceito"]
    },
    {
        "id": "lci",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "LCI", "letra de crédito imobiliário", "LH",
            "letra hipotecária"
        ],
        "termos_busca": [
            "LCI", "letra de crédito", "LH", "letra hipotecária"
        ],
        "descricao": "LCI (Letra de Crédito Imobiliário) e LH (Letra Hipotecária) são títulos de renda fixa lastreados em créditos imobiliários. Isentos de IR para pessoa física.",
        "temas_relacionados": ["cri", "composicao_carteira"]
    },
    {
        "id": "indexador",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "indexador", "índice", "CDI+", "IPCA+", "prefixado",
            "taxa", "remuneração"
        ],
        "termos_busca": [
            "indexador", "CDI", "IPCA", "prefixado", "taxa",
            "remuneração", "spread"
        ],
        "descricao": "O indexador define como a remuneração de um título é calculada. CDI+ = juro pós-fixado + spread. IPCA+ = inflação + taxa real. Prefixado = taxa fixa definida na compra.",
        "temas_relacionados": ["cri", "duration_conceito"]
    },
    {
        "id": "duration_conceito",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "duration", "prazo médio", "vencimento médio",
            "quando recebe de volta", "prazo"
        ],
        "termos_busca": [
            "duration", "prazo médio", "vencimento", "prazo remanescente"
        ],
        "descricao": "Duration é o prazo médio ponderado para o investidor receber de volta o capital investido e juros. Duration maior = maior sensibilidade a mudanças nas taxas de juros.",
        "temas_relacionados": ["cri", "indexador"]
    },
    {
        "id": "vacancia",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "vacância", "ocupação", "taxa de ocupação", "vazio",
            "desocupado", "inquilino"
        ],
        "termos_busca": [
            "vacância", "ocupação", "ABL", "locação", "inquilino",
            "desocupado"
        ],
        "descricao": "Vacância é o percentual de área não locada de um imóvel. Vacância alta = menos receita de aluguel. Vacância pode ser física (área vazia) ou financeira (sem receita).",
        "temas_relacionados": ["abl", "cap_rate"]
    },
    {
        "id": "abl",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "ABL", "área bruta locável", "área do imóvel",
            "tamanho", "metros quadrados"
        ],
        "termos_busca": [
            "ABL", "área bruta locável", "m²", "metros quadrados",
            "área"
        ],
        "descricao": "ABL (Área Bruta Locável) é a área total de um empreendimento disponível para locação, medida em metros quadrados.",
        "temas_relacionados": ["vacancia", "cap_rate"]
    },
    {
        "id": "bts",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "BTS", "built to suit", "construção sob medida",
            "contrato atípico"
        ],
        "termos_busca": [
            "BTS", "built to suit", "contrato atípico", "construção sob medida"
        ],
        "descricao": "Built-to-Suit (BTS) é um contrato em que o imóvel é construído sob medida para um inquilino específico, com prazo longo e multas de rescisão elevadas.",
        "temas_relacionados": ["composicao_carteira", "vacancia"]
    },
    {
        "id": "subscricao",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "subscrição", "oferta", "emissão de cotas", "follow-on",
            "captação", "novas cotas", "direito de subscrição"
        ],
        "termos_busca": [
            "subscrição", "oferta", "emissão", "captação", "novas cotas",
            "direito de subscrição", "preço de subscrição"
        ],
        "descricao": "Subscrição é o processo de emissão de novas cotas para captar recursos. Cotistas existentes têm direito de preferência (direito de subscrição) para manter sua participação.",
        "temas_relacionados": ["cota", "patrimonio"]
    },
    # =========================================================================
    # CATEGORIA 5: RISCO E GARANTIAS
    # =========================================================================
    {
        "id": "ltv",
        "categoria": "RISCO",
        "termos_usuario": [
            "LTV", "loan to value", "endividamento", "alavancagem do CRI",
            "nível de garantia"
        ],
        "termos_busca": [
            "LTV", "loan to value", "garantia", "endividamento",
            "cobertura"
        ],
        "descricao": "LTV (Loan-to-Value) = Valor da dívida / Valor do imóvel em garantia. LTV de 60% significa que a dívida é 60% do valor do imóvel. Quanto menor o LTV, mais segura a operação.",
        "temas_relacionados": ["cri", "garantias", "risco_credito"]
    },
    {
        "id": "garantias",
        "categoria": "RISCO",
        "termos_usuario": [
            "garantia", "garantias", "colateral", "alienação fiduciária",
            "fiança", "cobertura", "segurança"
        ],
        "termos_busca": [
            "garantia", "alienação fiduciária", "colateral", "cobertura",
            "fiança", "cessão fiduciária"
        ],
        "descricao": "Garantias são os ativos dados como segurança em operações de crédito (CRIs). Incluem alienação fiduciária de imóveis, cessão fiduciária de recebíveis e fianças.",
        "temas_relacionados": ["ltv", "cri", "risco_credito"]
    },
    {
        "id": "risco_credito",
        "categoria": "RISCO",
        "termos_usuario": [
            "risco de crédito", "inadimplência", "calote", "default",
            "risco do emissor", "rating"
        ],
        "termos_busca": [
            "risco de crédito", "inadimplência", "default", "rating",
            "classificação de risco"
        ],
        "descricao": "Risco de crédito é a possibilidade de o devedor não pagar suas obrigações. Em FIIs de papel, refere-se ao risco dos emissores dos CRIs.",
        "temas_relacionados": ["ltv", "garantias"]
    },
    {
        "id": "diversificacao",
        "categoria": "RISCO",
        "termos_usuario": [
            "diversificação", "concentração", "risco de concentração",
            "quantos ativos", "pulverizado"
        ],
        "termos_busca": [
            "diversificação", "concentração", "exposição", "setor",
            "pulverizado", "distribuição"
        ],
        "descricao": "Diversificação é a estratégia de distribuir investimentos entre diferentes ativos, setores e regiões para reduzir o risco. Menor concentração = menor risco específico.",
        "temas_relacionados": ["composicao_carteira", "risco_credito"]
    },
    {
        "id": "hedge",
        "categoria": "RISCO",
        "termos_usuario": [
            "hedge", "proteção", "proteger a carteira", "travar preço",
            "seguro", "cobertura de risco"
        ],
        "termos_busca": [
            "hedge", "proteção", "cobertura", "seguro", "travar"
        ],
        "descricao": "Hedge é uma estratégia de proteção contra riscos de mercado, usando instrumentos financeiros (opções, futuros) para limitar perdas potenciais.",
        "temas_relacionados": ["opcoes_basico", "collar", "volatilidade"]
    },
    {
        "id": "volatilidade",
        "categoria": "RISCO",
        "termos_usuario": [
            "volatilidade", "oscilação", "instabilidade", "risco de mercado",
            "variação", "sobe e desce", "IV", "volatilidade implícita"
        ],
        "termos_busca": [
            "volatilidade", "oscilação", "variação", "risco", "IV",
            "volatilidade implícita"
        ],
        "descricao": "Volatilidade mede a intensidade das oscilações de preço de um ativo. Alta volatilidade = maiores oscilações. Volatilidade implícita (IV) é usada na precificação de opções.",
        "temas_relacionados": ["hedge", "gregas_vega"]
    },
    # =========================================================================
    # CATEGORIA 6: MERCADO E NEGOCIAÇÃO
    # =========================================================================
    {
        "id": "liquidez",
        "categoria": "MERCADO",
        "termos_usuario": [
            "liquidez", "volume", "giro", "fácil de vender",
            "negociação", "quanto negocia"
        ],
        "termos_busca": [
            "liquidez", "volume", "giro", "negociação", "transação",
            "compra e venda"
        ],
        "descricao": "Liquidez é a facilidade de comprar ou vender um ativo sem afetar significativamente seu preço. Maior volume de negociação = maior liquidez.",
        "temas_relacionados": ["spread_mercado", "cotacao"]
    },
    {
        "id": "spread_mercado",
        "categoria": "MERCADO",
        "termos_usuario": [
            "spread", "diferença de preço", "bid ask", "compra e venda",
            "book de ofertas"
        ],
        "termos_busca": [
            "spread", "bid", "ask", "book de ofertas", "compra e venda"
        ],
        "descricao": "Spread é a diferença entre o melhor preço de compra (bid) e o melhor preço de venda (ask). Spread menor = mercado mais líquido.",
        "temas_relacionados": ["liquidez"]
    },
    {
        "id": "cotacao",
        "categoria": "MERCADO",
        "termos_usuario": [
            "cotação", "preço atual", "quanto está", "quanto custa",
            "valor de mercado", "preço de tela"
        ],
        "termos_busca": [
            "cotação", "preço", "valor de mercado", "cota de mercado"
        ],
        "descricao": "Cotação é o preço de um ativo no mercado em determinado momento, definido pela oferta e demanda.",
        "temas_relacionados": ["cota", "liquidez"]
    },
    {
        "id": "mercado_secundario",
        "categoria": "MERCADO",
        "termos_usuario": [
            "mercado secundário", "negociação em bolsa", "comprar na bolsa",
            "vender na bolsa"
        ],
        "termos_busca": [
            "mercado secundário", "bolsa", "B3", "negociação"
        ],
        "descricao": "Mercado secundário é onde os investidores negociam cotas/ações entre si após a emissão inicial. As transações ocorrem na B3.",
        "temas_relacionados": ["liquidez", "cotacao"]
    },
    {
        "id": "cotistas",
        "categoria": "MERCADO",
        "termos_usuario": [
            "cotistas", "investidores", "base de cotistas", "quantos investidores",
            "número de cotistas", "acionistas"
        ],
        "termos_busca": [
            "cotistas", "investidores", "base de cotistas", "número de cotistas",
            "crescimento"
        ],
        "descricao": "Cotistas são os investidores que detêm cotas de um fundo. O crescimento da base de cotistas indica popularidade e demanda pelo fundo.",
        "temas_relacionados": ["cota", "liquidez"]
    },
    # =========================================================================
    # CATEGORIA 7: DERIVATIVOS E OPÇÕES
    # =========================================================================
    {
        "id": "opcoes_basico",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "opção", "opções", "mercado de opções", "derivativo",
            "derivativos"
        ],
        "termos_busca": [
            "opção", "opções", "derivativo", "contrato", "direito",
            "obrigação"
        ],
        "descricao": "Opção é um contrato que dá ao comprador o direito (não a obrigação) de comprar ou vender um ativo a um preço predeterminado até uma data específica. Pode ser de compra (call) ou de venda (put).",
        "temas_relacionados": ["call", "put", "strike", "premio"]
    },
    {
        "id": "call",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "call", "opção de compra", "compra de call", "venda de call",
            "direito de comprar"
        ],
        "termos_busca": [
            "call", "opção de compra", "direito de comprar", "strike"
        ],
        "descricao": "Call (opção de compra) dá ao titular o direito de comprar um ativo pelo preço de exercício (strike). O comprador paga um prêmio. O vendedor (lançador) assume a obrigação de vender se exercido.",
        "temas_relacionados": ["put", "strike", "premio", "covered_call"]
    },
    {
        "id": "put",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "put", "opção de venda", "compra de put", "venda de put",
            "direito de vender", "proteção com put"
        ],
        "termos_busca": [
            "put", "opção de venda", "direito de vender", "strike",
            "proteção"
        ],
        "descricao": "Put (opção de venda) dá ao titular o direito de vender um ativo pelo preço de exercício (strike). Usada frequentemente como proteção (hedge) contra quedas.",
        "temas_relacionados": ["call", "strike", "premio", "hedge"]
    },
    {
        "id": "strike",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "strike", "preço de exercício", "exercício", "preço strike",
            "a quanto pode comprar/vender"
        ],
        "termos_busca": [
            "strike", "preço de exercício", "exercício"
        ],
        "descricao": "Strike (preço de exercício) é o preço predeterminado pelo qual o ativo pode ser comprado (call) ou vendido (put) ao exercer a opção.",
        "temas_relacionados": ["call", "put", "moneyness"]
    },
    {
        "id": "premio",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "prêmio", "prêmio da opção", "custo da opção",
            "quanto custa a opção", "valor do prêmio"
        ],
        "termos_busca": [
            "prêmio", "custo", "valor intrínseco", "valor extrínseco",
            "valor temporal"
        ],
        "descricao": "Prêmio é o valor pago pelo comprador da opção ao vendedor. Composto de valor intrínseco (diferença entre preço do ativo e strike) + valor extrínseco (tempo + volatilidade).",
        "temas_relacionados": ["call", "put", "gregas_theta"]
    },
    {
        "id": "moneyness",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "ITM", "OTM", "ATM", "no dinheiro", "fora do dinheiro",
            "dentro do dinheiro", "in the money", "out of the money",
            "at the money"
        ],
        "termos_busca": [
            "ITM", "OTM", "ATM", "in the money", "out of the money",
            "at the money", "no dinheiro"
        ],
        "descricao": "Moneyness classifica opções: ITM (in the money) = com valor intrínseco; ATM (at the money) = strike ≈ preço do ativo; OTM (out of the money) = sem valor intrínseco.",
        "temas_relacionados": ["strike", "premio"]
    },
    {
        "id": "vencimento_opcao",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "vencimento", "expiração", "data de vencimento",
            "quando vence", "série"
        ],
        "termos_busca": [
            "vencimento", "expiração", "série", "data de exercício"
        ],
        "descricao": "Vencimento é a data em que a opção expira. Após essa data, o direito deixa de existir. Opções americanas podem ser exercidas a qualquer momento até o vencimento; europeias apenas no vencimento.",
        "temas_relacionados": ["gregas_theta", "premio"]
    },
    # --- Gregas ---
    {
        "id": "gregas_delta",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "delta", "sensibilidade ao preço", "quanto a opção muda",
            "probabilidade de exercício"
        ],
        "termos_busca": [
            "delta", "sensibilidade", "variação", "preço do ativo"
        ],
        "descricao": "Delta mede quanto o preço da opção muda quando o ativo subjacente muda R$1. Call: delta entre 0 e 1. Put: delta entre -1 e 0. ATM ≈ 0,50. Delta também aproxima a probabilidade de exercício.",
        "temas_relacionados": ["gregas_gamma", "call", "put"]
    },
    {
        "id": "gregas_gamma",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "gamma", "aceleração do delta", "segunda derivada",
            "como delta muda"
        ],
        "termos_busca": [
            "gamma", "aceleração", "delta", "variação"
        ],
        "descricao": "Gamma mede a taxa de variação do delta. É maior para opções ATM próximas do vencimento. Alto gamma = delta muda rapidamente, bom para compradores, arriscado para vendedores.",
        "temas_relacionados": ["gregas_delta"]
    },
    {
        "id": "gregas_theta",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "theta", "decaimento temporal", "time decay",
            "perda de valor por tempo", "erosão"
        ],
        "termos_busca": [
            "theta", "decaimento temporal", "time decay", "valor extrínseco"
        ],
        "descricao": "Theta mede quanto a opção perde de valor por dia devido à passagem do tempo. Negativo para compradores (perdem valor), positivo para vendedores (ganham com o tempo). Acelera perto do vencimento.",
        "temas_relacionados": ["premio", "vencimento_opcao"]
    },
    {
        "id": "gregas_vega",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "vega", "sensibilidade à volatilidade", "volatilidade implícita",
            "IV crush"
        ],
        "termos_busca": [
            "vega", "volatilidade implícita", "IV", "sensibilidade"
        ],
        "descricao": "Vega mede quanto o preço da opção muda quando a volatilidade implícita (IV) muda 1%. Maior para opções ATM e de prazo mais longo. IV crush = queda brusca de volatilidade após eventos.",
        "temas_relacionados": ["volatilidade", "premio"]
    },
    {
        "id": "gregas_rho",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "rho", "sensibilidade a juros", "taxa de juros",
            "impacto da selic"
        ],
        "termos_busca": [
            "rho", "taxa de juros", "selic", "juros"
        ],
        "descricao": "Rho mede a sensibilidade do preço da opção a mudanças na taxa de juros. Mais relevante para opções de longo prazo (LEAPS). Calls se beneficiam de juros altos; puts de juros baixos.",
        "temas_relacionados": ["premio"]
    },
    # --- Estruturas de Opções ---
    {
        "id": "collar",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "collar", "fence", "cerca", "colar", "proteção com collar",
            "estratégia collar"
        ],
        "termos_busca": [
            "collar", "fence", "compra de put", "venda de call",
            "proteção", "corredor de preços"
        ],
        "descricao": "Collar (ou Fence/Cerca) combina: ações + compra de put (proteção contra queda) + venda de call (gera receita mas limita alta). Cria um 'corredor' de preços. Custo geralmente baixo ou zero (zero-cost collar).",
        "temas_relacionados": ["call", "put", "hedge"]
    },
    {
        "id": "call_spread",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "call spread", "trava de alta", "bull call spread",
            "spread de alta com call"
        ],
        "termos_busca": [
            "call spread", "trava de alta", "bull call", "spread vertical"
        ],
        "descricao": "Call Spread (trava de alta): compra call com strike menor + vende call com strike maior. Aposta em alta moderada com risco limitado. Lucro máximo = diferença entre strikes - prêmio pago.",
        "temas_relacionados": ["call", "put_spread"]
    },
    {
        "id": "put_spread",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "put spread", "trava de baixa", "bear put spread",
            "spread de baixa com put"
        ],
        "termos_busca": [
            "put spread", "trava de baixa", "bear put", "spread vertical"
        ],
        "descricao": "Put Spread (trava de baixa): compra put com strike maior + vende put com strike menor. Aposta em queda moderada com risco limitado.",
        "temas_relacionados": ["put", "call_spread"]
    },
    {
        "id": "butterfly",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "butterfly", "borboleta", "estratégia borboleta",
            "butterfly spread"
        ],
        "termos_busca": [
            "butterfly", "borboleta", "3 strikes", "compra e vende calls"
        ],
        "descricao": "Butterfly usa 4 opções com 3 strikes: compra 1 call baixo + vende 2 calls no meio + compra 1 call alto. Lucro máximo quando ativo fica no strike médio. Risco limitado, zona de lucro estreita.",
        "temas_relacionados": ["condor", "opcoes_basico"]
    },
    {
        "id": "condor",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "condor", "iron condor", "estratégia condor",
            "condor de ferro"
        ],
        "termos_busca": [
            "condor", "iron condor", "4 strikes", "venda de put e call"
        ],
        "descricao": "Condor usa 4 opções com 4 strikes diferentes. Iron Condor: vende put OTM + vende call OTM + compra put mais OTM + compra call mais OTM. Lucro quando ativo fica entre os strikes vendidos. Zona de lucro mais ampla que butterfly.",
        "temas_relacionados": ["butterfly", "opcoes_basico"]
    },
    {
        "id": "straddle",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "straddle", "compra de straddle", "venda de straddle",
            "aposta na volatilidade"
        ],
        "termos_busca": [
            "straddle", "compra call e put", "mesmo strike",
            "volatilidade"
        ],
        "descricao": "Straddle: compra call + put no MESMO strike. Long straddle lucra com movimento grande em qualquer direção. Short straddle lucra quando ativo fica parado. Ideal antes de eventos de alta volatilidade.",
        "temas_relacionados": ["strangle", "volatilidade"]
    },
    {
        "id": "strangle",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "strangle", "compra de strangle", "venda de strangle"
        ],
        "termos_busca": [
            "strangle", "compra call OTM e put OTM", "strikes diferentes"
        ],
        "descricao": "Strangle: compra call OTM + put OTM com strikes DIFERENTES. Mais barato que straddle mas precisa de movimento maior para lucrar. Long strangle = aposta em volatilidade. Short strangle = aposta em mercado lateral.",
        "temas_relacionados": ["straddle", "volatilidade"]
    },
    {
        "id": "covered_call",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "covered call", "venda coberta", "lançamento coberto",
            "renda com opções", "vender call coberta"
        ],
        "termos_busca": [
            "covered call", "venda coberta", "lançamento coberto",
            "renda", "prêmio"
        ],
        "descricao": "Covered Call (venda coberta): possui ações + vende call OTM. Gera renda extra com o prêmio recebido. Se exercida, vende as ações pelo strike. Ideal para gerar renda em mercado lateral ou ligeiramente altista.",
        "temas_relacionados": ["call", "premio"]
    },
    {
        "id": "cash_secured_put",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "cash secured put", "venda de put coberta", "put cash secured",
            "comprar ação mais barata"
        ],
        "termos_busca": [
            "cash secured put", "venda de put", "caixa reservado",
            "aquisição"
        ],
        "descricao": "Cash-Secured Put: vende put com dinheiro reservado para comprar as ações se exercida. Gera renda com o prêmio. Se exercida, compra ações a um preço efetivo menor (strike - prêmio). Estratégia para 'ser pago enquanto espera'.",
        "temas_relacionados": ["put", "premio"]
    },
    {
        "id": "contrato_futuro",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "futuro", "contrato futuro", "mercado futuro",
            "mini índice", "mini dólar", "ajuste diário"
        ],
        "termos_busca": [
            "futuro", "contrato futuro", "mercado futuro", "ajuste diário",
            "margem de garantia"
        ],
        "descricao": "Contrato futuro é um acordo de compra/venda de um ativo em data futura a preço fixado hoje. Possui ajuste diário de lucros e prejuízos. Exige margem de garantia. Usado para hedge ou especulação.",
        "temas_relacionados": ["hedge", "alavancagem"]
    },
    {
        "id": "swap",
        "categoria": "DERIVATIVOS",
        "termos_usuario": [
            "swap", "troca de rendimentos", "swap cambial",
            "swap de juros"
        ],
        "termos_busca": [
            "swap", "troca", "câmbio", "CDI", "juros"
        ],
        "descricao": "Swap é um acordo de troca de rendimentos entre dois ativos diferentes (ex: câmbio por CDI). Usado para hedge cambial ou para trocar indexadores de dívidas.",
        "temas_relacionados": ["hedge", "contrato_futuro"]
    },
    # =========================================================================
    # CATEGORIA 8: OPERACIONAL E TRIBUTAÇÃO
    # =========================================================================
    {
        "id": "taxa_administracao",
        "categoria": "OPERACIONAL",
        "termos_usuario": [
            "taxa de administração", "quanto cobra", "custo do fundo",
            "taxa de gestão", "fee"
        ],
        "termos_busca": [
            "taxa de administração", "administração", "custo", "fee",
            "% ao ano"
        ],
        "descricao": "Taxa de administração é o percentual cobrado anualmente sobre o patrimônio líquido do fundo para remunerar gestor e administrador.",
        "temas_relacionados": ["taxa_performance", "resultado_operacional"]
    },
    {
        "id": "taxa_performance",
        "categoria": "OPERACIONAL",
        "termos_usuario": [
            "taxa de performance", "performance fee", "taxa sobre lucro",
            "taxa de desempenho"
        ],
        "termos_busca": [
            "taxa de performance", "performance", "benchmark", "excedente"
        ],
        "descricao": "Taxa de performance é cobrada sobre o retorno que excede o benchmark. Ex: 20% sobre o que exceder o IFIX. Nem todos os fundos cobram.",
        "temas_relacionados": ["taxa_administracao", "benchmark"]
    },
    {
        "id": "resultado_operacional",
        "categoria": "OPERACIONAL",
        "termos_usuario": [
            "resultado operacional", "receita", "despesa", "DRE",
            "demonstrativo", "balanço", "lucro do fundo", "quanto lucrou"
        ],
        "termos_busca": [
            "resultado operacional", "receita", "despesa", "lucro",
            "resultado por cota", "DRE"
        ],
        "descricao": "Resultado operacional mostra as receitas (aluguéis, juros de CRIs) menos despesas (administração, operacionais) do fundo. O resultado por cota indica quanto cada cota gerou de lucro.",
        "temas_relacionados": ["taxa_administracao", "dividendo"]
    },
    {
        "id": "ir_renda_variavel",
        "categoria": "OPERACIONAL",
        "termos_usuario": [
            "imposto", "IR", "imposto de renda", "tributação",
            "quanto pago de imposto", "isento", "isenção"
        ],
        "termos_busca": [
            "IR", "imposto", "tributação", "isenção", "isento",
            "DARF", "ganho de capital"
        ],
        "descricao": "Tributação em RV: Ações swing trade 15%, day trade 20%. FIIs: rendimentos isentos (PF, mín 50 cotistas), ganho de capital 20%. Opções: 15% swing, 20% day trade. IR é pago via DARF até último dia útil do mês seguinte.",
        "temas_relacionados": ["dividendo"]
    },
    {
        "id": "emolumentos",
        "categoria": "OPERACIONAL",
        "termos_usuario": [
            "emolumentos", "custos de transação", "taxa da B3",
            "custódia", "corretagem"
        ],
        "termos_busca": [
            "emolumentos", "custódia", "corretagem", "taxa", "B3"
        ],
        "descricao": "Emolumentos são taxas cobradas pela B3 nas operações. Taxa de custódia pela guarda dos ativos. Corretagem pela execução das ordens (muitas corretoras oferecem taxa zero).",
        "temas_relacionados": ["mercado_secundario"]
    },
    # =========================================================================
    # CONCEITOS ADICIONAIS DE MERCADO
    # =========================================================================
    {
        "id": "ipo",
        "categoria": "MERCADO",
        "termos_usuario": [
            "IPO", "abertura de capital", "oferta pública inicial",
            "estreia na bolsa"
        ],
        "termos_busca": [
            "IPO", "abertura de capital", "oferta pública", "estreia"
        ],
        "descricao": "IPO (Initial Public Offering) é a oferta pública inicial de ações quando uma empresa abre capital na bolsa pela primeira vez.",
        "temas_relacionados": ["subscricao", "mercado_secundario"]
    },
    {
        "id": "etf",
        "categoria": "MERCADO",
        "termos_usuario": [
            "ETF", "fundo de índice", "exchange traded fund",
            "réplica de índice"
        ],
        "termos_busca": [
            "ETF", "fundo de índice", "réplica", "Ibovespa", "S&P 500"
        ],
        "descricao": "ETF (Exchange Traded Fund) é um fundo que replica um índice e é negociado na bolsa como uma ação. Permite diversificação instantânea com baixo custo.",
        "temas_relacionados": ["benchmark", "diversificacao"]
    },
    {
        "id": "bdr",
        "categoria": "MERCADO",
        "termos_usuario": [
            "BDR", "ação estrangeira", "ação americana",
            "Brazilian Depositary Receipt", "investir no exterior"
        ],
        "termos_busca": [
            "BDR", "depositary receipt", "estrangeira", "exterior"
        ],
        "descricao": "BDR (Brazilian Depositary Receipt) é um certificado que representa ações de empresas estrangeiras negociadas na B3. Permite investir em empresas globais sem conta no exterior.",
        "temas_relacionados": ["mercado_secundario"]
    },
    {
        "id": "analise_fundamentalista",
        "categoria": "MERCADO",
        "termos_usuario": [
            "análise fundamentalista", "fundamentos", "balanço",
            "demonstrações financeiras", "valor justo", "valuation"
        ],
        "termos_busca": [
            "fundamentalista", "balanço", "demonstrações", "valor justo",
            "valuation", "fundamentos"
        ],
        "descricao": "Análise fundamentalista avalia o valor intrínseco de uma empresa/fundo usando dados financeiros, contábeis e setoriais para determinar se está barato ou caro.",
        "temas_relacionados": ["pl_ratio", "roe", "pvp"]
    },
    {
        "id": "analise_tecnica",
        "categoria": "MERCADO",
        "termos_usuario": [
            "análise técnica", "gráfico", "grafista", "suporte",
            "resistência", "tendência", "candle"
        ],
        "termos_busca": [
            "análise técnica", "gráfico", "suporte", "resistência",
            "tendência", "candle", "média móvel"
        ],
        "descricao": "Análise técnica estuda padrões de preço e volume em gráficos para prever movimentos futuros. Usa indicadores como médias móveis, suporte/resistência e padrões de candle.",
        "temas_relacionados": ["cotacao", "volatilidade"]
    },
    {
        "id": "alavancagem",
        "categoria": "MERCADO",
        "termos_usuario": [
            "alavancagem", "alavancado", "margem", "operar alavancado",
            "margem de garantia"
        ],
        "termos_busca": [
            "alavancagem", "margem", "margem de garantia", "capital de terceiros"
        ],
        "descricao": "Alavancagem é o uso de capital de terceiros ou margem para ampliar o potencial de retorno (e risco). Permite operar volumes maiores que o capital disponível.",
        "temas_relacionados": ["contrato_futuro", "volatilidade"]
    },
    {
        "id": "stop_loss_gain",
        "categoria": "MERCADO",
        "termos_usuario": [
            "stop loss", "stop gain", "stop", "ordem automática",
            "proteger lucro", "limitar perda"
        ],
        "termos_busca": [
            "stop loss", "stop gain", "ordem", "automática", "limite"
        ],
        "descricao": "Stop Loss é uma ordem automática de venda quando o ativo atinge preço de perda máxima. Stop Gain vende ao atingir o preço-alvo de lucro. Essenciais para gestão de risco.",
        "temas_relacionados": ["hedge", "volatilidade"]
    },
    {
        "id": "day_trade",
        "categoria": "MERCADO",
        "termos_usuario": [
            "day trade", "scalp", "swing trade", "position",
            "operação de curto prazo", "intraday"
        ],
        "termos_busca": [
            "day trade", "swing trade", "position", "scalp", "intraday"
        ],
        "descricao": "Day trade = compra e venda no mesmo dia. Swing trade = operações de dias a semanas. Position = operações de meses a anos. Cada tipo tem tributação diferente.",
        "temas_relacionados": ["ir_renda_variavel", "analise_tecnica"]
    },
    {
        "id": "acoes_on_pn",
        "categoria": "MERCADO",
        "termos_usuario": [
            "ação ordinária", "ação preferencial", "ON", "PN",
            "direito a voto", "tipo de ação"
        ],
        "termos_busca": [
            "ordinária", "preferencial", "ON", "PN", "voto",
            "dividendo preferencial"
        ],
        "descricao": "Ações ordinárias (ON, terminam em 3) dão direito a voto. Ações preferenciais (PN, terminam em 4) têm prioridade no recebimento de dividendos mas geralmente sem voto.",
        "temas_relacionados": ["dividendo", "ipo"]
    },
    {
        "id": "blue_chip",
        "categoria": "MERCADO",
        "termos_usuario": [
            "blue chip", "large cap", "small cap", "mid cap",
            "empresa grande", "empresa pequena"
        ],
        "termos_busca": [
            "blue chip", "large cap", "small cap", "mid cap",
            "capitalização"
        ],
        "descricao": "Blue chips são ações de grandes empresas com alta liquidez (Petrobras, Vale). Small caps são de empresas menores com maior potencial de crescimento mas maior risco.",
        "temas_relacionados": ["liquidez", "volatilidade"]
    },
    # =========================================================================
    # CONCEITOS ESPECÍFICOS DE FIIs
    # =========================================================================
    {
        "id": "incorporacao",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "incorporação", "incorporação residencial", "desenvolvimento",
            "projeto imobiliário", "construção", "VGV"
        ],
        "termos_busca": [
            "incorporação", "residencial", "desenvolvimento", "projeto",
            "construção", "VGV", "obra", "lançamento"
        ],
        "descricao": "Incorporação imobiliária é o desenvolvimento de novos empreendimentos. VGV (Valor Geral de Vendas) é o valor total estimado das unidades. Inclui acompanhamento de obras, vendas e lançamentos.",
        "temas_relacionados": ["estrategia_investimento", "composicao_carteira"]
    },
    {
        "id": "recebimento_preferencial",
        "categoria": "COMPOSICAO",
        "termos_usuario": [
            "recebimento preferencial", "preferencial", "estrutura preferencial",
            "sênior", "mezanino", "subordinação"
        ],
        "termos_busca": [
            "preferencial", "sênior", "mezanino", "subordinação",
            "estrutura", "recebimento"
        ],
        "descricao": "Recebimento preferencial é uma estrutura onde o investidor tem prioridade no recebimento de retornos antes dos demais. Similar à subordinação em CRIs (sênior recebe primeiro).",
        "temas_relacionados": ["estrategia_investimento", "cri"]
    },
    {
        "id": "perspectivas",
        "categoria": "ESTRUTURA_FUNDO",
        "termos_usuario": [
            "perspectiva", "perspectivas", "outlook", "futuro",
            "o que esperar", "projeção", "cenário", "comentário do gestor"
        ],
        "termos_busca": [
            "perspectiva", "outlook", "projeção", "cenário", "futuro",
            "expectativa", "comentário do gestor", "balanço do ano"
        ],
        "descricao": "Perspectivas são as projeções e expectativas da gestão do fundo para o futuro, incluindo cenário macroeconômico, estratégia e projeções de dividendos.",
        "temas_relacionados": ["guidance", "estrategia_investimento"]
    },
    # =========================================================================
    # CATEGORIA 8: OPÇÕES E DERIVATIVOS (ESTRATÉGIAS E CONCEITOS ADICIONAIS)
    # =========================================================================
    {
        "id": "put_seca",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "put seca", "put a seco", "compra de put", "comprar put",
            "venda a descoberto com put"
        ],
        "termos_busca": [
            "put seca", "put a seco", "compra de put", "opção de venda",
            "aposta na queda", "risco limitado ao prêmio"
        ],
        "descricao": "Compra de put a seco é a aquisição de uma opção de venda sem possuir o ativo-objeto. O investidor aposta na queda do ativo. O risco é limitado ao prêmio pago e o ganho potencial é alto se o ativo cair significativamente.",
        "temas_relacionados": ["put", "premio", "call_seca"]
    },
    {
        "id": "call_seca",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "call seca", "call a seco", "compra de call", "comprar call"
        ],
        "termos_busca": [
            "call seca", "call a seco", "compra de call", "opção de compra",
            "aposta na alta", "risco limitado ao prêmio"
        ],
        "descricao": "Compra de call a seco é a aquisição de uma opção de compra sem possuir o ativo-objeto. O investidor aposta na alta do ativo. O risco é limitado ao prêmio pago e o ganho potencial é ilimitado se o ativo subir.",
        "temas_relacionados": ["call", "premio", "put_seca"]
    },
    {
        "id": "venda_put",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "vender put", "venda de put", "lançar put", "lançamento de put"
        ],
        "termos_busca": [
            "venda de put", "lançamento de put", "obrigação de compra",
            "exercício", "prêmio recebido"
        ],
        "descricao": "Venda de put (lançamento) é quando o investidor vende uma opção de venda, recebendo o prêmio. Se exercido, tem a obrigação de comprar o ativo pelo preço de exercício. Estratégia usada para comprar ações com desconto ou gerar renda.",
        "temas_relacionados": ["put", "premio", "venda_call"]
    },
    {
        "id": "venda_call",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "vender call", "venda de call", "lançar call", "lançamento de call",
            "lançamento coberto", "lançamento descoberto", "venda coberta"
        ],
        "termos_busca": [
            "venda de call", "lançamento de call", "lançamento coberto",
            "lançamento descoberto", "venda coberta", "obrigação de vender"
        ],
        "descricao": "Venda de call (lançamento) é quando o investidor vende uma opção de compra, recebendo o prêmio. Lançamento coberto = possui o ativo (risco limitado). Lançamento descoberto = não possui o ativo (risco ilimitado). Se exercido, tem obrigação de vender.",
        "temas_relacionados": ["call", "premio", "covered_call", "venda_put"]
    },
    {
        "id": "premio_opcao",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "prêmio da opção", "custo da opção", "preço da opção",
            "valor do prêmio"
        ],
        "termos_busca": [
            "prêmio", "prêmio da opção", "valor intrínseco", "valor extrínseco",
            "custo da opção", "preço da opção"
        ],
        "descricao": "Prêmio da opção é o valor pago pelo comprador ao vendedor da opção. É composto de valor intrínseco (diferença entre preço do ativo e strike quando favorável) + valor extrínseco (tempo restante + volatilidade implícita).",
        "temas_relacionados": ["premio", "gregas_theta", "volatilidade_implicita"]
    },
    {
        "id": "exercicio_opcao",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "exercício", "exercer", "dia de exercício", "vencimento de opção",
            "expiração", "data de vencimento"
        ],
        "termos_busca": [
            "exercício", "exercer opção", "dia de exercício", "vencimento",
            "expiração", "ITM", "OTM", "ATM"
        ],
        "descricao": "Exercício de opção é quando o titular utiliza seu direito de comprar (call) ou vender (put) o ativo pelo preço de exercício. Só faz sentido exercer opções ITM (in the money). Opções OTM expiram sem valor.",
        "temas_relacionados": ["moneyness", "vencimento_opcao", "strike"]
    },
    {
        "id": "opcao_americana_europeia",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "opção americana", "opção europeia", "americana", "europeia",
            "estilo da opção"
        ],
        "termos_busca": [
            "opção americana", "opção europeia", "estilo americano",
            "estilo europeu", "exercício antecipado"
        ],
        "descricao": "Opção americana pode ser exercida a qualquer momento até o vencimento. Opção europeia só pode ser exercida na data de vencimento. No Brasil, opções de ações são geralmente americanas e opções sobre índice são europeias.",
        "temas_relacionados": ["exercicio_opcao", "vencimento_opcao"]
    },
    {
        "id": "trava_alta",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "trava de alta", "bull spread", "call spread",
            "trava de alta com call"
        ],
        "termos_busca": [
            "trava de alta", "bull spread", "call spread",
            "compra e venda de call", "spread de alta"
        ],
        "descricao": "Trava de alta (bull spread) combina compra de call com strike menor e venda de call com strike maior. Lucra com alta moderada do ativo. Risco e retorno são limitados. O custo é menor que comprar call seca.",
        "temas_relacionados": ["call", "trava_baixa", "call_seca"]
    },
    {
        "id": "trava_baixa",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "trava de baixa", "bear spread", "put spread",
            "trava de baixa com put"
        ],
        "termos_busca": [
            "trava de baixa", "bear spread", "put spread",
            "compra e venda de put", "spread de baixa"
        ],
        "descricao": "Trava de baixa (bear spread) combina compra de put com strike maior e venda de put com strike menor. Lucra com queda moderada do ativo. Risco e retorno são limitados.",
        "temas_relacionados": ["put", "trava_alta", "put_seca"]
    },
    {
        "id": "borboleta",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "borboleta", "butterfly", "butterfly spread"
        ],
        "termos_busca": [
            "borboleta", "butterfly", "butterfly spread",
            "faixa de preço", "aposta lateral"
        ],
        "descricao": "Borboleta (butterfly spread) é uma estratégia que aposta que o ativo ficará numa faixa de preço específica no vencimento. Combina compra e venda de opções em três strikes diferentes. Risco e retorno são limitados.",
        "temas_relacionados": ["condor", "trava_alta", "trava_baixa"]
    },
    {
        "id": "gregas_opcoes",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "gregas", "sensibilidade da opção", "rho"
        ],
        "termos_busca": [
            "gregas", "delta", "gamma", "theta", "vega", "rho",
            "sensibilidade", "precificação de opções"
        ],
        "descricao": "As gregas medem a sensibilidade do preço da opção a diferentes fatores: Delta (preço do ativo), Gamma (variação do delta), Theta (tempo), Vega (volatilidade) e Rho (taxa de juros). Essenciais para gestão de risco em opções.",
        "temas_relacionados": ["gregas_delta", "gregas_gamma", "gregas_theta", "gregas_vega"]
    },
    {
        "id": "volatilidade_implicita",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "volatilidade implícita", "vol implícita", "implied volatility",
            "smile de volatilidade", "skew"
        ],
        "termos_busca": [
            "volatilidade implícita", "IV", "implied volatility",
            "smile de volatilidade", "skew", "expectativa de oscilação"
        ],
        "descricao": "Volatilidade implícita (IV) reflete a expectativa do mercado sobre a oscilação futura do ativo, embutida no preço das opções. Smile de volatilidade mostra como a IV varia por strike. Skew mostra a assimetria. IV alta = opções mais caras.",
        "temas_relacionados": ["gregas_vega", "volatilidade", "premio"]
    },
    {
        "id": "mini_contratos",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "mini contrato", "mini índice", "mini dólar",
            "WIN", "WDO", "IND", "DOL"
        ],
        "termos_busca": [
            "mini contrato", "mini índice", "mini dólar",
            "WIN", "WDO", "IND", "DOL", "day trade", "B3 futuros"
        ],
        "descricao": "Mini contratos são versões menores dos contratos futuros, acessíveis a investidores pessoa física. Mini índice (WIN) = 20% do contrato cheio de Ibovespa. Mini dólar (WDO) = 20% do contrato cheio de dólar. Os mais negociados na B3 para day trade e hedge.",
        "temas_relacionados": ["contrato_futuro", "margem_garantia", "hedge"]
    },
    {
        "id": "termo",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "a termo", "operação a termo", "contrato a termo",
            "termo de ações"
        ],
        "termos_busca": [
            "operação a termo", "contrato a termo", "termo de ações",
            "compra a termo", "venda a termo", "balcão"
        ],
        "descricao": "Operação a termo é um contrato para comprar ou vender um ativo em data futura a preço acordado. Diferente dos futuros, é negociado em balcão e não tem ajuste diário. Usado para alavancar posições em ações.",
        "temas_relacionados": ["contrato_futuro", "margem_garantia"]
    },
    {
        "id": "coe",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "COE", "certificado de operações estruturadas", "nota estruturada",
            "structured note", "capital protegido"
        ],
        "termos_busca": [
            "COE", "certificado de operações estruturadas", "nota estruturada",
            "capital protegido", "proteção de capital", "derivativo estruturado"
        ],
        "descricao": "COE (Certificado de Operações Estruturadas) combina elementos de renda fixa com derivativos. Pode oferecer proteção total ou parcial do capital investido. Permite acesso a estratégias sofisticadas de forma simplificada.",
        "temas_relacionados": ["operacao_estruturada", "hedge"]
    },
    {
        "id": "margem_garantia",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "margem", "margem de garantia", "chamada de margem",
            "margin call", "garantia de operação"
        ],
        "termos_busca": [
            "margem de garantia", "chamada de margem", "margin call",
            "garantia", "depósito de margem", "colateral"
        ],
        "descricao": "Margem de garantia é o capital ou ativos depositados como garantia para operar derivativos (futuros, opções vendidas, termo). Chamada de margem (margin call) ocorre quando a garantia se torna insuficiente e o investidor precisa depositar mais recursos.",
        "temas_relacionados": ["contrato_futuro", "venda_call", "venda_put"]
    },
    {
        "id": "mercado_opcoes",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "mercado de opções", "calls e puts", "call e put",
            "compra e venda de opções"
        ],
        "termos_busca": [
            "mercado de opções", "calls e puts", "opções de ações",
            "derivativos", "B3 opções"
        ],
        "descricao": "O mercado de opções é o ambiente onde se negociam contratos que conferem o direito de comprar (call) ou vender (put) um ativo a preço predeterminado. Na B3, as opções mais negociadas são sobre ações como PETR4, VALE3 e BOVA11.",
        "temas_relacionados": ["call", "put", "opcoes_basico"]
    },
    {
        "id": "operacao_estruturada",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "operação estruturada", "estruturada", "estrutura com opções",
            "montagem de operação"
        ],
        "termos_busca": [
            "operação estruturada", "estrutura com opções", "combinação de opções",
            "perfil de risco-retorno", "montagem de estratégia"
        ],
        "descricao": "Operação estruturada é a combinação de dois ou mais instrumentos financeiros (ações, opções, futuros) para atingir um perfil de risco-retorno específico. Exemplos: collar, trava, borboleta, condor.",
        "temas_relacionados": ["collar", "trava_alta", "trava_baixa", "borboleta"]
    },
    {
        "id": "financiamento_opcoes",
        "categoria": "OPCOES_DERIVATIVOS",
        "termos_usuario": [
            "financiamento", "financiamento com opções", "venda coberta de call",
            "income strategy"
        ],
        "termos_busca": [
            "financiamento com opções", "venda coberta de call", "covered call",
            "income strategy", "geração de renda", "lançamento coberto"
        ],
        "descricao": "Financiamento com opções (covered call) é a estratégia de gerar renda vendendo calls sobre ações que o investidor já possui. Se exercido, vende as ações pelo strike. Se não exercido, fica com o prêmio recebido como renda extra.",
        "temas_relacionados": ["covered_call", "venda_call", "call"]
    },
    # =========================================================================
    # CATEGORIA 9: RENDA FIXA
    # =========================================================================
    {
        "id": "tesouro_direto",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "tesouro direto", "NTN-B", "NTN-F", "LFT", "tesouro IPCA",
            "tesouro selic", "tesouro prefixado", "título público"
        ],
        "termos_busca": [
            "tesouro direto", "NTN-B", "NTN-F", "LFT", "tesouro IPCA",
            "tesouro selic", "tesouro prefixado", "título público", "governo federal"
        ],
        "descricao": "Tesouro Direto é o programa de compra de títulos públicos federais. Tesouro Selic (LFT) = pós-fixado à Selic. Tesouro IPCA+ (NTN-B) = inflação + taxa real. Tesouro Prefixado (NTN-F/LTN) = taxa fixa. Considerados os investimentos mais seguros do Brasil.",
        "temas_relacionados": ["copom_selic", "ipca", "marcacao_mercado"]
    },
    {
        "id": "cdb",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "CDB", "certificado de depósito bancário", "CDB DI", "CDB pré"
        ],
        "termos_busca": [
            "CDB", "certificado de depósito bancário", "CDB DI",
            "CDB prefixado", "CDB IPCA", "renda fixa bancária"
        ],
        "descricao": "CDB (Certificado de Depósito Bancário) é um título de renda fixa emitido por bancos. Pode ser pós-fixado (% do CDI), prefixado ou atrelado à inflação. Conta com garantia do FGC até R$250 mil por CPF/instituição.",
        "temas_relacionados": ["fgc", "copom_selic", "indexador"]
    },
    {
        "id": "debenture",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "debênture", "debêntures", "debênture incentivada",
            "dívida corporativa", "crédito privado"
        ],
        "termos_busca": [
            "debênture", "debênture incentivada", "dívida corporativa",
            "crédito privado", "emissão de dívida", "rating corporativo"
        ],
        "descricao": "Debêntures são títulos de dívida emitidos por empresas para captar recursos. Debêntures incentivadas (Lei 12.431) são isentas de IR para pessoa física. Crédito privado envolve risco do emissor e spread sobre títulos públicos.",
        "temas_relacionados": ["spread_credito", "risco_credito", "indexador"]
    },
    {
        "id": "cra",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "CRA", "certificado de recebíveis do agronegócio", "agronegócio"
        ],
        "termos_busca": [
            "CRA", "certificado de recebíveis do agronegócio",
            "recebíveis agrícolas", "agronegócio", "securitização"
        ],
        "descricao": "CRA (Certificado de Recebíveis do Agronegócio) é um título de renda fixa lastreado em recebíveis do setor agrícola. Isento de IR para pessoa física. Similar ao CRI, mas voltado ao agronegócio.",
        "temas_relacionados": ["cri", "debenture", "indexador"]
    },
    {
        "id": "marcacao_mercado",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "marcação a mercado", "MtM", "mark to market", "precificação",
            "variação de preço do título"
        ],
        "termos_busca": [
            "marcação a mercado", "MtM", "mark to market", "precificação",
            "variação de preço", "PU", "preço unitário"
        ],
        "descricao": "Marcação a mercado (MtM) é a atualização diária do preço de um título de renda fixa de acordo com as condições de mercado. Se as taxas de juros sobem, o preço do título cai (e vice-versa). Afeta quem vende antes do vencimento.",
        "temas_relacionados": ["curva_juros", "duration_conceito", "carrego"]
    },
    {
        "id": "carrego",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "carrego", "carry", "levar até o vencimento", "carregar o título"
        ],
        "termos_busca": [
            "carrego", "carry", "vencimento", "carregar título",
            "retorno contratado", "taxa contratada"
        ],
        "descricao": "Carrego é o retorno obtido ao manter um título de renda fixa até o vencimento, recebendo a taxa contratada. Diferente de vender antes (marcação a mercado), no carrego o investidor recebe exatamente o combinado.",
        "temas_relacionados": ["marcacao_mercado", "duration_conceito"]
    },
    {
        "id": "spread_credito",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "spread de crédito", "prêmio de risco",
            "risco de crédito corporativo"
        ],
        "termos_busca": [
            "spread de crédito", "prêmio de risco", "risco corporativo",
            "spread sobre CDI", "spread sobre NTN-B"
        ],
        "descricao": "Spread de crédito é o prêmio de risco adicional que um título privado paga acima de um título público de referência. Quanto maior o risco do emissor, maior o spread exigido pelo mercado.",
        "temas_relacionados": ["debenture", "risco_credito", "cri"]
    },
    {
        "id": "curva_juros",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "curva de juros", "yield curve", "estrutura a termo",
            "DI futuro", "curva pré"
        ],
        "termos_busca": [
            "curva de juros", "yield curve", "estrutura a termo",
            "DI futuro", "curva pré", "taxa futura"
        ],
        "descricao": "Curva de juros mostra a relação entre taxas de juros e seus prazos de vencimento. Curva normal = taxas maiores para prazos maiores. Curva invertida = taxas curtas maiores que longas (sinal de recessão). DI futuro é o principal indicador no Brasil.",
        "temas_relacionados": ["copom_selic", "marcacao_mercado", "duration_conceito"]
    },
    {
        "id": "convexidade",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "convexidade", "convexity", "sensibilidade à taxa"
        ],
        "termos_busca": [
            "convexidade", "convexity", "sensibilidade à taxa de juros",
            "segunda derivada do preço", "duration modificada"
        ],
        "descricao": "Convexidade complementa a duration para medir a sensibilidade do preço de um título a variações nas taxas de juros. Quanto maior a convexidade, mais o título se beneficia de quedas nas taxas e menos sofre com altas.",
        "temas_relacionados": ["duration_conceito", "marcacao_mercado", "curva_juros"]
    },
    {
        "id": "copom_selic",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "Selic", "COPOM", "taxa básica", "taxa de juros",
            "reunião do COPOM", "meta Selic"
        ],
        "termos_busca": [
            "Selic", "COPOM", "taxa básica de juros", "meta Selic",
            "reunião do COPOM", "política monetária", "Banco Central"
        ],
        "descricao": "A Selic é a taxa básica de juros da economia brasileira, definida pelo COPOM (Comitê de Política Monetária) do Banco Central a cada 45 dias. Influencia todas as taxas de juros do mercado, câmbio e inflação.",
        "temas_relacionados": ["ipca", "curva_juros", "tesouro_direto"]
    },
    {
        "id": "ipca",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "IPCA", "inflação", "IGP-M", "deflação",
            "índice de preços", "CPI"
        ],
        "termos_busca": [
            "IPCA", "inflação", "IGP-M", "deflação", "índice de preços",
            "IBGE", "custo de vida"
        ],
        "descricao": "IPCA (Índice de Preços ao Consumidor Amplo) é o índice oficial de inflação do Brasil, medido pelo IBGE. IGP-M é outro índice, usado em contratos de aluguel. A inflação corrói o poder de compra e impacta diretamente os investimentos.",
        "temas_relacionados": ["copom_selic", "tesouro_direto", "indexador"]
    },
    {
        "id": "fgc",
        "categoria": "RENDA_FIXA",
        "termos_usuario": [
            "FGC", "fundo garantidor", "garantia do FGC",
            "seguro do investimento"
        ],
        "termos_busca": [
            "FGC", "fundo garantidor de créditos", "garantia",
            "R$250 mil", "proteção do investidor", "cobertura FGC"
        ],
        "descricao": "FGC (Fundo Garantidor de Créditos) garante até R$250 mil por CPF por instituição financeira em caso de quebra do banco. Cobre CDB, LCI, LCA, poupança e LC. Não cobre debêntures, CRI, CRA, ações ou fundos.",
        "temas_relacionados": ["cdb", "lci", "risco_credito"]
    },
    # =========================================================================
    # CATEGORIA 10: TRADING E OPERAÇÕES
    # =========================================================================
    {
        "id": "short_selling",
        "categoria": "TRADING",
        "termos_usuario": [
            "short", "venda a descoberto", "operar vendido",
            "short selling", "posição vendida", "apostar na queda"
        ],
        "termos_busca": [
            "short selling", "venda a descoberto", "posição vendida",
            "aluguel de ações", "operar vendido", "aposta na queda"
        ],
        "descricao": "Venda a descoberto (short selling) é a estratégia de vender ações emprestadas (alugadas) apostando na queda. O investidor aluga as ações, vende no mercado e recompra mais barato para devolver. Lucro = diferença de preço menos custos.",
        "temas_relacionados": ["aluguel_acoes", "short_squeeze", "margem_garantia"]
    },
    {
        "id": "short_squeeze",
        "categoria": "TRADING",
        "termos_usuario": [
            "short squeeze", "squeeze", "cobertura de short"
        ],
        "termos_busca": [
            "short squeeze", "squeeze", "cobertura de short",
            "alta forçada", "posições vendidas"
        ],
        "descricao": "Short squeeze é uma alta forçada no preço de um ativo quando muitos investidores vendidos (short) precisam recomprar simultaneamente para cobrir suas posições, gerando pressão compradora e elevando ainda mais o preço.",
        "temas_relacionados": ["short_selling", "aluguel_acoes"]
    },
    {
        "id": "circuit_breaker",
        "categoria": "TRADING",
        "termos_usuario": [
            "circuit breaker", "circuit", "parada de negociação",
            "queda brusca"
        ],
        "termos_busca": [
            "circuit breaker", "parada de negociação", "interrupção",
            "queda brusca", "proteção do mercado"
        ],
        "descricao": "Circuit breaker é a interrupção temporária das negociações na bolsa quando o índice Ibovespa cai além de limites pré-definidos (10%, 15%). Serve para evitar pânico e dar tempo ao mercado de se reorganizar.",
        "temas_relacionados": ["volatilidade", "fluxo_estrangeiro"]
    },
    {
        "id": "aluguel_acoes",
        "categoria": "TRADING",
        "termos_usuario": [
            "aluguel de ações", "empréstimo de ações", "BTC",
            "doador", "tomador"
        ],
        "termos_busca": [
            "aluguel de ações", "empréstimo de ações", "BTC",
            "doador", "tomador", "taxa de aluguel"
        ],
        "descricao": "Aluguel de ações permite que um investidor (doador) empreste suas ações a outro (tomador) mediante pagamento de uma taxa. O tomador usa as ações para operar vendido (short). O doador recebe renda extra sem vender suas ações.",
        "temas_relacionados": ["short_selling", "short_squeeze"]
    },
    {
        "id": "fluxo_estrangeiro",
        "categoria": "TRADING",
        "termos_usuario": [
            "fluxo estrangeiro", "gringo", "investidor estrangeiro",
            "fluxo de capital", "saída de capital"
        ],
        "termos_busca": [
            "fluxo estrangeiro", "investidor estrangeiro", "capital estrangeiro",
            "entrada de capital", "saída de capital", "fluxo gringo"
        ],
        "descricao": "Fluxo estrangeiro representa o capital entrando ou saindo da bolsa brasileira por investidores internacionais. Fluxo positivo (entrada) tende a valorizar ativos. Fluxo negativo (saída) tende a pressionar preços para baixo.",
        "temas_relacionados": ["liquidez", "volatilidade"]
    },
    {
        "id": "book_ofertas",
        "categoria": "TRADING",
        "termos_usuario": [
            "book", "book de ofertas", "livro de ofertas",
            "ordem de compra", "ordem de venda", "bid", "ask", "spread bid-ask"
        ],
        "termos_busca": [
            "book de ofertas", "livro de ofertas", "bid", "ask",
            "spread bid-ask", "profundidade de mercado"
        ],
        "descricao": "Book de ofertas (livro de ofertas) mostra todas as ordens de compra (bid) e venda (ask) pendentes para um ativo, organizadas por preço. O spread bid-ask é a diferença entre a melhor oferta de compra e a melhor oferta de venda.",
        "temas_relacionados": ["spread_mercado", "liquidez", "order_types"]
    },
    {
        "id": "after_market",
        "categoria": "TRADING",
        "termos_usuario": [
            "after market", "pós-mercado", "horário estendido"
        ],
        "termos_busca": [
            "after market", "pós-mercado", "horário estendido",
            "negociação fora do horário", "after hours"
        ],
        "descricao": "After market é o período adicional de negociação após o fechamento normal da bolsa (17h30-18h). Tem regras especiais: variação limitada a 2% do preço de fechamento e menor liquidez.",
        "temas_relacionados": ["liquidez", "order_types"]
    },
    {
        "id": "follow_on",
        "categoria": "TRADING",
        "termos_usuario": [
            "follow-on", "oferta subsequente", "re-IPO",
            "oferta secundária", "bookbuilding"
        ],
        "termos_busca": [
            "follow-on", "oferta subsequente", "oferta secundária",
            "bookbuilding", "emissão de ações", "oferta pública"
        ],
        "descricao": "Follow-on é uma nova emissão de ações por empresa já listada na bolsa. Pode ser primária (empresa emite novas ações e recebe os recursos) ou secundária (acionistas existentes vendem suas ações). O bookbuilding define o preço.",
        "temas_relacionados": ["subscricao", "free_float", "liquidez"]
    },
    {
        "id": "lote_padrao",
        "categoria": "TRADING",
        "termos_usuario": [
            "lote padrão", "lote fracionário", "mercado fracionário",
            "F na frente", "comprar fracionado"
        ],
        "termos_busca": [
            "lote padrão", "lote fracionário", "mercado fracionário",
            "100 ações", "fração"
        ],
        "descricao": "Lote padrão na B3 é de 100 ações. No mercado fracionário, é possível comprar de 1 a 99 ações, adicionando F ao ticker (ex: PETR4F). O fracionário pode ter menor liquidez e spread maior.",
        "temas_relacionados": ["liquidez", "book_ofertas"]
    },
    {
        "id": "order_types",
        "categoria": "TRADING",
        "termos_usuario": [
            "ordem a mercado", "ordem limitada", "ordem stop",
            "ordem casada", "ordem start", "tipo de ordem"
        ],
        "termos_busca": [
            "ordem a mercado", "ordem limitada", "ordem stop",
            "ordem casada", "ordem start", "tipo de ordem", "stop loss", "stop gain"
        ],
        "descricao": "Tipos de ordem: A mercado = executa no melhor preço disponível. Limitada = executa só no preço definido ou melhor. Stop = dispara quando atinge um preço gatilho. Casada = compra e venda simultâneas. Start = compra quando atinge preço de disparo.",
        "temas_relacionados": ["book_ofertas", "liquidez"]
    },
    # =========================================================================
    # CATEGORIA 11: JARGÃO DO ASSESSOR
    # =========================================================================
    {
        "id": "auc",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "AuC", "assets under custody", "patrimônio sob custódia",
            "custódia total"
        ],
        "termos_busca": [
            "AuC", "assets under custody", "patrimônio sob custódia",
            "custódia total", "volume sob gestão"
        ],
        "descricao": "AuC (Assets under Custody) é o volume total de recursos dos clientes sob custódia do assessor ou escritório de assessoria. É a principal métrica de tamanho e relevância de um assessor no mercado.",
        "temas_relacionados": ["captacao_liquida", "fee"]
    },
    {
        "id": "captacao_liquida",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "captação líquida", "captação", "NNM", "net new money",
            "entrada de recursos", "resgate líquido"
        ],
        "termos_busca": [
            "captação líquida", "NNM", "net new money", "entrada de recursos",
            "resgate líquido", "fluxo de clientes"
        ],
        "descricao": "Captação líquida (Net New Money) é a diferença entre recursos captados (novos investimentos) e resgatados pelos clientes. Captação positiva indica crescimento. É uma métrica-chave de desempenho do assessor.",
        "temas_relacionados": ["auc", "fee", "onboarding_cliente"]
    },
    {
        "id": "fee",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "fee", "fee fixo", "fee variável", "comissão",
            "receita do assessor", "rebate", "repasse", "RoA"
        ],
        "termos_busca": [
            "fee", "comissão", "rebate", "repasse", "RoA",
            "receita do assessor", "remuneração", "taxa de administração"
        ],
        "descricao": "Fee é a remuneração do assessor. Pode ser fixo (valor mensal) ou variável (% sobre produtos vendidos/rebate). RoA (Return on Assets) = receita anual / AuC. Rebate é a parcela da taxa de administração repassada ao assessor.",
        "temas_relacionados": ["auc", "captacao_liquida"]
    },
    {
        "id": "suitability",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "suitability", "adequação", "análise de perfil",
            "perfil do investidor", "perfil de risco", "conservador",
            "moderado", "agressivo", "arrojado"
        ],
        "termos_busca": [
            "suitability", "adequação", "perfil do investidor",
            "perfil de risco", "conservador", "moderado", "agressivo",
            "arrojado", "API"
        ],
        "descricao": "Suitability (adequação) é a avaliação do perfil do investidor para garantir que os produtos oferecidos são adequados ao seu perfil de risco. Perfis: conservador, moderado, agressivo/arrojado. Obrigatório por regulação da CVM.",
        "temas_relacionados": ["enquadramento", "onboarding_cliente"]
    },
    {
        "id": "cross_selling",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "cross-selling", "cross sell", "venda cruzada",
            "upselling", "oferta complementar"
        ],
        "termos_busca": [
            "cross-selling", "venda cruzada", "upselling",
            "oferta complementar", "produtos adicionais"
        ],
        "descricao": "Cross-selling é a prática de oferecer produtos financeiros adicionais a um cliente existente. Exemplo: cliente que tem renda fixa recebe oferta de fundos imobiliários ou previdência. Aumenta a receita e diversifica a carteira do cliente.",
        "temas_relacionados": ["fee", "suitability", "pipeline"]
    },
    {
        "id": "onboarding_cliente",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "onboarding", "cadastro de cliente", "abertura de conta",
            "transferência de custódia", "STVM", "portabilidade"
        ],
        "termos_busca": [
            "onboarding", "cadastro", "abertura de conta",
            "transferência de custódia", "STVM", "portabilidade"
        ],
        "descricao": "Onboarding é o processo de cadastro de um novo cliente: abertura de conta, análise de perfil (suitability), documentação. STVM é a transferência de custódia de outra corretora. Portabilidade é a transferência de investimentos.",
        "temas_relacionados": ["suitability", "captacao_liquida"]
    },
    {
        "id": "ipa",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "IPA", "AAI", "assessor de investimentos", "agente autônomo",
            "escritório de assessoria", "credenciado"
        ],
        "termos_busca": [
            "IPA", "AAI", "assessor de investimentos", "agente autônomo",
            "escritório de assessoria", "credenciado CVM"
        ],
        "descricao": "IPA (Intermediário de Produtos de Investimento) / AAI (Agente Autônomo de Investimentos) é o profissional credenciado pela CVM que atua como assessor de investimentos, intermediando a relação entre investidor e corretora.",
        "temas_relacionados": ["ancord", "suitability", "fee"]
    },
    {
        "id": "ancord",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "ANCORD", "CPA-10", "CPA-20", "CEA", "CFP",
            "certificação", "prova ANCORD", "certificado"
        ],
        "termos_busca": [
            "ANCORD", "CPA-10", "CPA-20", "CEA", "CFP",
            "certificação financeira", "habilitação profissional"
        ],
        "descricao": "Certificações profissionais do mercado financeiro: ANCORD (assessor de investimentos), CPA-10/CPA-20 (ANBIMA, para bancários), CEA (especialista ANBIMA), CFP (planejador financeiro). Obrigatórias para atuar no mercado.",
        "temas_relacionados": ["ipa", "suitability"]
    },
    {
        "id": "mesa_rv",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "mesa RV", "mesa de renda variável", "mesa de operações",
            "trader", "operador de mesa", "broker"
        ],
        "termos_busca": [
            "mesa de renda variável", "mesa de operações", "trader",
            "operador de mesa", "broker", "execução de ordens"
        ],
        "descricao": "Mesa de Renda Variável é a área da corretora responsável pela execução de ordens em ações, opções e derivativos. O trader/operador de mesa auxilia o assessor na execução de operações mais complexas.",
        "temas_relacionados": ["order_types", "operacao_estruturada", "ipa"]
    },
    {
        "id": "pipeline",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "pipeline", "pipe", "negócio em andamento",
            "oportunidade", "deal flow"
        ],
        "termos_busca": [
            "pipeline", "deal flow", "oportunidade de negócio",
            "funil de vendas", "prospecção"
        ],
        "descricao": "Pipeline é o conjunto de oportunidades de negócio em andamento do assessor: novos clientes em prospecção, transferências de custódia em processo, operações em análise. Deal flow é o fluxo de novas oportunidades.",
        "temas_relacionados": ["captacao_liquida", "onboarding_cliente", "cross_selling"]
    },
    {
        "id": "churning",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "churning", "giro excessivo", "overtrading",
            "excesso de operações"
        ],
        "termos_busca": [
            "churning", "giro excessivo", "overtrading",
            "prática irregular", "excesso de corretagem"
        ],
        "descricao": "Churning é a prática irregular de realizar giro excessivo na carteira do cliente para gerar comissões (corretagem) para o assessor. É vedado pela CVM e pode resultar em punições e ressarcimento ao cliente.",
        "temas_relacionados": ["fee", "suitability", "enquadramento"]
    },
    {
        "id": "enquadramento",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "enquadramento", "enquadrar carteira", "rebalanceamento",
            "adequação de carteira", "carteira adequada"
        ],
        "termos_busca": [
            "enquadramento", "adequação de carteira", "rebalanceamento",
            "perfil de risco", "carteira adequada"
        ],
        "descricao": "Enquadramento é o processo de ajustar a carteira do cliente ao seu perfil de risco (suitability). Inclui rebalanceamento de posições, substituição de ativos inadequados e adequação a limites regulatórios.",
        "temas_relacionados": ["suitability", "diversificacao"]
    },
    {
        "id": "come_cotas",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "come-cotas", "come cotas", "antecipação de IR",
            "tributação semestral"
        ],
        "termos_busca": [
            "come-cotas", "antecipação de IR", "tributação semestral",
            "maio e novembro", "imposto sobre fundos"
        ],
        "descricao": "Come-cotas é a antecipação do Imposto de Renda cobrada semestralmente (maio e novembro) sobre fundos de investimento abertos. Reduz o número de cotas do investidor. Alíquota de 15% (longo prazo) ou 20% (curto prazo).",
        "temas_relacionados": ["iof_ir", "dividendo"]
    },
    {
        "id": "iof_ir",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "IOF", "imposto de renda", "IR", "tributação",
            "tabela regressiva", "alíquota", "DARF",
            "IR sobre ganho de capital", "15%", "20%"
        ],
        "termos_busca": [
            "IOF", "imposto de renda", "IR", "tributação",
            "tabela regressiva", "alíquota", "DARF", "ganho de capital"
        ],
        "descricao": "IOF incide sobre resgates em menos de 30 dias. IR em renda fixa segue tabela regressiva: 22,5% (até 180 dias) a 15% (acima de 720 dias). Ações: 15% sobre ganho de capital (20% em day trade). DARF é a guia de pagamento do imposto.",
        "temas_relacionados": ["come_cotas", "dividendo"]
    },
    {
        "id": "pgbl_vgbl",
        "categoria": "ASSESSOR_JARGAO",
        "termos_usuario": [
            "PGBL", "VGBL", "previdência privada", "previdência",
            "aposentadoria", "plano de previdência"
        ],
        "termos_busca": [
            "PGBL", "VGBL", "previdência privada", "aposentadoria",
            "plano de previdência", "tabela regressiva", "tabela progressiva"
        ],
        "descricao": "PGBL permite deduzir até 12% da renda bruta no IR (indicado para quem faz declaração completa). VGBL não deduz, mas o IR incide só sobre os rendimentos (indicado para declaração simplificada). Ambos podem usar tabela regressiva ou progressiva.",
        "temas_relacionados": ["iof_ir", "come_cotas"]
    },
    # =========================================================================
    # CATEGORIA 12: CONCEITOS ADICIONAIS IMPORTANTES
    # =========================================================================
    {
        "id": "ebitda",
        "categoria": "PERFORMANCE",
        "termos_usuario": [
            "EBITDA", "lucro antes de juros", "resultado operacional",
            "LAJIDA"
        ],
        "termos_busca": [
            "EBITDA", "LAJIDA", "lucro operacional", "resultado operacional",
            "margem EBITDA"
        ],
        "descricao": "EBITDA (Lucro antes de Juros, Impostos, Depreciação e Amortização) mede a geração de caixa operacional de uma empresa. Margem EBITDA = EBITDA / Receita Líquida. Usado para comparar eficiência operacional entre empresas.",
        "temas_relacionados": ["pl_ratio", "roe", "noi"]
    },
    {
        "id": "free_float",
        "categoria": "MERCADO",
        "termos_usuario": [
            "free float", "ações em circulação", "percentual em circulação",
            "liquidez de mercado"
        ],
        "termos_busca": [
            "free float", "ações em circulação", "ações disponíveis",
            "liquidez", "percentual em circulação"
        ],
        "descricao": "Free float é o percentual de ações de uma empresa disponíveis para negociação no mercado, excluindo ações detidas por controladores e insiders. Maior free float = maior liquidez e facilidade de negociação.",
        "temas_relacionados": ["liquidez", "governanca", "follow_on"]
    },
    {
        "id": "tag_along",
        "categoria": "MERCADO",
        "termos_usuario": [
            "tag along", "proteção minoritário", "direito de saída",
            "100% tag along"
        ],
        "termos_busca": [
            "tag along", "proteção minoritário", "direito de saída",
            "mudança de controle", "oferta pública de aquisição"
        ],
        "descricao": "Tag along é o direito dos acionistas minoritários de vender suas ações por pelo menos 80% do preço pago ao controlador em caso de mudança de controle. No Novo Mercado, o tag along é de 100%.",
        "temas_relacionados": ["governanca", "free_float"]
    },
    {
        "id": "governanca",
        "categoria": "MERCADO",
        "termos_usuario": [
            "governança", "novo mercado", "nível 1", "nível 2",
            "segmento de listagem", "governança corporativa"
        ],
        "termos_busca": [
            "governança corporativa", "novo mercado", "nível 1", "nível 2",
            "segmento de listagem", "boas práticas"
        ],
        "descricao": "Governança corporativa são as práticas de gestão transparente e proteção aos acionistas. Na B3, os segmentos de listagem são: Novo Mercado (mais exigente, só ações ON, 100% tag along), Nível 2 e Nível 1 (menos exigentes).",
        "temas_relacionados": ["tag_along", "free_float"]
    },
    {
        "id": "split_grupamento",
        "categoria": "MERCADO",
        "termos_usuario": [
            "split", "desdobramento", "grupamento", "inplit",
            "ajuste de preço da ação"
        ],
        "termos_busca": [
            "split", "desdobramento", "grupamento", "inplit",
            "ajuste de preço", "proporção"
        ],
        "descricao": "Split (desdobramento) divide cada ação em várias, reduzindo o preço unitário sem alterar o valor total. Grupamento (inplit) é o inverso: junta várias ações em uma, aumentando o preço unitário. Não altera o patrimônio do investidor.",
        "temas_relacionados": ["cotacao", "liquidez"]
    },
    {
        "id": "bonificacao",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "bonificação", "ações bonificadas", "bonificação em ações",
            "distribuição gratuita de ações"
        ],
        "termos_busca": [
            "bonificação", "ações bonificadas", "distribuição gratuita",
            "incorporação de reservas"
        ],
        "descricao": "Bonificação é a distribuição gratuita de novas ações aos acionistas, geralmente originada da incorporação de reservas de lucro ao capital social. O acionista recebe mais ações proporcionalmente à sua participação.",
        "temas_relacionados": ["dividendo", "provento_tipos"]
    },
    {
        "id": "provento_tipos",
        "categoria": "DISTRIBUICAO",
        "termos_usuario": [
            "rendimento isento", "rendimento tributável", "proventos em ações",
            "direito de preferência", "sobras"
        ],
        "termos_busca": [
            "rendimento isento", "rendimento tributável", "proventos em ações",
            "direito de preferência", "sobras", "tipos de provento"
        ],
        "descricao": "Tipos de proventos: dividendos (isentos de IR), JCP (tributados na fonte), bonificação em ações, direito de preferência em subscrição e sobras (frações não exercidas). Cada tipo tem tratamento fiscal diferente.",
        "temas_relacionados": ["dividendo", "jcp", "bonificacao", "subscricao"]
    },
    {
        "id": "beta",
        "categoria": "RISCO",
        "termos_usuario": [
            "beta", "beta da ação", "risco sistemático",
            "correlação com mercado", "coeficiente beta"
        ],
        "termos_busca": [
            "beta", "coeficiente beta", "risco sistemático",
            "sensibilidade ao mercado", "Ibovespa"
        ],
        "descricao": "Beta mede a sensibilidade de uma ação em relação ao mercado (Ibovespa). Beta = 1: se move igual ao mercado. Beta > 1: mais volátil que o mercado. Beta < 1: menos volátil. Beta negativo: se move na direção oposta.",
        "temas_relacionados": ["volatilidade", "diversificacao", "benchmark"]
    },
]


# Índice invertido: termo → lista de conceitos
_TERM_INDEX: Dict[str, List[dict]] = {}
_INITIALIZED = False


def _build_index():
    """Constrói o índice invertido para busca rápida por termos."""
    global _TERM_INDEX, _INITIALIZED
    if _INITIALIZED:
        return
    
    for concept in FINANCIAL_CONCEPTS:
        for term in concept["termos_usuario"]:
            term_lower = term.lower()
            if term_lower not in _TERM_INDEX:
                _TERM_INDEX[term_lower] = []
            _TERM_INDEX[term_lower].append(concept)
    
    _INITIALIZED = True


def expand_query(user_message: str) -> Dict[str, any]:
    """
    Analisa a mensagem do usuário e retorna:
    - termos_busca_adicionais: termos extras para melhorar a busca vetorial
    - conceitos_detectados: lista de conceitos financeiros identificados
    - contexto_agente: texto descritivo para ajudar o GPT a entender a pergunta
    
    Args:
        user_message: Mensagem original do usuário
    
    Returns:
        Dict com termos_busca_adicionais, conceitos_detectados e contexto_agente
    """
    _build_index()
    
    msg_lower = user_message.lower()
    
    matched_concepts: Dict[str, dict] = {}
    matched_terms: Set[str] = set()
    
    sorted_terms = sorted(_TERM_INDEX.keys(), key=len, reverse=True)
    
    for term in sorted_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, msg_lower):
            for concept in _TERM_INDEX[term]:
                if concept["id"] not in matched_concepts:
                    matched_concepts[concept["id"]] = concept
                    matched_terms.add(term)
    
    if not matched_concepts:
        return {
            "termos_busca_adicionais": [],
            "conceitos_detectados": [],
            "contexto_agente": "",
            "categorias": []
        }
    
    termos_busca = set()
    categorias = set()
    contexto_parts = []
    
    for concept_id, concept in matched_concepts.items():
        for t in concept["termos_busca"]:
            termos_busca.add(t)
        
        categorias.add(concept["categoria"])
        
        contexto_parts.append(
            f"- {concept['id'].upper()}: {concept['descricao']}"
        )
        
        for related_id in concept.get("temas_relacionados", []):
            for c in FINANCIAL_CONCEPTS:
                if c["id"] == related_id and related_id not in matched_concepts:
                    for t in c["termos_busca"][:3]:
                        termos_busca.add(t)
                    break
    
    contexto_agente = (
        "CONCEITOS FINANCEIROS DETECTADOS NA PERGUNTA:\n" +
        "\n".join(contexto_parts)
    )
    
    return {
        "termos_busca_adicionais": list(termos_busca),
        "conceitos_detectados": list(matched_concepts.keys()),
        "contexto_agente": contexto_agente,
        "categorias": list(categorias)
    }


def get_concept_by_id(concept_id: str) -> Optional[dict]:
    """Retorna um conceito pelo seu ID."""
    for concept in FINANCIAL_CONCEPTS:
        if concept["id"] == concept_id:
            return concept
    return None


def get_concepts_by_category(category: str) -> List[dict]:
    """Retorna todos os conceitos de uma categoria."""
    return [c for c in FINANCIAL_CONCEPTS if c["categoria"] == category]


def get_all_categories() -> List[str]:
    """Retorna todas as categorias disponíveis."""
    return list(set(c["categoria"] for c in FINANCIAL_CONCEPTS))


def get_stats() -> dict:
    """Retorna estatísticas do glossário."""
    categories = {}
    total_terms = 0
    for c in FINANCIAL_CONCEPTS:
        cat = c["categoria"]
        categories[cat] = categories.get(cat, 0) + 1
        total_terms += len(c["termos_usuario"])
    
    return {
        "total_conceitos": len(FINANCIAL_CONCEPTS),
        "total_termos": total_terms,
        "categorias": categories
    }
