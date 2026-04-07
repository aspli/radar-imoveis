import google.generativeai as genai
import json

def analisar_oportunidade_gemini(api_key, descricao, valor, cidade, tipo_imovel):
    """
    Passa os dados rasgados pelo robô para a IA do Google Gemini.
    O Prompt exige uma resposta em JSON estrito para fácil integração com o Streamlit.
    """
    # Configura a chave da API
    genai.configure(api_key=api_key)
    
    # Usamos o modelo Gemini 1.5 Flash: Ele é extremamente rápido para ler textos 
    # longos (editais) e perfeito para tarefas de processamento em lote.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # O PROMPT MESTRE (Engenharia de Prompt Nível Sênior)
    prompt = f"""
    Você é um Analista Sênior de Investimentos em Leilões Imobiliários no Brasil.
    Sua tarefa é analisar os dados extraídos de um anúncio/edital de leilão e fornecer um parecer rápido, frio e focado em lucro e mitigação de riscos.

    DADOS DO IMÓVEL:
    - Cidade: {cidade}
    - Tipo: {tipo_imovel}
    - Valor Atual (R$): {valor}
    - Descrição/Edital: {descricao}

    INSTRUÇÕES DE ANÁLISE:
    1. Modalidade: Identifique se é Judicial (envolve Varas, processos, varas cíveis, penhora) ou Extrajudicial (Alienação fiduciária, bancos como Itaú, Bradesco, Santander).
    2. Ocupação: Procure indícios se está "Ocupado" ou "Desocupado". Se não mencionar, assuma "Não informado (Risco de Ocupação)".
    3. Risco Oculto: Identifique dívidas de IPTU, condomínio ou pendências averbadas na matrícula mencionadas no texto.
    4. Nota de Oportunidade (0 a 10): Baseada no tipo de leilão e na clareza das informações. (Leilões extrajudiciais de bancos tendem a ter nota maior por menor risco jurídico; leilões judiciais com muita dívida têm nota menor).

    RETORNO OBRIGATÓRIO (Responda APENAS com um JSON válido, sem usar formatação Markdown como ```json, apenas o texto do objeto):
    {{
        "modalidade": "Judicial ou Extrajudicial",
        "ocupacao": "Ocupado, Desocupado ou Não informado",
        "alertas_risco": "Resumo de 1 linha de possíveis dívidas ou rolos jurídicos",
        "nota": 8.5,
        "parecer_estrategico": "Frase de até 20 palavras dizendo se vale a pena analisar o edital completo ou fugir."
    }}
    """

    try:
        # Pede para a IA gerar o conteúdo
        response = model.generate_content(prompt)
        texto_limpo = response.text.strip()
        
        # Limpeza de segurança caso a IA ainda teime em mandar blocos de código Markdown
        if texto_limpo.startswith("```json"):
            texto_limpo = texto_limpo[7:]
        if texto_limpo.startswith("```"):
            texto_limpo = texto_limpo[3:]
        if texto_limpo.endswith("```"):
            texto_limpo = texto_limpo[:-3]
            
        # Converte o texto gerado pela IA em um Dicionário Python real
        analise_json = json.loads(texto_limpo.strip())
        return analise_json
        
    except Exception as e:
        # Se a IA falhar (timeout ou não gerar JSON), retorna um dicionário padrão de fallback
        print(f"Erro na IA: {e}")
        return {
            "modalidade": "Análise Indisponível",
            "ocupacao": "Desconhecido",
            "alertas_risco": "Falha ao processar com a IA.",
            "nota": 0.0,
            "parecer_estrategico": "Verifique manualmente."
        }