import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata

def formatar_slug(texto):
    """Remove acentos e espaços para montar a URL (Ex: São Paulo -> sao-paulo)"""
    texto_limpo = ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto_limpo.strip().lower().replace(' ', '-')

def buscar_mega_leiloes(estado, cidade):
    """
    Mini-robô especialista no Mega Leilões.
    Varre o HTML tradicional usando Cloudscraper.
    """
    scraper = cloudscraper.create_scraper()
    
    estado_lower = estado.lower()
    cidade_slug = formatar_slug(cidade)
    
    # Montando a URL base no padrão do site
    url_busca = f"https://www.megaleiloes.com.br/imoveis/{estado_lower}/{cidade_slug}?pagina=1"
    
    try:
        response = scraper.get(url_busca, timeout=20)
        
        if response.status_code != 200:
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Caçando todos os links da página de resultados
        links = soup.find_all('a', href=True)
        urls_imoveis = []
        
        for link in links:
            href = link['href']
            # O Mega Leilões costuma ter "/imoveis/" ou "/leilao/" no link do lote
            if ('/imoveis/' in href or 'leilao' in href) and len(href) > 30:
                url_completa = href if href.startswith('http') else f"https://www.megaleiloes.com.br{href}"
                urls_imoveis.append(url_completa)
                
        # Remove duplicados
        urls_imoveis = list(set(urls_imoveis))
        
        if not urls_imoveis:
            return pd.DataFrame()
            
        dados = []
        # Limitado a 5 imóveis para testes rápidos
        for url_imovel in urls_imoveis[:5]:
            try:
                res_imovel = scraper.get(url_imovel, timeout=15)
                soup_imovel = BeautifulSoup(res_imovel.text, 'html.parser')
                
                # Pega todo o texto da página do lote para a IA ler
                texto_pagina = soup_imovel.get_text(separator=' ', strip=True)
                
                # O código do lote no Mega Leilões geralmente fica no final da URL (ex: -j12345)
                codigo = url_imovel.split('-')[-1]
                
                dados.append({
                    "lote": codigo, 
                    "tipo": "Imóvel", 
                    "estado": estado.upper(), 
                    "cidade": cidade,
                    "url": url_imovel, 
                    "valor_2_praca": "Consultar edital", 
                    "data_encerramento": "Extração IA", 
                    "descricao": texto_pagina
                })
                time.sleep(1) # Pausa amigável
                
            except Exception:
                continue
                
        return pd.DataFrame(dados)
        
    except Exception as e:
        print(f"Erro no Mega Leilões: {e}")
        return pd.DataFrame()