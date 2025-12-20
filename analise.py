import yfinance as yf
import pandas as pd
import ta
from alertas import enviar_alerta_consolidado, enviar_relatorio_final 
import time

MAX_DISTANCIA_OPCOES = 0.10

def recomendar_estrutura(score_compra, score_venda, pontos_forca_compra, pontos_forca_venda, volatilidade_perc, rsi, adx, is_squeeze):    
    """
    Determina a estrutura de opções com base na força dos sinais e no ambiente de Volatilidade.

    Melhoria: Correlaciona a estrutura com a volatilidade:
    - VI Baixa (Proxies: ADX < 25, Squeeze, RSI 40-60) -> Compra a seco, THL (Comprar barato)
    - VI Alta (Proxies: ATR alta, RSI > 70 ou < 30) -> Venda Coberta, Jade Lizard (Vender caro)
    """

    vol_alta_sinal = (volatilidade_perc > 2.5) or (rsi > 70 or rsi < 30) 
    vol_baixa_sinal = (adx < 25 and 40 < rsi < 60) or is_squeeze         

    if (score_compra >= 5 and pontos_forca_compra >= 3 and score_compra > score_venda and
        (not vol_alta_sinal and volatilidade_perc < 3.5)):
        return "Compra de CALL a seco (VI baixa/normal, sinal MUITO forte)"
            
    elif (score_venda >= 5 and pontos_forca_venda >= 3 and score_venda > score_compra and
          (not vol_alta_sinal and volatilidade_perc < 3.5)):
        return "Compra de PUT a seco (VI baixa/normal, sinal MUITO forte)"
    
    elif (score_compra >= 4 and pontos_forca_compra >= 2 and score_compra > score_venda):
        if vol_alta_sinal:
            return "Venda Coberta de PUT (VI alta, prêmio gordo) ou Trava de Alta"
        else:
            return "Venda Coberta de PUT (ativo descontado)"
            
    elif (score_venda >= 4 and pontos_forca_venda >= 2 and score_venda > score_compra):
        if vol_alta_sinal:
            return "Venda Coberta de CALL (VI alta, prêmio gordo) ou Trava de Baixa"
        else:
            return "Venda Coberta de CALL (topo identificado)"
    
    elif vol_alta_sinal and 40 < rsi < 60 and adx < 30:
        return "JADE LIZARD / IRON CONDOR (VI alta, mercado neutro para vender prêmio)"
        
    elif vol_baixa_sinal and adx < 25 and 40 < rsi < 60:
        return "THL (Trava Horizontal de Linha) / COLLAR (Mercado Lateral ou Squeeze)"
        
    else:
        return "Sem recomendação para estrutura (baixo índice de confiança)"


