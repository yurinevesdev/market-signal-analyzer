import smtplib
from email.message import EmailMessage
import configparser
from datetime import datetime


def enviar_alerta_consolidado(alertas_por_tipo):
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    email_remetente = config.get('email', 'remetente', fallback='')
    senha_app = config.get('email', 'senha', fallback='')
    email_destinatario = config.get('email', 'destinatario', fallback='')
    
    if not email_remetente or not senha_app or not email_destinatario or email_remetente == 'seuemail@gmail.com':
        print("\n⚠️ AVISO: A função de envio de e-mail não está configurada.")
        print("Verifique e preencha o arquivo 'config.ini' com suas credenciais.")
        return False
    
    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    
    emojis = {
        "Compra": "📈",
        "Venda": "📉",
        "Lateral/Consolidação": "⚖️",
        "Sinal Fraco/Aguardar": "⚪"
    }
    
    total_enviados = 0
    
    for tipo, alertas in alertas_por_tipo.items():
        if not alertas:
            continue
            
        emoji = emojis.get(tipo, "⚪")
        
        corpo = f"""{emoji} ALERTAS DE {tipo.upper()} - {len(alertas)} ATIVO(S)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RESUMO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Data/Hora: {data_hora}
🎯 Tipo de Sinal: {tipo.upper()}
📊 Quantidade de ativos: {len(alertas)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 ATIVOS DETECTADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for i, (ticker, preco, dados_adicionais) in enumerate(alertas, 1):
            corpo += f"\n{i}. {ticker.replace('.SA', '')} - R$ {preco:,.2f}\n"
            corpo += "   " + "─" * 50 + "\n"
            
            if dados_adicionais:
                if 'RSI' in dados_adicionais:
                    corpo += f"   RSI (14): {dados_adicionais['RSI']:.2f}\n"
                if 'MME21' in dados_adicionais:
                    corpo += f"   MME 21: R$ {dados_adicionais['MME21']:,.2f}\n"
                if 'MME50' in dados_adicionais:
                    corpo += f"   MME 50: R$ {dados_adicionais['MME50']:,.2f}\n"
                if 'MACD_HIST' in dados_adicionais:
                    corpo += f"   MACD Histograma: {dados_adicionais['MACD_HIST']:.4f}\n"
                if 'Volatilidade_%' in dados_adicionais:
                    corpo += f"   Volatilidade: {dados_adicionais['Volatilidade_%']}\n"
                if 'estrutura' in dados_adicionais:
                    corpo += f"\n   💡 Estrutura: {dados_adicionais['estrutura']}\n"
                if 'Strike_Recomendado' in dados_adicionais:
                    corpo += f"   🎯 Strike: {dados_adicionais['Strike_Recomendado']}\n"
                if 'Range_Recomendado' in dados_adicionais:
                    corpo += f"   🎯 Range: {dados_adicionais['Range_Recomendado']}\n"
            
            corpo += "\n"
        
        msg = EmailMessage()
        msg['Subject'] = f"{emoji} {tipo.upper()}: {len(alertas)} Ativo(s) Detectado(s)"
        msg['From'] = email_remetente
        msg['To'] = email_destinatario
        msg.set_content(corpo)
        
        print(f"\n📧 Enviando alerta consolidado de {tipo} ({len(alertas)} ativos)...")
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_remetente, senha_app)
                smtp.send_message(msg)
            print(f"✅ Alerta consolidado de {tipo} enviado com sucesso!")
            total_enviados += 1
        except smtplib.SMTPAuthenticationError:
            print(f"❌ Erro de autenticação: Verifique seu e-mail e senha de aplicativo.")
            return False
        except Exception as e:
            print(f"❌ Erro ao enviar o e-mail de {tipo}: {e}")
            return False
    
    if total_enviados > 0:
        print(f"\n✅ Total de {total_enviados} e-mail(s) consolidado(s) enviado(s)!")
    
    return True


def enviar_relatorio_final(total_ativos, sinais_compra, sinais_venda, erros):
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    email_remetente = config.get('email', 'remetente', fallback='')
    senha_app = config.get('email', 'senha', fallback='')
    email_destinatario = config.get('email', 'destinatario', fallback='')
    
    if not email_remetente or not senha_app or not email_destinatario:
        print("\n⚠️ Não foi possível enviar o relatório final: e-mail não configurado.")
        return False
    
    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    
    corpo = f"""📊 RELATÓRIO DE ANÁLISE TÉCNICA
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
        corpo += "⚠️ ERROS ENCONTRADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, erro in erros:
            corpo += f"❌ {ticker}: {erro}\n"
        corpo += "\n"
    
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