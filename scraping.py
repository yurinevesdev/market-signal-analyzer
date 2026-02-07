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

def converter_para_float(valor_str):
    """Converte string para float, tratando vírgulas e valores inválidos."""
    if valor_str == 'N/A' or valor_str == '-' or valor_str is None:
        return None
    try:
        valor_limpo = str(valor_str).replace(',', '.').replace('%', '').strip()
        return float(valor_limpo)
    except (ValueError, AttributeError):
        return None

def extrair_dados_opcao(ticker_base, ticker_opcao):
    """Extrai todas as informações de uma opção do site opcoes.oplab.com.br."""
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

def extrair_lista_ativos_mercado(html_content=None):
    """Extrai a lista completa de ativos da página de mercado."""
    soup = None
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        url = "https://opcoes.oplab.com.br/mercado"
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
        return None

    ativos = []
    asset_cards = soup.find_all('a', class_='AssetCard_assetCard__iGiPy')
    
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
            
    return ativos

def analisar_ativo_tecnico(ativo):
    """Análise técnica de um ativo sob a perspectiva de um analista."""
    analise = {
        'score_volatilidade': 0,
        'classificacao_volatilidade': 'Baixa',
        'oportunidade_venda': False,
        'oportunidade_compra': False,
        'nivel_interesse': 'Baixo',
        'observacoes': []
    }
    
    vi = converter_para_float(ativo.get('volatilidade_implicita'))
    iv_rank = converter_para_float(ativo.get('iv_rank'))
    iv_percentil = converter_para_float(ativo.get('iv_percentil'))
    variacao = converter_para_float(ativo.get('variacao'))
    
    if vi is not None:
        if vi > 60:
            analise['score_volatilidade'] = 90
            analise['classificacao_volatilidade'] = 'Muito Alta'
            analise['oportunidade_venda'] = True
            analise['nivel_interesse'] = 'Muito Alto'
            analise['observacoes'].append('Volatilidade extremamente elevada - excelente para venda de opções')
        elif vi > 45:
            analise['score_volatilidade'] = 70
            analise['classificacao_volatilidade'] = 'Alta'
            analise['oportunidade_venda'] = True
            analise['nivel_interesse'] = 'Alto'
            analise['observacoes'].append('Volatilidade alta - bom momento para estratégias de venda')
        elif vi > 30:
            analise['score_volatilidade'] = 50
            analise['classificacao_volatilidade'] = 'Média'
            analise['nivel_interesse'] = 'Médio'
            analise['observacoes'].append('Volatilidade moderada - mercado equilibrado')
        elif vi > 20:
            analise['score_volatilidade'] = 30
            analise['classificacao_volatilidade'] = 'Baixa'
            analise['oportunidade_compra'] = True
            analise['nivel_interesse'] = 'Médio'
            analise['observacoes'].append('Volatilidade baixa - pode ser oportunidade para compra de opções')
        else:
            analise['score_volatilidade'] = 10
            analise['classificacao_volatilidade'] = 'Muito Baixa'
            analise['oportunidade_compra'] = True
            analise['nivel_interesse'] = 'Alto'
            analise['observacoes'].append('Volatilidade muito baixa - ótimo para compra de opções antes de movimentos')
    
    if iv_rank is not None and iv_rank > 70:
        analise['observacoes'].append(f'IV Rank em {iv_rank:.1f}% - volatilidade no topo histórico')
        analise['oportunidade_venda'] = True
    elif iv_rank is not None and iv_rank < 30:
        analise['observacoes'].append(f'IV Rank em {iv_rank:.1f}% - volatilidade abaixo da média histórica')
        analise['oportunidade_compra'] = True
    
    if iv_percentil is not None and iv_percentil > 80:
        analise['observacoes'].append('IV Percentil muito alto - possível reversão de volatilidade')
    elif iv_percentil is not None and iv_percentil < 20:
        analise['observacoes'].append('IV Percentil muito baixo - possível aumento de volatilidade')
    
    if variacao is not None:
        if abs(variacao) > 5:
            analise['observacoes'].append(f'Movimento significativo de {variacao:+.2f}% no dia')
        elif abs(variacao) > 3:
            analise['observacoes'].append(f'Movimento moderado de {variacao:+.2f}% no dia')
    
    return analise

