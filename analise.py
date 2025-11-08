# PARTE 1

# import yfinance as yf
# import pandas as pd
# import ta
# from alertas import enviar_alerta, enviar_relatorio_final
# import time

# def analisar_ativo(ticker):
#     """
#     Baixa os dados do ativo, calcula os indicadores, verifica os sinais
#     e dispara alertas se necessário.
#     """
#     print(f"Analisando o ativo: {ticker}...")
    
#     dados = yf.download(ticker, period="6mo", interval="1d", auto_adjust=False)

#     if dados.empty:
#         print(f"Não foi possível obter dados para o ticker {ticker}.")
#         return None

#     if isinstance(dados.columns, pd.MultiIndex):
#         dados.columns = dados.columns.droplevel(1)

#     high_prices = dados["High"].squeeze()
#     low_prices = dados["Low"].squeeze()
#     close_prices = dados["Close"].squeeze()

#     dados["MME21"] = pd.Series(
#         ta.trend.EMAIndicator(close_prices, 21).ema_indicator(),
#         index=dados.index
#     )
#     dados["MME50"] = pd.Series(
#         ta.trend.EMAIndicator(close_prices, 50).ema_indicator(),
#         index=dados.index
#     )
    
#     macd = ta.trend.MACD(close_prices)
#     dados["MACD_HIST"] = pd.Series(macd.macd_diff(), index=dados.index)

#     dados["RSI"] = pd.Series(
#         ta.momentum.RSIIndicator(close_prices, 14).rsi(),
#         index=dados.index
#     )
#     dados["ATR"] = pd.Series(
#         ta.volatility.AverageTrueRange(high_prices, low_prices, close_prices, 14).average_true_range(),
#         index=dados.index
#     )

#     dados["Compra"] = (
#         (dados["MME21"].shift(1) <= dados["MME50"].shift(1)) &
#         (dados["MME21"] > dados["MME50"]) &
#         (dados["Close"] > dados["MME21"]) &
#         (dados["MACD_HIST"] > dados["MACD_HIST"].shift(1)) &
#         (dados["RSI"].between(50, 65)) &
#         (dados["ATR"] > dados["ATR"].rolling(50).mean()) &
#         (dados["Volume"] > dados["Volume"].rolling(20).mean())
#     )

#     dados["Venda"] = (
#         (dados["MME21"].shift(1) >= dados["MME50"].shift(1)) &
#         (dados["MME21"] < dados["MME50"]) &
#         (dados["Close"] < dados["MME21"]) &
#         (dados["MACD_HIST"] < dados["MACD_HIST"].shift(1)) &
#         (dados["RSI"] < 50)
#     )

#     print("\nÚltimos 10 dias:")
#     print(dados[["Close", "Compra", "Venda"]].tail(10))

#     ultimo_registro = dados.iloc[-1]
#     preco_atual = ultimo_registro["Close"]

#     resultado = {"sinal": None, "preco": preco_atual}

#     if ultimo_registro["Compra"]:
#         print(f"\nSinal de COMPRA detectado para {ticker} em {ultimo_registro.name.date()}.")
#         enviar_alerta(ticker, "Compra", preco_atual)
#         resultado["sinal"] = "compra"
#     elif ultimo_registro["Venda"]:
#         print(f"\nSinal de VENDA detectado para {ticker} em {ultimo_registro.name.date()}.")
#         enviar_alerta(ticker, "Venda", preco_atual)
#         resultado["sinal"] = "venda"
#     else:
#         print(f"\nNenhum novo sinal de compra ou venda para {ticker} no último pregão.")
    
#     return resultado


# def analisar_multiplos_ativos(lista_tickers):
#     """
#     Analisa múltiplos ativos de uma lista.
    
#     Args:
#         lista_tickers (list): Lista de tickers para analisar (ex: ['PETR4.SA', 'VALE3.SA'])
#     """
#     print(f"Iniciando análise de {len(lista_tickers)} ativos...")
#     print("=" * 70)
    
#     resultados = []
#     sinais_compra = []
#     sinais_venda = []
#     erros = []
    
#     for i, ticker in enumerate(lista_tickers, 1):
#         print(f"\n[{i}/{len(lista_tickers)}] Processando {ticker}")
#         print("-" * 70)
        
