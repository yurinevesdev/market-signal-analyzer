# import yfinance as yf
# import pandas as pd
# import ta
# import numpy as np
# from alertas import enviar_alerta_consolidado, enviar_relatorio_final
# import time
# import json

# SCORE_MINIMO_OPERACAO = 70  
# CONFIANCA_MINIMA = 0.75 

# def carregar_dados_volatilidade():
#     """Carrega dados consolidados do scraper."""
#     try:
#         with open('dados_mercado_consolidado.json', 'r', encoding='utf-8') as f:
#             dados = json.load(f)
#             print(f"✅ Dados OpLab carregados: {len(dados)} tickers")
#             return dados
#     except Exception as e:
#         print(f"⚠️ Sem dados OpLab. Análise limitada. ({e})")
#         return {}

# def converter_para_float(valor):
#     """Converte strings para float com tratamento robusto."""
#     if valor in ['N/A', '-', None, '']:
#         return None
#     try:
#         return float(str(valor).replace(',', '.').replace('%', '').replace('R$', '').strip())
#     except:
#         return None

# def calcular_score_iv_completo(vol_info):
#     """
#     Sistema de scoring avançado para volatilidade implícita.
#     Retorna: (score_0_100, confianca_0_1, direcao, justificativas)
#     """
#     ivr = converter_para_float(vol_info.get('iv_rank'))
#     ivp = converter_para_float(vol_info.get('iv_percentil'))
#     vi = converter_para_float(vol_info.get('volatilidade_implicita'))
    
#     score = 0
#     confianca = 0.5
#     direcao = 'neutro'
#     justificativas = []
    
#     if ivr is None or ivp is None or vi is None:
#         return 0, 0.3, 'neutro', ['⚠️ Dados de IV incompletos - baixa confiança']
    
#     if ivr > 80:
#         score += 35
#         confianca += 0.20
#         direcao = 'venda_premium'
#         justificativas.append(f'🔥 IV Rank EXTREMO ({ivr:.1f}%) - 95º percentil histórico')
#     elif ivr > 70:
#         score += 30
#         confianca += 0.15
#         direcao = 'venda_premium'
#         justificativas.append(f'✓ IV Rank MUITO ALTO ({ivr:.1f}%) - topo da faixa')
#     elif ivr > 60:
#         score += 20
#         confianca += 0.10
#         direcao = 'venda_premium'
#         justificativas.append(f'✓ IV Rank ALTO ({ivr:.1f}%) - acima de 60%')
#     elif ivr < 20:
#         score += 30
#         confianca += 0.15
#         direcao = 'compra_premium'
#         justificativas.append(f'✓ IV Rank BAIXÍSSIMO ({ivr:.1f}%) - fundo histórico')
#     elif ivr < 30:
#         score += 20
#         confianca += 0.10
#         direcao = 'compra_premium'
#         justificativas.append(f'✓ IV Rank BAIXO ({ivr:.1f}%) - abaixo de 30%')
#     else:
#         justificativas.append(f'○ IV Rank neutro ({ivr:.1f}%)')
    
#     if ivp > 85:
#         score += 25
#         confianca += 0.10
#         justificativas.append(f'✓ IV Percentil EXTREMO ({ivp:.1f}%) - reversão provável')
#     elif ivp > 75 and ivr > 65:
#         score += 20
#         confianca += 0.08
#         justificativas.append(f'✓ IV Percentil + Rank convergem para VENDA ({ivp:.1f}%)')
#     elif ivp < 15:
#         score += 25
#         confianca += 0.10
#         justificativas.append(f'✓ IV Percentil MÍNIMO ({ivp:.1f}%) - expansão esperada')
#     elif ivp < 25 and ivr < 35:
#         score += 20
#         confianca += 0.08
#         justificativas.append(f'✓ IV Percentil + Rank convergem para COMPRA ({ivp:.1f}%)')
    
#     if vi > 70:
#         score += 20
#         confianca += 0.08
#         justificativas.append(f'✓ VI EXTREMA ({vi:.1f}%) - prêmios GORDOS')
#     elif vi > 55:
#         score += 15
#         justificativas.append(f'✓ VI ALTA ({vi:.1f}%) - prêmios atrativos')
#     elif vi < 20:
#         score += 20
#         confianca += 0.08
#         justificativas.append(f'✓ VI MUITO BAIXA ({vi:.1f}%) - opções BARATAS')
#     elif vi < 30:
#         score += 15
#         justificativas.append(f'✓ VI BAIXA ({vi:.1f}%) - custo reduzido')
    
#     if ivr and ivp:
#         diff = abs(ivr - ivp)
#         if diff < 10:
#             score += 20
#             confianca += 0.12
#             justificativas.append(f'🔥 CONVERGÊNCIA FORTE: IVR={ivr:.1f}% / IVP={ivp:.1f}% (diff={diff:.1f}%)')
#         elif diff < 20:
#             score += 10
#             confianca += 0.05
#             justificativas.append(f'✓ Convergência razoável (diff={diff:.1f}%)')
#         else:
#             confianca -= 0.10
#             justificativas.append(f'⚠️ DIVERGÊNCIA: IVR vs IVP (diff={diff:.1f}%) - cautela')
    
#     confianca = max(0, min(1, confianca))
    
#     return score, confianca, direcao, justificativas

# def calcular_score_tecnico(df, ticker):
#     """
#     Scoring técnico avançado com múltiplos timeframes e indicadores.
#     Retorna: (score_0_100, confianca_0_1, direcao, justificativas)
#     """
#     if len(df) < 200:
#         return 0, 0.2, 'neutro', ['⚠️ Histórico insuficiente']
    
#     cp = df['Close'].squeeze()
#     hp = df['High'].squeeze()
#     lp = df['Low'].squeeze()
#     vol = df['Volume'].squeeze()
    
#     ult = df.iloc[-1]
#     pen = df.iloc[-2]
    
#     score = 0
#     confianca = 0.5
#     direcao = 'neutro'
#     justificativas = []
    
