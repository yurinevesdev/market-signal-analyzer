import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

def get_text_safe(element, selector=None, strip=True):
    """Extrai texto de forma segura de um elemento BeautifulSoup."""
    if element is None:
        return 'N/A'
    if selector:
        try:
            found = element.select_one(selector)
            return found.get_text(strip=strip) if found else 'N/A'
        except (AttributeError, TypeError):
            return 'N/A'
    return element.get_text(strip=strip)

def find_by_h3_text(element, h3_text, tag='span'):
    """Encontra elemento específico (span ou h2) que é irmão de um h3 com texto específico."""
    try:
        h3_elem = element.find(lambda t: t.name == 'h3' and h3_text in t.get_text())
        if h3_elem:
            if tag == 'span':
                sibling = h3_elem.find_previous_sibling('span')
            else:
                sibling = h3_elem.find_previous_sibling('h2')
            return sibling.get_text(strip=True) if sibling else 'N/A'
    except (AttributeError, TypeError):
        pass
    return 'N/A'

def extrair_dados_opcao(ticker_base, ticker_opcao):
    """
    Extrai todas as informações de uma opção do site opcoes.oplab.com.br.
    """
    url = f"https://opcoes.oplab.com.br/mercado/opcoes/{ticker_base}/{ticker_opcao}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    dados = {
        'url': url,
        'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ticker_base': ticker_base,
        'ticker_opcao': ticker_opcao
    }

    # --- ATIVO BASE ---
    asset_section = soup.find('section', class_='AssetInfo_assetInfo__77NiQ')
    if asset_section:
        # Preço do ativo
        general_section = asset_section.find('section', class_='AssetInfo_general__23J9N')
        if general_section:
            # Nome do ativo
            h2_nome = general_section.find('h2')
            if h2_nome:
                dados['ativo_nome'] = get_text_safe(h2_nome)
            
            # Preço e variação
            close_li = general_section.find('li', class_='AssetInfo_close__AcrYC')
            if close_li:
                preco_ul = close_li.find('ul')
                dados['ativo_preco'] = get_text_safe(preco_ul) if preco_ul else 'N/A'
                
                variacao_p = close_li.find('p')
                dados['ativo_variacao'] = get_text_safe(variacao_p) if variacao_p else 'N/A'
        
        # Informações do ativo
        info_container = asset_section.find('li', class_='AssetInfo_infoContainer__qPl8D')
        if info_container:
            dados['ativo_maxima'] = find_by_h3_text(info_container, 'Máxima', 'span')
            dados['ativo_minima'] = find_by_h3_text(info_container, 'Mínima', 'span')
            dados['ativo_volume'] = find_by_h3_text(info_container, 'Volume', 'span')
            dados['ativo_ultimo_negocio'] = find_by_h3_text(info_container, 'Último Negócio', 'span')
            dados['ativo_abertura'] = find_by_h3_text(info_container, 'Abertura', 'span')
            dados['ativo_volume_financeiro'] = find_by_h3_text(info_container, 'Volume Financeiro', 'span')

        # Tendências
        trends_section = asset_section.find('section', class_='AssetInfo_trends__HTuuh')
        if trends_section:
            trends_li = trends_section.find_all('li')
            if len(trends_li) >= 2:
                dados['tendencia_curto_prazo'] = get_text_safe(trends_li[0], 'span')
                dados['tendencia_longo_prazo'] = get_text_safe(trends_li[1], 'span')

        # Indicadores
        indicators_section = asset_section.find('section', class_='AssetInfo_indicators__Rv0FY')
        if indicators_section:
            dados['desvio_padrao_1a'] = find_by_h3_text(indicators_section, 'Desvio Padrão', 'span')
            dados['iv_1a'] = find_by_h3_text(indicators_section, 'IV', 'span')
            dados['ewma_1a'] = find_by_h3_text(indicators_section, 'EWMA', 'span')
            dados['beta'] = find_by_h3_text(indicators_section, 'Beta', 'span')

    # --- OPÇÃO ---
    option_section = soup.find('section', class_='Option_optionInfo__89gWK')
    if option_section:
        # Informações básicas da opção
        info_ul = option_section.find('ul', class_='Option_info__vq2sN')
        if info_ul:
            # Tipo (CALL ou PUT)
            tipo_h2 = info_ul.find('h2', class_='Option_direction__hBbLo')
            dados['opcao_tipo'] = get_text_safe(tipo_h2) if tipo_h2 else 'N/A'
            
            # Código
            dados['opcao_codigo'] = find_by_h3_text(info_ul, 'Código', 'h2')
            
            # Vencimento
            vencimento_raw = find_by_h3_text(info_ul, 'Vencimento', 'h2')
            vencimento_match = re.search(r'(\d{2}/\d{2}/\d{2})', vencimento_raw)
            dados['opcao_vencimento'] = vencimento_match.group(1) if vencimento_match else vencimento_raw
            
            # Dias até vencimento
            dias_match = re.search(r'(\d+)\s*dias', vencimento_raw)
            dados['opcao_dias_vencimento'] = dias_match.group(1) if dias_match else 'N/A'
            
            # Strike
            dados['opcao_strike'] = find_by_h3_text(info_ul, 'Strike', 'h2')
            
            # Moneyness
            dados['opcao_moneyness'] = find_by_h3_text(info_ul, 'Moneyness', 'h2')

        # Preços da opção
        price_ul = option_section.find('ul', class_='Option_price__sXqxm')
        if price_ul:
            dados['opcao_ultimo_negociado'] = find_by_h3_text(price_ul, 'Último Negociado', 'h2')
            dados['opcao_teorico_bs'] = find_by_h3_text(price_ul, 'Teórico calculado', 'h2')
            
            # Variação
            variacao_li = price_ul.find(lambda t: t.name == 'h3' and 'Variação' in t.get_text())
            if variacao_li:
                variacao_p = variacao_li.find_previous_sibling('p')
                dados['opcao_variacao'] = get_text_safe(variacao_p) if variacao_p else 'N/A'
            
            dados['opcao_bid'] = find_by_h3_text(price_ul, 'Bid', 'h2')
            dados['opcao_ask'] = find_by_h3_text(price_ul, 'Ask', 'h2')
            dados['opcao_mid'] = find_by_h3_text(price_ul, 'Mid', 'h2')
            dados['opcao_volume_financeiro'] = find_by_h3_text(price_ul, 'Volume Financeiro', 'h2')
            dados['opcao_vi'] = find_by_h3_text(price_ul, 'VI', 'h2')
            dados['opcao_ve'] = find_by_h3_text(price_ul, 'VE', 'h2')

        # Volatilidade
        vol_ul = option_section.find('ul', class_='Option_vol__cjher')
        if vol_ul:
            dados['volatilidade_implicita_ultimo'] = find_by_h3_text(vol_ul, 'Implícita (último)', 'h2')
            dados['volatilidade_implicita_ask'] = find_by_h3_text(vol_ul, 'Implícita Ask', 'h2')
            dados['volatilidade_implicita_bid'] = find_by_h3_text(vol_ul, 'Implícita Bid', 'h2')

        # Gregas
        greeks_ul = option_section.find('ul', class_='Option_greeks__gOWys')
        if greeks_ul:
            dados['delta'] = find_by_h3_text(greeks_ul, 'Delta', 'h2')
            dados['theta'] = find_by_h3_text(greeks_ul, 'Theta', 'h2')
            dados['gamma'] = find_by_h3_text(greeks_ul, 'Gamma', 'h2')
            dados['vega'] = find_by_h3_text(greeks_ul, 'Vega', 'h2')
            dados['rho'] = find_by_h3_text(greeks_ul, 'Rho', 'h2')

        # Lançamento Coberto
        covered_ul = option_section.find('ul', class_='Option_covered__L9OuZ')
        if covered_ul:
            dados['prob_exercicio'] = find_by_h3_text(covered_ul, 'Probabilidade de Exercício', 'h2')
            dados['custo'] = find_by_h3_text(covered_ul, 'Custo', 'h2')
            dados['protecao'] = find_by_h3_text(covered_ul, 'Proteção', 'h2')
            dados['taxa'] = find_by_h3_text(covered_ul, 'Taxa', 'h2')

    return dados