#         try:
#             resultado = analisar_ativo(ticker)
#             resultados.append((ticker, "Sucesso"))
            
#             if resultado and resultado["sinal"] == "compra":
#                 sinais_compra.append((ticker, resultado["preco"]))
#             elif resultado and resultado["sinal"] == "venda":
#                 sinais_venda.append((ticker, resultado["preco"]))
                
#         except Exception as e:
#             erro_msg = str(e)
#             print(f"Erro ao analisar {ticker}: {erro_msg}")
#             resultados.append((ticker, f"Erro: {erro_msg}"))
#             erros.append((ticker, erro_msg))
        
#         if i < len(lista_tickers):
#             time.sleep(1)
        
#         print("=" * 70)
    
#     print("\n" + "=" * 70)
#     print("RESUMO DA ANÁLISE")
#     print("=" * 70)
#     for ticker, status in resultados:
#         print(f"{ticker}: {status}")
#     print("=" * 70)
    
#     print("\nEnviando relatório final por e-mail...")
#     enviar_relatorio_final(
#         total_ativos=len(lista_tickers),
#         sinais_compra=sinais_compra,
#         sinais_venda=sinais_venda,
#         erros=erros
#     )

# PARTE 2

# import yfinance as yf
# import pandas as pd
# import ta
# from alertas import enviar_alerta, enviar_relatorio_final
# import time

# def analisar_ativo(ticker, score_minimo=4):
#     """
#     Analisa um ativo usando sistema rigoroso de pontuação.
    
#     Args:
#         ticker (str): Código do ativo
#         score_minimo (int): Pontuação mínima para disparar alerta (padrão: 4)
    
#     Returns:
#         dict: {"sinal": "compra"/"venda"/None, "preco": float, "score_compra": int, "score_venda": int}
#     """
#     print(f"Analisando o ativo: {ticker}...")
#     dados = yf.download(ticker, period="6mo", interval="1d", auto_adjust=False, progress=False)
    
#     if dados.empty:
#         print(f"❌ Não foi possível obter dados para {ticker}.")
#         return None

#     if isinstance(dados.columns, pd.MultiIndex):
#         dados.columns = dados.columns.droplevel(1)

#     high_prices = dados["High"].squeeze()
#     low_prices = dados["Low"].squeeze()
#     close_prices = dados["Close"].squeeze()

#     dados["MME9"] = ta.trend.EMAIndicator(close_prices, 9).ema_indicator()
#     dados["MME21"] = ta.trend.EMAIndicator(close_prices, 21).ema_indicator()
#     dados["MME50"] = ta.trend.EMAIndicator(close_prices, 50).ema_indicator()
#     dados["MME200"] = ta.trend.EMAIndicator(close_prices, 200).ema_indicator()
    
#     macd = ta.trend.MACD(close_prices)
#     dados["MACD"] = macd.macd()
#     dados["MACD_SIGNAL"] = macd.macd_signal()
#     dados["MACD_HIST"] = macd.macd_diff()
    
#     dados["RSI"] = ta.momentum.RSIIndicator(close_prices, 14).rsi()
#     dados["ATR"] = ta.volatility.AverageTrueRange(high_prices, low_prices, close_prices, 14).average_true_range()
    
#     bollinger = ta.volatility.BollingerBands(close_prices)
#     dados["BB_HIGH"] = bollinger.bollinger_hband()
#     dados["BB_LOW"] = bollinger.bollinger_lband()
#     dados["BB_MID"] = bollinger.bollinger_mavg()
    
#     dados["Volume_Media20"] = dados["Volume"].rolling(20).mean()
#     dados["Volume_Media50"] = dados["Volume"].rolling(50).mean()
#     dados["ATR_Media50"] = dados["ATR"].rolling(50).mean()

#     ultimo = dados.iloc[-1]
#     penultimo = dados.iloc[-2]
#     ante_penultimo = dados.iloc[-3]
    
#     score_compra = 0
#     score_venda = 0
#     detalhes_compra = []
#     detalhes_venda = []
#     pontos_forca_compra = 0 
#     pontos_forca_venda = 0

