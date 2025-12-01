import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configuração ---
st.set_page_config(page_title="CRI Rating Pro", page_icon="🏗️", layout="wide")

# CSS para deixar a tabela de sensibilidade bonita
st.markdown("""
<style>
    div[data-testid="stMetricValue"] {font-size: 1.8rem;}
    .stAlert {padding: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# --- Lógica Avançada de Cálculo ---
def calcular_rating_avancado(dados):
    score = 0
    penalidades = 0
    
    # --- 1. Lastro e Garantias (Máx 50 pts) ---
    # LTV Stress (Venda Forçada)
    ltv_stress = dados['ltv_stress']
    if ltv_stress < 40: score += 20
    elif ltv_stress < 60: score += 15
    elif ltv_stress < 75: score += 10
    else: penalidades += 5 # LTV muito alto no stress é perigoso

    # Liquidez do Ativo (Localização/Tipologia)
    score += dados['score_liquidez'] # 0 a 15 pts
    
    # Estágio de Obra (Risco de Performance)
    if dados['tipo_risco'] == "Performance (Obras)":
        if dados['poc'] > 90: score += 15
        elif dados['poc'] > 50: score += 10
        elif dados['poc'] > 20: score += 5
        else: penalidades += 5 # Obra no início
    else:
        score += 15 # Imóvel performado/Corporativo é menos arriscado que obra

    # --- 2. Capacidade de Pagamento (Máx 30 pts) ---
    # ICSD (Índice de Cobertura)
    if dados['icsd'] > 1.5: score += 15
    elif dados['icsd'] > 1.2: score += 10
    elif dados['icsd'] >= 1.0: score += 5
    else: penalidades += 10 # ICSD < 1 é calote técnico

    # Razão de Garantia (Fundo de Reserva)
    if dados['pmts_reserva'] >= 3: score += 15
    elif dados['pmts_reserva'] >= 1: score += 10
    else: score += 0

    # --- 3. Qualitativo e Sponsor (Máx 20 pts) ---
    score += dados['score_sponsor'] # 0 a 20

    # Cálculo Final
    final_score = max(0, min(100, score - penalidades))
    return final_score

def get_grade(score):
    if score >= 90: return "AAA (Excel)", "#2E8B57"
    elif score >= 80: return "AA (Muito Bom)", "#3CB371"
    elif score >= 70: return "A (Bom)", "#9ACD32"
    elif score >= 60: return "BBB (Adequado)", "#FFD700"
    elif score >= 40: return "BB (Especulativo)", "#FFA500"
    else: return "C/D (Risco Alto)", "#FF4500"

# --- Interface ---
st.title("🏗️ CRI Analyst Pro: Ferramenta de Análise Estruturada")

col_head1, col_head2 = st.columns([3,1])
with col_head1:
    st.markdown("**Objetivo:** Simulação de cenários e rating preliminar para operações imobiliárias (Corporativo ou Pulverizado).")
with col_head2:
    tipo_operacao = st.selectbox("Tipo de Risco", ["Corporativo (Aluguel/BTS)", "Desenvolvimento (Incorporação/Loteamento)"])

st.divider()

# --- INPUTS (Organizados em Colunas para densidade de informação) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Garantias & Ativo")
    valor_emissao = st.number_input("Valor da Emissão (R$ MM)", value=50.0)
    valor_garantia = st.number_input("Valor de Avaliação (Laudo) (R$ MM)", value=80.0)
    haircut = st.slider("Haircut Forçado (%) - Cenário de Liquidação", 0, 50, 20, help="Desconto aplicado ao valor do imóvel para simular venda rápida.")
    
    val_garantia_stress = valor_garantia * (1 - (haircut/100))
    ltv_stress = (valor_emissao / val_garantia_stress) * 100 if val_garantia_stress > 0 else 0
    
    st.metric("LTV Stress (Venda Forçada)", f"{ltv_stress:.1f}%", delta=f"-{haircut}% no valor do ativo", delta_color="inverse")
    
    liquidez = st.select_slider("Liquidez do Ativo (Localização/Classe)", 
                                options=["Baixa (Terciária)", "Média", "Alta (Prime)"], value="Média")
    score_liquidez_map = {"Baixa (Terciária)": 5, "Média": 10, "Alta (Prime)": 15}

with col2:
    st.subheader("2. Fluxo e Obras")
    if tipo_operacao == "Desenvolvimento (Incorporação/Loteamento)":
        poc = st.slider("POC (Percentual de Obra Concluída)", 0, 100, 30)
        vendas = st.slider("Velocidade de Vendas (% Vendido)", 0, 100, 40)
        tipo_risco_interno = "Performance (Obras)"
    else:
        st.info("Operação de Renda/Corporativo: Risco focado em Vacância e Crédito do Locatário.")
        poc = 100
        tipo_risco_interno = "Corporativo"
        
    receita_op = st.number_input("NOI / EBITDA Projetado (Ano) (R$ MM)", value=12.0)
    servico_divida = st.number_input("Serviço da Dívida (PMT Ano) (R$ MM)", value=8.0)
    
    icsd = receita_op / servico_divida if servico_divida > 0 else 0
    st.metric("ICSD (Cobertura Atual)", f"{icsd:.2f}x")
    
    pmts_reserva = st.number_input("Fundo de Reserva (nº de PMTs)", 0, 12, 3)

with col3:
    st.subheader("3. Sponsor & Quali")
    track_record = st.selectbox("Track Record do Emissor", ["Novo no Mercado", "Histórico com Soluços", "Bom Histórico", "Tier 1 / Listado"])
    gov_corp = st.radio("Governança", ["Familiar/Baixa", "Auditada/Profissional"])
    
    score_sponsor = 0
    if track_record == "Tier 1 / Listado": score_sponsor += 15
    elif track_record == "Bom Histórico": score_sponsor += 10
    
    if gov_corp == "Auditada/Profissional": score_sponsor += 5

# --- CÁLCULO CENTRAL ---
dados_calculo = {
    'ltv_stress': ltv_stress,
    'score_liquidez': score_liquidez_map[liquidez],
    'tipo_risco': tipo_risco_interno,
    'poc': poc,
    'icsd': icsd,
    'pmts_reserva': pmts_reserva,
    'score_sponsor': score_sponsor
}

score_final = calcular_rating_avancado(dados_calculo)
rating_txt, color_hex = get_grade(score_final)

st.divider()

# --- DASHBOARD DE RESULTADOS E STRESS ---
st.subheader("🎯 Resultado e Análise de Sensibilidade")

c_res1, c_res2 = st.columns([1, 2])

with c_res1:
    st.markdown(f"""
    <div style="background-color: {color_hex}20; padding: 20px; border-radius: 15px; border: 2px solid {color_hex}; text-align: center;">
        <h4 style="color: {color_hex}; margin:0;">Rating Estimado</h4>
        <h1 style="font-size: 60px; margin:0; color: {color_hex};">{rating_txt.split()[0]}</h1>
        <p><b>{rating_txt.split()[1]}</b> (Score: {score_final})</p>
    </div>
    """, unsafe_allow_html=True)
    
    if score_final < 60:
        st.warning("⚠️ Atenção: Operação com riscos estruturais relevantes.")

with c_res2:
    # Tabela de Sensibilidade (O "Pulo do Gato" para analistas)
    st.markdown("#### 📉 Teste de Estresse do Fluxo (Impacto no ICSD)")
    st.caption("Como a cobertura da dívida se comporta se a Receita cair ou a Despesa/Juros subir?")
    
    # Criando cenários
    cenarios = [-20, -10, 0, 10, 20] # Variação na Receita
    icsd_stress = []
    
    for c in cenarios:
        receita_stress = receita_op * (1 + (c/100))
        res = receita_stress / servico_divida if servico_divida > 0 else 0
        icsd_stress.append(res)
        
    df_stress = pd.DataFrame({
        "Variação NOI": [f"{x}%" for x in cenarios],
        "NOI Estressado (MM)": [f"R$ {receita_op * (1 + x/100):.1f}" for x in cenarios],
        "ICSD Resultante": icsd_stress
    })
    
    # Formatação condicional simples no Pandas para Streamlit
    def color_icsd(val):
        color = 'red' if val < 1.0 else ('orange' if val < 1.2 else 'green')
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df_stress.style.applymap(color_icsd, subset=['ICSD Resultante'])
                 .format({"ICSD Resultante": "{:.2f}x"}),
        use_container_width=True,
        hide_index=True
    )
    
    if icsd_stress[1] < 1.0: # Se cair 10% e quebrar
        st.error("🚨 ALERTA: Uma queda de 10% no NOI compromete o pagamento da dívida.")
    elif icsd_stress[0] < 1.0:
        st.warning("⚠️ Cuidado: O projeto não aguenta desaforo de 20% na receita.")
    else:
        st.success("✅ Resiliente: O projeto suporta queda de 20% no NOI e mantém ICSD > 1.0x")
