import smtplib
from email.message import EmailMessage
import configparser
from datetime import datetime

def enviar_alerta_consolidado(alertas_por_tipo):
    """
    Envia alertas consolidados aproveitando TODOS os novos campos do sistema elite:
    - Regime de Mercado (ADX)
    - Volatilidade Relativa (IV/HV)
    - Probabilidade de Lucro (POP)
    - Setup de Opções (strikes, delta)
    """
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
        email_remetente = config.get("email", "remetente", fallback="")
        senha_app = config.get("email", "senha", fallback="")
        email_destinatario = config.get("email", "destinatario", fallback="")
    except Exception as e:
        print(f"\n❌ ERRO: Falha ao ler 'config.ini': {e}")
        return False

    if not email_remetente or email_remetente == "seuemail@gmail.com":
        print("\n⚠️ AVISO: E-mail não configurado no config.ini.")
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    info_setups = {
        "Alta_Confianca": {
            "emoji": "🔥", 
            "titulo": "OPORTUNIDADES ELITE (≥75%)", 
            "descricao": "Setups com máxima probabilidade de lucro"
        },
        "Venda_Premium": {
            "emoji": "💰", 
            "titulo": "VENDA DE PRÊMIO", 
            "descricao": "IV alta - Prêmios gordos disponíveis"
        },
        "Compra_Alavancada": {
            "emoji": "🚀", 
            "titulo": "COMPRA ALAVANCADA", 
            "descricao": "IV baixa - Opções baratas"
        },
    }

    total_enviados = 0

    for tipo, alertas in alertas_por_tipo.items():
        if not alertas: 
            continue

        setup = info_setups.get(tipo, {
            "emoji": "🔍", 
            "titulo": tipo.upper(), 
            "descricao": "Análise profissional"
        })
        emoji = setup["emoji"]
        
        corpo = f"""{emoji} ALERTAS: {setup['titulo']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ANÁLISE PROFISSIONAL DE OPÇÕES v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Data/Hora: {data_hora}
📊 Ativos Elite: {len(alertas)}
💡 {setup['descricao']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        for i, (ticker, preco, dados) in enumerate(alertas, 1):
            ticker_limpo = ticker.replace('.SA', '')
            
            # Campos básicos
            score_final = dados.get('score_final', 0)
            confianca = dados.get('confianca', 0)
            estrategia = dados.get('estrategia', dados.get('estrutura', 'N/A'))
            
            # NOVOS campos do sistema elite
            regime = dados.get('regime', 'N/A')
            adx = dados.get('adx', 0)
            edge_type = dados.get('edge_type', 'N/A')
            iv_hv_ratio = dados.get('iv_hv_ratio')
            setup_opcoes = dados.get('setup_opcoes', {})
            
            # Cabeçalho do ativo
            corpo += f"\n{'═'*60}\n"
            corpo += f"{i}. {ticker_limpo} - R$ {preco:,.2f}\n"
            corpo += f"{'═'*60}\n\n"
            
            # Regime de Mercado
            corpo += f"📈 REGIME: {regime}"
            if adx > 0:
                corpo += f" (ADX: {adx:.1f})"
            corpo += "\n"
            
            # Volatilidade Relativa
            corpo += f"💹 VOLATILIDADE: "
            if iv_hv_ratio:
                corpo += f"IV/HV = {iv_hv_ratio:.2f} → {edge_type}\n"
                if iv_hv_ratio >= 1.2:
                    corpo += f"   • VI está {((iv_hv_ratio - 1) * 100):.0f}% ACIMA da HV (prêmios caros)\n"
                elif iv_hv_ratio <= 0.8:
                    corpo += f"   • VI está {((1 - iv_hv_ratio) * 100):.0f}% ABAIXO da HV (prêmios baratos)\n"
            else:
                corpo += f"{edge_type}\n"
            
            # IV Rank/Percentil (se disponível)
            if 'iv_rank' in dados and dados['iv_rank']:
                corpo += f"   • IV Rank: {dados['iv_rank']:.1f}%"
                if 'iv_percentil' in dados and dados['iv_percentil']:
                    corpo += f" | IV Percentil: {dados['iv_percentil']:.1f}%\n"
                else:
                    corpo += "\n"
            
            # Estratégia
            corpo += f"\n🎯 ESTRATÉGIA: {estrategia}\n"
            corpo += f"   Score: {score_final:.1f}/100 | Confiança: {confianca:.1%}\n"
            
            # Setup de Opções (NOVO - muito útil!)
            if setup_opcoes:
                corpo += f"\n📊 SETUP DE OPÇÕES:\n"
                
                # Strikes e POP
                if 'pop' in setup_opcoes:
                    corpo += f"   • POP (Prob. Lucro): {setup_opcoes['pop']:.1f}%\n"
                
                if 'strike_sugerido' in setup_opcoes:
                    corpo += f"   • Strike: R$ {setup_opcoes['strike_sugerido']:.2f}"
                    if 'delta_aproximado' in setup_opcoes:
                        corpo += f" (Delta: {setup_opcoes['delta_aproximado']})\n"
                    else:
                        corpo += "\n"
                
                # Spreads (calls/puts)
                if 'strike_compra' in setup_opcoes:
                    corpo += f"   • Compra: R$ {setup_opcoes['strike_compra']:.2f}\n"
                if 'strike_venda' in setup_opcoes:
                    corpo += f"   • Vende: R$ {setup_opcoes['strike_venda']:.2f}\n"
                
                # Iron Condor
                if 'put_venda' in setup_opcoes:
                    corpo += f"   • PUT: Vende {setup_opcoes['put_venda']:.2f} / Compra {setup_opcoes.get('put_compra', 'N/A'):.2f}\n"
                if 'call_venda' in setup_opcoes:
                    corpo += f"   • CALL: Vende {setup_opcoes['call_venda']:.2f} / Compra {setup_opcoes.get('call_compra', 'N/A'):.2f}\n"
                
                # Risco/Retorno
                if 'max_loss' in setup_opcoes:
                    corpo += f"   • Risco Máx: {setup_opcoes['max_loss']}\n"
                if 'max_gain' in setup_opcoes:
                    corpo += f"   • Ganho Máx: {setup_opcoes['max_gain']}\n"
            
            # Indicadores técnicos
            if 'rsi' in dados or 'adx' in dados:
                corpo += f"\n📊 INDICADORES:\n"
                if 'rsi' in dados:
                    rsi = dados['rsi']
                    corpo += f"   • RSI: {rsi:.1f}"
                    if rsi < 30:
                        corpo += " (Sobrevenda)"
                    elif rsi > 70:
                        corpo += " (Sobrecompra)"
                    corpo += "\n"
                
                if 'adx' in dados and dados['adx'] > 0:
                    corpo += f"   • ADX: {dados['adx']:.1f}"
                    if dados['adx'] >= 25:
                        corpo += " (Tendência forte)"
                    else:
                        corpo += " (Mercado lateral)"
                    corpo += "\n"
            
            # Justificativas (top 4 mais importantes)
            justificativas = dados.get('justificativas', [])
            if justificativas:
                corpo += f"\n💡 POR QUE OPERAR:\n"
                for just in justificativas[:4]:
                    # Remover emojis duplicados se já tiver no texto
                    just_limpo = just.strip()
                    corpo += f"   {just_limpo}\n"
            
            corpo += "\n"

        # Rodapé com avisos importantes
        corpo += f"\n{'═'*60}\n"
        corpo += "⚠️ CHECKLIST PRÉ-OPERAÇÃO:\n"
        corpo += "   □ Verificar liquidez da série no book de opções\n"
        corpo += "   □ Conferir eventos próximos (resultados, dividendos)\n"
        corpo += "   □ Validar strikes disponíveis com open interest\n"
        corpo += "   □ Calcular margem de garantia necessária\n"
        corpo += "   □ Tamanho de posição: máximo 5% do capital\n"
        corpo += f"{'═'*60}\n"

        # Envio do email
        msg = EmailMessage()
        msg["Subject"] = f"{emoji} {len(alertas)} Oportunidade(s) Elite - {setup['titulo']}"
        msg["From"] = email_remetente
        msg["To"] = email_destinatario
        msg.set_content(corpo)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(email_remetente, senha_app)
                smtp.send_message(msg)
            print(f"✅ E-mail de {tipo} enviado com {len(alertas)} ativo(s)!")
            total_enviados += 1
        except Exception as e:
            print(f"❌ Erro no envio de {tipo}: {e}")

    return total_enviados > 0


def enviar_relatorio_final(total_ativos, sinais_compra, sinais_venda, erros):
    """
    Relatório final consolidado com estatísticas avançadas.
    Agora com breakdown por regime, estratégia e POP médio.
    """
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
        email_remetente = config.get("email", "remetente", fallback="")
        senha_app = config.get("email", "senha", fallback="")
        email_destinatario = config.get("email", "destinatario", fallback="")
    except:
        return False

    if not email_remetente or email_remetente == "seuemail@gmail.com":
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    
    # Combinar todos os sinais
    todas_operacoes = sinais_compra + sinais_venda
    total_sinais = len(todas_operacoes)
    
    # Calcular estatísticas
    if todas_operacoes:
        # Confiança média
        confiancas = [op.get('confianca', 0) for op in todas_operacoes if isinstance(op, dict)]
        if not confiancas:  # Fallback para formato antigo (tuplas)
            confiancas = [op[2].get('confianca', 0) for op in todas_operacoes if isinstance(op, tuple) and len(op) > 2]
        confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0
        
        # POP médio (NOVO)
        pops = []
        for op in todas_operacoes:
            if isinstance(op, dict):
                setup = op.get('setup_opcoes', {})
            elif isinstance(op, tuple) and len(op) > 2:
                setup = op[2].get('setup_opcoes', {})
            else:
                setup = {}
            
            if 'pop' in setup:
                pops.append(setup['pop'])
        
        pop_medio = sum(pops) / len(pops) if pops else 0
        
        # Breakdown por regime (NOVO)
        regimes = {}
        for op in todas_operacoes:
            if isinstance(op, dict):
                regime = op.get('regime', 'N/A')
            elif isinstance(op, tuple) and len(op) > 2:
                regime = op[2].get('regime', 'N/A')
            else:
                regime = 'N/A'
            
            regimes[regime] = regimes.get(regime, 0) + 1
        
        # Breakdown por estratégia (NOVO)
        estrategias = {}
        for op in todas_operacoes:
            if isinstance(op, dict):
                est = op.get('estrategia', op.get('estrutura', 'N/A'))
            elif isinstance(op, tuple) and len(op) > 2:
                est = op[2].get('estrategia', op[2].get('estrutura', 'N/A'))
            else:
                est = 'N/A'
            
            estrategias[est] = estrategias.get(est, 0) + 1
    else:
        confianca_media = 0
        pop_medio = 0
        regimes = {}
        estrategias = {}
    
    # Montar corpo do email
    corpo = f"""📊 RELATÓRIO FINAL - ANÁLISE PROFISSIONAL v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ CONCLUSÃO DA VARREDURA ELITE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Data/Hora: {data_hora}
