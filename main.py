from analise import analisar_multiplos_ativos
import time

if __name__ == "__main__":
    """
    Ponto de entrada do script.
    Define os ativos a serem analisados, combinando uma lista de alta liquidez
    com uma lista de carteira pessoal, removendo duplicatas antes de analisar.
    """
    
    lista_alta_liquidez = [
        "PETR4",    
        "VALE3",    
        "ITUB4",   
        "BBDC4",    
        "ABEV3",    
        "BBAS3",   
        "WEGE3",    
        "RENT3",    
        "MGLU3",    
        "B3SA3",
        "BOVA11",
        "GGBR4",
        "SUZB3",
        "CSNA3",
        "USIM5",
        "ELET3",
    ]
    
    lista_carteira_pessoal = [
        "UNIP6",
        "ELET6",
        "B3SA3",
        "BBAS3",
        "VALE3",
        "EGIE3",
        "BBSE3",
        "BRBI11",
        "AURA33",
        "BMEB4",
        "VLID3",
        "POMO4",
        "WIZC3",
        "FESA4",
        "ODPV3",
        "CAML3",
        "ALOS3",
        "CBAV3",
        "RAPT4",
        "TUPY3",
        "DXCO3",
        "AZZA3",
        "GUAR3",
        "LEVE3",
        "MYPK3",
        "TASA4",
        "ALPA4",
        "FLRY3",
        "CRPG5"
    ]

    lista_combinada = lista_alta_liquidez + lista_carteira_pessoal
    
    tickers_unicos = sorted(list(set(lista_combinada)))
    
    lista_ativos_final = [f"{ticker}.SA" for ticker in tickers_unicos]
    
    print(f"Iniciando análise de {len(lista_ativos_final)} ativos únicos...")
    print(lista_ativos_final)
    print("=" * 70)
    
    analisar_multiplos_ativos(lista_ativos_final)