def salvar_em_json(dados, nome_arquivo='dados_opcoes.json'):
    """
    Salva os dados extraídos em um arquivo JSON.
    Se o arquivo já existe, atualiza os dados da opção específica.
    """
    # Tenta carregar dados existentes
    dados_existentes = {}
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            dados_existentes = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Arquivo não existe ou está vazio/corrompido
        dados_existentes = {}
    
    # Cria uma chave única para cada opção
    chave_opcao = f"{dados['ticker_base']}_{dados['ticker_opcao']}"
    
    # Atualiza ou adiciona os dados da opção
    dados_existentes[chave_opcao] = dados
    
    # Salva o arquivo JSON atualizado
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados_existentes, f, indent=2, ensure_ascii=False)
    
    print(f"Dados salvos/atualizados em {nome_arquivo}")

def processar_multiplos_tickers(lista_opcoes, nome_arquivo='dados_opcoes.json'):
    """
    Processa múltiplos tickers de opções.
    
    lista_opcoes: Lista de tuplas (ticker_base, ticker_opcao)
    Exemplo: [('UNIP6', 'UNIPA730'), ('PETR4', 'PETRA100')]
    """
    total = len(lista_opcoes)
    sucesso = 0
    falhas = 0
    
    for i, (ticker_base, ticker_opcao) in enumerate(lista_opcoes, 1):
        print(f"\nProcessando {i}/{total}: {ticker_base}/{ticker_opcao}")
        
        dados = extrair_dados_opcao(ticker_base, ticker_opcao)
        
        if dados:
            salvar_em_json(dados, nome_arquivo)
            print(f"✓ Sucesso!")
            sucesso += 1
        else:
            print(f"✗ Falha ao extrair dados")
            falhas += 1
    
    print(f"\n{'='*50}")
    print(f"Processamento concluído!")
    print(f"Sucessos: {sucesso} | Falhas: {falhas}")
    print(f"Arquivo salvo: {nome_arquivo}")