def analisar_ativo(ticker, score_minimo=4, alertas_por_tipo=None):
    print(f"Analisando o ativo: {ticker}...")
    dados = yf.download(ticker, period="1y", interval="1d", auto_adjust=False, progress=False) 
    
    if dados.empty:
        print(f"❌ Não foi possível obter dados para {ticker}.")
        return None

    if isinstance(dados.columns, pd.MultiIndex):
        dados.columns = dados.columns.droplevel(1)

    if len(dados) < 200:
        mme200_period = len(dados) if len(dados) > 50 else 50
    else:
        mme200_period = 200

    high_prices = dados["High"].squeeze()
    low_prices = dados["Low"].squeeze()
    close_prices = dados["Close"].squeeze()

    dados["MME9"] = ta.trend.EMAIndicator(close_prices, 9).ema_indicator()
    dados["MME21"] = ta.trend.EMAIndicator(close_prices, 21).ema_indicator()
    dados["MME50"] = ta.trend.EMAIndicator(close_prices, 50).ema_indicator()
    dados["MME200"] = ta.trend.EMAIndicator(close_prices, mme200_period).ema_indicator() 
    
    macd = ta.trend.MACD(close_prices)
    dados["MACD"] = macd.macd()
    dados["MACD_SIGNAL"] = macd.macd_signal()
    dados["MACD_HIST"] = macd.macd_diff()
    
    dados["RSI"] = ta.momentum.RSIIndicator(close_prices, 14).rsi()
    dados["ATR"] = ta.volatility.AverageTrueRange(high_prices, low_prices, close_prices, 14).average_true_range()
    
    bollinger = ta.volatility.BollingerBands(close_prices)
    dados["BB_HIGH"] = bollinger.bollinger_hband()
    dados["BB_LOW"] = bollinger.bollinger_lband()
    dados["BB_MID"] = bollinger.bollinger_mavg()
    
    dados["Volume_Media20"] = dados["Volume"].rolling(20).mean()
    dados["Volume_Media50"] = dados["Volume"].rolling(50).mean()
    dados["ATR_Media50"] = dados["ATR"].rolling(50).mean()

    dados["BB_WIDTH"] = dados["BB_HIGH"] - dados["BB_LOW"]
    dados["BB_WIDTH_Media"] = dados["BB_WIDTH"].rolling(20).mean() 

    if dados.isnull().any(axis=1).iloc[-1]:
        print(f"⚠️ Indicadores incompletos no último dia para {ticker}. Pulando análise.")
        return None

    adx = ta.trend.ADXIndicator(high=high_prices, low=low_prices, close=close_prices, window=14).adx().iloc[-1]

    ultimo = dados.iloc[-1]
    penultimo = dados.iloc[-2]
    ante_penultimo = dados.iloc[-3]

    score_compra = 0
    score_venda = 0
    detalhes_compra = []
    detalhes_venda = []
    pontos_forca_compra = 0
    pontos_forca_venda = 0
    
    is_squeeze = ultimo["BB_WIDTH"] < ultimo["BB_WIDTH_Media"] * 0.7 
    if is_squeeze:
        pontos_forca_compra += 1
        pontos_forca_venda += 1
        detalhes_compra.append("✓ Squeeze de Bollinger (VI baixa, provável explosão)")
        detalhes_venda.append("✓ Squeeze de Bollinger (VI baixa, provável explosão)")

    if mme200_period >= 200:
        tendencia_alta = (
            ultimo["MME9"] > ultimo["MME21"] > ultimo["MME50"] and
            ultimo["Close"] > ultimo["MME200"]
        )
        if tendencia_alta:
            score_compra += 1
            detalhes_compra.append("✓ Tendência de alta clara (MMs alinhadas)")
            pontos_forca_compra += 2 

        tendencia_baixa = (
            ultimo["MME9"] < ultimo["MME21"] < ultimo["MME50"] and
            ultimo["Close"] < ultimo["MME200"]
        )
        if tendencia_baixa:
            score_venda += 1
            detalhes_venda.append("✓ Tendência de baixa clara (MMs alinhadas)")
            pontos_forca_venda += 2 

    cruzamento_alta = (penultimo["MME9"] <= penultimo["MME21"] and ultimo["MME9"] > ultimo["MME21"])
    if cruzamento_alta:
        score_compra += 1
        detalhes_compra.append("✓ Cruzamento de médias (9/21) detectado")
        pontos_forca_compra += 2
    elif ultimo["MME9"] > ultimo["MME21"]:
        score_compra += 1
        detalhes_compra.append("✓ MME9 > MME21")
        
    cruzamento_baixa = (penultimo["MME9"] >= penultimo["MME21"] and ultimo["MME9"] < ultimo["MME21"])
    if cruzamento_baixa:
        score_venda += 1
        detalhes_venda.append("✓ Cruzamento de baixa (9/21) detectado")
        pontos_forca_venda += 2
    elif ultimo["MME9"] < ultimo["MME21"]:
        score_venda += 1
        detalhes_venda.append("✓ MME9 < MME21")

    macd_positivo = (ultimo["MACD"] > ultimo["MACD_SIGNAL"] and ultimo["MACD_HIST"] > penultimo["MACD_HIST"])
    if macd_positivo:
        score_compra += 1
        detalhes_compra.append("✓ MACD forte e crescente (acelerando)")
        pontos_forca_compra += 1

    macd_negativo = (ultimo["MACD"] < ultimo["MACD_SIGNAL"] and ultimo["MACD_HIST"] < penultimo["MACD_HIST"])
    if macd_negativo:
        score_venda += 1
        detalhes_venda.append("✓ MACD fraco e decrescente (acelerando)")
        pontos_forca_venda += 1

    rsi_ideal = 50 <= ultimo["RSI"] <= 70
    if rsi_ideal:
        score_compra += 1
        detalhes_compra.append(f"✓ RSI ideal ({ultimo['RSI']:.1f})")
        if 55 <= ultimo["RSI"] <= 65:
            pontos_forca_compra += 1

    rsi_fraco = ultimo["RSI"] < 45
    if rsi_fraco:
        score_venda += 1
        detalhes_venda.append(f"✓ RSI fraco ({ultimo['RSI']:.1f})")
        if ultimo["RSI"] < 35:
            pontos_forca_venda += 1
            
    if adx < 20:
        detalhes_compra.append(f"✓ ADX baixo ({adx:.1f}) - Mercado lateral")
        detalhes_venda.append(f"✓ ADX baixo ({adx:.1f}) - Mercado lateral")
        pontos_forca_compra += 1 
        pontos_forca_venda += 1

    volume_forte = ultimo["Volume"] > ultimo["Volume_Media20"] * 1.2
    if volume_forte:
        pontos_forca_compra += 1
        pontos_forca_venda += 1
        detalhes_compra.append("✓ Volume muito acima da média")
        detalhes_venda.append("✓ Volume muito acima da média")

    preco_bb = ultimo["Close"]
    dist_bb_baixa = (preco_bb - ultimo["BB_LOW"]) / (ultimo["BB_HIGH"] - ultimo["BB_LOW"])
    
    if 0.1 <= dist_bb_baixa <= 0.4:
        score_compra += 1
        detalhes_compra.append("✓ Preço em boa posição (Bollinger)")
        pontos_forca_compra += 1
    
    if 0.6 <= dist_bb_baixa <= 0.9:
        score_venda += 1
        detalhes_venda.append("✓ Preço no topo (Bollinger)")
        pontos_forca_venda += 1

    volatilidade_alta = ultimo["ATR"] > ultimo["ATR_Media50"] * 1.5
    if volatilidade_alta:
        detalhes_venda.append("✓ Volatilidade elevada (ATR alta - bom para VENDAS)")
        pontos_forca_venda += 1
    
    print(f"📊 Score Compra: {score_compra}/7 (+{pontos_forca_compra} força) | Score Venda: {score_venda}/7 (+{pontos_forca_venda} força)")

    resultado = {
        "sinal": None,
        "preco": ultimo["Close"],
        "score_compra": score_compra,
        "score_venda": score_venda,
    }

    score_total_compra = score_compra + (pontos_forca_compra * 0.3)
    score_total_venda = score_venda + (pontos_forca_venda * 0.3)

    volatilidade_perc = (ultimo["ATR"] / ultimo["Close"]) * 100 

    tipo_estrutura_original = recomendar_estrutura(
        score_compra,
        score_venda,
        pontos_forca_compra,
        pontos_forca_venda,
        volatilidade_perc, 
        ultimo["RSI"],
        adx,
        is_squeeze 
    )
    
    strike_call_sugerido = f"R$ {ultimo['BB_HIGH']:.2f} (BB Topo)"
    strike_put_sugerido = f"R$ {ultimo['BB_LOW']:.2f} (BB Suporte)"
    range_thl_sugerido = f"CALL: {ultimo['BB_HIGH']:.2f} / PUT: {ultimo['BB_LOW']:.2f} (BB Range)"
    
    tipo_estrutura = tipo_estrutura_original
    strike_recomendado = None
    operacao_viavel = True
        
    preco_atual = ultimo["Close"]
    bb_high = ultimo['BB_HIGH']
    bb_low = ultimo['BB_LOW']
    
    if ("PUT" in tipo_estrutura_original and ("Venda Coberta" in tipo_estrutura_original or "Trava de Alta" in tipo_estrutura_original or "JADE LIZARD" in tipo_estrutura_original)):
        distancia_put = abs(preco_atual - bb_low) / preco_atual
        
        if distancia_put <= MAX_DISTANCIA_OPCOES:
            strike_recomendado = strike_put_sugerido
        else:
            tipo_estrutura = f"Aguardar liquidez/preço (Suporte BB: {distancia_put*100:.1f}%)"
            operacao_viavel = False 
            print(f"⚠️ Atenção: Suporte BB ({bb_low:.2f}) muito distante. Estrutura suspensa.")

    elif ("CALL" in tipo_estrutura_original and ("Venda Coberta" in tipo_estrutura_original or "Trava de Baixa" in tipo_estrutura_original or "JADE LIZARD" in tipo_estrutura_original)):
        distancia_call = abs(bb_high - preco_atual) / preco_atual
        
        if distancia_call <= MAX_DISTANCIA_OPCOES:
            strike_recomendado = strike_call_sugerido
        else:
            tipo_estrutura = f"Aguardar liquidez/preço (Topo BB: {distancia_call*100:.1f}%)"
            operacao_viavel = False 
            print(f"⚠️ Atenção: Topo BB ({bb_high:.2f}) muito distante. Estrutura suspensa.")
            

    dados_adicionais = {
        "RSI": ultimo["RSI"],
        "ADX": adx,
        "MME21": ultimo["MME21"],
        "MME50": ultimo["MME50"],
        "Volatilidade_%": f"{volatilidade_perc:.2f}%",
        "estrutura": tipo_estrutura  
    }
    
    if strike_recomendado:
        dados_adicionais["Strike_Recomendado"] = strike_recomendado
    
    
    if (score_compra >= score_minimo and pontos_forca_compra >= 2 and score_total_compra > score_total_venda + 1):
        print(f"🟢 SINAL DE COMPRA FORTE ({score_compra}/7, força: {pontos_forca_compra}) para {ticker}")
        if detalhes_compra:
            print("   " + "\n   ".join(detalhes_compra))
        print(f"   Estrutura recomendada: {tipo_estrutura}")
        
        if strike_recomendado:
            print(f"   🎯 Strike Sugerido: {strike_recomendado}")
        
        if operacao_viavel and alertas_por_tipo is not None:
            alertas_por_tipo['Compra'].append((ticker, ultimo["Close"], dados_adicionais))
        
        resultado["sinal"] = "compra"

    elif (score_venda >= score_minimo and pontos_forca_venda >= 2 and score_total_venda > score_total_compra + 1):
        print(f"🔴 SINAL DE VENDA FORTE ({score_venda}/7, força: {pontos_forca_venda}) para {ticker}")
        if detalhes_venda:
            print("   " + "\n   ".join(detalhes_venda))
        print(f"   Estrutura recomendada: {tipo_estrutura}")
        
        if strike_recomendado:
            print(f"   🎯 Strike Sugerido: {strike_recomendado}")
            
        if operacao_viavel and alertas_por_tipo is not None:
            alertas_por_tipo['Venda'].append((ticker, ultimo["Close"], dados_adicionais))
        
        resultado["sinal"] = "venda"

    else:
        print(f"⚪ Sem sinal suficientemente forte para {ticker}")
        print(
            f"   (Compra: {score_compra}/7 +{pontos_forca_compra}, Venda: {score_venda}/7 +{pontos_forca_venda})"
        )
        print(f"   Estrutura recomendada: {tipo_estrutura}")

        if tipo_estrutura in ["THL (Trava Horizontal de Linha) / COLLAR (Mercado Lateral ou Squeeze)", 
                              "JADE LIZARD / IRON CONDOR (VI alta, mercado neutro para vender prêmio)"]:
            print(f"   🎯 Range Sugerido (COLLAR/THL/JL): {range_thl_sugerido}")
            dados_adicionais["Range_Recomendado"] = range_thl_sugerido
            
            if alertas_por_tipo is not None:
                alertas_por_tipo['Lateral/Consolidação'].append((ticker, ultimo["Close"], dados_adicionais))
        
    return resultado