#     mme9 = ta.trend.EMAIndicator(cp, 9).ema_indicator()
#     mme21 = ta.trend.EMAIndicator(cp, 21).ema_indicator()
#     mme50 = ta.trend.EMAIndicator(cp, 50).ema_indicator()
#     mme200 = ta.trend.EMAIndicator(cp, 200).ema_indicator()
    
#     rsi = ta.momentum.RSIIndicator(cp, 14).rsi()
#     macd_obj = ta.trend.MACD(cp)
#     macd = macd_obj.macd()
#     macd_signal = macd_obj.macd_signal()
#     macd_hist = macd_obj.macd_diff()
    
#     adx_obj = ta.trend.ADXIndicator(hp, lp, cp, 14)
#     adx = adx_obj.adx()
    
#     bb = ta.volatility.BollingerBands(cp)
#     bb_high = bb.bollinger_hband()
#     bb_low = bb.bollinger_lband()
#     bb_mid = bb.bollinger_mavg()
    
#     atr = ta.volatility.AverageTrueRange(hp, lp, cp, 14).average_true_range()
    
#     sma20 = cp.rolling(20).mean()
#     std20 = cp.rolling(20).std()
#     z_score = ((cp - sma20) / std20).iloc[-1]
    
#     preco = ult['Close']
#     rsi_atual = rsi.iloc[-1]
#     rsi_ant = rsi.iloc[-2]
#     adx_atual = adx.iloc[-1]
#     macd_atual = macd.iloc[-1]
#     signal_atual = macd_signal.iloc[-1]
#     hist_atual = macd_hist.iloc[-1]
#     hist_ant = macd_hist.iloc[-2]
    
#     bb_pos = (preco - bb_low.iloc[-1]) / (bb_high.iloc[-1] - bb_low.iloc[-1])
    
#     m9, m21, m50, m200 = mme9.iloc[-1], mme21.iloc[-1], mme50.iloc[-1], mme200.iloc[-1]
    
#     if preco > m9 > m21 > m50 > m200:
#         score += 25
#         confianca += 0.15
#         direcao = 'alta'
#         justificativas.append(f'🔥 TENDÊNCIA DE ALTA PERFEITA (todas MMs alinhadas)')
#     elif preco < m9 < m21 < m50 < m200:
#         score += 25
#         confianca += 0.15
#         direcao = 'baixa'
#         justificativas.append(f'🔥 TENDÊNCIA DE BAIXA PERFEITA (todas MMs alinhadas)')
#     elif preco > m21 > m50:
#         score += 15
#         confianca += 0.08
#         direcao = 'alta'
#         justificativas.append(f'✓ Tendência de alta (MMs curtas alinhadas)')
#     elif preco < m21 < m50:
#         score += 15
#         confianca += 0.08
#         direcao = 'baixa'
#         justificativas.append(f'✓ Tendência de baixa (MMs curtas alinhadas)')
#     elif pen['Close'] <= mme21.iloc[-2] and preco > m21:
#         score += 20
#         confianca += 0.12
#         direcao = 'alta'
#         justificativas.append(f'🔥 CRUZAMENTO DE ALTA detectado (preço rompeu MME21)')
#     elif pen['Close'] >= mme21.iloc[-2] and preco < m21:
#         score += 20
#         confianca += 0.12
#         direcao = 'baixa'
#         justificativas.append(f'🔥 CRUZAMENTO DE BAIXA detectado (preço perdeu MME21)')
#     else:
#         justificativas.append('○ Médias sem tendência clara')
    
#     if rsi_atual < 30:
#         score += 25
#         confianca += 0.12
#         direcao = 'alta'
#         justificativas.append(f'🔥 RSI SOBREVENDA ({rsi_atual:.1f}) - reversão provável')
#     elif rsi_atual < 40 and rsi_atual > rsi_ant:
#         score += 15
#         confianca += 0.08
#         direcao = 'alta'
#         justificativas.append(f'✓ RSI baixo virando ({rsi_atual:.1f})')
#     elif rsi_atual > 70:
#         score += 25
#         confianca += 0.12
#         direcao = 'baixa'
#         justificativas.append(f'🔥 RSI SOBRECOMPRA ({rsi_atual:.1f}) - reversão provável')
#     elif rsi_atual > 60 and rsi_atual < rsi_ant:
#         score += 15
#         confianca += 0.08
#         direcao = 'baixa'
#         justificativas.append(f'✓ RSI alto virando ({rsi_atual:.1f})')
#     elif 45 <= rsi_atual <= 55:
#         justificativas.append(f'○ RSI neutro ({rsi_atual:.1f}) - mercado equilibrado')
    
#     if macd_atual > signal_atual and hist_atual > hist_ant and hist_atual > 0:
#         score += 20
#         confianca += 0.10
#         if direcao == 'alta':
#             confianca += 0.05
#         direcao = 'alta'
#         justificativas.append(f'✓ MACD positivo e acelerando')
#     elif macd_atual < signal_atual and hist_atual < hist_ant and hist_atual < 0:
#         score += 20
#         confianca += 0.10
#         if direcao == 'baixa':
#             confianca += 0.05
#         direcao = 'baixa'
#         justificativas.append(f'✓ MACD negativo e acelerando')
    
#     if z_score > 2.5:
#         score += 15
#         confianca += 0.08
#         direcao = 'baixa'
#         justificativas.append(f'🔥 Z-SCORE EXTREMO ({z_score:.2f}) - sobrecompra estatística')
#     elif z_score > 2.0:
#         score += 10
#         justificativas.append(f'✓ Z-Score alto ({z_score:.2f}) - acima de 2 desvios')
#     elif z_score < -2.5:
#         score += 15
#         confianca += 0.08
#         direcao = 'alta'
#         justificativas.append(f'🔥 Z-SCORE EXTREMO ({z_score:.2f}) - sobrevenda estatística')
#     elif z_score < -2.0:
#         score += 10
#         justificativas.append(f'✓ Z-Score baixo ({z_score:.2f}) - abaixo de 2 desvios')
    