def consolidar_dados_compativel(lista_opcoes=None):
    print("=== CONSOLIDAÇÃO DE DADOS COMPATÍVEL COM ANALISE.PY ===\n")
    
    print("1. Extraindo lista de ativos do mercado...")
    ativos = extrair_lista_ativos_mercado()
    
    if not ativos:
        print("Erro: Não foi possível extrair ativos do mercado")
        return None
    
    print(f"   ✓ {len(ativos)} ativos extraídos\n")
    
    dados_por_ticker = {}
    
    for ativo in ativos:
        ticker = ativo.get('ticker')
        if not ticker or ticker == 'N/A':
            continue
        
        analise = analisar_ativo_tecnico(ativo)
        
        dados_por_ticker[ticker] = {
            'ticker': ticker,
            'descricao': ativo.get('descricao', 'N/A'),
            'preco': ativo.get('preco', 'N/A'),
            'variacao': ativo.get('variacao', 'N/A'),
            'volatilidade_implicita': ativo.get('volatilidade_implicita', 'N/A'),
            'iv_rank': ativo.get('iv_rank', 'N/A'),
            'iv_percentil': ativo.get('iv_percentil', 'N/A'),
            'link': ativo.get('link', 'N/A'),
            'analise_tecnica': analise, 
            'opcoes_detalhadas': []
        }
    
    print(f"   ✓ {len(dados_por_ticker)} ativos processados\n")
    
    if lista_opcoes:
        print(f"2. Extraindo detalhes de {len(lista_opcoes)} opções específicas...")
        for ticker_base, ticker_opcao in lista_opcoes:
            print(f"   - Processando {ticker_base}/{ticker_opcao}...")
            dados_opcao = extrair_dados_opcao(ticker_base, ticker_opcao)
            
            if dados_opcao and ticker_base in dados_por_ticker:
                dados_por_ticker[ticker_base]['opcoes_detalhadas'].append(dados_opcao)
                print(f"     ✓ Sucesso - opção adicionada a {ticker_base}")
            elif dados_opcao:
                dados_por_ticker[ticker_base] = {
                    'ticker': ticker_base,
                    'descricao': dados_opcao.get('ativo_nome', 'N/A'),
                    'preco': dados_opcao.get('ativo_preco', 'N/A'),
                    'variacao': dados_opcao.get('ativo_variacao', 'N/A'),
                    'volatilidade_implicita': 'N/A',
                    'iv_rank': 'N/A',
                    'iv_percentil': 'N/A',
                    'link': 'N/A',
                    'opcoes_detalhadas': [dados_opcao]
                }
                print(f"     ✓ Sucesso - novo ticker criado para {ticker_base}")
            else:
                print(f"     ✗ Falha ao extrair opção")
        print()
    
    vi_values = []
    for ticker, dados in dados_por_ticker.items():
        vi = converter_para_float(dados.get('volatilidade_implicita'))
        if vi is not None:
            vi_values.append(vi)
    
    total_com_opcoes = len([t for t in dados_por_ticker.values() if t['opcoes_detalhadas']])
    
    print("=== ESTATÍSTICAS ===")
    print(f"Total de tickers: {len(dados_por_ticker)}")
    print(f"Tickers com opções detalhadas: {total_com_opcoes}")
    if vi_values:
        print(f"VI Média: {sum(vi_values)/len(vi_values):.2f}%")
        print(f"VI Máxima: {max(vi_values):.2f}%")
        print(f"VI Mínima: {min(vi_values):.2f}%")
    
    return dados_por_ticker

def salvar_formato_analise_py(dados_por_ticker, nome_arquivo='dados_mercado_consolidado.json'):
    """
    Salva os dados no formato que analise.py espera ler.
    """
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados_por_ticker, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"✅ DADOS SALVOS COM SUCESSO!")
    print(f"{'='*70}")
    print(f"Arquivo: {nome_arquivo}")
    print(f"Formato: Compatível com analise.py")
    print(f"Total de tickers: {len(dados_por_ticker)}")
    
    tickers_ordenados = sorted(
        dados_por_ticker.items(),
        key=lambda x: converter_para_float(x[1].get('volatilidade_implicita')) or 0,
        reverse=True
    )
    
    print(f"\n{'='*70}")
    print("📊 TOP 10 ATIVOS POR VOLATILIDADE IMPLÍCITA")
    print(f"{'='*70}")
    print(f"{'Ticker':<8} {'VI%':>8} {'IV Rank%':>10} {'IV Perc%':>10} {'Preço':>10}")
    print('-' * 70)
    
    for ticker, dados in tickers_ordenados[:10]:
        vi = dados.get('volatilidade_implicita', 'N/A')
        iv_rank = dados.get('iv_rank', 'N/A')
        iv_perc = dados.get('iv_percentil', 'N/A')
        preco = dados.get('preco', 'N/A')
        
        print(f"{ticker:<8} {vi:>8} {iv_rank:>10} {iv_perc:>10} {preco:>10}")
    
    print(f"\n{'='*70}")
    print("✅ Arquivo pronto para ser usado pelo analise.py!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    lista_opcoes = [
        ('UNIP6', 'UNIPA730'),
        ('PETR4', 'PETRA100'),
        ('VALE3', 'VALEC200'),
    ]
    
    dados = consolidar_dados_compativel(lista_opcoes=lista_opcoes)
    
    if dados:
        salvar_formato_analise_py(dados, 'dados_mercado_consolidado.json')
        
        print("=" * 70)
    else:
        print("Erro na consolidação dos dados")