import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Controle de Quantidade",
    page_icon="🔢",
    layout="wide"
)

# --- AUTENTICAÇÃO E CONEXÃO COM GOOGLE SHEETS ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def connect_to_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    # ATENÇÃO: Substitua "Controle de Estoque App" pelo nome exato da sua planilha
    spreadsheet = client.open("Controle de Estoque App")
    return spreadsheet

# --- FUNÇÕES DE DADOS ---
def carregar_dados(spreadsheet):
    try:
        estoque_ws = spreadsheet.worksheet("Estoque")
        # .dropna(how='all') remove linhas que estão completamente vazias
        estoque_df = get_as_dataframe(estoque_ws).dropna(how='all')
        
        if not estoque_df.empty:
            estoque_df['Quantidade'] = pd.to_numeric(estoque_df['Quantidade'])

        movimentacoes_ws = spreadsheet.worksheet("Movimentacoes")
        movimentacoes_df = get_as_dataframe(movimentacoes_ws).dropna(how='all')

        return estoque_df, movimentacoes_df
    except gspread.exceptions.WorksheetNotFound:
        st.error("Uma das abas ('Estoque' ou 'Movimentacoes') não foi encontrada na planilha.")
        return pd.DataFrame(columns=['Item', 'Quantidade']), pd.DataFrame(columns=['Timestamp', 'Tipo', 'Item', 'Quantidade'])
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados: {e}")
        return pd.DataFrame(columns=['Item', 'Quantidade']), pd.DataFrame(columns=['Timestamp', 'Tipo', 'Item', 'Quantidade'])

# --- INICIALIZAÇÃO ---
try:
    spreadsheet = connect_to_gsheet()
    esto
