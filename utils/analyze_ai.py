from google import genai 
import json

def analyze_ai(descricao, api_key):
    if not api_key:
        return {"status": "ERRO", "tipo_imovel": "Desconhecido", "resumo": "API Key não informada.", "favoraveis": [], "criticos": []}
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Você é um advogado especialista em leilões imobiliários. 
        Analise o texto do edital e retorne EXATAMENTE um objeto JSON válido com esta estrutura, sem formatação markdown ou crases:
        {{
            "tipo_imovel": "Descubra o tipo exato (ex: Apartamento, Casa, Terreno, Galpão, Comercial)",
            "status": "VERDE",
            "resumo": "Veredito direto em uma frase curta.",
            "favoraveis": ["ponto bom 1", "ponto bom 2"],
            "criticos": ["ponto de risco 1", "ponto de risco 2"]
        }}
        Use "VERDE" (propriedade plena, desocupado), "AMARELO" (atenção com dívidas ou ocupado), ou "VERMELHO" (cilada, direitos fiduciários).
        TEXTO DO EDITAL:
        {descricao[:5000]}
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto_limpo = response.text.strip().replace('```json', '').replace('```', '')
        
        resultado = json.loads(texto_limpo)
        
        if not isinstance(resultado, dict):
            raise ValueError("A IA não retornou um dicionário válido.")
            
        return resultado
    except Exception as e:
        return {"status": "ERRO", "tipo_imovel": "Erro", "resumo": f"Falha na IA: {e}", "favoraveis": [], "criticos": []}
    