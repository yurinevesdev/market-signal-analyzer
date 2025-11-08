import smtplib
from email.message import EmailMessage
import configparser
from datetime import datetime


def enviar_alerta(ticker, tipo, preco, dados_adicionais=None):
    import smtplib
    from email.message import EmailMessage
    import configparser
    from datetime import datetime

    config = configparser.ConfigParser()
    config.read('config.ini')

    email_remetente = config.get('email', 'remetente', fallback='')
    senha_app = config.get('email', 'senha', fallback='')
    email_destinatario = config.get('email', 'destinatario', fallback='')

    if not email_remetente or not senha_app or not email_destinatario or email_remetente == 'seuemail@gmail.com':
        print("\n⚠️  AVISO: A função de envio de e-mail não está configurada.")
        print("Verifique e preencha o arquivo 'config.ini' com suas credenciais.")
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    
    if tipo.lower() == "compra":
        emoji = "📈"
    elif tipo.lower() == "venda":
        emoji = "📉"
    elif tipo.lower() == "lateral/consolidação":
        emoji = "⚖️"
    else:
        emoji = "⚪"
    
    corpo = f"""
{emoji} ALERTA DE {tipo.upper()} - {ticker.replace('.SA', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 INFORMAÇÕES DO SINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️  Ativo: {ticker.replace('.SA', '')}
💰 Preço: R$ {preco:,.2f}
📅 Data/Hora: {data_hora}
🎯 Sinal: {tipo.upper()}

"""

    if dados_adicionais:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "📈 INDICADORES TÉCNICOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if 'RSI' in dados_adicionais:
            corpo += f"RSI (14): {dados_adicionais['RSI']:.2f}\n"
        if 'MME21' in dados_adicionais:
            corpo += f"MME 21: R$ {dados_adicionais['MME21']:,.2f}\n"
        if 'MME50' in dados_adicionais:
            corpo += f"MME 50: R$ {dados_adicionais['MME50']:,.2f}\n"
        if 'MACD_HIST' in dados_adicionais:
            corpo += f"MACD Histograma: {dados_adicionais['MACD_HIST']:.4f}\n"
        if 'estrutura' in dados_adicionais:
            corpo += f"\n💡 Estrutura recomendada: {dados_adicionais['estrutura']}\n"

        if 'Strike_Recomendado' in dados_adicionais:
            corpo += f"   🎯 Strike Sugerido: {dados_adicionais['Strike_Recomendado']}\n"
            
        if 'Range_Recomendado' in dados_adicionais:
            corpo += f"   🎯 Range Sugerido (CALL/PUT): {dados_adicionais['Range_Recomendado']}\n"

    corpo += """\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Este é um alerta automático baseado em 
análise técnica. Não é uma recomendação de 
investimento. Faça sua própria análise antes 
de tomar qualquer decisão.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    msg = EmailMessage()
    msg['Subject'] = f"{emoji} {tipo.upper()}: {ticker.replace('.SA', '')} - R$ {preco:,.2f}"
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg.set_content(corpo)

    print(f"\n📧 Enviando alerta de {tipo} para {ticker}...")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)
        print(f"✅ Alerta de {tipo} para {ticker} enviado com sucesso!")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Erro de autenticação: Verifique seu e-mail e senha de aplicativo.")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar o e-mail: {e}")
        return False


def enviar_relatorio_final(total_ativos, sinais_compra, sinais_venda, erros):
    """
    Envia um e-mail com o resumo completo da análise de todos os ativos.
    
    Args:
        total_ativos (int): Total de ativos analisados
        sinais_compra (list): Lista de tuplas (ticker, preco) com sinais de compra
        sinais_venda (list): Lista de tuplas (ticker, preco) com sinais de venda
        erros (list): Lista de tuplas (ticker, erro) com erros encontrados
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    email_remetente = config.get('email', 'remetente', fallback='')
    senha_app = config.get('email', 'senha', fallback='')
    email_destinatario = config.get('email', 'destinatario', fallback='')

    if not email_remetente or not senha_app or not email_destinatario:
        print("\n⚠️  Não foi possível enviar o relatório final: e-mail não configurado.")
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    
    corpo = f"""
📊 RELATÓRIO DE ANÁLISE TÉCNICA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RESUMO GERAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Data/Hora: {data_hora}
📈 Total de ativos analisados: {total_ativos}
✅ Análises bem-sucedidas: {total_ativos - len(erros)}
❌ Erros: {len(erros)}

🟢 Sinais de COMPRA: {len(sinais_compra)}
🔴 Sinais de VENDA: {len(sinais_venda)}
⚪ Sem sinal: {total_ativos - len(sinais_compra) - len(sinais_venda) - len(erros)}

"""

    if sinais_compra:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "📈 SINAIS DE COMPRA DETECTADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, preco in sinais_compra:
            corpo += f"🟢 {ticker.replace('.SA', '')}: R$ {preco:,.2f}\n"
        corpo += "\n"

    if sinais_venda:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "📉 SINAIS DE VENDA DETECTADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, preco in sinais_venda:
            corpo += f"🔴 {ticker.replace('.SA', '')}: R$ {preco:,.2f}\n"
        corpo += "\n"

    if erros:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "⚠️  ERROS ENCONTRADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, erro in erros:
            corpo += f"❌ {ticker}: {erro}\n"
        corpo += "\n"

    corpo += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Análise concluída com sucesso!

⚠️  Este é um relatório automático baseado em 
análise técnica. Não é uma recomendação de 
investimento. Faça sua própria análise antes 
de tomar qualquer decisão.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    msg = EmailMessage()
    
    if sinais_compra or sinais_venda:
        emoji_assunto = "🎯"
        status = f"{len(sinais_compra)} compra(s) | {len(sinais_venda)} venda(s)"
    else:
        emoji_assunto = "✅"
        status = "Sem sinais"
    
    msg['Subject'] = f"{emoji_assunto} Relatório de Análise - {status}"
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg.set_content(corpo)

    print(f"\n📧 Enviando relatório final...")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)
        print(f"✅ Relatório final enviado com sucesso para {email_destinatario}!")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Erro de autenticação ao enviar relatório final.")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar relatório final: {e}")
        return False