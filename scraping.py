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

    asset_section = soup.find('section', class_='AssetInfo_assetInfo__77NiQ')
    if asset_section:
        general_section = asset_section.find('section', class_='AssetInfo_general__23J9N')
        if general_section:
            h2_nome = general_section.find('h2')
            if h2_nome:
                dados['ativo_nome'] = get_text_safe(h2_nome)
            
            close_li = general_section.find('li', class_='AssetInfo_close__AcrYC')
            if close_li:
                preco_ul = close_li.find('ul')
                dados['ativo_preco'] = get_text_safe(preco_ul) if preco_ul else 'N/A'
                
                variacao_p = close_li.find('p')
                dados['ativo_variacao'] = get_text_safe(variacao_p) if variacao_p else 'N/A'
        
        info_container = asset_section.find('li', class_='AssetInfo_infoContainer__qPl8D')
        if info_container:
            dados['ativo_maxima'] = find_by_h3_text(info_container, 'Máxima', 'span')
            dados['ativo_minima'] = find_by_h3_text(info_container, 'Mínima', 'span')
            dados['ativo_volume'] = find_by_h3_text(info_container, 'Volume', 'span')
            dados['ativo_ultimo_negocio'] = find_by_h3_text(info_container, 'Último Negócio', 'span')
            dados['ativo_abertura'] = find_by_h3_text(info_container, 'Abertura', 'span')
            dados['ativo_volume_financeiro'] = find_by_h3_text(info_container, 'Volume Financeiro', 'span')

        trends_section = asset_section.find('section', class_='AssetInfo_trends__HTuuh')
        if trends_section:
            trends_li = trends_section.find_all('li')
            if len(trends_li) >= 2:
                dados['tendencia_curto_prazo'] = get_text_safe(trends_li[0], 'span')
                dados['tendencia_longo_prazo'] = get_text_safe(trends_li[1], 'span')

        indicators_section = asset_section.find('section', class_='AssetInfo_indicators__Rv0FY')
        if indicators_section:
            dados['desvio_padrao_1a'] = find_by_h3_text(indicators_section, 'Desvio Padrão', 'span')
            dados['iv_1a'] = find_by_h3_text(indicators_section, 'IV', 'span')
            dados['ewma_1a'] = find_by_h3_text(indicators_section, 'EWMA', 'span')
            dados['beta'] = find_by_h3_text(indicators_section, 'Beta', 'span')

    option_section = soup.find('section', class_='Option_optionInfo__89gWK')
    if option_section:
        info_ul = option_section.find('ul', class_='Option_info__vq2sN')
        if info_ul:
            tipo_h2 = info_ul.find('h2', class_='Option_direction__hBbLo')
            dados['opcao_tipo'] = get_text_safe(tipo_h2) if tipo_h2 else 'N/A'
            
            dados['opcao_codigo'] = find_by_h3_text(info_ul, 'Código', 'h2')
            
            vencimento_raw = find_by_h3_text(info_ul, 'Vencimento', 'h2')
            vencimento_match = re.search(r'(\d{2}/\d{2}/\d{2})', vencimento_raw)
            dados['opcao_vencimento'] = vencimento_match.group(1) if vencimento_match else vencimento_raw
            
            dias_match = re.search(r'(\d+)\s*dias', vencimento_raw)
            dados['opcao_dias_vencimento'] = dias_match.group(1) if dias_match else 'N/A'
            
            dados['opcao_strike'] = find_by_h3_text(info_ul, 'Strike', 'h2')
            
            dados['opcao_moneyness'] = find_by_h3_text(info_ul, 'Moneyness', 'h2')

        price_ul = option_section.find('ul', class_='Option_price__sXqxm')
        if price_ul:
            dados['opcao_ultimo_negociado'] = find_by_h3_text(price_ul, 'Último Negociado', 'h2')
            dados['opcao_teorico_bs'] = find_by_h3_text(price_ul, 'Teórico calculado', 'h2')
            
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

        vol_ul = option_section.find('ul', class_='Option_vol__cjher')
        if vol_ul:
            dados['volatilidade_implicita_ultimo'] = find_by_h3_text(vol_ul, 'Implícita (último)', 'h2')
            dados['volatilidade_implicita_ask'] = find_by_h3_text(vol_ul, 'Implícita Ask', 'h2')
            dados['volatilidade_implicita_bid'] = find_by_h3_text(vol_ul, 'Implícita Bid', 'h2')

        greeks_ul = option_section.find('ul', class_='Option_greeks__gOWys')
        if greeks_ul:
            dados['delta'] = find_by_h3_text(greeks_ul, 'Delta', 'h2')
            dados['theta'] = find_by_h3_text(greeks_ul, 'Theta', 'h2')
            dados['gamma'] = find_by_h3_text(greeks_ul, 'Gamma', 'h2')
            dados['vega'] = find_by_h3_text(greeks_ul, 'Vega', 'h2')
            dados['rho'] = find_by_h3_text(greeks_ul, 'Rho', 'h2')

        covered_ul = option_section.find('ul', class_='Option_covered__L9OuZ')
        if covered_ul:
            dados['prob_exercicio'] = find_by_h3_text(covered_ul, 'Probabilidade de Exercício', 'h2')
            dados['custo'] = find_by_h3_text(covered_ul, 'Custo', 'h2')
            dados['protecao'] = find_by_h3_text(covered_ul, 'Proteção', 'h2')
            dados['taxa'] = find_by_h3_text(covered_ul, 'Taxa', 'h2')

    return dados