🔍 Ativos Analisados: {total_ativos}
✅ Oportunidades Elite: {total_sinais}
"""
    
    if total_sinais > 0:
        corpo += f"\n📈 ESTATÍSTICAS:\n"
        corpo += f"   • Confiança Média: {confianca_media:.1%}\n"
        
        if pop_medio > 0:
            corpo += f"   • POP Médio: {pop_medio:.1f}%\n"
        
        # Taxa de aprovação
        taxa_aprovacao = (total_sinais / total_ativos * 100) if total_ativos > 0 else 0
        corpo += f"   • Taxa de Aprovação: {taxa_aprovacao:.1f}%\n"
        
        # Breakdown por regime
        if regimes:
            corpo += f"\n🎯 POR REGIME DE MERCADO:\n"
            for regime, count in sorted(regimes.items(), key=lambda x: x[1], reverse=True):
                corpo += f"   • {regime}: {count} operação(ões)\n"
        
        # Breakdown por estratégia
        if estrategias:
            corpo += f"\n💼 POR ESTRATÉGIA:\n"
            for est, count in sorted(estrategias.items(), key=lambda x: x[1], reverse=True):
                corpo += f"   • {est}: {count} operação(ões)\n"
        
        # Top 3 oportunidades
        corpo += f"\n🏆 TOP 3 OPORTUNIDADES:\n"
        
        # Ordenar por confiança
        ops_ordenadas = []
        for op in todas_operacoes:
            if isinstance(op, dict):
                ops_ordenadas.append(op)
            elif isinstance(op, tuple) and len(op) > 2:
                ops_ordenadas.append(op[2])
        
        ops_ordenadas.sort(key=lambda x: x.get('confianca', 0), reverse=True)
        
        for i, op in enumerate(ops_ordenadas[:3], 1):
            ticker = op.get('ticker', 'N/A').replace('.SA', '')
            preco = op.get('preco', 0)
            estrategia = op.get('estrategia', op.get('estrutura', 'N/A'))
            confianca = op.get('confianca', 0)
            
            corpo += f"   {i}. {ticker} - R$ {preco:.2f}\n"
            corpo += f"      {estrategia} (Conf: {confianca:.1%})\n"
    else:
        corpo += f"\n💡 ANÁLISE:\n"
        corpo += f"   Nenhuma oportunidade Elite identificada pelos filtros.\n"
        corpo += f"   Isso pode indicar:\n"
        corpo += f"   • Mercado em consolidação sem setups claros\n"
        corpo += f"   • Volatilidades em níveis neutros (IV/HV ≈ 1.0)\n"
        corpo += f"   • Tendências fracas (ADX < 25) sem extremos de RSI\n"
    
    if erros:
        corpo += f"\n❌ ERROS: {len(erros)}\n"
    
    corpo += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    corpo += "Sistema: Análise Profissional de Opções v2.0\n"
    corpo += "Critérios: Score ≥ 70/100 | Confiança ≥ 75%\n"
    corpo += "Metodologia: ADX Regime | IV/HV Ratio | POP Matemático\n"
    corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    # Configurar assunto do email
    msg = EmailMessage()
    if total_sinais == 0:
        msg["Subject"] = "📭 Scanner Concluído - Aguardar Setups"
    elif total_sinais <= 3:
        msg["Subject"] = f"✅ Scanner Concluído - {total_sinais} Oportunidade(s) Elite"
    else:
        msg["Subject"] = f"🔥 Scanner Concluído - {total_sinais} Oportunidades Elite!"
    
    msg["From"] = email_remetente
    msg["To"] = email_destinatario
    msg.set_content(corpo)

    # Enviar
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)
        print("✅ Relatório final enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar relatório final: {e}")
        return False


def enviar_alerta_individual(ticker, preco, dados, tipo_alerta="OPORTUNIDADE ELITE"):
    """
    Alerta individual ENRIQUECIDO com todos os dados do sistema elite.
    Ideal para alertas em tempo real ou notificações prioritárias.
    """
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
        email_remetente = config.get("email", "remetente", fallback="")
        senha_app = config.get("email", "senha", fallback="")
        email_destinatario = config.get("email", "destinatario", fallback="")
    except:
        return False

    if not email_remetente or email_remetente == "seuemail@gmail.com":
        return False

    ticker_limpo = ticker.replace('.SA', '')
    estrategia = dados.get('estrategia', dados.get('estrutura', 'N/A'))
    confianca = dados.get('confianca', 0)
    score = dados.get('score_final', dados.get('score', 0))
    
    # Novos campos
    regime = dados.get('regime', 'N/A')
    adx = dados.get('adx', 0)
    edge_type = dados.get('edge_type', 'N/A')
    iv_hv_ratio = dados.get('iv_hv_ratio')
    setup_opcoes = dados.get('setup_opcoes', {})

    corpo = f"""🚨 ALERTA INDIVIDUAL: {ticker_limpo}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 PREÇO ATUAL: R$ {preco:.2f}

