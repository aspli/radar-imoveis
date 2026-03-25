import unicodedata
import urllib.parse

# ==========================================
# 1. FUNÇÕES DE TRATAMENTO DE TEXTO
# ==========================================
def remover_acentos(texto):
    """Remove acentos (São Paulo -> Sao Paulo)"""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')

def formatar_slug(texto):
    """Padrão de URL limpa (São José do Rio Preto -> sao-jose-do-rio-preto)"""
    return remover_acentos(texto).lower().strip().replace(' ', '-')

def formatar_frazao(texto):
    """Padrão Frazão: Mantém acentos, Iniciais Maiúsculas, espaços viram %20"""
    # O urllib.parse.quote converte caracteres especiais e espaços para o padrão web (%20, %C3, etc)
    return urllib.parse.quote(texto.title())


# ==========================================
# 2. BANCO DE DADOS DE MAPEAMENTO (DE-PARA)
# ==========================================
# Como alguns sites usam códigos e não nomes, precisamos mapear as cidades do seu radar.
MAPEAMENTO_CIDADES = {
    "Araçatuba": {
        "ibge": "3502804",                      # Usado no Leilão Imóvel
        "alfa_cidade": "4737",                  # Usado no Alfa Leilões
        "sold_place_id": "ChIJAfGqendElpQRJx0Kzs-iseg", # Usado no Sold (Google Place ID)
        "zuk_regiao": "interior"                # Usado no Portal Zuk
    },
    "São Paulo": {
        "ibge": "3550308",
        "alfa_cidade": "4955", # Exemplo hipotético
        "sold_place_id": "ChIJ0WGkg4FEzpQRrlsz_hc-qKw",
        "zuk_regiao": "capital"
    }
}

MAPEAMENTO_ESTADOS = {
    "SP": {"alfa_estado": "26"} # Alfa Leilões usa '26' para SP
}


# ==========================================
# 3. O MOTOR GERADOR DE URLs EXCLUSIVAS
# ==========================================
def compor_urls_dinamicas(estado, cidade):
    urls_geradas = {}
    
    # Prepara as variáveis de texto
    estado_lower = estado.lower()
    estado_upper = estado.upper()
    cidade_slug = formatar_slug(cidade)
    cidade_frazao = formatar_frazao(cidade)
    
    # Busca os dados no nosso mapeamento (Se a cidade não estiver lá, retorna dicionário vazio)
    dados_cidade = MAPEAMENTO_CIDADES.get(cidade, {})
    dados_estado = MAPEAMENTO_ESTADOS.get(estado_upper, {})

    # 1. Mega Leilões (Padrão: /sp/aracatuba)
    urls_geradas['Mega Leilões'] = f"https://www.megaleiloes.com.br/{estado_lower}/{cidade_slug}"
    
    # 2. Leilões Judiciais (Padrão: /sp?cidade=aracatuba)
    urls_geradas['Leilões Judiciais'] = f"https://www.leiloesjudiciais.com.br/imoveis/todos-bens/{estado_lower}?cidade={cidade_slug}"
    
    # 3. Frazão Leilões (Padrão: estado=SP&cidade=Ara%C3%A7atuba)
    urls_geradas['Frazão Leilões'] = f"https://www.frazaoleiloes.com.br/sale/searchLot?estado={estado_upper}&cidade={cidade_frazao}"
    
    # 4. Portal Zuk (Exige região: /sp/interior/aracatuba)
    regiao_zuk = dados_cidade.get("zuk_regiao", "interior") # Assume interior se não souber
    urls_geradas['Portal Zuk'] = f"https://www.portalzuk.com.br/leilao-de-imoveis/c/todos-imoveis/{estado_lower}/{regiao_zuk}/{cidade_slug}"
    
    # 5. Alfa Leilões (Exige ID do Estado e ID da Cidade)
    if "alfa_estado" in dados_estado and "alfa_cidade" in dados_cidade:
        urls_geradas['Alfa Leilões'] = f"https://alfaleiloes.com/leiloes/?search=&estado={dados_estado['alfa_estado']}&cidade={dados_cidade['alfa_cidade']}"
        
    # 6. Leilão Imóvel (Exige Código IBGE)
    if "ibge" in dados_cidade:
        urls_geradas['Leilão Imóvel'] = f"https://www.leilaoimovel.com.br/encontre-seu-imovel?s=&cidade={dados_cidade['ibge']}"
        
    # 7. Sold / Superbid (Exige Google Place ID)
    if "sold_place_id" in dados_cidade:
        urls_geradas['Sold'] = f"https://www.sold.com.br/categorias/imoveis?searchType=opened&filter=product.subCategory.category.description:imoveis-residenciais;isShopping:false&placeId={dados_cidade['sold_place_id']}&pageNumber=1&pageSize=15&orderBy=price:desc"

    return urls_geradas


# ==========================================
# 4. TESTANDO O CÓDIGO
# ==========================================
print("=== GERANDO URLs PARA ARAÇATUBA ===")
urls_aracatuba = compor_urls_dinamicas("SP", "Araçatuba")
for site, link in urls_aracatuba.items():
    print(f"{site}: {link}")

print("\n=== GERANDO URLs PARA SÃO PAULO ===")
urls_sp = compor_urls_dinamicas("SP", "São Paulo")
for site, link in urls_sp.items():
    print(f"{site}: {link}")
    