#     if adx_atual > 25:
#         confianca += 0.10
#         justificativas.append(f'✓ ADX forte ({adx_atual:.1f}) - tendência confirmada')
#     elif adx_atual < 20:
#         confianca -= 0.05
#         justificativas.append(f'⚠️ ADX fraco ({adx_atual:.1f}) - mercado lateral')
    
#     if bb_pos < 0.2:
#         score += 10
#         justificativas.append(f'✓ Preço na banda inferior BB (suporte)')
#     elif bb_pos > 0.8:
#         score += 10
#         justificativas.append(f'✓ Preço na banda superior BB (resistência)')
    
#     bb_width = (bb_high.iloc[-1] - bb_low.iloc[-1]) / bb_mid.iloc[-1]
#     bb_width_media = bb_width
#     if bb_width < 0.05:
#         confianca += 0.08
#         justificativas.append(f'🔥 SQUEEZE de Bollinger - explosão iminente')
    
#     vol_media = vol.rolling(20).mean().iloc[-1]
#     if ult['Volume'] > vol_media * 1.5:
#         confianca += 0.08
#         justificativas.append(f'✓ Volume FORTE (150%+ da média)')
    
#     confianca = max(0, min(1, confianca))
    
#     return score, confianca, direcao, justificativas

# def determinar_estrutura_otima(score_iv, conf_iv, dir_iv, score_tec, conf_tec, dir_tec, vol_info, dados_tecnicos, just_tec):
#     """
#     Inteligência de decisão com HIERARQUIA DE FUNIL (Sem sobreposição).
#     1. EXAUSTÃO (Veto Supremo)
#     2. TENDÊNCIA FORTE (Seguir Fluxo)
#     3. CORREÇÃO/REVERSÃO (Ajuste Fino)
#     4. LATERALIDADE (Mercado Neutro)
#     """
    
#     peso_iv = 0.60 
#     peso_tec = 0.40
#     score_final = (score_iv * peso_iv) + (score_tec * peso_tec)
#     confianca_final = (conf_iv * peso_iv) + (conf_tec * peso_tec)
    
#     ivr = converter_para_float(vol_info.get('iv_rank')) or 0
#     rsi = dados_tecnicos.get('rsi', 50)
#     z_score = dados_tecnicos.get('z_score', 0)
    
#     estrutura = "AGUARDAR - Sem configuração clara"
#     justificativa = []

#     alta_perfeita = any("TENDÊNCIA DE ALTA PERFEITA" in j for j in just_tec)
#     baixa_perfeita = any("TENDÊNCIA DE BAIXA PERFEITA" in j for j in just_tec)

#     if rsi > 85 or z_score > 3.0:
#         estrutura = "BEAR CALL SPREAD (Exaustão Extrema de Topo)"
#         justificativa.append(f"⚠️ CAPITULAÇÃO: Ativo esticou demais (RSI={rsi:.1f}). Probabilidade alta de reversão.")
#         score_final += 15
#         confianca_final = min(0.98, confianca_final + 0.15)

#     elif rsi < 15 or z_score < -3.0:
#         estrutura = "BULL PUT SPREAD (Exaustão Extrema de Fundo)"
#         justificativa.append(f"⚠️ CAPITULAÇÃO: Ativo caiu demais (RSI={rsi:.1f}). Repique estatístico iminente.")
#         score_final += 15
#         confianca_final = min(0.98, confianca_final + 0.15)

#     elif alta_perfeita:
#         if ivr < 40:
#             estrutura = "🔥🔥 BULL CALL SPREAD (Trend Following + IV Baixa)"
#             justificativa.append("🚀 MOMENTUM: Alta perfeita detectada. IV baixa permite compra de opções baratas.")
#         elif ivr >= 60:
#             estrutura = "🔥🔥 VENDA DE PUT COBERTA (Alta + Renda com IV Alta)"
#             justificativa.append("💰 APROVEITAMENTO: Tendência de alta com IV alta = Prêmio gordo com proteção.")
#         else:
#             estrutura = "BULL CALL SPREAD (Moderado)"
#         confianca_final = min(0.98, confianca_final + 0.10)

#     elif baixa_perfeita:
#         if ivr < 40:
#             estrutura = "🔥🔥 BEAR PUT SPREAD (Trend Following + IV Baixa)"
#             justificativa.append("📉 MOMENTUM: Baixa forte detectada. IV baixa favorece travas de proteção baratas.")
#         elif ivr >= 60:
#             estrutura = "🔥🔥 VENDA DE CALL COBERTA (Baixa + Renda com IV Alta)"
#             justificativa.append("🛡️ DEFESA: Tendência de queda com IV alta permite remunerar via venda de call.")
#         else:
#             estrutura = "BEAR PUT SPREAD (Moderado)"
#         confianca_final = min(0.98, confianca_final + 0.10)

#     elif ivr >= 60:
#         if rsi < 35 or z_score < -2.0:
#             estrutura = "🔥🔥 VENDA DE PUT COBERTA (Setup Clássico de Fundo)"
#             justificativa.append(f"💰 SETUP: Sobrevenda técnica (RSI={rsi:.1f}) + IV Rank Alto ({ivr:.1f}%).")
#         elif rsi > 65 or z_score > 2.0:
#             estrutura = "🔥🔥 VENDA DE CALL COBERTA (Setup Clássico de Topo)"
#             justificativa.append(f"💰 SETUP: Sobrecompra técnica (RSI={rsi:.1f}) + IV Rank Alto ({ivr:.1f}%).")
#         else:
#             if score_final > 60:
#                 estrutura = "IRON CONDOR / STRANGLE (Mercado Lateral)"
#                 justificativa.append("⏳ LATERAL: IV alta em mercado sem tendência. Lucro no decaimento (Theta).")

#     elif ivr < 25 and score_tec > 65:
#         if dir_tec == 'alta':
#             estrutura = "🔥 COMPRA DE CALL A SECO (Alavancagem Barata)"
#             justificativa.append("🚀 OPORTUNIDADE: IV mínima com sinal técnico forte de alta.")
#         elif dir_tec == 'baixa':
#             estrutura = "🔥 COMPRA DE PUT A SECO (Alavancagem Barata)"
#             justificativa.append("🚀 OPORTUNIDADE: IV mínima com sinal técnico forte de baixa.")

