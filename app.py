import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
import unicodedata
import scrapers
from utils import analyze_ai

# ==========================================
# BASE DE DADOS DE PORTAIS (TEMPLATES)
# ==========================================
# Aqui você cadastra as URLs base. Use {estado} e {cidade} onde as variáveis devem entrar.
BASE_PORTAIS = {
    "Portal Zuk": "https://www.portalzuk.com.br/leilao-de-imoveis/{estado}/{cidade}",
    "Mega Leilões": "https://www.megaleiloes.com.br/{estado}/{cidade}",
    "Sodré Santoro": "https://www.sodresantoro.com.br/leilao/imoveis/{estado}/{cidade}/",
    "Milan Leilões": "https://www.milanleiloes.com.br/imoveis/{estado}/{cidade}",
    "Freitas Leiloeiro": "https://www.freitasleiloeiro.com.br/imoveis/{estado}/{cidade}"
}

def formatar_para_url(texto):
    """
    Remove acentos, cê-cedilha e troca espaços por traços.
    Ex: 'São Paulo' -> 'sao-paulo' | 'Araçatuba' -> 'aracatuba'
    """
    # Remove os acentos usando a biblioteca nativa unicodedata
    texto_limpo = ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    # Transforma em minúsculo e troca espaços por hífens
    texto_limpo = texto_limpo.strip().lower().replace(' ', '-')
    return texto_limpo

def gerar_urls_dinamicas(estado, cidade):
    """
    Cruza o estado e a cidade com todos os templates da base de dados.
    """
    estado_url = formatar_para_url(estado)
    cidade_url = formatar_para_url(cidade)
    
    lista_urls = []
    
    # Faz um loop pela nossa "base de dados" e injeta os nomes limpos na URL
    for nome_portal, template in BASE_PORTAIS.items():
        url_pronta = template.format(estado=estado_url, cidade=cidade_url)
        lista_urls.append({"portal": nome_portal, "url": url_pronta})
        
    return lista_urls

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# ==========================================
# A SOLUÇÃO DO ERRO (VARIÁVEL GLOBAL)
# ==========================================
# Garante que a variável sempre exista. Se não tiver no .env, ela fica vazia ("").
api_key = os.getenv("GEMINI_API_KEY", "")

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Radar de Leilões", page_icon="🏢", layout="wide")

st.title("🏢 Radar de Leilões Inteligente")
st.markdown("Busca **REAL** no Portal Zuk e análise visual de editais com IA.")

# ==========================================
# BARRA LATERAL (SIDEBAR) - CONTROLES
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Agora a lógica só verifica se a variável (já criada lá em cima) tem texto dentro
    if api_key:
        st.success("✅ IA Conectada (Chave do arquivo .env)")
    else:
        api_key = st.text_input("Chave da API do Google (Gemini)", type="password")
        if not api_key:
            st.warning("Insira a chave da API para análise automática.")
    
    st.markdown("---")
    st.header("🔍 Link da Busca")
    url_busca_zuk = st.text_input(
        "Cole a URL de busca do Portal Zuk", 
        value="https://www.portalzuk.com.br/leilao-de-imoveis/c/todos-imoveis/sp/interior/aracatuba"
    )
    buscar_btn = st.button("🚀 Iniciar Varredura Real", use_container_width=True)

# ==========================================
# MÓDULO DE EXTRAÇÃO REAL (CLOUDSCRAPER)
# ==========================================
def buscar_leiloes_reais_zuk(url_busca):
    scraper = cloudscraper.create_scraper() 
    try:
        response = scraper.get(url_busca, timeout=20)
        if response.status_code != 200:
            st.error(f"Erro ao acessar a página. Código: {response.status_code}")
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        urls_imoveis = []
        
        for link in links:
            href = link['href']
            if ('/imovel/' in href or '/leilao/' in href) and len(href) > 20:
                url_completa = f"https://www.portalzuk.com.br{href}" if href.startswith('/') else href
                urls_imoveis.append(url_completa)
                
        urls_imoveis = list(set(urls_imoveis))
        if not urls_imoveis:
            st.warning("O robô não encontrou links de imóveis na página.")
            return pd.DataFrame()
            
        dados = []
        for url_imovel in urls_imoveis[:5]: # LIMITADO A 5 para testes
            try:
                res_imovel = scraper.get(url_imovel, timeout=15)
                soup_imovel = BeautifulSoup(res_imovel.text, 'html.parser')
                texto_pagina = soup_imovel.get_text(separator=' ', strip=True)
                codigo = url_imovel.split('-')[-1]
                
                partes_url = url_imovel.split('/')
                estado_extraido = partes_url[4].upper() if len(partes_url) > 4 else "SP"
                cidade_extraida = partes_url[5].replace('-', ' ').title() if len(partes_url) > 5 else "Cidade"
                
                tipo = "Apartamento" if "apartamento" in texto_pagina.lower() else "Casa/Outro"
                if "terreno" in texto_pagina.lower(): tipo = "Terreno"
                
                dados.append({
                    "lote": codigo, "tipo": tipo, "estado": estado_extraido, "cidade": cidade_extraida,
                    "url": url_imovel, "valor_2_praca": "Consultar site", 
                    "data_encerramento": "Extração IA", "descricao": texto_pagina
                })
                time.sleep(1)
            except Exception:
                continue
        return pd.DataFrame(dados)
    except Exception as e:
        st.error(f"Erro na conexão com o CloudScraper: {e}")
        return pd.DataFrame()

