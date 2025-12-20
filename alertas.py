import smtplib
from email.message import EmailMessage
import configparser
from datetime import datetime
import json


def carregar_dados_volatilidade():
    """
    Carrega os dados de volatilidade dos arquivos JSON.
    Cria um dicionário unificado com ticker como chave.
    """
    volatilidade_por_ticker = {}
    arquivos_json = ["ativos_por_iv_rank.json", "ativos_por_iv_percentil.json"]

    for nome_arquivo in arquivos_json:
        try:
            with open(nome_arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            for ativo in dados.get("ativos", []):
                ticker = ativo.get("ticker")
                if not ticker:
                    continue

                # Se o ticker ainda não está no dicionário, adicione-o
                if ticker not in volatilidade_por_ticker:
                    volatilidade_por_ticker[ticker] = {
                        "iv_rank": "N/A",
                        "iv_percentil": "N/A",
                    }

                # Atualize com os dados encontrados neste arquivo
                if "iv_rank" in ativo and ativo["iv_rank"] is not None:
                    volatilidade_por_ticker[ticker]["iv_rank"] = ativo["iv_rank"]
                if "iv_percentil" in ativo and ativo["iv_percentil"] is not None:
                    volatilidade_por_ticker[ticker]["iv_percentil"] = ativo[
                        "iv_percentil"
                    ]

        except FileNotFoundError:
            print(
                f"\n⚠️ AVISO: Arquivo de volatilidade '{nome_arquivo}' não encontrado. Alguns dados podem estar ausentes."
            )
            continue  # Continua para o próximo arquivo
        except json.JSONDecodeError:
            print(
                f"\n❌ ERRO: Falha ao decodificar o arquivo JSON '{nome_arquivo}'. Verifique seu formato."
            )
            continue
        except Exception as e:
            print(
                f"\n❌ ERRO: Ocorreu um erro inesperado ao carregar '{nome_arquivo}': {e}"
            )
            continue

    return volatilidade_por_ticker


def enviar_alerta_consolidado(alertas_por_tipo):
    """
    Envia e-mails consolidados por tipo de sinal (Compra, Venda, Lateral/Consolidação).
    Busca credenciais no config.ini, carrega dados de volatilidade e utiliza smtplib para envio.
    """
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
        email_remetente = config.get("email", "remetente", fallback="")
        senha_app = config.get("email", "senha", fallback="")
        email_destinatario = config.get("email", "destinatario", fallback="")
    except Exception as e:
        print(f"\n❌ ERRO: Falha ao ler 'config.ini'. Erro: {e}")
        return False

    if (
        not email_remetente
        or not senha_app
        or not email_destinatario
        or email_remetente == "seuemail@gmail.com"
    ):
        print(
            "\n⚠️ AVISO: A função de envio de e-mail não está configurada em 'config.ini'."
        )
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    emojis = {
        "Compra": "📈",
        "Venda": "📉",
        "Lateral/Consolidação": "⚖️",
        "Sinal Fraco/Aguardar": "⚪",
    }

    # Carrega os dados de volatilidade dos arquivos JSON
    volatilidade_data = carregar_dados_volatilidade()

    total_enviados = 0

    for tipo, alertas in alertas_por_tipo.items():
        if tipo not in ["Compra", "Venda", "Lateral/Consolidação"] or not alertas:
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
            ticker_limpo = ticker.replace(".SA", "")
            corpo += f"\n{i}. {ticker_limpo} - R$ {preco:,.2f}\n"
            corpo += "   " + "─" * 50 + "\n"

            if dados_adicionais:
                # Adiciona dados técnicos
                if "RSI" in dados_adicionais:
                    corpo += f"   RSI (14): {dados_adicionais['RSI']:.2f}\n"
                if "ADX" in dados_adicionais:
                    corpo += f"   ADX (Força): {dados_adicionais['ADX']:.2f}\n"
                if "MME21" in dados_adicionais:
                    corpo += f"   MME 21: R$ {dados_adicionais['MME21']:,.2f}\n"
                if "MME50" in dados_adicionais:
                    corpo += f"   MME 50: R$ {dados_adicionais['MME50']:,.2f}\n"
                if "MACD_HIST" in dados_adicionais:
                    corpo += (
                        f"   MACD Histograma: {dados_adicionais['MACD_HIST']:.4f}\n"
                    )
                if "Volatilidade_%" in dados_adicionais:
                    corpo += f"   Volatilidade: {dados_adicionais['Volatilidade_%']}\n"

                # Adiciona dados de volatilidade do JSON
                vol_info = volatilidade_data.get(ticker_limpo)
                if vol_info:
                    corpo += "\n   --- Volatilidade Implícita ---\n"
                    if vol_info.get("iv_rank") != "N/A":
                        corpo += f"   IV Rank: {vol_info['iv_rank']}\n"
                    if vol_info.get("iv_percentil") != "N/A":
                        corpo += f"   IV Percentil: {vol_info['iv_percentil']}\n"

                # Adiciona estrutura e strikes
                corpo += "\n"
                if "estrutura" in dados_adicionais:
                    corpo += f"   💡 Estrutura: {dados_adicionais['estrutura']}\n"
                if "Strike_Recomendado" in dados_adicionais:
                    corpo += f"   🎯 Strike: {dados_adicionais['Strike_Recomendado']}\n"
                if "Range_Recomendado" in dados_adicionais:
                    corpo += f"   🎯 Range: {dados_adicionais['Range_Recomendado']}\n"

            corpo += "\n"

        msg = EmailMessage()
        msg["Subject"] = f"{emoji} {tipo.upper()}: {len(alertas)} Ativo(s) Detectado(s)"
        msg["From"] = email_remetente
        msg["To"] = email_destinatario
        msg.set_content(corpo)

        print(
            f"\n📧 Tentando enviar alerta consolidado de {tipo} ({len(alertas)} ativos)..."
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(email_remetente, senha_app)
                smtp.send_message(msg)
            print(f"✅ Alerta consolidado de {tipo} enviado com sucesso!")
            total_enviados += 1
        except smtplib.SMTPAuthenticationError:
            print(
                f"❌ Erro de autenticação: Verifique seu e-mail e senha de aplicativo. O envio parou."
            )
            return False
        except Exception as e:
            print(f"❌ Erro ao enviar o e-mail de {tipo}: {e}. O envio parou.")
            return False

    if total_enviados > 0:
        print(f"\n✅ Total de {total_enviados} e-mail(s) consolidado(s) enviado(s)!")

    return True


def enviar_relatorio_final(total_ativos, sinais_compra, sinais_venda, erros):
    """
    Envia um e-mail de resumo final após todas as análises.
    (Esta função não precisou de alterações, pois o formato já estava correto)
    """
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
        email_remetente = config.get("email", "remetente", fallback="")
        senha_app = config.get("email", "senha", fallback="")
        email_destinatario = config.get("email", "destinatario", fallback="")
    except Exception:
        print(
            "\n❌ ERRO: Falha ao ler 'config.ini' para relatório final. Pulando envio."
        )
        return False

    if not email_remetente or not senha_app or not email_destinatario:
        return False

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    sem_sinal_e_sem_erro = (
        total_ativos - len(sinais_compra) - len(sinais_venda) - len(erros)
    )

    corpo = f"""📊 RELATÓRIO DE ANÁLISE TÉCNICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RESUMO GERAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Data/Hora: {data_hora}
📈 Total de ativos analisados: {total_ativos}
✅ Análises bem-sucedidas: {total_ativos - len(erros)}
❌ Erros: {len(erros)}

🟢 Sinais de COMPRA (Viáveis): {len(sinais_compra)}
🔴 Sinais de VENDA (Viáveis): {len(sinais_venda)}
⚪ Outros/Sem Sinal Forte: {sem_sinal_e_sem_erro}

"""
    if sinais_compra:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "📈 SINAIS DE COMPRA DETECTADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, preco, _ in sinais_compra:
            corpo += f"🟢 {ticker.replace('.SA', '')}: R$ {preco:,.2f}\n"
        corpo += "\n"

    if sinais_venda:
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        corpo += "📉 SINAIS DE VENDA DETECTADOS\n"
        corpo += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for ticker, preco, _ in sinais_venda:
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
        status = "Análise concluída (Sem sinais fortes)"

    msg["Subject"] = f"{emoji_assunto} Relatório de Análise - {status}"
    msg["From"] = email_remetente
    msg["To"] = email_destinatario
    msg.set_content(corpo)

    print(f"\n📧 Tentando enviar relatório final...")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)
        print(f"✅ Relatório final enviado com sucesso para {email_destinatario}!")
        return True
    except smtplib.SMTPAuthenticationError:
        print(
            f"❌ Erro de autenticação ao enviar relatório final. Verifique seu e-mail e senha de aplicativo."
        )
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar relatório final: {e}")
        return False
