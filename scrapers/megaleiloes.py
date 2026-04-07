import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata
import re

def formatar_slug(texto):
    """Remove acentos e espaços para montar a URL."""
    texto_limpo = ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto_limpo.strip().lower().replace(' ', '-')

def buscar_mega_leiloes(estado, cidade):
    """
    Mini-robô do Mega Leilões com Simulação Humana e Raio-X.
    """
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    estado_lower = estado.lower()
    cidade_slug = formatar_slug(cidade)
    
    url_busca = (
        f"https://www.megaleiloes.com.br/{estado_lower}/{cidade_slug}"
        f"?tov=igbr&tipo%5B0%5D=1&tipo%5B1%5D=2&tipo%5B2%5D=3&pagina=1"
    )
    
    try:
        # TRUQUE DE ENGENHARIA: Acessa a home primeiro para gerar Cookies de sessão
        scraper.get("https://www.megaleiloes.com.br/", timeout=15)
        time.sleep(1) # Respira igual humano
        
        # Agora sim, faz a busca
        response = scraper.get(url_busca, timeout=30)
        
        if response.status_code != 200:
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        urls_imoveis = []
        
        for link in links:
            # Corta fora o "?" (UTMs) e o "#" (âncoras) para limpar o link
            href_limpo = link['href'].split('?')[0].split('#')[0]
            
            # FILTRO RELAXADO: Se tiver a cidade e terminar com -j ou -x seguido de números, é imóvel!
            if cidade_slug in href_limpo.lower() and re.search(r'-[jx]\d+', href_limpo, re.IGNORECASE):
                url_completa = href_limpo if href_limpo.startswith('http') else f"https://www.megaleiloes.com.br{href_limpo}"
                urls_imoveis.append(url_completa)
                
        # Remove duplicados
        urls_imoveis = list(set(urls_imoveis))
        
        # ==========================================
        # O RAIO-X: Se der errado, ele fofoca no terminal!
        # ==========================================
        if not urls_imoveis:
            print("\n" + "="*50)
            print("🚨 DIAGNÓSTICO MEGA LEILÕES (Olhe aqui!)")
            print(f"Status da resposta: {response.status_code}")
            print(f"Tamanho do HTML baixado: {len(response.text)} caracteres")
            tem_casa = "Copacabana" in response.text or "copacabana" in response.text
            print(f"A casa 'Copacabana' está invisível no HTML? {'NÃO (Ela está lá!)' if tem_casa else 'SIM (O HTML veio vazio/bloqueado)'}")
            print("="*50 + "\n")
            return pd.DataFrame()
            
        dados = []
        for url_imovel in urls_imoveis[:5]: 
            try:
                res_imovel = scraper.get(url_imovel, timeout=20)
                soup_imovel = BeautifulSoup(res_imovel.text, 'html.parser')
                texto_pagina = soup_imovel.get_text(separator=' ', strip=True)
                
                match = re.search(r'-([jx]\d+)', url_imovel, re.IGNORECASE)
                codigo = match.group(1).upper() if match else "N/A"
                
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
                time.sleep(1.5) 
                
            except Exception:
                continue
                
        return pd.DataFrame(dados)
        
    except Exception as e:
        print(f"Erro no Mega Leilões: {e}")
        return pd.DataFrame()