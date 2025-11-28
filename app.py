import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestora CRI - Rating & Pricing", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# A conexão busca as credenciais nos "Secrets" do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name):
    try:
        # Lê a aba específica. TTL=0 garante que não faça cache e pegue dados frescos
        return conn.read(worksheet=worksheet_name, ttl=0)
    except:
        # Retorna dataframe vazio com as colunas se der erro (ou for primeira vez)
        return pd.DataFrame(columns=[
            "data_analise", "ticker", "nome_operacao", "score_final", 
            "rating", "taxa_mercado", "spread_sugerido", "taxa_final", "tipo_indexador"
        ])

def save_data(df, worksheet_name):
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear() # Limpa cache para recarregar na hora

# --- MOTOR DE CÁLCULO (RATING ENGINE) ---
def calcular_rating(inputs):
    # Ponderação dos Pilares
    pesos = {
        "Empreendedor": 0.20,
        "Projeto_Financeiro": 0.30,
        "Garantias": 0.30,
        "Juridico_Estrutura": 0.20
    }
    
    score = (
        inputs["score_emp"] * pesos["Empreendedor"] +
        inputs["score_fin"] * pesos["Projeto_Financeiro"] +
        inputs["score_gar"] * pesos["Garantias"] +
        inputs["score_jur"] * pesos["Juridico_Estrutura"]
    )
    
    # Escala de Rating (Simplificada)
    if score >= 4.5: rating = "AAA"
    elif score >= 4.0: rating = "AA"
    elif score >= 3.5: rating = "A"
    elif score >= 3.0: rating = "BBB"
    elif score >= 2.0: rating = "BB"
    else: rating = "B/C"
    
    # Matriz de Spread Sugerido (Risk Premium) - Exemplo hipotético
    spreads = {
        "AAA": 1.50, "AA": 2.00, "A": 2.75, 
        "BBB": 3.75, "BB": 5.00, "B/C": 8.00
    }
    
    return score, rating, spreads[rating]

# --- INTERFACE DO USUÁRIO ---

st.title("📊 Sistema de Rating e Precificação de CRIs")

# Menu Lateral
menu = st.sidebar.radio("Navegação", ["Nova Análise / Atualização", "Portfolio Interno (Histórico)", "Pipeline Externo"])