#     tendencia_alta = (
#         ultimo["MME9"] > ultimo["MME21"] > ultimo["MME50"] and
#         ultimo["Close"] > ultimo["MME200"] 
#     )
#     if tendencia_alta:
#         score_compra += 1
#         detalhes_compra.append("✓ Tendência de alta clara")
#         pontos_forca_compra += 2
    
#     cruzamento_alta = (
#         penultimo["MME9"] <= penultimo["MME21"] and
#         ultimo["MME9"] > ultimo["MME21"]
#     )
#     if cruzamento_alta:
#         score_compra += 1
#         detalhes_compra.append("✓ Cruzamento de médias detectado")
#         pontos_forca_compra += 2
#     elif ultimo["MME9"] > ultimo["MME21"]:
#         score_compra += 1
#         detalhes_compra.append("✓ MME9 > MME21")
    
#     macd_positivo = (
#         ultimo["MACD"] > ultimo["MACD_SIGNAL"] and
#         ultimo["MACD_HIST"] > penultimo["MACD_HIST"] > ante_penultimo["MACD_HIST"]
#     )
#     if macd_positivo:
#         score_compra += 1
#         detalhes_compra.append("✓ MACD forte e crescente")
#         pontos_forca_compra += 1
    
#     rsi_ideal = 50 <= ultimo["RSI"] <= 70
#     if rsi_ideal:
#         score_compra += 1
#         detalhes_compra.append(f"✓ RSI ideal ({ultimo['RSI']:.1f})")
#         if 55 <= ultimo["RSI"] <= 65:
#             pontos_forca_compra += 1  # zona ótima
    
#     volume_forte = ultimo["Volume"] > ultimo["Volume_Media20"] * 1.2  # 20% acima
#     if volume_forte:
#         score_compra += 1
#         detalhes_compra.append("✓ Volume muito acima da média")
#         pontos_forca_compra += 1
    
#     preco_bb = ultimo["Close"]
#     dist_bb_baixa = (preco_bb - ultimo["BB_LOW"]) / (ultimo["BB_HIGH"] - ultimo["BB_LOW"])
#     if 0.1 <= dist_bb_baixa <= 0.4:
#         score_compra += 1
#         detalhes_compra.append("✓ Preço em boa posição (Bollinger)")
#         pontos_forca_compra += 1
    
#     volatilidade_ok = ultimo["ATR"] <= ultimo["ATR_Media50"] * 1.3
#     if volatilidade_ok:
#         detalhes_compra.append("✓ Volatilidade controlada")
#         pontos_forca_compra += 1

#     tendencia_baixa = (
#         ultimo["MME9"] < ultimo["MME21"] < ultimo["MME50"] and
#         ultimo["Close"] < ultimo["MME200"]
#     )
#     if tendencia_baixa:
#         score_venda += 1
#         detalhes_venda.append("✓ Tendência de baixa clara")
#         pontos_forca_venda += 2
    
#     cruzamento_baixa = (
#         penultimo["MME9"] >= penultimo["MME21"] and
#         ultimo["MME9"] < ultimo["MME21"]
#     )
#     if cruzamento_baixa:
#         score_venda += 1
#         detalhes_venda.append("✓ Cruzamento de baixa detectado")
#         pontos_forca_venda += 2
#     elif ultimo["MME9"] < ultimo["MME21"]:
#         score_venda += 1
#         detalhes_venda.append("✓ MME9 < MME21")
    
#     macd_negativo = (
#         ultimo["MACD"] < ultimo["MACD_SIGNAL"] and
#         ultimo["MACD_HIST"] < penultimo["MACD_HIST"] < ante_penultimo["MACD_HIST"]
#     )
#     if macd_negativo:
#         score_venda += 1
#         detalhes_venda.append("✓ MACD fraco e decrescente")
#         pontos_forca_venda += 1
    
#     rsi_fraco = ultimo["RSI"] < 45
#     if rsi_fraco:
#         score_venda += 1
#         detalhes_venda.append(f"✓ RSI fraco ({ultimo['RSI']:.1f})")
#         if ultimo["RSI"] < 35:
#             pontos_forca_venda += 1
    
