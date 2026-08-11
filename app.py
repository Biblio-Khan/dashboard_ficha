import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import json

# Configuração da página
st.set_page_config(page_title="Admin - Créditos", page_icon="🛠️", layout="wide")

# Função de Conexão com a Planilha
def conectar_planilha():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        gc = gspread.service_account(filename='credenciais.json')
        
    return gc.open("créditos_fichajud")

st.title("🛠️ Painel de Gestão e Análise")

# --- LOGIN SIMPLES ---
password = st.sidebar.text_input("Senha Admin:", type="password")

if password == st.secrets["admin_senha"]:
    try:
        sh = conectar_planilha()
        sheet_principal = sh.worksheet("Página1")
        df = pd.DataFrame(sheet_principal.get_all_records())
        
        # --- CRIAÇÃO DAS ABAS ---
        aba_gestao, aba_graficos = st.tabs(["🛠️ Gestão e Recargas", "📊 Análise de Usuários"])
        
        # --- ABA 1: GESTÃO E RECARGAS ---
        with aba_gestao:
            st.subheader("📋 Usuários Cadastrados")
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            st.subheader("⚡ Ações Rápidas")
            
            email_input = st.text_input("E-mail do usuário")
            qtd = st.number_input("Créditos para recarga", value=10, min_value=1)
            
            if st.button("Recarregar Créditos"):
                if not email_input.strip():
                    st.error("Digite um e-mail válido.")
                else:
                    celula = sheet_principal.find(email_input.lower().strip())
                    if celula:
                        saldo_atual = int(sheet_principal.cell(celula.row, 2).value or 0)
                        novo_saldo = saldo_atual + qtd
                        
                        # 1. Atualiza o saldo na Página1
                        sheet_principal.update_cell(celula.row, 2, novo_saldo)
                        
                        # 2. Registra na aba Histórico automaticamente
                        try:
                            aba_hist = sh.worksheet("Historico")
                            aba_hist.append_row([
                                datetime.now().strftime("%d/%m/%Y %H:%M"),
                                email_input.lower().strip(),
                                qtd,
                                saldo_atual,
                                novo_saldo
                            ])
                        except Exception as e:
                            st.warning(f"Aba 'Historico' não encontrada ou com erro: {e}. A recarga foi feita, mas não foi logada.")
                        
                        st.success(f"Recarga feita! Saldo do usuário foi de {saldo_atual} para {novo_saldo}.")
                        st.rerun()
                    else:
                        st.error("Usuário não encontrado.")

        # --- ABA 2: ANÁLISE DE USUÁRIOS E GRÁFICOS ---
        with aba_graficos:
            st.subheader("📊 Relatórios e Comportamento de Compra")
            
            # Métricas gerais da Página1
            if not df.empty and len(df.columns) >= 2:
                col_creditos_nome = df.columns[1]
                df[col_creditos_nome] = pd.to_numeric(df[col_creditos_nome], errors='coerce').fillna(0)
                
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Total de Usuários Cadastrados", len(df))
                with m2:
                    st.metric("Créditos Totais em Circulação", int(df[col_creditos_nome].sum()))
            
            st.divider()

            # Leitura da aba Histórico para gráficos
            try:
                aba_hist = sh.worksheet("Historico")
                dados_hist = aba_hist.get_all_records()
                
                if dados_hist:
                    df_hist = pd.DataFrame(dados_hist)
                    
                    # Padroniza os nomes das colunas automaticamente
                    df_hist.columns = [str(col).strip().lower() for col in df_hist.columns]
                    
                    # Expander para conferência dos dados brutos
                    with st.expander("Ver dados brutos do Histórico"):
                        st.write("Colunas detectadas:", df_hist.columns.tolist())
                        st.dataframe(df_hist)
                    
                    st.markdown("### 📈 Histórico de Movimentações")
                    
                    col_email = next((c for c in df_hist.columns if 'email' in c), None)
                    col_qtd = next((c for c in df_hist.columns if 'quant' in c or 'qtd' in c or 'credito' in c), None)
                    
                    if col_email and col_qtd:
                        st.write("Ranking de Usuários que Mais Recarregam (Volume):")
                        ranking = df_hist.groupby(col_email)[col_qtd].sum().sort_values(ascending=False)
                        st.bar_chart(ranking)
                    else:
                        st.warning("Não foi possível identificar automaticamente as colunas de 'Email' e 'Quantidade' na sua aba Historico. Verifique os nomes no expander acima.")
                else:
                    st.info("A aba 'Historico' está vazia no momento. Faça uma recarga para gerar dados.")
            except Exception as e:
                st.error(f"Erro ao ler histórico: {e}")

    except Exception as e:
        st.error(f"Erro ao conectar ou carregar dados da planilha: {e}")
else:
    st.info("Insira a senha correta na barra lateral para acessar o painel.")
