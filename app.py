import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(
    page_title="CRI Rating System",
    page_icon="🏢",
    layout="wide"
)

# --- Estilos CSS Customizados ---
st.markdown("""
    <style>
    .main {background-color: #f9f9f9;}
    .stButton>button {width: 100%;}
    .metric-card {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    </style>
    """, unsafe_allow_html=True)

# --- Lógica de Cálculo de Rating (Modelo Simplificado) ---
def calcular_score(financas, garantias, qualitativo):
    score = 0
    
    # 1. Financeiro (Peso 40%)
    # Dívida Líq/EBITDA (Menor é melhor)
    if financas['avancagem'] < 2.0: score += 15
    elif financas['avancagem'] < 3.5: score += 10
    elif financas['avancagem'] < 5.0: score += 5
    
    # Índice de Cobertura (ICSD) (Maior é melhor)
    if financas['icsd'] > 2.0: score += 15
    elif financas['icsd'] > 1.2: score += 10
    elif financas['icsd'] > 1.0: score += 5
    
    # Margem Líquida
    if financas['margem'] > 0.15: score += 10
    elif financas['margem'] > 0.05: score += 5

    # 2. Estrutura e Garantias (Peso 40%)
    # LTV (Loan to Value) (Menor é melhor)
    if garantias['ltv'] < 40: score += 20
    elif garantias['ltv'] < 60: score += 15
    elif garantias['ltv'] < 80: score += 5
    
    # Tipo de Garantia
    if garantias['tipo'] == "Alienação Fiduciária (Imóvel Performado)": score += 20
    elif garantias['tipo'] == "Alienação Fiduciária (Terreno/Obras)": score += 10
    elif garantias['tipo'] == "Hipoteca": score += 5

    # 3. Qualitativo (Peso 20%)
    # Track Record
    if qualitativo['track_record'] == "Excelente": score += 10
    elif qualitativo['track_record'] == "Bom": score += 5
    
    # Setor
    if qualitativo['risco_setor'] == "Baixo": score += 10
    elif qualitativo['risco_setor'] == "Médio": score += 5

    return min(score, 100)

def obter_rating_grade(score):
    if score >= 90: return "AAA", "green"
    elif score >= 80: return "AA", "lightgreen"
    elif score >= 70: return "A", "yellow"
    elif score >= 60: return "BBB", "orange"
    elif score >= 50: return "BB", "orange"
    else: return "C/D", "red"

# --- Interface Principal ---

st.title("🏢 Calculadora de Rating de Crédito - CRI")
st.markdown("Ferramenta interna para análise preliminar de risco de operações imobiliárias.")

# Sidebar - Dados Básicos
with st.sidebar:
    st.header("Dados da Operação")
    nome_cri = st.text_input("Nome do Emissor/Devedor", "Construtora Exemplo S.A.")
    ticker = st.text_input("Ticker (opcional)", "CRI-123")
    valor_emissao = st.number_input("Valor da Emissão (R$)", value=50000000)
    st.markdown("---")
    st.info("Preencha as abas ao lado para calcular o rating.")

# Abas de Input
tab1, tab2, tab3, tab4 = st.tabs(["📊 Financeiro", "brick Estrutura & Garantias", "🧠 Qualitativo", "🎯 Resultado"])

with tab1:
    st.subheader("Análise Financeira do Devedor (Peso 40%)")
    col1, col2 = st.columns(2)
    with col1:
        alavancagem = st.number_input("Dívida Líquida / EBITDA (x)", 0.0, 20.0, 2.5, help="Quanto menor, melhor.")
        icsd = st.number_input("Índice de Cobertura do Serviço da Dívida (ICSD)", 0.0, 10.0, 1.5, help="Quanto maior, melhor (EBITDA / Serviço da Dívida).")
    with col2:
        margem = st.number_input("Margem Líquida (%)", 0.0, 100.0, 12.0) / 100
    
    financas = {'avancagem': alavancagem, 'icsd': icsd, 'margem': margem}

with tab2:
    st.subheader("Estrutura e Garantias (Peso 40%)")
    col1, col2 = st.columns(2)
    with col1:
        valor_garantia = st.number_input("Valor de Avaliação da Garantia (R$)", value=80000000)
        ltv = (valor_emissao / valor_garantia) * 100 if valor_garantia > 0 else 0
        st.metric("LTV Calculado (Loan-to-Value)", f"{ltv:.1f}%")
    with col2:
        tipo_garantia = st.selectbox("Tipo de Garantia Principal", 
                                     ["Alienação Fiduciária (Imóvel Performado)", 
                                      "Alienação Fiduciária (Terreno/Obras)", 
                                      "Hipoteca", 
                                      "Aval/Fiança Apenas"])
    
    garantias = {'ltv': ltv, 'tipo': tipo_garantia}

with tab3:
    st.subheader("Fatores Qualitativos (Peso 20%)")
    col1, col2 = st.columns(2)
    with col1:
        track_record = st.select_slider("Track Record do Gestor/Devedor", options=["Ruim", "Regular", "Bom", "Excelente"], value="Bom")
    with col2:
        risco_setor = st.select_slider("Risco do Setor (Vacância/Vendas)", options=["Alto", "Médio", "Baixo"], value="Médio")

    qualitativo = {'track_record': track_record, 'risco_setor': risco_setor}

with tab4:
    st.subheader("Resultado da Análise")
    
    if st.button("Calcular Rating", type="primary"):
        final_score = calcular_score(financas, garantias, qualitativo)
        rating, color = obter_rating_grade(final_score)
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown(f"""
            <div style="text-align: center; border: 2px solid {color}; padding: 20px; border-radius: 10px;">
                <h3 style="margin:0">Rating Sugerido</h3>
                <h1 style="font-size: 80px; margin:0; color: {color}">{rating}</h1>
                <p>Score: {final_score}/100</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            # Gráfico de Velocímetro (Gauge)
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = final_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Pontuação de Crédito"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}],
                }
            ))
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

        st.success("Análise gerada com sucesso. Verifique os inputs antes de formalizar.")

        # Exportação Simples
        report_data = {
            "Operação": [nome_cri],
            "Score": [final_score],
            "Rating": [rating],
            "LTV": [f"{ltv:.1f}%"],
            "Dívida/EBITDA": [alavancagem]
        }
        df_report = pd.DataFrame(report_data)
        
        st.download_button(
            label="📥 Baixar Relatório (CSV)",
            data=df_report.to_csv(index=False).encode('utf-8'),
            file_name=f"rating_{ticker}.csv",
            mime='text/csv',
        )