#     elif dir_tec == 'neutro' and 40 <= ivr <= 60:
#         estrutura = "THL / IRON CONDOR (Mercado em Consolidação)"
#         justificativa.append("○ NEUTRO: Mercado sem direção e IV em níveis médios.")

#     return estrutura, score_final, confianca_final, justificativa

# def analisar_ativo_completo(ticker_sa, vol_data):
#     """
#     Análise ULTRA ASSERTIVA combinando todos os fatores.
#     """
#     print(f"\n{'='*70}")
#     print(f"📊 Análise Ultra Assertiva: {ticker_sa}")
#     print('-'*70)
    
#     df = yf.download(ticker_sa, period="1y", interval="1d", auto_adjust=False, progress=False)
#     if df.empty or len(df) < 200:
#         print(f"❌ Dados insuficientes para {ticker_sa}")
#         return None
    
#     if isinstance(df.columns, pd.MultiIndex):
#         df.columns = df.columns.droplevel(1)
    
#     ticker_limpo = ticker_sa.replace('.SA', '')
#     vol_info = vol_data.get(ticker_limpo, {})
    
#     score_iv, conf_iv, dir_iv, just_iv = calcular_score_iv_completo(vol_info)
#     score_tec, conf_tec, dir_tec, just_tec = calcular_score_tecnico(df, ticker_sa)

#     preco_atual = df['Close'].iloc[-1]
#     rsi = df['Close'].pipe(lambda x: ta.momentum.RSIIndicator(x, 14).rsi().iloc[-1])
#     sma20 = df['Close'].rolling(20).mean()
#     std20 = df['Close'].rolling(20).std()
#     z_score = ((df['Close'] - sma20) / std20).iloc[-1]
    
#     dados_tecnicos = {
#         'rsi': rsi,
#         'z_score': z_score,
#         'preco_atual': preco_atual
#     }
    
#     estrutura, score_final, confianca_final, just_estrutura = determinar_estrutura_otima(
#         score_iv, conf_iv, dir_iv,
#         score_tec, conf_tec, dir_tec,
#         vol_info, dados_tecnicos, just_tec
#     )
    
#     print(f"\n📈 PREÇO ATUAL: R$ {preco_atual:.2f}")
#     print(f"\n🎯 SCORES:")
#     print(f"   IV Score: {score_iv:.1f}/100 (Confiança: {conf_iv:.1%}) → {dir_iv.upper()}")
#     print(f"   Técnico: {score_tec:.1f}/100 (Confiança: {conf_tec:.1%}) → {dir_tec.upper()}")
#     print(f"   FINAL: {score_final:.1f}/100 (Confiança: {confianca_final:.1%})")
    
#     print(f"\n💡 JUSTIFICATIVAS IV:")
#     for j in just_iv:
#         print(f"   {j}")
    
#     print(f"\n💡 JUSTIFICATIVAS TÉCNICAS:")
#     for j in just_tec:
#         print(f"   {j}")
    
#     print(f"\n🎯 ESTRUTURA RECOMENDADA:")
#     print(f"   {estrutura}")
#     for j in just_estrutura:
#         print(f"   → {j}")
    
#     if score_final >= SCORE_MINIMO_OPERACAO and confianca_final >= CONFIANCA_MINIMA:
#         print(f"\n✅ OPERAÇÃO RECOMENDADA (Score: {score_final:.1f}, Conf: {confianca_final:.1%})")
#         print('='*70)
        
#         return {
#             'ticker': ticker_sa,
#             'preco': round(preco_atual, 2),
#             'estrutura': estrutura,
#             'score_final': round(score_final, 1),
#             'confianca': round(confianca_final, 3),
#             'score_iv': round(score_iv, 1),
#             'score_tecnico': round(score_tec, 1),
#             'direcao_iv': dir_iv,
#             'direcao_tecnica': dir_tec,
#             'iv_rank': converter_para_float(vol_info.get('iv_rank')),
#             'iv_percentil': converter_para_float(vol_info.get('iv_percentil')),
#             'justificativas': just_iv + just_tec + just_estrutura
#         }
#     else:
#         print(f"\n⏸️ AGUARDAR - Não atinge critérios mínimos")
#         print(f"   (Score: {score_final:.1f}/{SCORE_MINIMO_OPERACAO}, Conf: {confianca_final:.1%}/{CONFIANCA_MINIMA:.1%})")
#         print('='*70)
#         return None

# def analisar_multiplos_ativos(lista_ativos):
#     """
#     Processa lista completa com sistema ultra assertivo.
#     """
#     print(f"\n{'='*70}")
#     print(f"🚀 ANÁLISE ULTRA ASSERTIVA")
#     print(f"{'='*70}")
#     print(f"Total de ativos: {len(lista_ativos)}")
#     print(f"Score mínimo: {SCORE_MINIMO_OPERACAO}/100")
#     print(f"Confiança mínima: {CONFIANCA_MINIMA:.1%}")
#     print(f"{'='*70}\n")
    
#     vol_data = carregar_dados_volatilidade()
    
#     alertas_por_tipo = {
#         "Alta_Confianca": [],
#         "Venda_Premium": [],
#         "Compra_Alavancada": [],
#         "Spreads": [],
#         "Neutras": []
#     }
    
#     resultados = []
    
#     for idx, ticker in enumerate(lista_ativos, 1):
#         print(f"\n[{idx}/{len(lista_ativos)}]")
#         try:
#             res = analisar_ativo_completo(ticker, vol_data)
            
#             if res:
#                 if res['confianca'] >= 0.85:
#                     alertas_por_tipo["Alta_Confianca"].append((ticker, res['preco'], res))
                
#                 if 'VENDA COBERTA' in res['estrutura']:
#                     alertas_por_tipo["Venda_Premium"].append((ticker, res['preco'], res))
#                 elif 'COMPRA' in res['estrutura'] and 'SECO' in res['estrutura']:
#                     alertas_por_tipo["Compra_Alavancada"].append((ticker, res['preco'], res))
#                 elif 'SPREAD' in res['estrutura']:
#                     alertas_por_tipo["Spreads"].append((ticker, res['preco'], res))
#                 else:
#                     alertas_por_tipo["Neutras"].append((ticker, res['preco'], res))
                
