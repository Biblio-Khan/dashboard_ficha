import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import json

# Configuração da página
st.set_page_config(page_title="Admin - Créditos", page_icon="🛠️")

# Função de Conexão
def conectar_planilha():
    # Se estiver no Streamlit Cloud, pegamos dos Secrets
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        # Se estiver rodando local, usa o arquivo json
        gc = gspread.service_account(filename='credenciais.json')
    
    return gc.open("créditos_fichajud").worksheet("Página1")

st.title("🛠️ Painel de Gestão de Créditos")

# --- LOGIN SIMPLES ---
password = st.sidebar.text_input("Senha Admin:", type="password")
if password == "1234": # TROQUE SUA SENHA AQUI
    try:
        sheet = conectar_planilha()
        df = pd.DataFrame(sheet.get_all_records())
        
        st.dataframe(df)
        
        col1, col2 = st.columns(2)
        email_input = st.text_input("E-mail do usuário")
        
        with col1:
            if st.button("Presentear 4 Créditos (Novo)"):
                if sheet.find(email_input.lower().strip()):
                    st.warning("Usuário já existe.")
                else:
                    sheet.append_row([email_input.lower().strip(), 4, datetime.now().strftime("%d/%m/%Y")])
                    st.success("Usuário criado com 4 créditos!")
                    st.rerun()

        with col2:
            qtd = st.number_input("Créditos para recarga", value=10)
            if st.button("Recarregar Créditos"):
                celula = sheet.find(email_input.lower().strip())
                if celula:
                    saldo_atual = int(sheet.cell(celula.row, 2).value or 0)
                    sheet.update_cell(celula.row, 2, saldo_atual + qtd)
                    st.success("Recarga feita!")
                    st.rerun()
                else:
                    st.error("Usuário não encontrado.")
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
else:
    st.info("Insira a senha na barra lateral para começar.")