def extrair_lista_ativos_mercado():
    """
    Extrai a lista completa de ativos da página de mercado com IV Rank e IV Percentil.
    Retorna uma lista ordenada por IV (Volatilidade Implícita).
    """
    url = "https://opcoes.oplab.com.br/mercado"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página de mercado: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    ativos = []

    # Encontra todos os cards de ativos
    asset_cards = soup.find_all('a', class_='AssetCard_assetCard__iGiPy')
    
    print(f"Total de cards encontrados: {len(asset_cards)}")
    
    for idx, card in enumerate(asset_cards, 1):
        try:
            ativo = {}
            
            # Símbolo do ativo
            symbol = card.find('p', class_='AssetCard_symbol__0AOFx')
            ativo['ticker'] = get_text_safe(symbol) if symbol else 'N/A'
            
            # Descrição
            description = card.find('p', class_='AssetCard_description__bvu_R')
            ativo['descricao'] = get_text_safe(description) if description else 'N/A'
            
            # Preço
            price = card.find('p', class_='AssetCard_close__K127U')
            ativo['preco'] = get_text_safe(price) if price else 'N/A'
            
            # Variação
            variation_p = card.find('p', style=lambda x: x and 'color:' in str(x).lower())
            if variation_p:
                ativo['variacao'] = get_text_safe(variation_p)
            else:
                ativo['variacao'] = 'N/A'
            
            # Busca TODOS os <p> dentro do card
            all_p_tags = card.find_all('p')
            
            # Procura especificamente pelos 3 últimos <p> que contêm os valores numéricos
            # Eles aparecem após os cabeçalhos "Vol. Implícita", "IV. Rank", "IV. Percentil"
            valores_encontrados = []
            
            for p in all_p_tags:
                texto = get_text_safe(p)
                # Ignora textos vazios e os cabeçalhos
                if texto and texto not in ['Vol. Implícita', 'IV. Rank', 'IV. Percentil', 'N/A']:
                    # Verifica se tem estilo com font-weight: bold e números/percentuais
                    style = p.get('style', '')
                    if 'font-weight: bold' in style or 'font-weight:bold' in style:
                        # Pode ser um valor numérico
                        if any(char.isdigit() for char in texto) or texto == '-':
                            valores_encontrados.append(texto)
            
            # Os últimos 3 valores devem ser VI, IV Rank e IV Percentil
            if len(valores_encontrados) >= 3:
                # Pega os últimos 3 valores
                vi_text = valores_encontrados[-3]
                iv_rank_text = valores_encontrados[-2]
                iv_percentil_text = valores_encontrados[-1]
                
                # Limpa os valores
                ativo['volatilidade_implicita'] = vi_text if vi_text != '-' else 'N/A'
                ativo['iv_rank'] = iv_rank_text if iv_rank_text != '-' else 'N/A'
                ativo['iv_percentil'] = iv_percentil_text if iv_percentil_text != '-' else 'N/A'
            else:
                ativo['volatilidade_implicita'] = 'N/A'
                ativo['iv_rank'] = 'N/A'
                ativo['iv_percentil'] = 'N/A'
            
            # Link do ativo
            href = card.get('href', '')
            ativo['link'] = f"https://opcoes.oplab.com.br{href}" if href else 'N/A'
            
            ativos.append(ativo)
            
            # Debug: mostra os primeiros 10
            if idx <= 10:
                print(f"\nAtivo {idx}: {ativo['ticker']}")
                print(f"  VI: {ativo['volatilidade_implicita']}")
                print(f"  IV Rank: {ativo['iv_rank']}")
                print(f"  IV Percentil: {ativo['iv_percentil']}")
                if idx == 1:
                    print(f"  DEBUG - Total de <p> encontrados: {len(all_p_tags)}")
                    print(f"  DEBUG - Valores encontrados: {valores_encontrados}")
            
        except Exception as e:
            print(f"Erro ao processar card {idx}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\nTotal de ativos extraídos: {len(ativos)}")
    
    # Conta quantos têm valores válidos
    com_vi = len([a for a in ativos if a['volatilidade_implicita'] != 'N/A'])
    com_rank = len([a for a in ativos if a['iv_rank'] != 'N/A'])
    com_percentil = len([a for a in ativos if a['iv_percentil'] != 'N/A'])
    
    print(f"Ativos com VI válida: {com_vi}")
    print(f"Ativos com IV Rank válido: {com_rank}")
    print(f"Ativos com IV Percentil válido: {com_percentil}")
    
    return ativos

