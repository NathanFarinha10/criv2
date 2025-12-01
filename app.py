import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- Configurações Iniciais ---
st.set_page_config(page_title="CRI Rating Enterprise", page_icon="🏢", layout="wide")

# CSS Customizado
st.markdown("""
<style>
    .header-style {font-size:20px; font-weight:bold; color:#1f77b4;}
    .sub-header {font-size:16px; font-weight:bold; color:#555;}
    .metric-box {border: 1px solid #e6e6e6; padding: 15px; border-radius: 5px; text-align: center;}
</style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares de Pontuação ---
def map_qualitativo(valor, opcoes, scores):
    """Mapeia uma escolha textual para um score numérico."""
    try:
        index = opcoes.index(valor)
        return scores[index]
    except:
        return 0

def calcular_rating_final(scores_dict):
    """Calcula o rating final ponderado."""
    # Pesos Sugeridos (Total 100%)
    pesos = {
        'governanca': 10,
        'historico': 10,
        'financeiro': 15,
        'ativo_especifico': 20, # O peso mais alto é o risco do projeto/carteira
        'estrutura_capital': 5,
        'reforco': 5,
        'garantias': 15,
        'conflitos': 5,
        'prestadores': 5,
        'contratual': 10
    }
    
    score_total = sum([scores_dict[k] * (pesos[k]/100) for k in pesos])
    return score_total

def get_grade(score):
    if score >= 90: return "AAA", "#1f77b4" # Azul
    elif score >= 80: return "AA", "#2ca02c"  # Verde
    elif score >= 70: return "A", "#98df8a"   # Verde Claro
    elif score >= 60: return "BBB", "#ff7f0e" # Laranja
    elif score >= 50: return "BB", "#ffbb78"  # Laranja Claro
    elif score >= 40: return "B", "#d62728"   # Vermelho
    else: return "C/D", "#8c564b" # Marrom

# --- Interface Principal ---

st.title("🏢 Sistema de Rating de Crédito Estruturado (CRI)")
st.markdown("**Metodologia 10-Pontos:** Análise Institucional, Financeira e Estrutural.")

# --- Sidebar: Definição do Tipo de Análise ---
with st.sidebar:
    st.header("Configuração da Operação")
    nome_emissor = st.text_input("Emissor/Devedor", "Empresa Exemplo S.A.")
    tipo_ativo = st.selectbox(
        "Natureza do Risco (Pilar 4)", 
        ["Desenvolvimento Imobiliário (Projeto)", "Carteira de Recebíveis (Pulverizado)"]
    )
    st.divider()
    st.info("Preencha as 3 abas principais para gerar o relatório.")

# --- ABAS DE INPUTS ---
tab_inst, tab_fin, tab_estrut, tab_res = st.tabs([
    "🏛️ 1. Institucional & Sponsor", 
    "📈 2. Financeiro & Ativo", 
    "🧱 3. Estrutura & Garantias", 
    "🎯 Resultado"
])

# Dicionário para guardar os scores parciais (0-100)
scores = {}

# --- ABA 1: Institucional, Histórico, Conflitos e Prestadores ---
with tab_inst:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="header-style">1. Governança e Reputação</p>', unsafe_allow_html=True)
        audit_opt = ["Sem auditoria/Local", "Big 4 / Top Tier", "Auditado (Mid-tier)"]
        audit_val = st.selectbox("Qualidade da Auditoria & Compliance", audit_opt)
        score_gov = map_qualitativo(audit_val, audit_opt, [20, 100, 70])
        
        esg_opt = ["Riscos Relevantes", "Neutro", "Políticas Claras/Certificado"]
        esg_val = st.select_slider("Fatores ESG & Litígios", options=esg_opt)
        score_gov = (score_gov + map_qualitativo(esg_val, esg_opt, [0, 50, 100])) / 2
        scores['governanca'] = score_gov

        st.markdown('<p class="header-style">2. Histórico Operacional</p>', unsafe_allow_html=True)
        track_opt = ["Iniciante/Problemas", "Histórico Mediano", "Track Record Comprovado"]
        track_val = st.select_slider("Experiência e Entregas", options=track_opt)
        scores['historico'] = map_qualitativo(track_val, track_opt, [30, 70, 100])

    with col2:
        st.markdown('<p class="header-style">8. Conflitos de Interesse</p>', unsafe_allow_html=True)
        skin_opt = ["Retenção Baixa/Nula", "Retenção Média (Subordinada)", "Alto Alinhamento (Skin in the Game)"]
        skin_val = st.selectbox("Alinhamento Originador x Investidor", skin_opt)
        scores['conflitos'] = map_qualitativo(skin_val, skin_opt, [40, 70, 100])

        st.markdown('<p class="header-style">9. Qualidade dos Prestadores</p>', unsafe_allow_html=True)
        serv_opt = ["Genéricos/Internos", "Renomados e Independentes"]
        serv_val = st.radio("Agente Fiduciário / Securitizadora", serv_opt)
        scores['prestadores'] = map_qualitativo(serv_val, serv_opt, [50, 100])

# --- ABA 2: Financeiro e O "Garfo" do Ativo (Pilar 4) ---
with tab_fin:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="header-style">3. Saúde Financeira (Corporativa/SPE)</p>', unsafe_allow_html=True)
        div_liq_ebitda = st.number_input("Dívida Líquida / EBITDA (x)", 0.0, 15.0, 2.5)
        
        # Score Financeiro Inverso (Quanto menor a alavancagem, maior a nota)
        if div_liq_ebitda < 1.0: s_fin = 100
        elif div_liq_ebitda < 2.5: s_fin = 85
        elif div_liq_ebitda < 4.0: s_fin = 60
        else: s_fin = 30
        
        liquidez_corr = st.number_input("Índice de Liquidez Corrente", 0.0, 5.0, 1.5)
        if liquidez_corr > 1.5: s_fin += 0 # Bonus já incluso
        elif liquidez_corr < 1.0: s_fin -= 20 # Penalidade
        
        scores['financeiro'] = max(0, min(100, s_fin))

    with col2:
        st.markdown(f'<p class="header-style">4. Risco do Ativo: {tipo_ativo}</p>', unsafe_allow_html=True)
        
        s_ativo = 0
        if tipo_ativo == "Desenvolvimento Imobiliário (Projeto)":
            # Análise de Desenvolvimento
            ivv = st.slider("IVV (Velocidade de Vendas Recente) %", 0, 100, 30)
            poc_fisico = st.slider("Avanço Físico (POC) %", 0, 100, 40)
            custo_coberto = st.radio("Custo da Obra Coberto?", ["Parcialmente", "Sim (Equity + Finam)"])
            
            s_ativo = (ivv * 0.4) + (poc_fisico * 0.4)
            if custo_coberto == "Sim (Equity + Finam)": s_ativo += 20
            
        else:
            # Análise de Carteira/Pulverizado
            ltv_medio = st.slider("LTV Médio da Carteira %", 0, 100, 50)
            inadimplencia = st.number_input("Inadimplência Histórica (>90 dias) %", 0.0, 50.0, 2.0)
            concentracao = st.selectbox("Concentração (Maiores Devedores)", ["Alta", "Média", "Baixa/Pulverizada"])
            
            # Score Carteira
            s_ativo = 100 - ltv_medio # Base
            s_ativo -= (inadimplencia * 5) # Penalidade pesada por inadimplência
            if concentracao == "Alta": s_ativo -= 20
            elif concentracao == "Baixa/Pulverizada": s_ativo += 10
            
        scores['ativo_especifico'] = max(0, min(100, s_ativo))

# --- ABA 3: Estrutura, Reforço e Garantias ---
with tab_estrut:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<p class="header-style">5. Estrutura de Capital</p>', unsafe_allow_html=True)
        subordinada = st.slider("% de Subordinação (Júnior/Mez)", 0, 50, 10)
        waterfall = st.checkbox("Cascata de Pagamentos Clara?", value=True)
        
        s_est = min(100, subordinada * 3) # 30% subordinação = quase 90 pts
        if not waterfall: s_est = s_est / 2
        scores['estrutura_capital'] = s_est

        st.markdown('<p class="header-style">6. Mecanismos de Reforço</p>', unsafe_allow_html=True)
        reserva = st.number_input("Fundo de Reserva (nº PMTs)", 0, 12, 3)
        scores['reforco'] = min(100, reserva * 20) # 5 PMTs = 100 pts

    with col2:
        st.markdown('<p class="header-style">7. Qualidade das Garantias</p>', unsafe_allow_html=True)
        tipo_garantia = st.selectbox("Tipo de Garantia", ["Aval/Fiança", "Hipoteca", "Alienação Fiduciária"])
        liquidez_garantia = st.select_slider("Liquidez do Imóvel/Garantia", ["Baixa", "Média", "Alta"])
        
        s_gar = 0
        if tipo_garantia == "Alienação Fiduciária": s_gar += 60
        elif tipo_garantia == "Hipoteca": s_gar += 30
        
        if liquidez_garantia == "Alta": s_gar += 40
        elif liquidez_garantia == "Média": s_gar += 20
        
        scores['garantias'] = s_gar

    with col3:
        st.markdown('<p class="header-style">10. Robustez Contratual</p>', unsafe_allow_html=True)
        covenants = st.multiselect("Covenants Financeiros Presentes", ["Dívida Liq/EBITDA", "ICSD Mínimo", "LTV Máximo", "Cross Default"])
        scores['contratual'] = min(100, len(covenants) * 25)

# --- ABA RESULTADO ---
with tab_res:
    # Calcular
    final_score = calcular_rating_final(scores)
    grade, color = get_grade(final_score)
    
    col_top1, col_top2 = st.columns([1, 2])
    
    with col_top1:
        st.markdown(f"""
        <div style="background-color: {color}20; padding: 20px; border-radius: 10px; border-left: 10px solid {color}; text-align: center;">
            <h3 style="margin:0; color: #333;">Rating Calculado</h3>
            <h1 style="font-size: 70px; margin:0; color: {color};">{grade}</h1>
            <p style="font-size: 18px;">Score Global: <b>{final_score:.1f}</b> / 100</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de Download
        df_export = pd.DataFrame([scores])
        st.download_button(
            label="📥 Exportar Dados da Análise (CSV)",
            data=df_export.to_csv(index=False).encode('utf-8'),
            file_name=f'rating_{nome_emissor.replace(" ", "_")}.csv',
            mime='text/csv'
        )

    with col_top2:
        # Gráfico de Radar (Spider Chart)
        # Agrupando categorias para o gráfico não ficar ilegível
        radar_data = {
            'Institucional': (scores['governanca'] + scores['historico'] + scores['conflitos'])/3,
            'Financeiro': scores['financeiro'],
            'Risco Ativo': scores['ativo_especifico'],
            'Estrutura': (scores['estrutura_capital'] + scores['reforco'])/2,
            'Garantias': scores['garantias'],
            'Jurídico': (scores['contratual'] + scores['prestadores'])/2
        }
        
        fig = go.Figure(data=go.Scatterpolar(
            r=list(radar_data.values()),
            theta=list(radar_data.keys()),
            fill='toself',
            name=nome_emissor
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title="Radar de Risco da Operação"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # Detalhamento Tabular
    st.subheader("Detalhamento por Pilar")
    df_detalhe = pd.DataFrame(list(scores.items()), columns=['Categoria', 'Score (0-100)'])
    
    # Formatação visual da tabela
    st.dataframe(
        df_detalhe.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=100),
        use_container_width=True
    )
