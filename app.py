import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv

# Carrega a chave da API protegida
load_dotenv()

# ==========================================
# IMPORTAÇÃO DOS MÓDULOS 
# ==========================================
from utils.analyze_ai import analisar_oportunidade_ia
from scrapers.zuk import buscar_portal_zuk
from scrapers.sold import buscar_leiloes_sold_api
from scrapers.leilaoimovel import buscar_leilao_imovel_html
from scrapers.megaleiloes import buscar_mega_leiloes

# ==========================================
# DICIONÁRIO DE MAPEAMENTO
# ==========================================
MAPEAMENTO_CIDADES = {
    "Araçatuba": {
        "ibge": "3502804", 
        "sold_place_id": "ChIJAfGqendElpQRJx0Kzs-iseg"
    },
    "São Paulo": {
        "ibge": "3550308", 
        "sold_place_id": "ChIJ0WGkg4FEzpQRrlsz_whLqZs"
    }
}

# ==========================================
# CONFIGURAÇÃO DA TELA E MEMÓRIA
# ==========================================
st.set_page_config(page_title="Radar de Leilões", page_icon="🏢", layout="wide")
st.title("🏢 Radar de Leilões Inteligente")
st.markdown("Orquestrador Multi-Portais com Inteligência Artificial em Lote.")

# INJEÇÃO DE MEMÓRIA: Garante que os dados não sumam ao clicar em botões/filtros
if 'df_resultados' not in st.session_state:
    st.session_state['df_resultados'] = None

api_key = os.getenv("GROQ_API_KEY", "")

# ==========================================
# BARRA LATERAL (CONTROLES)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações do Sistema")
    if api_key:
        st.success("✅ IA Conectada (Chave .env)")
    else:
        st.error("❌ Chave API não encontrada no .env")
        api_key = st.text_input("Insira a chave Gemini", type="password")
        
    st.markdown("---")
    st.header("🔍 Critérios de Busca")
    
    estado_alvo = st.selectbox("Estado", ["SP", "GO", "MG", "RJ", "PR", "SC", "RS", "DF"])
    cidade_alvo = st.selectbox("Cidade", ["Araçatuba", "São Paulo"]) 
    
    buscar_btn = st.button("🚀 Iniciar Varredura Global", use_container_width=True)

# ==========================================
# MOTOR DO ORQUESTRADOR E IA (EM LOTE)
# ==========================================
if buscar_btn:
    lista_de_tabelas = []
    dados_cidade = MAPEAMENTO_CIDADES.get(cidade_alvo, {})
    
    st.markdown("---")
    st.markdown("### 📡 Status da Extração")
    
    # 1. ACIONA ROBÔ ZUK
    with st.spinner("Robô Zuk: Lendo HTML via Cloudscraper..."):
        df_zuk = buscar_portal_zuk(estado_alvo, cidade_alvo)
        if not df_zuk.empty: lista_de_tabelas.append(df_zuk)
            
    # 2. ACIONA ROBÔ SOLD 
    place_id = dados_cidade.get("sold_place_id")
    if place_id:
        with st.spinner("Robô Sold: Conectando à API Oculta..."):
            df_sold = buscar_leiloes_sold_api(place_id, cidade_alvo, estado_alvo)
            if not df_sold.empty: lista_de_tabelas.append(df_sold)
                
    # 3. ACIONA ROBÔ LEILÃO IMÓVEL
    ibge_id = dados_cidade.get("ibge")
    if ibge_id:
        with st.spinner("Robô Leilão Imóvel: Varrendo sistema tradicional..."):
            df_li = buscar_leilao_imovel_html(ibge_id, cidade_alvo, estado_alvo)
            if not df_li.empty: lista_de_tabelas.append(df_li)
    
    # 4. ACIONA ROBÔ MEGA LEILÕES
    with st.spinner("Robô Mega Leilões: Varrendo HTML base..."):
        df_mega = buscar_mega_leiloes(estado_alvo, cidade_alvo)
        if not df_mega.empty: lista_de_tabelas.append(df_mega)

    # PROCESSAMENTO DA INTELIGÊNCIA ARTIFICIAL
    if not lista_de_tabelas:
        st.error("🚨 Nenhum dos robôs conseguiu encontrar imóveis para esta região.")
        st.session_state['df_resultados'] = pd.DataFrame()
    else:
        df_final = pd.concat(lista_de_tabelas, ignore_index=True)
        
        st.markdown("---")
        st.markdown(f"### 🧠 Analisando {len(df_final)} Editais com IA (Processamento em Lote)")
        
        pareceres_estruturados = []
        barra_progresso = st.progress(0)
        
        for contador, row in df_final.iterrows():
            with st.spinner(f"Extraindo prós e contras do lote {row['lote']} ({contador + 1}/{len(df_final)})..."):
                
                # Envia os dados para o Gemini
                resultado_ia = analisar_oportunidade_ia(
                    api_key=api_key, 
                    descricao=row['descricao'], 
                    valor=row['valor_2_praca'], 
                    cidade=row['cidade'], 
                    tipo_imovel=row['tipo']
                )
                pareceres_estruturados.append(resultado_ia)
                
                # Pausa amigável de 3 segundos para não estourar o limite gratuito do Google
                time.sleep(3) 
                barra_progresso.progress((contador + 1) / len(df_final))
                
        # Junta a análise da IA com a tabela de imóveis e salva na Memória
        df_final['Analise_JSON'] = pareceres_estruturados
        st.session_state['df_resultados'] = df_final