#                 resultados.append(res)
            
#             time.sleep(1)
        
#         except Exception as e:
#             print(f"❌ Erro em {ticker}: {e}")
    
#     print(f"\n{'='*70}")
#     print("📊 RESUMO FINAL")
#     print(f"{'='*70}")
#     print(f"Ativos analisados: {len(lista_ativos)}")
#     print(f"Operações recomendadas: {len(resultados)}")
#     print(f"   → Alta confiança (≥85%): {len(alertas_por_tipo['Alta_Confianca'])}")
#     print(f"   → Venda de Prêmio: {len(alertas_por_tipo['Venda_Premium'])}")
#     print(f"   → Compra Alavancada: {len(alertas_por_tipo['Compra_Alavancada'])}")
#     print(f"   → Spreads: {len(alertas_por_tipo['Spreads'])}")
#     print(f"   → Neutras/Lateral: {len(alertas_por_tipo['Neutras'])}")
#     print(f"{'='*70}\n")
    
#     if resultados:
#         resultados_ordenados = sorted(resultados, key=lambda x: (x['confianca'], x['score_final']), reverse=True)
        
#         print("🏆 TOP 5 MELHORES OPORTUNIDADES:")
#         print(f"{'='*70}")
#         for i, res in enumerate(resultados_ordenados[:5], 1):
#             print(f"\n{i}. {res['ticker']} - R$ {res['preco']:.2f}")
#             print(f"   Estrutura: {res['estrutura']}")
#             print(f"   Score: {res['score_final']:.1f}/100 | Confiança: {res['confianca']:.1%}")
#             print(f"   IV: {res['score_iv']:.1f} ({res['direcao_iv']}) | Técnico: {res['score_tecnico']:.1f} ({res['direcao_tecnica']})")
#             if res['iv_rank']:
#                 print(f"   IV Rank: {res['iv_rank']:.1f}% | IV Percentil: {res['iv_percentil']:.1f}%")
#         print(f"\n{'='*70}\n")
    
#     if resultados:
#         print("📧 Enviando alertas...")
        
#         sinais_compra = alertas_por_tipo['Compra_Alavancada'] + [
#             item for item in alertas_por_tipo['Venda_Premium'] 
#             if 'PUT' in item[2].get('estrutura', '')
#         ]
        
#         sinais_venda = [
#             item for item in alertas_por_tipo['Venda_Premium']
#             if 'CALL' in item[2].get('estrutura', '')
#         ]
        
#         try:
#             enviar_alerta_consolidado(alertas_por_tipo)
#             enviar_relatorio_final(
#                 total_ativos=len(lista_ativos),
#                 sinais_compra=sinais_compra,
#                 sinais_venda=sinais_venda,
#                 erros=[]
#             )
#             print("✅ Alertas enviados com sucesso!")
#         except Exception as e:
#             print(f"⚠️ Erro ao enviar alertas: {e}")
#     else:
#         print("📭 Nenhuma operação atingiu os critérios mínimos hoje.")
#         print("💡 Sugestão: Revise os critérios ou aguarde melhores configurações de mercado.")
    
#     return resultados


# def analise_rapida(ticker, vol_data=None):
#     """
#     Análise rápida de um único ativo.
#     Útil para testes e verificações pontuais.
#     """
#     if vol_data is None:
#         vol_data = carregar_dados_volatilidade()
    
#     ticker_sa = ticker if '.SA' in ticker else f"{ticker}.SA"
#     return analisar_ativo_completo(ticker_sa, vol_data)


# def exportar_resultados(resultados, nome_arquivo='resultados_analise.json'):
#     """
#     Exporta os resultados da análise para um arquivo JSON.
#     """
#     if not resultados:
#         print("⚠️ Nenhum resultado para exportar.")
#         return
    
#     dados_exportacao = {
#         'data_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
#         'total_operacoes': len(resultados),
#         'score_minimo_usado': SCORE_MINIMO_OPERACAO,
#         'confianca_minima_usada': CONFIANCA_MINIMA,
#         'operacoes': resultados
#     }
    
#     with open(nome_arquivo, 'w', encoding='utf-8') as f:
#         json.dump(dados_exportacao, f, indent=2, ensure_ascii=False)
    
#     print(f"✅ Resultados exportados para: {nome_arquivo}")


# if __name__ == '__main__':
#     print("="*70)
#     print("🎯 SISTEMA DE ANÁLISE ULTRA ASSERTIVA")
#     print("="*70)
#     print("\nEste script deve ser importado e usado via main.py")
#     print("Exemplo de uso:")
#     print("""
#     from analise import analisar_multiplos_ativos
    
#     tickers = ['PETR4.SA', 'VALE3.SA', 'BBDC4.SA']
#     resultados = analisar_multiplos_ativos(tickers)
#     """)
#     print("="*70)

import yfinance as yf
import pandas as pd
import ta
import numpy as np
from alertas import enviar_alerta_consolidado, enviar_relatorio_final
import time
import json

SCORE_MINIMO_OPERACAO = 85
CONFIANCA_MINIMA = 0.88
ADX_MINIMO_TENDENCIA = 25
IV_RANK_ALTO = 65 
IV_RANK_BAIXO = 30 

