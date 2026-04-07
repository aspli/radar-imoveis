import requests
import pandas as pd
import unicodedata
import re

# ==========================================
# FUNÇÃO PARA CRIAR A URL PERFEITA
# ==========================================
def criar_slug_url(texto):
    """
    Transforma 'Casa 400m² no Santana' em 'casa-400m-no-santana'
    para podermos montar o link idêntico ao site da Sold.
    """
    if not texto:
        return "imovel"
    # Tira acentos
    texto = unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('utf-8').lower()
    # Troca espaços e caracteres especiais por traço (-)
    texto = re.sub(r'[^a-z0-9]+', '-', texto)
    # Remove traços sobrando nas pontas
    return texto.strip('-')

# ==========================================
# MINI-ROBÔ DA SOLD (API DIRETA)
# ==========================================
def buscar_leiloes_sold_api(place_id, cidade, estado):
    """
    Acessa a API oculta da Superbid/Sold e remonta os links
    no formato novo: /oferta/slug-do-imovel-ID
    """
    url_api = (
        f"https://offer-query.superbid.net/offers/?portalId=[2,15]&requestOrigin=store&locale=pt_BR"
        f"&searchType=opened"
        f"&filter=product.productType.description:imoveis;isShopping:false"
        f"&pageNumber=1&pageSize=50&orderBy=price:desc"
        f"&placeId={place_id}" 
        f"&fieldList=id;linkURL;price;endDate;product.shortDesc"
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.sold.com.br',
        'Referer': 'https://www.sold.com.br/'
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return pd.DataFrame()
            
        dados_json = response.json()
        
        # Lendo a gaveta correta onde os imóveis estão escondidos
        lista_ofertas = dados_json.get('offers', [])
        
        if not lista_ofertas:
            return pd.DataFrame()
            
        dados = []
        for oferta in lista_ofertas:
            # Pegando o ID do lote
            codigo = str(oferta.get('id', ''))
            
            # Pegando a descrição para formar o link
            produto = oferta.get('product', {})
            descricao = produto.get('shortDesc', 'imovel')
            
            valor = oferta.get('price', 0)
            data_fim = oferta.get('endDate', 'Consultar site')
            
            # A MÁGICA DA URL:
            # O Python limpa a descrição e junta com o código do imóvel
            # A MÁGICA DA URL (AGORA NA NAVE-MÃE):
            # Trocamos sold.com.br por superbid.net para englobar todos os parceiros
            slug_imovel = criar_slug_url(descricao)
            link_imovel = f"https://www.superbid.net/oferta/{slug_imovel}-{codigo}"
            
            dados.append({
                "lote": codigo, 
                "tipo": "Imóvel", 
                "estado": estado, 
                "cidade": cidade,
                "url": link_imovel, 
                "valor_2_praca": float(valor) if valor else 0.0, 
                "data_encerramento": data_fim, 
                "descricao": descricao
            })
            
        return pd.DataFrame(dados)
        
    except Exception as e:
        print(f"Falha de conexão com a API Sold: {e}")
        return pd.DataFrame()