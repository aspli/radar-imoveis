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
# Ferramentas
from utils.analyze_ai import analisar_com_ia
# Mini-Robôs
from scrapers.zuk import buscar_portal_zuk
from scrapers.sold import buscar_leiloes_sold_api
from scrapers.leilaoimovel import buscar_leilao_imovel_html

# ==========================================
# DICIONÁRIO DE MAPEAMENTO (DE-PARA)
# ==========================================
# Dica de Engenharia: No futuro, você pode mover isso para o utils/url_treatment.py
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
st.markdown("Orquestrador Multi-Portais com Inteligência Artificial.")

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
    # Convertido para selectbox para garantir que bate com o nosso dicionário
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
                
    # 3. ACIONA ROBÔ LEILÃO IMÓVEL (HTML Dinâmico)
    ibge_id = dados_cidade.get("ibge")
    if ibge_id:
        with st.spinner("Robô Leilão Imóvel: Varrendo sistema tradicional..."):
            df_li = buscar_leilao_imovel_html(ibge_id, cidade_alvo, estado_alvo)
            if not df_li.empty:
                lista_de_tabelas.append(df_li)
                st.success(f"✅ Leilão Imóvel: {len(df_li)} imóveis encontrados.")
            else:
                st.warning("⚠️ Leilão Imóvel: Nenhum imóvel encontrado.")

    # ==========================================
    # JUNÇÃO E ANÁLISE DE IA
    # ==========================================
    if not lista_de_tabelas:
        st.error("🚨 Nenhum dos robôs conseguiu encontrar imóveis para esta região.")
    else:
        # A Mágica do Pandas: Junta todas as tabelas em uma só!
        df_final = pd.concat(lista_de_tabelas, ignore_index=True)
        
        st.markdown("---")
        st.markdown(f"### 🧠 Analisando {len(df_final)} Editais com IA")
        
        pareceres_estruturados = []
        barra_progresso = st.progress(0)
        
        for contador, row in df_final.iterrows():
            with st.spinner(f"Extraindo prós e contras do lote {row['lote']}..."):
                analise_dict = analisar_com_ia(row['descricao'], api_key)
                pareceres_estruturados.append(analise_dict)
                
                # Freio de mão para não estourar a API gratuita do Google
                time.sleep(4) 
                barra_progresso.progress((contador + 1) / len(df_final))
                
        df_final['Analise_JSON'] = pareceres_estruturados
        
        # ==========================================
        # RENDERIZAÇÃO DO PAINEL TÁTICO
        # ==========================================
        st.markdown("---")
        col_titulo, col_filtro = st.columns([2, 1])
        with col_titulo:
            st.markdown("### 📋 Painel Tático de Oportunidades")
        with col_filtro:
            ocultar_vermelhos = st.checkbox("🟢 Mostrar Apenas Oportunidades")
            
        for index, row in df_final.iterrows():
            dados_ia = row.get('Analise_JSON', {})
            if not isinstance(dados_ia, dict): dados_ia = {} 
                
            status_ia = str(dados_ia.get('status', 'ERRO')).upper()
            if ocultar_vermelhos and status_ia in ["VERMELHO", "ERRO"]:
                continue
            
            icone_status = "🟢" if status_ia == "VERDE" else "🟡" if status_ia == "AMARELO" else "🔴"
            tipo_ia = dados_ia.get('tipo_imovel', 'Imóvel')
            
            # Repare que agora mostramos qual portal trouxe o imóvel!
            origem = "Sold" if "sold.com" in row['url'] else "Zuk" if "portalzuk" in row['url'] else "Leilão Imóvel"
            
            with st.expander(f"{icone_status} {tipo_ia} - Ref: {row['lote']} | {row['cidade']}/{row['estado']} | Fonte: {origem}"):
                st.markdown(f"**Veredito:** {dados_ia.get('resumo', 'Resumo indisponível.')}")
                st.markdown(f"[🔗 Acessar Página no {origem}]({row['url']})")
                st.write("") 
                
                col_positiva, col_negativa = st.columns(2)
                with col_positiva:
                    st.success("👍 **Pontos Favoráveis**")
                    pontos_fav = dados_ia.get('favoraveis', [])
                    if isinstance(pontos_fav, list) and pontos_fav:
                        for ponto in pontos_fav: st.write(f"- {ponto}")
                    else:
                        st.write("- Nenhum ponto favorável.")
                        
                with col_negativa:
                    st.error("🚨 **Pontos Críticos (Atenção)**")
                    pontos_crit = dados_ia.get('criticos', [])
                    if isinstance(pontos_crit, list) and pontos_crit:
                        for ponto in pontos_crit: st.write(f"- {ponto}")
                    else:
                        st.write("- Nenhum risco encontrado.")
                        