#     if volume_forte:
#         score_venda += 1
#         detalhes_venda.append("✓ Volume alto (pressão vendedora)")
#         pontos_forca_venda += 1
    
#     if 0.6 <= dist_bb_baixa <= 0.9:
#         score_venda += 1
#         detalhes_venda.append("✓ Preço no topo (Bollinger)")
#         pontos_forca_venda += 1
    
#     volatilidade_alta = ultimo["ATR"] > ultimo["ATR_Media50"] * 1.5
#     if volatilidade_alta:
#         detalhes_venda.append("✓ Volatilidade elevada")
#         pontos_forca_venda += 1

#     print(f"📊 Score Compra: {score_compra}/7 (+{pontos_forca_compra} força) | Score Venda: {score_venda}/7 (+{pontos_forca_venda} força)")

#     resultado = {
#         "sinal": None,
#         "preco": ultimo["Close"],
#         "score_compra": score_compra,
#         "score_venda": score_venda
#     }

#     score_total_compra = score_compra + (pontos_forca_compra * 0.3)
#     score_total_venda = score_venda + (pontos_forca_venda * 0.3)
    
#     if (score_compra >= score_minimo and 
#         pontos_forca_compra >= 2 and 
#         score_total_compra > score_total_venda + 1):
        
#         print(f"🟢 SINAL DE COMPRA FORTE ({score_compra}/7, força: {pontos_forca_compra}) para {ticker}")
#         if detalhes_compra:
#             print("   " + "\n   ".join(detalhes_compra))
        
#         dados_adicionais = {
#             "RSI": ultimo["RSI"],
#             "MME21": ultimo["MME21"],
#             "MME50": ultimo["MME50"],
#             "MACD_HIST": ultimo["MACD_HIST"]
#         }
#         enviar_alerta(ticker, "Compra", ultimo["Close"], dados_adicionais)
#         resultado["sinal"] = "compra"
        
#     elif (score_venda >= score_minimo and 
#           pontos_forca_venda >= 2 and 
#           score_total_venda > score_total_compra + 1):
        
#         print(f"🔴 SINAL DE VENDA FORTE ({score_venda}/7, força: {pontos_forca_venda}) para {ticker}")
#         if detalhes_venda:
#             print("   " + "\n   ".join(detalhes_venda))
        
#         dados_adicionais = {
#             "RSI": ultimo["RSI"],
#             "MME21": ultimo["MME21"],
#             "MME50": ultimo["MME50"],
#             "MACD_HIST": ultimo["MACD_HIST"]
#         }
#         enviar_alerta(ticker, "Venda", ultimo["Close"], dados_adicionais)
#         resultado["sinal"] = "venda"
        
#     else:
#         print(f"⚪ Sem sinal suficientemente forte para {ticker}")
#         print(f"   (Compra: {score_compra}/7 +{pontos_forca_compra}, Venda: {score_venda}/7 +{pontos_forca_venda})")

#     return resultado


# def analisar_multiplos_ativos(lista_tickers, score_minimo=4):
#     """
#     Analisa múltiplos ativos com critérios rigorosos.
    
#     Args:
#         lista_tickers (list): Lista de tickers para analisar
#         score_minimo (int): Pontuação mínima (padrão: 4 - rigoroso)
#     """
#     print(f"\n{'='*70}")
#     print(f"🚀 Iniciando análise RIGOROSA de {len(lista_tickers)} ativos")
#     print(f"📊 Score mínimo: {score_minimo}/7 + 2 pontos de força")
#     print(f"🎯 Apenas sinais de ALTA PROBABILIDADE serão enviados")
#     print(f"{'='*70}\n")
    
#     resultados = []
#     sinais_compra = []
#     sinais_venda = []
#     erros = []

#     for i, ticker in enumerate(lista_tickers, 1):
#         print(f"\n[{i}/{len(lista_tickers)}] 🔍 {ticker}")
#         print("-" * 70)
        
#         try:
#             resultado = analisar_ativo(ticker, score_minimo)
            
#             if resultado is None:
#                 erros.append((ticker, "Sem dados disponíveis"))
#                 resultados.append((ticker, "❌ Erro: Sem dados"))
#                 continue
            
