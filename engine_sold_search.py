import requests
import pandas as pd

def buscar_leiloes_sold_api(place_id, cidade, estado):
    """
    Função de alta performance que consome a API oficial da Superbid/Sold.
    """
    # A URL exata que você encontrou, parametrizada para aceitar qualquer cidade
    url_api = (
        f"https://offer-query.superbid.net/offers/?portalId=[2,15]&requestOrigin=store&locale=pt_BR"
        f"&timeZoneId=America%2FSao_Paulo&searchType=opened"
        f"&filter=product.productType.description:imoveis;stores.id:[1161,1741];"
        f"product.subCategory.category.description:imoveis-residenciais;isShopping:false;auction.modalityId:[1,4,5,7]"
        f"&pageNumber=1&pageSize=15&radius=200&orderBy=endDate:asc;price:desc"
        f"&placeId={place_id}" # <- Injetamos o ID da cidade aqui
        f"&fieldList=id;linkURL;price;endDate;product.shortDesc" # Pedimos apenas o que importa
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Erro na API da Sold. Código: {response.status_code}")
            return pd.DataFrame()
            
        dados_json = response.json()
        
        # O Superbid retorna os resultados dentro de 'items'
        lista_ofertas = dados_json.get('items', [])
        
        if not lista_ofertas:
            return pd.DataFrame()
            
        dados = []
        for oferta in lista_ofertas:
            codigo = oferta.get('id', 'N/A')
            
            # Navega no JSON para pegar a descrição (se existir)
            produto = oferta.get('product', {})
            descricao = produto.get('shortDesc', 'Descrição não fornecida na API.')
            
            # Tratamento do Preço e Data
            valor = oferta.get('price', 0)
            data_fim = oferta.get('endDate', 'Consultar site')
            
            # A API às vezes manda a URL pronta, senão montamos na mão
            link_imovel = oferta.get('linkURL', f"https://www.sold.com.br/lote/{codigo}")
            
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