def carregar_dados_volatilidade():
    """Carrega dados consolidados do scraper."""
    try:
        with open('dados_mercado_consolidado.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            print(f"✅ Dados OpLab carregados: {len(dados)} tickers")
            return dados
    except Exception as e:
        print(f"⚠️ Sem dados OpLab. Análise limitada. ({e})")
        return {}

def converter_para_float(valor):
    """Converte strings para float com tratamento robusto."""
    if valor in ['N/A', '-', None, '']:
        return None
    try:
        return float(str(valor).replace(',', '.').replace('%', '').replace('R$', '').strip())
    except:
        return None

def calcular_score_iv_elite(vol_info):
    """
    Scoring ELITE de volatilidade implícita.
    Foco: convergência IV Rank + IV Percentil para máxima assertividade.
    """
    ivr = converter_para_float(vol_info.get('iv_rank'))
    ivp = converter_para_float(vol_info.get('iv_percentil'))
    vi = converter_para_float(vol_info.get('volatilidade_implicita'))
    
    score = 0
    confianca = 0.5
    direcao = 'neutro'
    justificativas = []
    
    if ivr is None or ivp is None or vi is None:
        return 0, 0.2, 'neutro', ['❌ Dados de IV incompletos - REJEITADO']
    
    divergencia = abs(ivr - ivp)
    
    if ivr >= IV_RANK_ALTO and ivp >= 65:
        if divergencia < 15:
            score = 90
            confianca = 0.92
            direcao = 'venda_premium'
            justificativas.append(f'🔥 CONVERGÊNCIA PERFEITA: IVR={ivr:.1f}% / IVP={ivp:.1f}% (diff={divergencia:.1f}%)')
            justificativas.append(f'💰 VI={vi:.1f}% - PRÊMIOS EXTREMAMENTE GORDOS')
        else:
            score = 70
            confianca = 0.75
            direcao = 'venda_premium'
            justificativas.append(f'⚠️ IVR alto mas DIVERGÊNCIA com IVP (diff={divergencia:.1f}%) - Cautela')
    
    elif ivr <= IV_RANK_BAIXO and ivp <= 35:
        if divergencia < 15:
            score = 90
            confianca = 0.92
            direcao = 'compra_premium'
            justificativas.append(f'🔥 CONVERGÊNCIA PERFEITA: IVR={ivr:.1f}% / IVP={ivp:.1f}% (diff={divergencia:.1f}%)')
            justificativas.append(f'💎 VI={vi:.1f}% - OPÇÕES EXTREMAMENTE BARATAS')
        else:
            score = 70
            confianca = 0.75
            direcao = 'compra_premium'
            justificativas.append(f'⚠️ IVR baixo mas DIVERGÊNCIA com IVP (diff={divergencia:.1f}%) - Cautela')
    
    else:
        score = 30
        confianca = 0.4
        justificativas.append(f'○ IV Rank neutro ({ivr:.1f}%) - NÃO É OPORTUNIDADE EXCEPCIONAL')
    
    return score, confianca, direcao, justificativas

def calcular_score_tecnico_elite(df):
    """
    Scoring técnico ELITE com múltiplas validações.
    Foco: apenas tendências confirmadas com momentum forte.
    """
    if len(df) < 200:
        return 0, 0.2, 'neutro', {}, ['❌ Histórico insuficiente']
    
    cp = df['Close'].squeeze()
    hp = df['High'].squeeze()
    lp = df['Low'].squeeze()
    vol = df['Volume'].squeeze()
    
    m9 = ta.trend.EMAIndicator(cp, 9).ema_indicator()
    m21 = ta.trend.EMAIndicator(cp, 21).ema_indicator()
    m50 = ta.trend.EMAIndicator(cp, 50).ema_indicator()
    m200 = ta.trend.EMAIndicator(cp, 200).ema_indicator()
    
    rsi = ta.momentum.RSIIndicator(cp, 14).rsi()
    adx_obj = ta.trend.ADXIndicator(hp, lp, cp, 14)
    adx = adx_obj.adx()
    
    macd_obj = ta.trend.MACD(cp)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()
    macd_hist = macd_obj.macd_diff()
    
    sma20 = cp.rolling(20).mean()
    std20 = cp.rolling(20).std()
    z_score = ((cp - sma20) / std20)
    
    preco = cp.iloc[-1]
    rsi_atual = rsi.iloc[-1]
    adx_atual = adx.iloc[-1]
    macd_hist_atual = macd_hist.iloc[-1]
    z_score_atual = z_score.iloc[-1]
    
    m9_atual = m9.iloc[-1]
    m21_atual = m21.iloc[-1]
    m50_atual = m50.iloc[-1]
    m200_atual = m200.iloc[-1]
    
    vol_media = vol.rolling(20).mean().iloc[-1]
    volume_forte = df['Volume'].iloc[-1] > vol_media * 1.2
    
    score = 0
    confianca = 0.5
    direcao = 'neutro'
    justificativas = []
    
    alta_perfeita = preco > m9_atual > m21_atual > m50_atual > m200_atual
    baixa_perfeita = preco < m9_atual < m21_atual < m50_atual < m200_atual
    
    dados_tech = {
        'rsi': rsi_atual,
        'adx': adx_atual,
        'macd_hist': macd_hist_atual,
        'z_score': z_score_atual,
        'alta_perfeita': alta_perfeita,
        'baixa_perfeita': baixa_perfeita,
        'volume_forte': volume_forte,
        'preco': preco
    }
    
    if rsi_atual > 80 or z_score_atual > 3.0:
        score = 40
        confianca = 0.5
        direcao = 'baixa'
        justificativas.append(f'⚠️ SOBRECOMPRA EXTREMA: RSI={rsi_atual:.1f}, Z={z_score_atual:.2f}')
        justificativas.append('🚨 RISCO ALTO: Ativo muito esticado para cima')
        dados_tech['extremo'] = 'sobrecompra'
        return score, confianca, direcao, dados_tech, justificativas
    
    elif rsi_atual < 20 or z_score_atual < -3.0:
        score = 40 
        confianca = 0.5
        direcao = 'alta'
        justificativas.append(f'⚠️ SOBREVENDA EXTREMA: RSI={rsi_atual:.1f}, Z={z_score_atual:.2f}')
        justificativas.append('🚨 RISCO ALTO: Ativo muito esticado para baixo')
        dados_tech['extremo'] = 'sobrevenda'
        return score, confianca, direcao, dados_tech, justificativas
    
    if alta_perfeita:
        score = 50 
        direcao = 'alta'
        justificativas.append('✓ Tendência de alta: Todas médias alinhadas')
        
        if adx_atual >= ADX_MINIMO_TENDENCIA:
            score += 20
            confianca += 0.15
            justificativas.append(f'✓ ADX={adx_atual:.1f} - Tendência FORTE confirmada')
        else:
            justificativas.append(f'⚠️ ADX={adx_atual:.1f} - Tendência FRACA (abaixo de {ADX_MINIMO_TENDENCIA})')
            confianca -= 0.10
        
        if macd_hist_atual > 0 and macd_hist_atual > macd_hist.iloc[-2]:
            score += 15
            confianca += 0.10
            justificativas.append('✓ MACD positivo e acelerando')
        else:
            justificativas.append('⚠️ MACD não confirma momentum')
        
        if 40 <= rsi_atual <= 70:
            score += 15
            confianca += 0.10
            justificativas.append(f'✓ RSI={rsi_atual:.1f} - Zona saudável')
        elif rsi_atual > 70:
            score -= 10
            confianca -= 0.10
            justificativas.append(f'⚠️ RSI={rsi_atual:.1f} - SOBRECOMPRADO (risco de correção)')
        
        if volume_forte:
            score += 10
            confianca += 0.08
            justificativas.append('✓ Volume forte confirma movimento')
    
    elif baixa_perfeita:
        score = 50 
        direcao = 'baixa'
        justificativas.append('✓ Tendência de baixa: Todas médias alinhadas')
        
        if adx_atual >= ADX_MINIMO_TENDENCIA:
            score += 20
            confianca += 0.15
            justificativas.append(f'✓ ADX={adx_atual:.1f} - Tendência FORTE confirmada')
        else:
            justificativas.append(f'⚠️ ADX={adx_atual:.1f} - Tendência FRACA')
            confianca -= 0.10
        
        if macd_hist_atual < 0 and macd_hist_atual < macd_hist.iloc[-2]:
            score += 15
            confianca += 0.10
            justificativas.append('✓ MACD negativo e acelerando')
        else:
            justificativas.append('⚠️ MACD não confirma momentum')
        
        if 30 <= rsi_atual <= 60:
            score += 15
            confianca += 0.10
            justificativas.append(f'✓ RSI={rsi_atual:.1f} - Zona saudável')
        elif rsi_atual < 30:
            score -= 10
            confianca -= 0.10
            justificativas.append(f'⚠️ RSI={rsi_atual:.1f} - SOBREVENDIDO (risco de repique)')
        
        if volume_forte:
            score += 10
            confianca += 0.08
            justificativas.append('✓ Volume forte confirma movimento')
    
    else:
        score = 20
        confianca = 0.3
        justificativas.append('❌ SEM TENDÊNCIA CLARA: Médias embaralhadas')
        justificativas.append('💡 Aguardar definição de direção')
    
    confianca = max(0, min(1, confianca))
    
    return score, confianca, direcao, dados_tech, justificativas

def determinar_estrutura_elite(
    score_iv, conf_iv, dir_iv,
    score_tec, conf_tec, dir_tec,
    vol_info, tech, just_tec
):
    ivr = converter_para_float(vol_info.get('iv_rank')) or 0
    ivp = converter_para_float(vol_info.get('iv_percentil')) or 0

    score_final = (score_iv * 0.55) + (score_tec * 0.45)
    confianca_final = (conf_iv * 0.55) + (conf_tec * 0.45)

    rsi = tech.get('rsi', 50)
    adx = tech.get('adx', 0)
    z_score = tech.get('z_score', 0)

    motivos_rejeicao = []
    justificativas = []

    if tech.get('extremo') == 'sobrecompra' and ivr < IV_RANK_ALTO:
        motivos_rejeicao.append(
            f"❌ SOBRECOMPRA extrema (RSI={rsi:.1f}, Z={z_score:.2f}) sem IV alta"
        )

    if tech.get('extremo') == 'sobrevenda' and ivr < IV_RANK_ALTO:
        motivos_rejeicao.append(
            f"❌ SOBREVENDA extrema (RSI={rsi:.1f}, Z={z_score:.2f}) sem IV alta"
        )

    if adx < ADX_MINIMO_TENDENCIA:
        motivos_rejeicao.append(
            f"❌ ADX fraco ({adx:.1f}) — tendência não confiável"
        )

    if abs(ivr - ivp) > 20:
        motivos_rejeicao.append(
            f"❌ Divergência IV (IVR={ivr:.1f}% / IVP={ivp:.1f}%)"
        )

    if motivos_rejeicao:
        return {
            'status': 'REJEITADO',
            'estrutura': 'AGUARDAR',
            'score_final': round(score_final, 1),
            'confianca_final': round(confianca_final, 3),
            'motivos_rejeicao': motivos_rejeicao
        }

    if tech.get('alta_perfeita') and dir_iv == 'compra_premium' and ivr <= IV_RANK_BAIXO:
        justificativas.append("🔥 BULL CALL SPREAD — Alta + IV Baixa")
        return {
            'status': 'APROVADO',
            'estrutura': 'BULL CALL SPREAD',
            'score_final': round(score_final + 10, 1),
            'confianca_final': min(0.95, round(confianca_final + 0.08, 3)),
            'justificativas': justificativas
        }

    if tech.get('alta_perfeita') and dir_iv == 'venda_premium' and ivr >= IV_RANK_ALTO:
        justificativas.append("🔥 VENDA DE PUT COBERTA — Alta + Prêmio Gordo")
        return {
            'status': 'APROVADO',
            'estrutura': 'VENDA PUT COBERTA',
            'score_final': round(score_final + 12, 1),
            'confianca_final': min(0.96, round(confianca_final + 0.10, 3)),
            'justificativas': justificativas
        }

    return {
        'status': 'REJEITADO',
        'estrutura': 'AGUARDAR',
        'score_final': round(score_final, 1),
        'confianca_final': round(confianca_final, 3),
        'motivos_rejeicao': [
            "❌ Nenhuma configuração ELITE identificada",
            f"IV Rank={ivr:.1f}%, ADX={adx:.1f}, RSI={rsi:.1f}"
        ]
    }

def analisar_ativo_elite(ticker_sa, vol_data):
    """Análise ELITE de um ativo com explicação de rejeição."""
    print(f"\n{'='*70}")
    print(f"📊 Análise Elite: {ticker_sa}")
    print('-'*70)
    
    df = yf.download(ticker_sa, period="1y", interval="1d",
                     auto_adjust=False, progress=False)

    if df.empty or len(df) < 200:
        print("❌ Dados insuficientes para análise técnica")
        print('=' * 70)
        return {
            'ticker': ticker_sa,
            'status': 'REJEITADO',
            'motivos': ['Histórico insuficiente (<200 candles)']
        }

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    ticker_limpo = ticker_sa.replace('.SA', '')
    vol_info = vol_data.get(ticker_limpo)

    if not vol_info:
        print("❌ Sem dados de volatilidade (OpLab)")
        print('=' * 70)
        return {
            'ticker': ticker_sa,
            'status': 'REJEITADO',
            'motivos': ['Dados de volatilidade indisponíveis']
        }

    # =========================
    # SCORES
    # =========================
    score_iv, conf_iv, dir_iv, just_iv = calcular_score_iv_elite(vol_info)
    score_tec, conf_tec, dir_tec, tech, just_tec = calcular_score_tecnico_elite(df)

    decisao = determinar_estrutura_elite(
        score_iv, conf_iv, dir_iv,
        score_tec, conf_tec, dir_tec,
        vol_info, tech, just_tec
    )

    preco_atual = tech.get('preco', df['Close'].iloc[-1])

    # =========================
    # PRINT PADRÃO
    # =========================
    print(f"\n📈 PREÇO: R$ {preco_atual:.2f}")

    print(f"\n🎯 SCORES:")
    print(f"   IV: {score_iv:.1f}/100 (Conf: {conf_iv:.1%}) → {dir_iv.upper()}")
    print(f"   Técnico: {score_tec:.1f}/100 (Conf: {conf_tec:.1%}) → {dir_tec.upper()}")

    print(f"\n💡 JUSTIFICATIVAS IV:")
    for j in just_iv:
        print(f"   {j}")

    print(f"\n💡 JUSTIFICATIVAS TÉCNICAS:")
    for j in just_tec:
        print(f"   {j}")

    # =========================
    # REJEIÇÃO EXPLICADA
    # =========================
    if decisao['status'] == 'REJEITADO':
        print(f"\n❌ ATIVO REJEITADO")
        for m in decisao.get('motivos_rejeicao', []):
            print(f"   {m}")

        print(f"\n⏸️ SCORE FINAL: {decisao['score_final']:.1f}/{SCORE_MINIMO_OPERACAO}")
        print(f"⏸️ CONFIANÇA: {decisao['confianca_final']:.1%}/{CONFIANCA_MINIMA:.1%}")
        print('=' * 70)

        return {
            'ticker': ticker_sa,
            'status': 'REJEITADO',
            'score_final': decisao['score_final'],
            'confianca': decisao['confianca_final'],
            'motivos': decisao.get('motivos_rejeicao', [])
        }

    # =========================
    # APROVAÇÃO FINAL
    # =========================
    score_final = decisao['score_final']
    conf_final = decisao['confianca_final']
    estrutura = decisao['estrutura']

    print(f"\n🎯 ESTRUTURA:")
    print(f"   {estrutura}")
    for j in decisao.get('justificativas', []):
        print(f"   {j}")

    if score_final >= SCORE_MINIMO_OPERACAO and conf_final >= CONFIANCA_MINIMA:
        print(f"\n✅ OPORTUNIDADE ELITE IDENTIFICADA!")
        print(f"   Score: {score_final:.1f}/{SCORE_MINIMO_OPERACAO}")
        print(f"   Conf: {conf_final:.1%}")
        print('=' * 70)

        return {
            'ticker': ticker_sa,
            'status': 'APROVADO',
            'preco': round(preco_atual, 2),
            'estrutura': estrutura,
            'score_final': round(score_final, 1),
            'confianca': round(conf_final, 3),
            'score_iv': round(score_iv, 1),
            'score_tecnico': round(score_tec, 1),
            'direcao_iv': dir_iv,
            'direcao_tecnica': dir_tec,
            'iv_rank': converter_para_float(vol_info.get('iv_rank')),
            'iv_percentil': converter_para_float(vol_info.get('iv_percentil')),
            'rsi': tech.get('rsi'),
            'adx': tech.get('adx'),
            'justificativas': just_iv + just_tec + decisao.get('justificativas', [])
        }

    print(f"\n⏸️ REPROVADO NO FUNIL FINAL")
    print(f"   Score: {score_final:.1f}/{SCORE_MINIMO_OPERACAO}")
    print(f"   Conf: {conf_final:.1%}/{CONFIANCA_MINIMA:.1%}")
    print('=' * 70)

    return {
        'ticker': ticker_sa,
        'status': 'REJEITADO',
        'score_final': score_final,
        'confianca': conf_final,
        'motivos': ['Não atingiu critérios ELITE finais']
    }

def analisar_multiplos_ativos(lista_ativos):
    print(f"🚀 INICIANDO SCANNER DE ELITE (Rigor: {SCORE_MINIMO_OPERACAO})")

    vol_data = carregar_dados_volatilidade()
    aprovados = []
    rejeitados = []

    for ticker in lista_ativos:
        try:
            res = analisar_ativo_elite(ticker, vol_data)

            if not res:
                continue

            if res.get('status') == 'APROVADO':
                aprovados.append(res)
            else:
                rejeitados.append(res)

            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Erro em {ticker}: {e}")

    print("\n📊 RESUMO DO SCANNER")
    print(f"   ✅ Aprovados: {len(aprovados)}")
    print(f"   ❌ Rejeitados: {len(rejeitados)}")

    if rejeitados:
        print("\n❌ REJEIÇÕES (RESUMO):")
        for r in rejeitados:
            motivos = r.get('motivos', [])
            if motivos:
                print(f"   {r['ticker']}: {motivos[0]}")

    return aprovados, rejeitados


if __name__ == '__main__':
    analisar_multiplos_ativos(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA', 'ITUB4.SA'])