#             resultados.append((ticker, "✅ Sucesso"))
            
#             if resultado["sinal"] == "compra":
#                 sinais_compra.append((ticker, resultado["preco"]))
#             elif resultado["sinal"] == "venda":
#                 sinais_venda.append((ticker, resultado["preco"]))
                
#         except Exception as e:
#             erro_msg = str(e)
#             print(f"❌ Erro ao analisar {ticker}: {erro_msg}")
#             resultados.append((ticker, f"❌ Erro: {erro_msg}"))
#             erros.append((ticker, erro_msg))
        
#         if i < len(lista_tickers):
#             time.sleep(1)
        
#         print("=" * 70)

#     # Resumo final
#     print(f"\n{'='*70}")
#     print("📋 RESUMO DA ANÁLISE")
#     print(f"{'='*70}")
#     for ticker, status in resultados:
#         print(f"{ticker}: {status}")
#     print(f"{'='*70}\n")

#     print("📊 ESTATÍSTICAS:")
#     print(f"   Total analisado: {len(lista_tickers)}")
#     print(f"   🟢 Sinais FORTES de compra: {len(sinais_compra)}")
#     print(f"   🔴 Sinais FORTES de venda: {len(sinais_venda)}")
#     print(f"   ⚪ Sem sinal suficiente: {len(lista_tickers) - len(sinais_compra) - len(sinais_venda) - len(erros)}")
#     print(f"   ❌ Erros: {len(erros)}\n")

#     print("📧 Enviando relatório final por e-mail...")
#     enviar_relatorio_final(
#         total_ativos=len(lista_tickers),
#         sinais_compra=sinais_compra,
#         sinais_venda=sinais_venda,
#         erros=erros
#     )

import yfinance as yf
import pandas as pd
import ta
from alertas import enviar_alerta, enviar_relatorio_final 
import time


def recomendar_estrutura(score_compra, score_venda, pontos_forca_compra, pontos_forca_venda, volatilidade_perc, rsi, adx):
    """
    Recomenda uma estratégia de opções baseada no score, força do sinal, RSI e volatilidade percentual (ATR/Preço).
    
    volatilidade_perc: ATR como porcentagem do preço.
    Limites sugeridos (ajuste conforme o mercado):
    - Baixa volatilidade: < 1.5%
    - Alta volatilidade: > 3.0%
    
    NOVA LÓGICA: Exige Score >= 5 E Força >= 3 para Compra/Venda de Opção a Seco (alto risco).
    """
    
    if (score_compra >= 5 and pontos_forca_compra >= 3 and score_compra > score_venda and
        volatilidade_perc > 3.0 and rsi > 65):
        return "Compra de CALL a seco (sinal MUITO forte)"
            
    elif (score_venda >= 5 and pontos_forca_venda >= 3 and score_venda > score_compra and
          volatilidade_perc > 3.0 and rsi < 35):
        return "Compra de PUT a seco (sinal MUITO forte)"
            
    elif (score_compra >= 4 and pontos_forca_compra >= 2 and score_compra > score_venda):
        if rsi > 50 and volatilidade_perc < 1.5:
            return "Trava de alta ou venda coberta de PUT (sinal sólido)"
        else:
            return "Venda coberta de PUT (ativo descontado)"
            
    elif (score_venda >= 4 and pontos_forca_venda >= 2 and score_venda > score_compra):
        if rsi < 45 and volatilidade_perc < 1.5:
            return "Trava de baixa ou venda coberta de CALL (sinal sólido)"
        else:
            return "Venda coberta de CALL (topo identificado)"
            
    elif adx < 20 and 45 < rsi < 60:
        return "Estrutura COLLAR ou THL (mercado lateral)"
        
    else:
        return "Sem recomendação para estrutura (baixo índice de confiança)"