# --- MÓDULO 1: NOVA ANÁLISE ---
if menu == "Nova Análise / Atualização":
    st.header("🧮 Calculadora de Rating & Pricing")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Ticker do CRI (Ex: CRI11)", placeholder="Código único").upper()
    with col2:
        nome_op = st.text_input("Nome da Operação", placeholder="Ex: Loteamento Viver Bem")
    
    tipo_analise = st.radio("Destino da Análise:", ["Atualização Trimestral (Interno)", "Nova Oportunidade (Externo)"], horizontal=True)

    st.markdown("---")
    
    # Formulário de Scorecard
    st.subheader("1. Scorecard de Crédito")
    st.info("Atribua notas de 1 (Pior) a 5 (Melhor) para cada critério.")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("**Governança & Empreendedor (20%)**")
        q1 = st.slider("Track Record / Experiência", 1, 5, 3)
        q2 = st.slider("Saúde Financeira Acionista", 1, 5, 3)
        score_emp = (q1 + q2) / 2
        
    with c2:
        st.markdown("**Financeiro do Projeto (30%)**")
        q3 = st.slider("LTV (Loan to Value)", 1, 5, 3, help="1: LTV Alto | 5: LTV Baixo")
        q4 = st.slider("Índice de Vendas / Obras", 1, 5, 3)
        q5 = st.slider("DSCR (Cob. Dívida)", 1, 5, 3)
        score_fin = (q3 + q4 + q5) / 3
        
    with c3:
        st.markdown("**Garantias (30%)**")
        q6 = st.slider("Liquidez da Garantia", 1, 5, 3)
        q7 = st.slider("Razão de Garantia (Cob.)", 1, 5, 3)
        score_gar = (q6 + q7) / 2
        
    with c4:
        st.markdown("**Jurídico & Estrutura (20%)**")
        q8 = st.slider("Qualidade Covenants", 1, 5, 3)
        q9 = st.slider("Due Diligence Legal", 1, 5, 3)
        score_jur = (q8 + q9) / 2

    # Cálculo em tempo real
    inputs = {
        "score_emp": score_emp, "score_fin": score_fin,
        "score_gar": score_gar, "score_jur": score_jur
    }
    score_final, rating_calc, spread_calc = calcular_rating(inputs)

    st.markdown("---")
    
    # Seção de Precificação
    st.subheader("2. Precificação (Pricing)")
    
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        indexador = st.selectbox("Indexador", ["IPCA", "CDI/DI"])
    with cp2:
        # Usuário insere a taxa livre de risco (ex: Yield da NTN-B de duration equivalente)
        taxa_livre = st.number_input(f"Taxa Livre de Risco Atual ({indexador} +)", value=6.0, step=0.1, format="%.2f")
    with cp3:
        st.metric(label="Spread de Crédito Sugerido (Rating)", value=f"{spread_calc:.2f}%")
    
    taxa_final = taxa_livre + spread_calc
    
    # Exibição do Resultado Final
    st.markdown("### 🏁 Resultado da Análise")
    r1, r2, r3 = st.columns(3)
    r1.metric("Score Ponderado", f"{score_final:.2f}/5.0")
    r2.metric("Rating Atribuído", rating_calc)
    r3.metric(f"Taxa Justa Estimada ({indexador})", f"{indexador} + {taxa_final:.2f}%")
    
    # Botão de Salvar
    if st.button("💾 Salvar Análise no Banco de Dados"):
        if not ticker or not nome_op:
            st.error("Por favor, preencha Ticker e Nome da Operação.")
        else:
            nova_linha = pd.DataFrame([{
                "data_analise": datetime.now().strftime("%Y-%m-%d"),
                "ticker": ticker,
                "nome_operacao": nome_op,
                "score_final": score_final,
                "rating": rating_calc,
                "taxa_mercado": taxa_livre,
                "spread_sugerido": spread_calc,
                "taxa_final": taxa_final,
                "tipo_indexador": indexador
            }])
            
            # Decide onde salvar
            sheet_target = "internal" if "Interno" in tipo_analise else "external"
            
            # Carrega dados existentes, concatena e salva
            df_atual = load_data(sheet_target)
            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
            save_data(df_final, sheet_target)
            
            st.success(f"Operação salva com sucesso na aba '{sheet_target}'!")

# --- MÓDULO 2: PORTFOLIO INTERNO ---
elif menu == "Portfolio Interno (Histórico)":
    st.header("📈 Monitoramento de Portfolio")
    
    df_internal = load_data("internal")
    
    if not df_internal.empty:
        # Filtros
        tickers_unicos = df_internal["ticker"].unique()
        ticker_sel = st.selectbox("Selecione o Ativo para ver histórico:", tickers_unicos)
        
        # Filtrar dados do ativo
        df_asset = df_internal[df_internal["ticker"] == ticker_sel].copy()
        df_asset["data_analise"] = pd.to_datetime(df_asset["data_analise"])
        df_asset = df_asset.sort_values("data_analise")
        
        # Mostrar Info Recente
        ultimo_dado = df_asset.iloc[-1]
        st.write(f"**Operação:** {ultimo_dado['nome_operacao']} | **Último Rating:** {ultimo_dado['rating']}")
        
        # Gráfico Histórico
        fig = px.line(df_asset, x="data_analise", y="score_final", markers=True, title=f"Evolução do Score de Crédito: {ticker_sel}")
        fig.update_yaxes(range=[1, 5])
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Histórico Tabular")
        st.dataframe(df_asset)
    else:
        st.warning("Nenhum dado encontrado na base interna.")

# --- MÓDULO 3: PIPELINE EXTERNO ---
elif menu == "Pipeline Externo":
    st.header("🔭 Pipeline de Novas Operações")
    
    df_external = load_data("external")
    
    if not df_external.empty:
        st.dataframe(df_external)
        
        st.markdown("### Comparativo de Retorno")
        fig_bar = px.bar(df_external, x="ticker", y="taxa_final", color="rating", 
                         title="Taxa Justa Calculada por Operação (Pipeline)",
                         text="taxa_final")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("O pipeline está vazio.")
