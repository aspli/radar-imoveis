import requests
import pandas as pd

def buscar_leiloes_sold_api(place_id, cidade, estado):
    """
    Mini-robô especialista na API da Superbid/Sold.
    Versão calibrada: Filtros abertos (pega terrenos/comerciais) e Headers de segurança.
    """
    # URL Limpa: Tiramos o 'imoveis-residenciais' e 'modalityId' para pegar TUDO da cidade
    url_api = (
        f"https://offer-query.superbid.net/offers/?portalId=[2,15]&requestOrigin=store&locale=pt_BR"
        f"&timeZoneId=America%2FSao_Paulo&searchType=opened"
        f"&filter=product.productType.description:imoveis;isShopping:false"
        f"&pageNumber=1&pageSize=50&orderBy=endDate:asc;price:desc"
        f"&placeId={place_id}&radius=100" 
        f"&fieldList=id;linkURL;price;endDate;product.shortDesc"
    )
    
    # Headers completos: Essenciais para o servidor achar que somos o Google Chrome original
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.sold.com.br',
        'Referer': 'https://www.sold.com.br/'
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Erro na API da Sold. Código: {response.status_code}")
            return pd.DataFrame()
            
        dados_json = response.json()
        lista_ofertas = dados_json.get('items', [])
        
        if not lista_ofertas:
            # Se ainda vier vazio, pelo menos a gente não quebra o código
            return pd.DataFrame()
            
        dados = []
        for oferta in lista_ofertas[:5]: # Pegamos até 5 para o teste
            codigo = oferta.get('id', 'N/A')
            
            # Pega a descrição dentro do bloco 'product'
            produto = oferta.get('product', {})
            descricao = produto.get('shortDesc', 'Descrição não fornecida na API.')
            
            valor = oferta.get('price', 0)
            data_fim = oferta.get('endDate', 'Consultar site')
            
            # Garante que a URL do imóvel fique clicável
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