import yfinance as yf
import pandas as pd
import ta
import numpy as np
from scipy import stats
from alertas import enviar_alerta_consolidado, enviar_relatorio_final
import time
import json

SCORE_MINIMO_OPERACAO = 70  
CONFIANCA_MINIMA = 0.75     
ADX_THRESHOLD_TENDENCIA = 25  
IV_HV_RATIO_CARO = 1.2       
IV_HV_RATIO_BARATO = 0.8     

def carregar_dados_volatilidade():
    """Carrega dados consolidados do scraper."""
    with open('dados_mercado_consolidado.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
        print(f"✅ Dados OpLab carregados: {len(dados)} tickers")
        return dados

def converter_para_float(valor):
    """Converte strings para float com tratamento robusto."""
    if valor in ['N/A', '-', None, '']:
        return None
    try:
        return float(str(valor).replace(',', '.').replace('%', '').replace('R$', '').strip())
    except:
        return None

def identificar_regime_mercado(df):
    cp = df['Close'].squeeze()
    hp = df['High'].squeeze()
    lp = df['Low'].squeeze()
    
    adx_obj = ta.trend.ADXIndicator(hp, lp, cp, 14)
    adx = adx_obj.adx().iloc[-1]
    adx_plus = adx_obj.adx_pos().iloc[-1]
    adx_minus = adx_obj.adx_neg().iloc[-1]
    
    m9 = ta.trend.EMAIndicator(cp, 9).ema_indicator().iloc[-1]
    m21 = ta.trend.EMAIndicator(cp, 21).ema_indicator().iloc[-1]
    m50 = ta.trend.EMAIndicator(cp, 50).ema_indicator().iloc[-1]
    m200 = ta.trend.EMAIndicator(cp, 200).ema_indicator().iloc[-1]
    
    preco = cp.iloc[-1]
    
    rsi = ta.momentum.RSIIndicator(cp, 14).rsi().iloc[-1]
    sma20 = cp.rolling(20).mean().iloc[-1]
    std20 = cp.rolling(20).std().iloc[-1]
    z_score = (preco - sma20) / std20 if std20 > 0 else 0
    
    if adx >= ADX_THRESHOLD_TENDENCIA:
        regime = 'TENDENCIA'
        
        if preco > m21 > m50 and adx_plus > adx_minus:
            direcao = 'ALTA'
            alinhamento = preco > m9 > m21 > m50 > m200
        elif preco < m21 < m50 and adx_minus > adx_plus:
            direcao = 'BAIXA'
            alinhamento = preco < m9 < m21 < m50 < m200
        else:
            direcao = 'INDEFINIDA'
            alinhamento = False
    else:
        regime = 'LATERAL'
        direcao = 'NEUTRO'
        alinhamento = False
    
    dados_regime = {
        'regime': regime,
        'adx': adx,
        'adx_plus': adx_plus,
        'adx_minus': adx_minus,
        'direcao': direcao,
        'alinhamento_perfeito': alinhamento,
        'rsi': rsi,
        'z_score': z_score,
        'preco': preco,
        'm9': m9,
        'm21': m21,
        'm50': m50,
        'm200': m200
    }
    
    return regime, adx, dados_regime

def calcular_volatilidade_relativa(df, vol_info):
    cp = df['Close'].squeeze()
    
    vi = converter_para_float(vol_info.get('volatilidade_implicita'))
    ivr = converter_para_float(vol_info.get('iv_rank'))
    ivp = converter_para_float(vol_info.get('iv_percentil'))
    
    if vi is None:
        return 'NEUTRO', None, {'erro': 'VI indisponível'}
    
    returns = cp.pct_change().dropna()
    hv_30d = returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100 
    
    iv_hv_ratio = vi / hv_30d if hv_30d > 0 else None
    
    if iv_hv_ratio is None:
        edge_type = 'NEUTRO'
        score_vol = 50
    elif iv_hv_ratio >= IV_HV_RATIO_CARO:
        edge_type = 'VENDA_PREMIUM'
        score_vol = min(100, 60 + (iv_hv_ratio - IV_HV_RATIO_CARO) * 100)
    elif iv_hv_ratio <= IV_HV_RATIO_BARATO:
        edge_type = 'COMPRA_PREMIUM'
        score_vol = min(100, 60 + (IV_HV_RATIO_BARATO - iv_hv_ratio) * 100)
    else:
        edge_type = 'NEUTRO'
        score_vol = 50
    
    if ivr is not None and ivp is not None:
        divergencia = abs(ivr - ivp)
        convergencia_score = max(0, 100 - divergencia * 2) 
    else:
        convergencia_score = 50
    
    dados_vol = {
        'vi': vi,
        'hv_30d': hv_30d,
        'iv_hv_ratio': iv_hv_ratio,
        'ivr': ivr,
        'ivp': ivp,
        'divergencia_ivr_ivp': abs(ivr - ivp) if ivr and ivp else None,
        'edge_type': edge_type,
        'score_vol': score_vol,
        'convergencia_score': convergencia_score
    }
    
    return edge_type, iv_hv_ratio, dados_vol

def calcular_probabilidade_lucro(df, vol_info, dados_regime, dados_vol, dias_ate_vencimento=30):
    preco = dados_regime['preco']
    vi = dados_vol.get('vi')
    
    if vi is None or vi == 0:
        return {}
    
    vi_decimal = vi / 100
    desvio_esperado = preco * vi_decimal * np.sqrt(dias_ate_vencimento / 365)
    
    estruturas = {}
    
    strike_put = preco - desvio_esperado

    pop_put = stats.norm.cdf(0) + (1 - stats.norm.cdf(1)) * 100  
    
    estruturas['VENDA_PUT_COBERTA'] = {
        'strike_sugerido': round(strike_put, 2),
        'delta_aproximado': -0.30,
        'pop': round(pop_put, 1),
        'max_loss': 'Limitado ao strike',
        'max_gain': 'Prêmio recebido'
    }
    
    strike_call = preco + desvio_esperado
    pop_call = stats.norm.cdf(0) + (1 - stats.norm.cdf(1)) * 100 
    
    estruturas['VENDA_CALL_COBERTA'] = {
        'strike_sugerido': round(strike_call, 2),
        'delta_aproximado': 0.30,
        'pop': round(pop_call, 1),
        'max_loss': 'Potencialmente ilimitado (se não tiver ação)',
        'max_gain': 'Prêmio recebido'
    }
    
    strike_compra_bull = preco
    strike_venda_bull = preco + (1.5 * desvio_esperado)
    pop_bull = stats.norm.cdf(0.5) * 100 
    
    estruturas['BULL_CALL_SPREAD'] = {
        'strike_compra': round(strike_compra_bull, 2),
        'strike_venda': round(strike_venda_bull, 2),
        'pop': round(pop_bull, 1),
        'max_loss': 'Débito pago',
        'max_gain': 'Diferença entre strikes - débito'
    }
    
    strike_compra_bear = preco
    strike_venda_bear = preco - (1.5 * desvio_esperado)
    pop_bear = stats.norm.cdf(0.5) * 100 
    
    estruturas['BEAR_PUT_SPREAD'] = {
        'strike_compra': round(strike_compra_bear, 2),
        'strike_venda': round(strike_venda_bear, 2),
        'pop': round(pop_bear, 1),
        'max_loss': 'Débito pago',
        'max_gain': 'Diferença entre strikes - débito'
    }
    
    pop_ic = (stats.norm.cdf(1) - stats.norm.cdf(-1)) * 100  # ~68%
    
    estruturas['IRON_CONDOR'] = {
        'put_venda': round(preco - desvio_esperado, 2),
        'put_compra': round(preco - 1.5 * desvio_esperado, 2),
        'call_venda': round(preco + desvio_esperado, 2),
        'call_compra': round(preco + 1.5 * desvio_esperado, 2),
        'pop': round(pop_ic, 1),
        'max_loss': 'Largura da perna - crédito',
        'max_gain': 'Crédito recebido'
    }
    
    return estruturas

def determinar_estrategia_otima(dados_regime, dados_vol, probabilidades):
    """
    Lógica de decisão baseada em REGIME + VOLATILIDADE + POP.
    """
    regime = dados_regime['regime']
    direcao = dados_regime['direcao']
    adx = dados_regime['adx']
    rsi = dados_regime['rsi']
    z_score = dados_regime['z_score']
    alinhamento = dados_regime['alinhamento_perfeito']
    
    edge_type = dados_vol['edge_type']
    iv_hv_ratio = dados_vol.get('iv_hv_ratio')
    score_vol = dados_vol['score_vol']
    
    estrategia = None
    score_final = 0
    confianca = 0.5
    justificativas = []
    
    if regime == 'TENDENCIA':
        justificativas.append(f"📈 REGIME: Tendência ({adx:.1f}) - Ignorando RSI/Z-Score")
        
        if direcao == 'ALTA':
            justificativas.append(f"🚀 Tendência de ALTA confirmada (ADX+ > ADX-)")
            
            if edge_type == 'COMPRA_PREMIUM':
                estrategia = 'BULL_CALL_SPREAD'
                score_final = 85
                confianca = 0.85
                justificativas.append(f"💎 IV/HV={iv_hv_ratio:.2f} - Prêmios BARATOS (ideal para compra)")
                
                if alinhamento:
                    score_final += 10
                    confianca += 0.08
                    justificativas.append("🔥 ALINHAMENTO PERFEITO de médias móveis")
            
            elif edge_type == 'VENDA_PREMIUM':
                estrategia = 'VENDA_PUT_COBERTA'
                score_final = 80
                confianca = 0.82
                justificativas.append(f"💰 IV/HV={iv_hv_ratio:.2f} - Prêmios CAROS (venda com proteção da alta)")
            
            else:  
                estrategia = 'BULL_CALL_SPREAD'
                score_final = 70
                confianca = 0.72
                justificativas.append("⚖️ IV neutra - Spread para limitar custo")
        
        elif direcao == 'BAIXA':
            justificativas.append(f"📉 Tendência de BAIXA confirmada (ADX- > ADX+)")
            
            if edge_type == 'COMPRA_PREMIUM':
                estrategia = 'BEAR_PUT_SPREAD'
                score_final = 85
                confianca = 0.85
                justificativas.append(f"💎 IV/HV={iv_hv_ratio:.2f} - Prêmios BARATOS (ideal para compra)")
                
                if alinhamento:
                    score_final += 10
                    confianca += 0.08
                    justificativas.append("🔥 ALINHAMENTO PERFEITO de médias móveis")
            
            elif edge_type == 'VENDA_PREMIUM':
                estrategia = 'VENDA_CALL_COBERTA'
                score_final = 80
                confianca = 0.82
                justificativas.append(f"💰 IV/HV={iv_hv_ratio:.2f} - Prêmios CAROS (venda com proteção da baixa)")
            
            else:  
                estrategia = 'BEAR_PUT_SPREAD'
                score_final = 70
                confianca = 0.72
                justificativas.append("⚖️ IV neutra - Spread para limitar custo")
        
        else:  
            justificativas.append("⚠️ Tendência sem direção clara - AGUARDAR")
            estrategia = 'AGUARDAR'
            score_final = 40
            confianca = 0.40

    else:  
        justificativas.append(f"⏸️ REGIME: Lateral (ADX={adx:.1f}) - Usando RSI/Z-Score")
        
        sobrevenda = rsi < 30 or z_score < -2.0
        sobrecompra = rsi > 70 or z_score > 2.0
        
        if sobrevenda and edge_type == 'VENDA_PREMIUM':
            estrategia = 'VENDA_PUT_COBERTA'
            score_final = 90
            confianca = 0.88
            justificativas.append(f"🎯 SETUP CLÁSSICO: Sobrevenda (RSI={rsi:.1f}, Z={z_score:.2f}) + IV alta")
            justificativas.append("💰 Venda de PUT para capturar reversão à média")
        
        elif sobrecompra and edge_type == 'VENDA_PREMIUM':
            estrategia = 'VENDA_CALL_COBERTA'
            score_final = 90
            confianca = 0.88
            justificativas.append(f"🎯 SETUP CLÁSSICO: Sobrecompra (RSI={rsi:.1f}, Z={z_score:.2f}) + IV alta")
            justificativas.append("💰 Venda de CALL para capturar reversão à média")
        
        elif edge_type == 'VENDA_PREMIUM':
            estrategia = 'IRON_CONDOR'
            score_final = 75
            confianca = 0.78
            justificativas.append(f"⏳ Mercado lateral + IV alta (IV/HV={iv_hv_ratio:.2f})")
            justificativas.append("💰 Iron Condor para lucrar com decaimento (Theta)")
        
        else:
            estrategia = 'AGUARDAR'
            score_final = 50
            confianca = 0.50
            justificativas.append("⚠️ Mercado lateral sem vantagem de volatilidade clara")
    
    score_final = (score_final * 0.6) + (score_vol * 0.4)
    
    return estrategia, score_final, confianca, justificativas

def analisar_ativo_completo(ticker_sa, vol_data):
    print(f"\n{'='*80}")
    print(f"📊 Análise Profissional: {ticker_sa}")
    print('-'*80)
    
    df = yf.download(ticker_sa, period="1y", interval="1d", auto_adjust=False, progress=False)
    if df.empty or len(df) < 200:
        print(f"❌ Dados insuficientes para {ticker_sa}")
        print('='*80)
        return None
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    
    ticker_limpo = ticker_sa.replace('.SA', '')
    vol_info = vol_data.get(ticker_limpo, {})
    
    regime, adx, dados_regime = identificar_regime_mercado(df)
    
    print(f"\n🎯 REGIME DE MERCADO: {regime}")
    print(f"   ADX: {adx:.1f}")
    print(f"   Direção: {dados_regime['direcao']}")
    print(f"   Preço: R$ {dados_regime['preco']:.2f}")
    if regime == 'TENDENCIA':
        print(f"   Alinhamento de MMs: {'✅ PERFEITO' if dados_regime['alinhamento_perfeito'] else '⚠️ PARCIAL'}")
    else:
        print(f"   RSI: {dados_regime['rsi']:.1f}")
        print(f"   Z-Score: {dados_regime['z_score']:.2f}")
    
    edge_type, iv_hv_ratio, dados_vol = calcular_volatilidade_relativa(df, vol_info)
    
    print(f"\n💹 VOLATILIDADE RELATIVA:")
    print(f"   VI: {dados_vol.get('vi', 'N/A'):.1f}%")
    print(f"   HV (30d): {dados_vol.get('hv_30d', 'N/A'):.1f}%")
    if iv_hv_ratio:
        print(f"   IV/HV Ratio: {iv_hv_ratio:.2f} → {edge_type}")
    print(f"   IV Rank: {dados_vol.get('ivr', 'N/A'):.1f}%")
    print(f"   IV Percentil: {dados_vol.get('ivp', 'N/A'):.1f}%")
    if dados_vol.get('divergencia_ivr_ivp'):
        print(f"   Divergência IVR/IVP: {dados_vol['divergencia_ivr_ivp']:.1f}%")
    print(f"   Score Volatilidade: {dados_vol['score_vol']:.1f}/100")
    
    probabilidades = calcular_probabilidade_lucro(df, vol_info, dados_regime, dados_vol)
    
    estrategia, score_final, confianca, justificativas = determinar_estrategia_otima(
        dados_regime, dados_vol, probabilidades
    )
    
    print(f"\n🎯 DECISÃO:")
    print(f"   Estratégia: {estrategia}")
    print(f"   Score Final: {score_final:.1f}/100")
    print(f"   Confiança: {confianca:.1%}")
    
    print(f"\n💡 JUSTIFICATIVAS:")
    for j in justificativas:
        print(f"   {j}")
    
    if estrategia in probabilidades:
        print(f"\n📊 SETUP DE OPÇÕES ({estrategia}):")
        setup = probabilidades[estrategia]
        for key, value in setup.items():
            if key != 'max_loss' and key != 'max_gain':
                print(f"   {key.replace('_', ' ').title()}: {value}")
        print(f"   Risco Máximo: {setup.get('max_loss', 'N/A')}")
        print(f"   Ganho Máximo: {setup.get('max_gain', 'N/A')}")
    
    if score_final >= SCORE_MINIMO_OPERACAO and confianca >= CONFIANCA_MINIMA and estrategia != 'AGUARDAR':
        print(f"\n✅ OPERAÇÃO RECOMENDADA")
        print('='*80)
        
        resultado = {
            'ticker': ticker_sa,
            'preco': round(dados_regime['preco'], 2),
            'regime': regime,
            'estrategia': estrategia,
            'score_final': round(score_final, 1),
            'confianca': round(confianca, 3),
            'edge_type': edge_type,
            'iv_hv_ratio': round(iv_hv_ratio, 2) if iv_hv_ratio else None,
            'adx': round(adx, 1),
            'rsi': round(dados_regime['rsi'], 1),
            'justificativas': justificativas,
            'setup_opcoes': probabilidades.get(estrategia, {}),
            'iv_rank': dados_vol.get('ivr'),
            'iv_percentil': dados_vol.get('ivp'),
            'direcao_iv': edge_type,
            'direcao_tecnica': dados_regime['direcao']
        }
        
        return resultado
    else:
        motivos_rejeicao = []
        
        if estrategia == 'AGUARDAR':
            motivos_rejeicao.append("Estratégia: AGUARDAR (sem setup claro)")
        
        if score_final < SCORE_MINIMO_OPERACAO:
            motivos_rejeicao.append(f"Score baixo ({score_final:.1f}/{SCORE_MINIMO_OPERACAO})")
        
        if confianca < CONFIANCA_MINIMA:
            motivos_rejeicao.append(f"Confiança baixa ({confianca:.1%}/{CONFIANCA_MINIMA:.1%})")
        
        if dados_regime['direcao'] == 'INDEFINIDA':
            motivos_rejeicao.append("Tendência sem direção clara")
        
        if edge_type == 'NEUTRO' and regime == 'LATERAL':
            motivos_rejeicao.append("Mercado lateral sem vantagem de volatilidade")
        
        motivo_principal = " | ".join(motivos_rejeicao) if motivos_rejeicao else "Critérios não atingidos"
        
        print(f"\n⏸️ AGUARDAR - {motivo_principal}")
        print('='*80)
        
        return None

def analisar_multiplos_ativos(lista_ativos):
    """
    Processa lista completa de ativos com o novo sistema.
    
    Retorna:
        aprovados: list - Ativos que passaram nos critérios
        rejeitados: list - Ativos que não passaram (com motivos)
    """
    print(f"\n{'='*80}")
    print(f"🚀 SISTEMA PROFISSIONAL DE ANÁLISE DE OPÇÕES")
    print(f"{'='*80}")
    print(f"Ativos: {len(lista_ativos)}")
    print(f"Score mínimo: {SCORE_MINIMO_OPERACAO}/100")
    print(f"Confiança mínima: {CONFIANCA_MINIMA:.1%}")
    print(f"{'='*80}\n")
    
    vol_data = carregar_dados_volatilidade()
    
    aprovados = []
    rejeitados = []
    
    for idx, ticker in enumerate(lista_ativos, 1):
        print(f"\n[{idx}/{len(lista_ativos)}]")
        try:
            res = analisar_ativo_completo(ticker, vol_data)
            
            if res:
                aprovados.append(res)
            else:
                rejeitados.append({
                    'ticker': ticker,
                    'motivo': 'Não atingiu critérios mínimos de score/confiança'
                })
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro em {ticker}: {e}")
            rejeitados.append({
                'ticker': ticker,
                'motivo': f'Erro na análise: {str(e)}'
            })
    
    print(f"\n{'='*80}")
    print("📊 RESUMO FINAL")
    print(f"{'='*80}")
    print(f"Ativos analisados: {len(lista_ativos)}")
    print(f"✅ Aprovados: {len(aprovados)}")
    print(f"❌ Rejeitados: {len(rejeitados)}")
    
    if aprovados:
        estrategias = {}
        for r in aprovados:
            est = r['estrategia']
            if est not in estrategias:
                estrategias[est] = []
            estrategias[est].append(r)
        
        print(f"\n📈 Aprovados por Estratégia:")
        for est, ops in estrategias.items():
            print(f"   {est}: {len(ops)} operações")
        
        resultados_ordenados = sorted(aprovados, key=lambda x: (x['confianca'], x['score_final']), reverse=True)
        
        print(f"\n🏆 TOP 5 OPORTUNIDADES:")
        print(f"{'='*80}")
        for i, r in enumerate(resultados_ordenados[:5], 1):
            print(f"\n{i}. {r['ticker']} - R$ {r['preco']:.2f}")
            print(f"   Regime: {r['regime']} (ADX={r['adx']:.1f})")
            print(f"   Estratégia: {r['estrategia']}")
            print(f"   Score: {r['score_final']:.1f}/100 | Confiança: {r['confianca']:.1%}")
            print(f"   Edge: {r['edge_type']}")
            if r['iv_hv_ratio']:
                print(f"   IV/HV: {r['iv_hv_ratio']:.2f}")
            
            if r.get('setup_opcoes'):
                setup = r['setup_opcoes']
                if 'pop' in setup:
                    print(f"   POP: {setup['pop']:.1f}%")
        
        print(f"\n{'='*80}\n")
    
    if rejeitados:
        print(f"\n⚠️ PRINCIPAIS MOTIVOS DE REJEIÇÃO:")
        motivos_count = {}
        for r in rejeitados:
            motivo = r.get('motivo', 'Não especificado')
            motivos_count[motivo] = motivos_count.get(motivo, 0) + 1
        
        for motivo, count in sorted(motivos_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   [{count}x] {motivo}")
        print()
    
    return aprovados, rejeitados

def analise_rapida(ticker, vol_data=None):
    """Análise rápida de um único ativo."""
    if vol_data is None:
        vol_data = carregar_dados_volatilidade()
    
    ticker_sa = ticker if '.SA' in ticker else f"{ticker}.SA"
    return analisar_ativo_completo(ticker_sa, vol_data)

if __name__ == '__main__':
    print("="*80)
    print("🎯 SISTEMA PROFISSIONAL DE ANÁLISE DE OPÇÕES")
    print("="*80)
    print("\nMelhorias implementadas:")
    print("1. ✅ Regimes de Mercado (ADX como filtro mestre)")
    print("2. ✅ Volatilidade Relativa (IV/HV ratio)")
    print("3. ✅ Probabilidade de Lucro (POP com strikes sugeridos)")
    print("\nEste script deve ser importado e usado via main.py")
    print("="*80)