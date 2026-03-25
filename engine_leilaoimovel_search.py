import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time

def buscar_leilao_imovel_html(codigo_ibge, cidade, estado):
    """
    Mini-robô especialista em varrer o portal Leilão Imóvel via HTML tradicional.
    """
    scraper = cloudscraper.create_scraper()
    
    # Montamos a URL dinâmica usando o código IBGE da cidade. 
    # Deixei na página 1 por padrão para pegar os mais recentes.
    url_busca = f"https://www.leilaoimovel.com.br/encontre-seu-imovel?s=&cidade={codigo_ibge}&pag=1"
    
    try:
        response = scraper.get(url_busca, timeout=20)
        
        if response.status_code != 200:
            print(f"Erro ao acessar Leilão Imóvel. Código: {response.status_code}")
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Como não sabemos a classe exata do Card, vamos caçar os links da página
        links = soup.find_all('a', href=True)
        urls_imoveis = []
        
        for link in links:
            href = link['href']
            # Filtro para pegar apenas links que parecem ser de páginas de leilões específicos
            if '/imovel/' in href or '/leilao/' in href or 'lote' in href:
                # Se o link for relativo (ex: /imovel/123), colocamos o domínio na frente
                url_completa = f"https://www.leilaoimovel.com.br{href}" if href.startswith('/') else href
                urls_imoveis.append(url_completa)
                
        # Remove links duplicados
        urls_imoveis = list(set(urls_imoveis))
        
        if not urls_imoveis:
            print("Nenhum link de imóvel encontrado na página do Leilão Imóvel.")
            return pd.DataFrame()
            
        dados = []
        # Limitamos a 5 imóveis para o teste ser rápido, igual fizemos no Zuk
        for url_imovel in urls_imoveis[:5]:
            try:
                res_imovel = scraper.get(url_imovel, timeout=15)
                soup_imovel = BeautifulSoup(res_imovel.text, 'html.parser')
                
                # Pegamos todo o texto da página para a nossa IA (Gemini) analisar depois
                texto_pagina = soup_imovel.get_text(separator=' ', strip=True)
                
                # O ID do lote geralmente é o final da URL
                codigo = url_imovel.split('/')[-1] 
                
                dados.append({
                    "lote": codigo, 
                    "tipo": "Imóvel", # A IA vai corrigir isso depois
                    "estado": estado, 
                    "cidade": cidade,
                    "url": url_imovel, 
                    "valor_2_praca": "Consultar edital", 
                    "data_encerramento": "Extração IA", 
                    "descricao": texto_pagina # O texto bruto vai para a IA mastigar
                })
                time.sleep(1) # Pausa amigável para não derrubar o site
            except Exception as e:
                continue
                
        return pd.DataFrame(dados)
        
    except Exception as e:
        print(f"Erro na varredura do Leilão Imóvel: {e}")
        return pd.DataFrame()