def converter_para_float(valor_str):
    """Converte string para float, tratando vírgulas e valores inválidos."""
    if valor_str == 'N/A' or valor_str == '-':
        return -1.0  # Valor para ordenação (coloca no final)
    try:
        # Remove espaços e substitui vírgula por ponto
        valor_limpo = valor_str.replace(',', '.').strip()
        return float(valor_limpo)
    except (ValueError, AttributeError):
        return -1.0

def ordenar_ativos_por_iv(ativos, campo='volatilidade_implicita'):
    """
    Ordena a lista de ativos por um campo específico (VI, IV Rank ou IV Percentil).
    
    campos disponíveis:
    - 'volatilidade_implicita'
    - 'iv_rank'
    - 'iv_percentil'
    """
    # Ordena do maior para o menor
    ativos_ordenados = sorted(
        ativos,
        key=lambda x: converter_para_float(x.get(campo, 'N/A')),
        reverse=True
    )
    
    # Remove ativos com valores N/A do resultado final
    ativos_validos = [a for a in ativos_ordenados if converter_para_float(a.get(campo, 'N/A')) > 0]
    
    return ativos_validos

def salvar_lista_ativos_json(ativos, campo_ordenacao='volatilidade_implicita', nome_arquivo='ativos_mercado.json'):
    """Salva a lista de ativos ordenada em JSON."""
    ativos_ordenados = ordenar_ativos_por_iv(ativos, campo_ordenacao)
    
    dados = {
        'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_ativos': len(ativos_ordenados),
        'campo_ordenacao': campo_ordenacao,
        'ativos': ativos_ordenados
    }
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    
    print(f"Lista de {len(ativos_ordenados)} ativos salva em {nome_arquivo}")
    print(f"Ordenado por: {campo_ordenacao}")
    
    return ativos_ordenados

if __name__ == '__main__':
    # Exemplo de uso: processa uma única opção
    print("=== SCRAPER DE OPÇÕES OPLAB ===\n")
    
    # Opção 1: Processar um único ticker
    ticker_base = "UNIP6"
    ticker_opcao = "UNIPA730"
    
    dados = extrair_dados_opcao(ticker_base, ticker_opcao)
    if dados:
        # Exibe no console
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        
        # Salva em arquivo JSON (atualiza se já existir)
        salvar_em_json(dados)
    
    
    lista_opcoes = [
        ('UNIP6', 'UNIPA730'),
        ('PETR4', 'PETRA100'),
        ('VALE3', 'VALEC200'),
    ]
    processar_multiplos_tickers(lista_opcoes)
    
    
    # Opção 3: Extrair lista completa de ativos do mercado ordenada por IV
    # Descomente as linhas abaixo para usar
    
    print("\n=== EXTRAINDO LISTA DE ATIVOS DO MERCADO ===\n")
    ativos = extrair_lista_ativos_mercado()
    
    if ativos:
        # Você pode ordenar por diferentes campos:
        # - 'volatilidade_implicita' (padrão)
        # - 'iv_rank'
        # - 'iv_percentil'
        
        # Ordena por Volatilidade Implícita
        salvar_lista_ativos_json(ativos, campo_ordenacao='volatilidade_implicita', nome_arquivo='ativos_por_vi.json')
        
        # Ordena por IV Rank
        salvar_lista_ativos_json(ativos, campo_ordenacao='iv_rank', nome_arquivo='ativos_por_iv_rank.json')
        
        # Ordena por IV Percentil
        salvar_lista_ativos_json(ativos, campo_ordenacao='iv_percentil', nome_arquivo='ativos_por_iv_percentil.json')
        
        # Exibe os top 10 por Volatilidade Implícita
        print("\n=== TOP 10 ATIVOS POR VOLATILIDADE IMPLÍCITA ===")
        ativos_por_vi = ordenar_ativos_por_iv(ativos, 'volatilidade_implicita')
        for i, ativo in enumerate(ativos_por_vi[:10], 1):
            print(f"{i}. {ativo['ticker']} - VI: {ativo['volatilidade_implicita']}% | "
                  f"IV Rank: {ativo['iv_rank']} | IV Percentil: {ativo['iv_percentil']}")
    