import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv

# Carrega a chave da API protegida
load_dotenv()

# ==========================================
# IMPORTAÇÃO DOS MÓDULOS (SUA ARQUITETURA)
# ==========================================
# Nova importação apontando para a função atualizada da IA
from utils.analyze_ai import analisar_oportunidade_gemini 

# Mini-Robôs
from scrapers.zuk import buscar_portal_zuk
from scrapers.sold import buscar_leiloes_sold_api
from scrapers.leilaoimovel import buscar_leilao_imovel_html
from scrapers.megaleiloes import buscar_mega_leiloes

# ==========================================
# DICIONÁRIO DE MAPEAMENTO (DE-PARA)
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
# CONFIGURAÇÃO DA TELA
# ==========================================
st.set_page_config(page_title="Radar de Leilões", page_icon="🏢", layout="wide")
st.title("🏢 Radar de Leilões Inteligente")
st.markdown("Orquestrador Multi-Portais com Inteligência Artificial sob demanda.")

# Garantia de que a chave da IA existe
api_key = os.getenv("GEMINI_API_KEY", "")

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
# MOTOR DO ORQUESTRADOR
# ==========================================
if buscar_btn:
    lista_de_tabelas = []
    dados_cidade = MAPEAMENTO_CIDADES.get(cidade_alvo, {})
    
    st.markdown("---")
    st.markdown("### 📡 Status da Extração")
    
    # 1. ACIONA ROBÔ ZUK
    with st.spinner("Robô Zuk: Lendo HTML via Cloudscraper..."):
        df_zuk = buscar_portal_zuk(estado_alvo, cidade_alvo)
        if not df_zuk.empty:
            lista_de_tabelas.append(df_zuk)
            st.success(f"✅ Zuk: {len(df_zuk)} imóveis encontrados.")
        else:
            st.warning("⚠️ Zuk: Nenhum imóvel encontrado ou bloqueio.")
            
    # 2. ACIONA ROBÔ SOLD (API)
    place_id = dados_cidade.get("sold_place_id")
    if place_id:
        with st.spinner("Robô Sold: Conectando à API Oculta..."):
            df_sold = buscar_leiloes_sold_api(place_id, cidade_alvo, estado_alvo)
            if not df_sold.empty:
                lista_de_tabelas.append(df_sold)
                st.success(f"✅ Sold: {len(df_sold)} imóveis encontrados.")
            else:
                st.warning("⚠️ Sold: Nenhum imóvel na API.")
                
    # 3. ACIONA ROBÔ LEILÃO IMÓVEL
    ibge_id = dados_cidade.get("ibge")
    if ibge_id:
        with st.spinner("Robô Leilão Imóvel: Varrendo sistema tradicional..."):
            df_li = buscar_leilao_imovel_html(ibge_id, cidade_alvo, estado_alvo)
            if not df_li.empty:
                lista_de_tabelas.append(df_li)
                st.success(f"✅ Leilão Imóvel: {len(df_li)} imóveis encontrados.")
            else:
                st.warning("⚠️ Leilão Imóvel: Nenhum imóvel encontrado.")
    
    # 4. ACIONA ROBÔ MEGA LEILÕES
    with st.spinner("Robô Mega Leilões: Varrendo HTML base..."):
        df_mega = buscar_mega_leiloes(estado_alvo, cidade_alvo)
        if not df_mega.empty:
            lista_de_tabelas.append(df_mega)
            st.success(f"✅ Mega Leilões: {len(df_mega)} imóveis encontrados.")
        else:
            st.warning("⚠️ Mega Leilões: Nenhum imóvel encontrado.")

    # ==========================================
    # RENDERIZAÇÃO DO PAINEL TÁTICO (NOVA VERSÃO SOB DEMANDA)
    # ==========================================
    if not lista_de_tabelas:
        st.error("🚨 Nenhum dos robôs conseguiu encontrar imóveis para esta região.")
    else:
        # Junta todas as tabelas em uma só
        df_final = pd.concat(lista_de_tabelas, ignore_index=True)
        
        st.markdown("---")
        st.markdown(f"### 📋 Painel Tático de Oportunidades ({len(df_final)} encontrados)")
            
        for index, row in df_final.iterrows():
            # Identifica a origem para o usuário
            origem = "Sold/Superbid" if "superbid" in row['url'] or "sold" in row['url'] else "Zuk" if "portalzuk" in row['url'] else "Mega Leilões" if "megaleiloes" in row['url'] else "Leilão Imóvel"
            
            with st.expander(f"🏠 Lote: {row['lote']} - {row['cidade']}/{row['estado']} | Fonte: {origem}"):
                st.write(f"**Valor:** R$ {row['valor_2_praca']}")
                st.markdown(f"[🔗 Acessar Página Original no {origem}]({row['url']})")
                st.write("---")
                
                # Botão que acorda a IA apenas quando você manda
                if st.button("🧠 Analisar Oportunidade com IA", key=f"btn_ia_{index}"):
                    with st.spinner("Consultando o Oráculo Sênior do Gemini..."):
                        resultado_ia = analisar_oportunidade_gemini(
                            api_key=api_key, 
                            descricao=row['descricao'], 
                            valor=row['valor_2_praca'], 
                            cidade=row['cidade'], 
                            tipo_imovel=row['tipo']
                        )
                        
                        # Pinta a tela com o JSON Estruturado que o Gemini devolveu
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Nota de Oportunidade", f"{resultado_ia.get('nota', '?')} / 10")
                        col2.metric("Modalidade", resultado_ia.get('modalidade', 'Não identificada'))
                        col3.metric("Ocupação", resultado_ia.get('ocupacao', 'Não informada'))
                        
                        st.warning(f"⚠️ **Riscos Ocultos:** {resultado_ia.get('alertas_risco', 'Nenhum risco extraído.')}")
                        st.success(f"🎯 **Parecer Estratégico:** {resultado_ia.get('parecer_estrategico', 'Análise não gerada.')}")