# ==========================================
# LÓGICA PRINCIPAL DO APP E FRONT-END VISUAL
# ==========================================
if buscar_btn:
    with st.spinner("Varrendo página de resultados..."):
        df_real = buscar_leiloes_reais_zuk(url_busca_zuk)
        
    if df_real.empty:
        st.warning("Nenhum leilão válido foi encontrado nesta URL ou a conexão falhou.")
    else:
        st.success(f"Encontrados {len(df_real)} imóveis ativos! Analisando os editais...")
        
        pareceres_estruturados = []
        barra_progresso = st.progress(0)
        
        for contador, row in df_real.iterrows():
            with st.spinner(f"Extraindo prós e contras do lote {row['lote']}..."):
                analise_dict = analyze_ai(row['descricao'], api_key)
                pareceres_estruturados.append(analise_dict)
                barra_progresso.progress((contador + 1) / len(df_real))
                time.sleep(5)
                
        df_real['Analise_JSON'] = pareceres_estruturados
        
        st.markdown("---")
        
        # NOVO: Checkbox para Ocultar Ciladas
        col_titulo, col_filtro = st.columns([2, 1])
        with col_titulo:
            st.markdown("### 📋 Painel Tático de Oportunidades")
        with col_filtro:
            ocultar_vermelhos = st.checkbox("🟢 Mostrar Apenas Oportunidades (Ocultar Vermelhos)")
        
        # Renderização Visual
        for index, row in df_real.iterrows():
            dados_ia = row.get('Analise_JSON', {})
            
            # Mais uma camada de segurança
            if not isinstance(dados_ia, dict):
                dados_ia = {} 
                
            status_ia = str(dados_ia.get('status', 'ERRO')).upper()
            
            # Lógica do filtro: pula o card inteiro se for vermelho ou erro
            if ocultar_vermelhos and status_ia in ["VERMELHO", "ERRO"]:
                continue
            
            icone_status = "🟢" if status_ia == "VERDE" else "🟡" if status_ia == "AMARELO" else "🔴"
            tipo_ia = dados_ia.get('tipo_imovel', 'Imóvel Não Identificado')
            resumo_ia = dados_ia.get('resumo', 'Resumo indisponível.')
            pontos_fav = dados_ia.get('favoraveis', [])
            pontos_crit = dados_ia.get('criticos', [])
            
            with st.expander(f"{icone_status} {tipo_ia} - Ref: {row['lote']} | {row['cidade']}/{row['estado']}"):
                st.markdown(f"**Veredito:** {resumo_ia}")
                st.markdown(f"[🔗 Acessar Página Original do Imóvel no Leiloeiro]({row['url']})")
                st.write("") 
                
                col_positiva, col_negativa = st.columns(2)
                with col_positiva:
                    st.success("👍 **Pontos Favoráveis**")
                    if isinstance(pontos_fav, list) and pontos_fav:
                        for ponto in pontos_fav:
                            st.write(f"- {ponto}")
                    else:
                        st.write("- Nenhum ponto favorável.")
                        
                with col_negativa:
                    st.error("🚨 **Pontos Críticos (Atenção)**")
                    if isinstance(pontos_crit, list) and pontos_crit:
                        for ponto in pontos_crit:
                            st.write(f"- {ponto}")
                    else:
                        st.write("- Nenhum risco encontrado.")
        
        st.markdown("---")
        
        # Exportação Segura para CSV
        df_export = df_real.copy()
        df_export['Resumo_IA'] = df_export['Analise_JSON'].apply(lambda x: x.get('resumo', '') if isinstance(x, dict) else '')
        df_export['Favoraveis'] = df_export['Analise_JSON'].apply(lambda x: ", ".join(x.get('favoraveis', [])) if isinstance(x, dict) and isinstance(x.get('favoraveis'), list) else '')
        df_export['Criticos'] = df_export['Analise_JSON'].apply(lambda x: ", ".join(x.get('criticos', [])) if isinstance(x, dict) and isinstance(x.get('criticos'), list) else '')
        
        df_csv = df_export[['lote', 'tipo', 'estado', 'cidade', 'url', 'Resumo_IA', 'Favoraveis', 'Criticos']]
        csv = df_csv.to_csv(index=False).encode('utf-8')
        
        st.download_button("📥 Baixar Planilha", data=csv, file_name='leiloes_analisados.csv', mime='text/csv')