def analisar_multiplos_ativos(lista_tickers, score_minimo=4):
    """
    Processa a lista de ativos e envia o relatório consolidado.
    """
    print(f"\n{'='*70}")
    print(f"🚀 Iniciando análise RIGOROSA de {len(lista_tickers)} ativos")
    print(f"📊 Score mínimo: {score_minimo}/7 + 2 pontos de força")
    print(f"🎯 Apenas sinais de ALTA PROBABILIDADE e VIÁVEIS (Liquidez 10%) serão incluídos no relatório.")
    print(f"{'='*70}\n")

    resultados = []
    erros = []
    
    alertas_por_tipo = {
        'Compra': [],
        'Venda': [],
        'Lateral/Consolidação': [],
        'Sinal Fraco/Aguardar': []
    }

    for i, ticker in enumerate(lista_tickers, 1):
        print(f"\n[{i}/{len(lista_tickers)}] 🔍 {ticker}")
        print("-" * 70)

        try:
            resultado = analisar_ativo(ticker, score_minimo, alertas_por_tipo)

            if resultado is None:
                erros.append((ticker, "Sem dados disponíveis ou incompletos"))
                resultados.append((ticker, "❌ Erro: Sem dados"))
                continue

            resultados.append((ticker, "✅ Sucesso"))

        except Exception as e:
            erro_msg = str(e)
            print(f"❌ Erro ao analisar {ticker}: {erro_msg}")
            resultados.append((ticker, f"❌ Erro: {erro_msg}"))
            erros.append((ticker, erro_msg))

        if i < len(lista_tickers):
            time.sleep(2) 

        print("=" * 70)
        
    sinais_compra_finais = alertas_por_tipo['Compra']
    sinais_venda_finais = alertas_por_tipo['Venda']
    sinais_laterais_finais = alertas_por_tipo['Lateral/Consolidação']


    print(f"\n{'='*70}")
    print("📋 RESUMO DA ANÁLISE")
    print(f"{'='*70}")
    for ticker, status in resultados:
        print(f"{ticker}: {status}")
    print(f"{'='*70}\n")

    print("📊 ESTATÍSTICAS DO RELATÓRIO ENVIADO:")
    print(f"   Total analisado: {len(lista_tickers)}")
    print(f"   🟢 Sinais FORTES de compra (Viáveis): {len(sinais_compra_finais)}")
    print(f"   🔴 Sinais FORTES de venda (Viáveis): {len(sinais_venda_finais)}")
    print(f"   ⚪ Sinais Laterais/Consolidação (Viáveis): {len(sinais_laterais_finais)}")
    print(f"   ❌ Erros: {len(erros)}\n")

    print("📧 Enviando alertas consolidados por tipo...")
    enviar_alerta_consolidado(alertas_por_tipo)

    print("\n📧 Enviando relatório final por e-mail...")
    enviar_relatorio_final(
        total_ativos=len(lista_tickers),
        sinais_compra=sinais_compra_finais, 
        sinais_venda=sinais_venda_finais,   
        erros=erros,
    )