📈 REGIME: {regime}"""

    if adx > 0:
        corpo += f" (ADX: {adx:.1f})"
    
    corpo += f"\n💹 VOLATILIDADE: {edge_type}"
    if iv_hv_ratio:
        corpo += f" (IV/HV: {iv_hv_ratio:.2f})"
    
    corpo += f"""

🎯 ESTRATÉGIA: {estrategia}
🔥 SCORE: {score:.1f}/100
📊 CONFIANÇA: {confianca:.1%}
"""

    # Setup de opções
    if setup_opcoes:
        corpo += "\n📊 SETUP DE OPÇÕES:\n"
        if 'pop' in setup_opcoes:
            corpo += f"   POP: {setup_opcoes['pop']:.1f}%\n"
        if 'strike_sugerido' in setup_opcoes:
            corpo += f"   Strike: R$ {setup_opcoes['strike_sugerido']:.2f}\n"
        if 'delta_aproximado' in setup_opcoes:
            corpo += f"   Delta: {setup_opcoes['delta_aproximado']}\n"

    corpo += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    corpo += "💡 JUSTIFICATIVAS\n"
    corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    justificativas = dados.get('justificativas', [])
    if justificativas:
        corpo += chr(10).join(f"{j}" for j in justificativas[:5])
    else:
        corpo += "Nenhuma justificativa disponível"

    corpo += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    corpo += "⚠️ Análise individual - Verifique liquidez antes de operar\n"
    corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    msg = EmailMessage()
    msg["Subject"] = f"🚨 {tipo_alerta}: {ticker_limpo} - {estrategia}"
    msg["From"] = email_remetente
    msg["To"] = email_destinatario
    msg.set_content(corpo)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)
        print(f"✅ Alerta individual de {ticker_limpo} enviado!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar alerta individual: {e}")
        return False