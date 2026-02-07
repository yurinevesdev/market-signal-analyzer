import scraping 
from analise import analisar_multiplos_ativos
from alertas import enviar_alerta_consolidado, enviar_relatorio_final
import time
import os

if __name__ == "__main__":
    print("🚀 Iniciando atualização de dados de volatilidade (Scraping)...")
    
    foco_opcoes = []
    
    dados_vols = scraping.consolidar_dados_compativel(lista_opcoes=foco_opcoes)
    
    if dados_vols:
        scraping.salvar_formato_analise_py(dados_vols, 'dados_mercado_consolidado.json')
        print("✅ Dados de mercado atualizados com sucesso.")
    else:
        print("⚠️ Falha ao atualizar dados de volatilidade. O script usará o último JSON disponível.")

    print("\n" + "=" * 70)
    
    lista_alta_liquidez = [
        "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "BBAS3", 
        "WEGE3", "RENT3", "MGLU3", "B3SA3", "BOVA11", "GGBR4", 
        "SUZB3", "CSNA3", "USIM5", "ELET3",
    ]
    
    lista_carteira_pessoal = [
        "UNIP6", "ELET6", "B3SA3", "BBAS3", "VALE3", "EGIE3", 
        "BBSE3", "BRBI11", "AURA33", "BMEB4", "VLID3", "POMO4", 
        "WIZC3", "FESA4", "ODPV3", "CAML3", "ALOS3", "CBAV3", 
        "RAPT4", "TUPY3", "DXCO3", "AZZA3", "GUAR3", "LEVE3", 
        "MYPK3", "TASA4", "ALPA4", "FLRY3", "CRPG5"
    ]

    lista_combinada = lista_alta_liquidez + lista_carteira_pessoal
    tickers_unicos = sorted(list(set(lista_combinada)))
    lista_ativos_final = [f"{ticker}.SA" for ticker in tickers_unicos]
    
    print(f"🔍 Iniciando análise de {len(lista_ativos_final)} ativos únicos...")
    print("=" * 70)
    
    aprovados, rejeitados = analisar_multiplos_ativos(lista_ativos_final)
    
    if aprovados:

        alertas_para_envio = {
            "Alta_Confianca": []
        }
        
        for ativo in aprovados:

            item = (ativo['ticker'], ativo.get('preco', 0), ativo)
            alertas_para_envio["Alta_Confianca"].append(item)
        
        print(f"\n📨 {len(aprovados)} oportunidades encontradas! Enviando e-mail...")
        enviar_alerta_consolidado(alertas_para_envio)
        

        enviar_relatorio_final(len(lista_ativos_final), aprovados, [], [])
    else:
        print("\n📭 Nenhuma oportunidade Elite encontrada pelos filtros.")

        enviar_relatorio_final(len(lista_ativos_final), [], [], [])
    
    print("\n🏁 Processo concluído com sucesso.")