def salvar_em_json(dados, nome_arquivo='dados_opcoes.json'):
    dados_existentes = {}
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            dados_existentes = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados_existentes = {}
    
    chave_opcao = f"{dados['ticker_base']}_{dados['ticker_opcao']}"
    
    dados_existentes[chave_opcao] = dados
    
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

def extrair_lista_ativos_mercado(html_content=None):
    """
    Extrai a lista completa de ativos da página de mercado com IV Rank e IV Percentil.
    Se html_content for fornecido, usa-o. Caso contrário, busca da URL.
    Retorna uma lista de dicionários de ativos.
    """
    soup = None
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        print("Analisando conteúdo HTML fornecido.")
    else:
        url = "https://opcoes.oplab.com.br/mercado"
        print(f"Buscando dados de {url}...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a página de mercado: {e}")
            return None

    if not soup:
        print("Falha ao carregar o conteúdo HTML.")
        return None

    ativos = []
    asset_cards = soup.find_all('a', class_='AssetCard_assetCard__iGiPy')
    
    print(f"Total de cards de ativos encontrados: {len(asset_cards)}")
    
    for card in asset_cards:
        try:
            ativo = {}
            
            ativo['ticker'] = get_text_safe(card.find('p', class_='AssetCard_symbol__0AOFx'))
            ativo['descricao'] = get_text_safe(card.find('p', class_='AssetCard_description__bvu_R'))
            ativo['preco'] = get_text_safe(card.find('p', class_='AssetCard_close__K127U'))
            
            description_p = card.find('p', class_='AssetCard_description__bvu_R')
            ativo['variacao'] = 'N/A'
            if description_p:
                variation_p = description_p.find_next_sibling('p')
                if variation_p:
                    ativo['variacao'] = get_text_safe(variation_p)

            ativo['volatilidade_implicita'] = 'N/A'
            ativo['iv_rank'] = 'N/A'
            ativo['iv_percentil'] = 'N/A'

            labels_div = card.find(lambda tag: tag.name == 'div' and 'Vol. Implícita' in tag.get_text())
            if labels_div:
                valores_div = labels_div.find_next_sibling('div')
                if valores_div:
                    valores_ps = valores_div.find_all('p')
                    if len(valores_ps) == 3:
                        vi_text = get_text_safe(valores_ps[0])
                        iv_rank_text = get_text_safe(valores_ps[1])
                        iv_percentil_text = get_text_safe(valores_ps[2])
                        
                        ativo['volatilidade_implicita'] = vi_text.replace('%', '').strip() if vi_text != '-' else 'N/A'
                        ativo['iv_rank'] = iv_rank_text.replace('%', '').strip() if iv_rank_text != '-' else 'N/A'
                        ativo['iv_percentil'] = iv_percentil_text.replace('%', '').strip() if iv_percentil_text != '-' else 'N/A'

            href = card.get('href', '')
            ativo['link'] = f"https://opcoes.oplab.com.br{href}" if href else 'N/A'
            
            ativos.append(ativo)
            
        except Exception as e:
            print(f"Erro ao processar um card de ativo: {e}")
            continue
            
    print(f"\nTotal de ativos extraídos com sucesso: {len(ativos)}")
    
    com_vi = len([a for a in ativos if a.get('volatilidade_implicita', 'N/A') != 'N/A'])
    com_rank = len([a for a in ativos if a.get('iv_rank', 'N/A') != 'N/A'])
    com_percentil = len([a for a in ativos if a.get('iv_percentil', 'N/A') != 'N/A'])
    
    print(f"Ativos com Volatilidade Implícita válida: {com_vi}")
    print(f"Ativos com IV Rank válido: {com_rank}")
    print(f"Ativos com IV Percentil válido: {com_percentil}")
    
    return ativos

