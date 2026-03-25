import requests
import pandas as pd

def buscar_leiloes_sold_api(place_id, cidade, estado):
    """
    Mini-robô da Sold.
    Versão de Produção: Chave de dicionário corrigida para 'offers'.
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
        
        # A MÁGICA FINAL: Mudamos de 'items' para 'offers'!!!
        lista_ofertas = dados_json.get('offers', [])
        
        if not lista_ofertas:
            return pd.DataFrame()
            
        dados = []
        for oferta in lista_ofertas:
            codigo = oferta.get('id', 'N/A')
            produto = oferta.get('product', {})
            descricao = produto.get('shortDesc', 'Descrição não fornecida.')
            valor = oferta.get('price', 0)
            data_fim = oferta.get('endDate', 'Consultar site')
            
            # Formata a URL pública do lote
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