def analisar_ativo(ticker, score_minimo=4):
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

    cruzamento_alta = (
        penultimo["MME9"] <= penultimo["MME21"] and
        ultimo["MME9"] > ultimo["MME21"]
    )
    if cruzamento_alta:
        score_compra += 1
        detalhes_compra.append("✓ Cruzamento de médias (9/21) detectado")
        pontos_forca_compra += 2
    elif ultimo["MME9"] > ultimo["MME21"]:
        score_compra += 1
        detalhes_compra.append("✓ MME9 > MME21")
        
    cruzamento_baixa = (
        penultimo["MME9"] >= penultimo["MME21"] and
        ultimo["MME9"] < ultimo["MME21"]
    )
    if cruzamento_baixa:
        score_venda += 1
        detalhes_venda.append("✓ Cruzamento de baixa (9/21) detectado")
        pontos_forca_venda += 2
    elif ultimo["MME9"] < ultimo["MME21"]:
        score_venda += 1
        detalhes_venda.append("✓ MME9 < MME21")


    macd_positivo = (
        ultimo["MACD"] > ultimo["MACD_SIGNAL"] and
        ultimo["MACD_HIST"] > penultimo["MACD_HIST"] > ante_penultimo["MACD_HIST"]
    )
    if macd_positivo:
        score_compra += 1
        detalhes_compra.append("✓ MACD forte e crescente (acelerando)")
        pontos_forca_compra += 1

    macd_negativo = (
        ultimo["MACD"] < ultimo["MACD_SIGNAL"] and
        ultimo["MACD_HIST"] < penultimo["MACD_HIST"] < ante_penultimo["MACD_HIST"]
    )
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

    volume_forte = ultimo["Volume"] > ultimo["Volume_Media20"] * 1.2
    if volume_forte:
        score_compra += 1 
        pontos_forca_compra += 1
        detalhes_compra.append("✓ Volume muito acima da média")
        
        score_venda += 1
        pontos_forca_venda += 1
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

    volatilidade_ok = ultimo["ATR"] <= ultimo["ATR_Media50"] * 1.3
    if volatilidade_ok:
        detalhes_compra.append("✓ Volatilidade controlada")
        pontos_forca_compra += 1

    volatilidade_alta = ultimo["ATR"] > ultimo["ATR_Media50"] * 1.5
    if volatilidade_alta:
        detalhes_venda.append("✓ Volatilidade elevada (cuidado/oportunidade de put)")
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

    tipo_estrutura = recomendar_estrutura(
        score_compra,
        score_venda,
        pontos_forca_compra,
        pontos_forca_venda,
        volatilidade_perc, 
        ultimo["RSI"],
        adx,
    )
    
    strike_call_sugerido = f"R$ {ultimo['BB_HIGH']:.2f} (BB Topo)"
    strike_put_sugerido = f"R$ {ultimo['BB_LOW']:.2f} (BB Suporte)"
    range_thl_sugerido = f"CALL: {ultimo['BB_HIGH']:.2f} / PUT: {ultimo['BB_LOW']:.2f} (BB Range)"

    dados_adicionais = {
        "RSI": ultimo["RSI"],
        "MME21": ultimo["MME21"],
        "MME50": ultimo["MME50"],
        "MACD_HIST": ultimo["MACD_HIST"],
        "Volatilidade_%": f"{volatilidade_perc:.2f}%",
        "estrutura": tipo_estrutura  
    }
    
    if (score_compra >= score_minimo and pontos_forca_compra >= 2 and score_total_compra > score_total_venda + 1):
        print(f"🟢 SINAL DE COMPRA FORTE ({score_compra}/7, força: {pontos_forca_compra}) para {ticker}")
        if detalhes_compra:
            print("   " + "\n   ".join(detalhes_compra))
        print(f"   Estrutura recomendada: {tipo_estrutura}")
        
        if "PUT" in tipo_estrutura:
            print(f"   🎯 Strike Sugerido (Venda PUT): {strike_put_sugerido}")
            dados_adicionais["Strike_Recomendado"] = strike_put_sugerido
        elif "CALL a seco" in tipo_estrutura:
             print(f"   ⚠️ Atenção: Compra a seco (Alto Risco/Recompensa)")
        
        enviar_alerta(ticker, "Compra", ultimo["Close"], dados_adicionais)
        resultado["sinal"] = "compra"

    elif (score_venda >= score_minimo and pontos_forca_venda >= 2 and score_total_venda > score_total_compra + 1):
        print(f"🔴 SINAL DE VENDA FORTE ({score_venda}/7, força: {pontos_forca_venda}) para {ticker}")
        if detalhes_venda:
            print("   " + "\n   ".join(detalhes_venda))
        print(f"   Estrutura recomendada: {tipo_estrutura}")
        
        if "CALL" in tipo_estrutura:
            print(f"   🎯 Strike Sugerido (Venda CALL): {strike_call_sugerido}")
            dados_adicionais["Strike_Recomendado"] = strike_call_sugerido
        elif "PUT a seco" in tipo_estrutura:
             print(f"   ⚠️ Atenção: Compra a seco (Alto Risco/Recompensa)")
        
        enviar_alerta(ticker, "Venda", ultimo["Close"], dados_adicionais)
        resultado["sinal"] = "venda"

    else:
        print(f"⚪ Sem sinal suficientemente forte para {ticker}")
        print(
            f"   (Compra: {score_compra}/7 +{pontos_forca_compra}, Venda: {score_venda}/7 +{pontos_forca_venda})"
        )
        print(f"   Estrutura recomendada: {tipo_estrutura}")

        if tipo_estrutura in ["Estrutura COLLAR ou THL (mercado lateral)"]:
            print(f"   🎯 Range Sugerido (COLLAR/THL): {range_thl_sugerido}")
            dados_adicionais["Range_Recomendado"] = range_thl_sugerido 
            enviar_alerta(ticker, "Lateral/Consolidação", ultimo["Close"], dados_adicionais)
        elif tipo_estrutura != "Sem recomendação para estrutura (baixo índice de confiança)":
            enviar_alerta(ticker, "Sinal Fraco/Aguardar", ultimo["Close"], dados_adicionais)


    return resultado