def converter_para_float(valor_str):
    """Converte string para float, tratando vírgulas e valores inválidos."""
    if valor_str == 'N/A' or valor_str == '-':
        return -1.0 
    try:
        valor_limpo = valor_str.replace(',', '.').strip()
        return float(valor_limpo)
    except (ValueError, AttributeError):
        return -1.0

def ordenar_ativos_por_iv(ativos, campo='volatilidade_implicita'):
    ativos_ordenados = sorted(
        ativos,
        key=lambda x: converter_para_float(x.get(campo, 'N/A')),
        reverse=True
    )
    
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
    print("=== SCRAPER DE OPÇÕES OPLAB ===\n")
    
    ticker_base = "UNIP6"
    ticker_opcao = "UNIPA730"
    dados = extrair_dados_opcao(ticker_base, ticker_opcao)
    if dados:
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        salvar_em_json(dados)
    
    lista_opcoes = [
        ('UNIP6', 'UNIPA730'),
        ('PETR4', 'PETRA100'),
        ('VALE3', 'VALEC200'),
    ]
    processar_multiplos_tickers(lista_opcoes)
    
    
    print("\n=== EXTRAINDO LISTA DE ATIVOS DO MERCADO ===\n")
    
    html_content = None
    try:
        with open('exemplo2.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print("Arquivo 'exemplo2.html' lido com sucesso para análise.")
    except FileNotFoundError:
        print("Arquivo 'exemplo2.html' não encontrado. A função tentará buscar os dados da web.")

    ativos = extrair_lista_ativos_mercado()
    
    if ativos:
        salvar_lista_ativos_json(ativos, campo_ordenacao='volatilidade_implicita', nome_arquivo='ativos_por_vi.json')
        
        salvar_lista_ativos_json(ativos, campo_ordenacao='iv_rank', nome_arquivo='ativos_por_iv_rank.json')
        
        salvar_lista_ativos_json(ativos, campo_ordenacao='iv_percentil', nome_arquivo='ativos_por_iv_percentil.json')
        
        print("\n=== TOP 10 ATIVOS POR IV PERCENTIL (AMOSTRA) ===")
        ativos_por_percentil = ordenar_ativos_por_iv(ativos, 'iv_percentil')
        for i, ativo in enumerate(ativos_por_percentil[:10], 1):
            print(f"{i}. {ativo['ticker']:<7} - VI: {ativo.get('volatilidade_implicita', 'N/A'):>7} | "
                  f"IV Rank: {ativo.get('iv_rank', 'N/A'):>7} | IV Percentil: {ativo.get('iv_percentil', 'N/A'):>7}")