import json
import time
from groq import Groq

def analisar_oportunidade_ia(api_key, descricao, valor, cidade, tipo_imovel):
    """
    Analisa o edital usando Llama 3.1 8B.
    Inclui compressão de texto (limitando a 3500 caracteres) para não estourar a cota de Tokens!
    """
    
    max_tentativas = 3
    
    # A MÁGICA DA ENGENHARIA DE DADOS: A Dieta de Tokens
    # Cortamos a descrição para os primeiros 3500 caracteres. Salva 80% do seu limite diário!
    descricao_segura = str(descricao)[:3500] if descricao else "Sem descrição."
    
    for tentativa in range(max_tentativas):
        try:
            client = Groq(api_key=api_key)
            
            prompt = f"""Você é um Analista Sênior de Investimentos em Leilões Imobiliários no Brasil.
            Sua tarefa é analisar os dados extraídos de um anúncio/edital de leilão e fornecer um parecer focado em lucro e riscos.

            DADOS DO IMÓVEL:
            - Cidade: {cidade}
            - Tipo: {tipo_imovel}
            - Valor Atual (R$): {valor}
            - Descrição/Edital: {descricao_segura}

            INSTRUÇÕES DE ANÁLISE:
            1. Modalidade: Identifique se é Judicial (envolve processos) ou Extrajudicial (Bancos).
            2. Ocupação: Procure indícios se está "Ocupado" ou "Desocupado". Se não achar, ponha "Não informado".
            3. Risco Oculto: Identifique dívidas de IPTU, condomínio ou pendências averbadas.
            4. Nota de Oportunidade (0 a 10): Baseada no tipo de leilão e na clareza das informações.

            RETORNO OBRIGATÓRIO EM JSON:
            {{
                "modalidade": "Judicial ou Extrajudicial",
                "ocupacao": "Ocupado, Desocupado ou Não informado",
                "alertas_risco": "Resumo de 1 linha de possíveis dívidas",
                "nota": 8.5,
                "parecer_estrategico": "Frase de até 20 palavras."
            }}"""
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você responde APENAS em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                # Mudamos para a versão 8B: Limites muito maiores e processamento relâmpago
                model="llama-3.1-8b-instant", 
                temperature=0.1, 
                response_format={"type": "json_object"} 
            )
            
            texto_resposta = chat_completion.choices[0].message.content
            return json.loads(texto_resposta)
            
        except Exception as e:
            erro_str = str(e)
            if ("429" in erro_str or "503" in erro_str) and tentativa < max_tentativas - 1:
                tempo_espera = 5 * (tentativa + 1) 
                print(f"⚠️ Groq ocupada (Tentativa {tentativa + 1}/{max_tentativas}). Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue 
            else:
                print(f"❌ Erro definitivo na IA: {erro_str}")
                return {
                    "modalidade": "Erro na Análise",
                    "ocupacao": "Desconhecido",
                    "alertas_risco": "Limite de tokens ou falha de conexão.",
                    "nota": 0.0,
                    "parecer_estrategico": "Verifique o edital manualmente."
                }