def analisar_multiplos_ativos(lista_tickers, score_minimo=4):
    print(f"\n{'='*70}")
    print(f"🚀 Iniciando análise RIGOROSA de {len(lista_tickers)} ativos")
    print(f"📊 Score mínimo: {score_minimo}/7 + 2 pontos de força")
    print(f"🎯 Apenas sinais de ALTA PROBABILIDADE serão enviados")
    print(f"{'='*70}\n")

    resultados = []
    sinais_compra = []
    sinais_venda = []
    erros = []

    for i, ticker in enumerate(lista_tickers, 1):
        print(f"\n[{i}/{len(lista_tickers)}] 🔍 {ticker}")
        print("-" * 70)

        try:
            resultado = analisar_ativo(ticker, score_minimo)

            if resultado is None:
                erros.append((ticker, "Sem dados disponíveis ou incompletos"))
                resultados.append((ticker, "❌ Erro: Sem dados"))
                continue

            resultados.append((ticker, "✅ Sucesso"))

            if resultado["sinal"] == "compra":
                sinais_compra.append((ticker, resultado["preco"]))
            elif resultado["sinal"] == "venda":
                sinais_venda.append((ticker, resultado["preco"]))

        except Exception as e:
            erro_msg = str(e)
            print(f"❌ Erro ao analisar {ticker}: {erro_msg}")
            resultados.append((ticker, f"❌ Erro: {erro_msg}"))
            erros.append((ticker, erro_msg))

        if i < len(lista_tickers):
            time.sleep(2) 

        print("=" * 70)

    print(f"\n{'='*70}")
    print("📋 RESUMO DA ANÁLISE")
    print(f"{'='*70}")
    for ticker, status in resultados:
        print(f"{ticker}: {status}")
    print(f"{'='*70}\n")

    print("📊 ESTATÍSTICAS:")
    print(f"   Total analisado: {len(lista_tickers)}")
    print(f"   🟢 Sinais FORTES de compra: {len(sinais_compra)}")
    print(f"   🔴 Sinais FORTES de venda: {len(sinais_venda)}")
    print(f"   ⚪ Sem sinal suficiente: {len(lista_tickers) - len(sinais_compra) - len(sinais_venda) - len(erros)}")
    print(f"   ❌ Erros: {len(erros)}\n")

    print("📧 Enviando relatório final por e-mail...")
    enviar_relatorio_final(
        total_ativos=len(lista_tickers),
        sinais_compra=sinais_compra,
        sinais_venda=sinais_venda,
        erros=erros,
    )