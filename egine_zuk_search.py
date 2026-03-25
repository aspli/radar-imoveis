import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata

def formatar_slug(texto):
    """Remove acentos e transforma espaços em traços (Ex: São Paulo -> sao-paulo)"""
    texto_limpo = ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto_limpo.strip().lower().replace(' ', '-')

def buscar_portal_zuk(estado, cidade, regiao="interior"):
    """
    Mini-robô especialista em varrer o Portal Zuk.
    Usa CloudScraper para burlar o bloqueio antibot (Cloudflare).
    """
    scraper = cloudscraper.create_scraper()
    
    # Prepara os textos para a URL
    estado_lower = estado.lower()
    cidade_slug = formatar_slug(cidade)
    
    # Monta a URL dinâmica no padrão exato do Zuk
    url_busca = f"https://www.portalzuk.com.br/leilao-de-imoveis/c/todos-imoveis/{estado_lower}/{regiao}/{cidade_slug}"
    
    try:
        response = scraper.get(url_busca, timeout=20)
        
        if response.status_code != 200:
            print(f"Erro ao acessar Portal Zuk. Código: {response.status_code}")
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Caça todos os links da página de resultados
        links = soup.find_all('a', href=True)
        urls_imoveis = []
        
        for link in links:
            href = link['href']
            # O Zuk usa /imovel/ ou /leilao/ nas URLs dos lotes
            if ('/imovel/' in href or '/leilao/' in href) and len(href) > 20:
                url_completa = f"https://www.portalzuk.com.br{href}" if href.startswith('/') else href
                urls_imoveis.append(url_completa)
                
        urls_imoveis = list(set(urls_imoveis)) # Remove duplicados
        
        if not urls_imoveis:
            print("Zuk: Nenhum link de imóvel encontrado nesta cidade.")
            return pd.DataFrame()
            
        dados = []
        # Limitado a 5 para testes rápidos. No futuro você pode tirar esse [:5]
        for url_imovel in urls_imoveis[:5]:
            try:
                # Entra na página específica do edital do imóvel
                res_imovel = scraper.get(url_imovel, timeout=15)
                soup_imovel = BeautifulSoup(res_imovel.text, 'html.parser')
                
                # Extrai absolutamente TUDO que é texto da página para a IA ler depois
                texto_pagina = soup_imovel.get_text(separator=' ', strip=True)
                codigo = url_imovel.split('-')[-1]
                
                # Devolve o padrão exato que a IA e o Streamlit esperam
                dados.append({
                    "lote": codigo, 
                    "tipo": "Imóvel", # A IA corrige isso depois
                    "estado": estado.upper(), 
                    "cidade": cidade,
                    "url": url_imovel, 
                    "valor_2_praca": "Consultar edital", 
                    "data_encerramento": "Extração IA", 
                    "descricao": texto_pagina
                })
                time.sleep(1.5) # Freio de mão para não ser banido
                
            except Exception:
                continue
                
        return pd.DataFrame(dados)
        
    except Exception as e:
        print(f"Erro na varredura do Zuk: {e}")
        return pd.DataFrame()