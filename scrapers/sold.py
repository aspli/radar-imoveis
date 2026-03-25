import requests
import pandas as pd
import urllib.parse

def buscar_leiloes_sold_api(place_id, cidade, estado):
    """
    Mini-robô especialista na API da Superbid/Sold.
    Versão Híbrida: Ignora o GPS e busca pelo nome da cidade em texto, 
    incluindo todas as modalidades de leilão.
    """
    # Converte "Araçatuba" para o formato web (Ara%C3%A7atuba) para não quebrar a URL
    cidade_url = urllib.parse.quote(cidade)
    
    # A URL definitiva com as modalidades e a busca por texto (queryString)
    url_api = (
        f"https://offer-query.superbid.net/offers/?portalId=[2,15]&requestOrigin=store&locale=pt_BR"
        f"&timeZoneId=America%2FSao_Paulo&searchType=opened"
        f"&filter=product.productType.description:imoveis;stores.id:[1161,1741];isShopping:false;auction.modalityId:[1,4,5,7]"
        f"&pageNumber=1&pageSize=50&orderBy=endDate:asc;price:desc"
        f"&queryString={cidade_url}" # BUSCA CEGA POR TEXTO! Pega tudo que tiver a cidade escrita.
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
        lista_ofertas = dados_json.get('items', [])
        
        if not lista_ofertas:
            return pd.DataFrame()
            
        dados = []
        for oferta in lista_ofertas:
            codigo = oferta.get('id', 'N/A')
            produto = oferta.get('product', {})
            descricao = produto.get('shortDesc', 'Descrição não fornecida.')
            valor = oferta.get('price', 0)
            data_fim = oferta.get('endDate', 'Consultar site')
            link_imovel = oferta.get('linkURL', f"https://www.sold.com.br/lote/{codigo}")
            if link_imovel.startswith('/'):
                link_imovel = f"https://www.sold.com.br{link_imovel}"
            
            dados.append({
                "lote": str(codigo), 
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