# ==========================================
# RENDERIZAÇÃO DO PAINEL TÁTICO
# ==========================================
if st.session_state['df_resultados'] is not None and not st.session_state['df_resultados'].empty:
    df_render = st.session_state['df_resultados']
    
    st.markdown("---")
    col_titulo, col_filtro = st.columns([2, 1])
    with col_titulo:
        st.markdown(f"### 📋 Painel Tático de Oportunidades ({len(df_render)} avaliados)")
    with col_filtro:
        # Filtro de qualidade baseado na nota da IA!
        ocultar_risco = st.checkbox("🟢 Ocultar Notas Baixas (< 5.0)")
        
    for index, row in df_render.iterrows():
        dados_ia = row.get('Analise_JSON', {})
        
        # Garante que a nota seja tratada como número para o filtro funcionar
        try:
            nota = float(dados_ia.get('nota', 0))
        except:
            nota = 0.0
            
        # Aplica o filtro de tela
        if ocultar_risco and nota < 5.0:
            continue
            
        origem = "Sold/Superbid" if "superbid" in row['url'] or "sold" in row['url'] else "Zuk" if "portalzuk" in row['url'] else "Mega Leilões" if "megaleiloes" in row['url'] else "Leilão Imóvel"
        cor_nota = "🟢" if nota >= 7 else "🟡" if nota >= 5 else "🔴"
        
        # O título do card já mostra a nota da IA para você bater o olho rápido
        with st.expander(f"{cor_nota} Lote: {row['lote']} - {row['cidade']} | Nota: {nota}/10 | Fonte: {origem}"):
            st.write(f"**Valor:** R$ {row['valor_2_praca']}")
            st.markdown(f"[🔗 Acessar Página Original no {origem}]({row['url']})")
            st.write("---")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Nota de Oportunidade", f"{nota} / 10")
            col2.metric("Modalidade", dados_ia.get('modalidade', 'Não identificada'))
            col3.metric("Ocupação", dados_ia.get('ocupacao', 'Não informada'))
            
            st.warning(f"⚠️ **Riscos Ocultos:** {dados_ia.get('alertas_risco', 'Nenhum risco extraído.')}")
            st.success(f"🎯 **Parecer Estratégico:** {dados_ia.get('parecer_estrategico', 'Análise não gerada.')}")