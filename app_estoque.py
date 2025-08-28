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
    estoque_df, movimentacoes_df = carregar_dados(spreadsheet)
except Exception as e:
    st.error(f"Não foi possível conectar à planilha. Verifique suas credenciais. Erro: {e}")
    estoque_df = pd.DataFrame(columns=['Item', 'Quantidade'])
    movimentacoes_df = pd.DataFrame(columns=['Timestamp', 'Tipo', 'Item', 'Quantidade'])

# --- TÍTULO DO APP ---
st.title("🔢 Sistema de Controle de Quantidade")
st.markdown("---")

# --- ABAS (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "📥 Entrada de Itens", 
    "📤 Saída de Itens",
    "✏️ Editar Nome do Item"
])

# --- ABA 1: DASHBOARD ---
with tab1:
    st.header("Dashboard do Estoque")

    if not estoque_df.empty:
        total_itens_estoque = estoque_df['Quantidade'].sum()
        itens_unicos = estoque_df['Item'].nunique()

        col1, col2 = st.columns(2)
        col1.metric(label="Itens Únicos", value=f"{itens_unicos}")
        col2.metric(label="Total de Itens no Estoque", value=f"{total_itens_estoque:,.0f}")
        
        st.subheader("Quantidade por Item")
        # Criamos uma cópia para evitar o SettingWithCopyWarning
        df_chart = estoque_df.copy()
        df_chart.set_index('Item', inplace=True)
        st.bar_chart(df_chart['Quantidade'])

    else:
        st.warning("Estoque vazio.")

    st.markdown("---")
    st.subheader("Estoque Atual")
    st.dataframe(estoque_df, use_container_width=True)
    
    st.subheader("Histórico de Movimentações")
    st.dataframe(movimentacoes_df.sort_values('Timestamp', ascending=False), use_container_width=True)

# --- ABA 2: ENTRADA DE ITENS ---
with tab2:
    st.header("Registrar Entrada no Estoque")
    with st.form("form_entrada", clear_on_submit=True):
        nome_item = st.text_input("Nome do Item").strip()
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        
        submitted = st.form_submit_button("Adicionar ao Estoque")
        if submitted:
            if not nome_item:
                st.error("O nome do item é obrigatório.")
            else:
                nova_movimentacao = pd.DataFrame([{'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Tipo': 'Entrada', 'Item': nome_item, 'Quantidade': quantidade}])
                movimentacoes_df = pd.concat([movimentacoes_df, nova_movimentacao], ignore_index=True)

                item_existente = estoque_df[estoque_df['Item'].astype(str).str.lower() == nome_item.lower()]
                
                if not item_existente.empty:
                    idx = item_existente.index[0]
                    estoque_df.loc[idx, 'Quantidade'] += quantidade
                else:
                    novo_item = pd.DataFrame([{'Item': nome_item, 'Quantidade': quantidade}])
                    estoque_df = pd.concat([estoque_df, novo_item], ignore_index=True)
                
                # Atualizar planilha
                set_with_dataframe(spreadsheet.worksheet("Estoque"), estoque_df)
                set_with_dataframe(spreadsheet.worksheet("Movimentacoes"), movimentacoes_df)
                
                st.success(f"✅ {quantidade} unidade(s) de '{nome_item}' adicionada(s)!")
                st.rerun()

# --- ABA 3: SAÍDA DE ITENS ---
with tab3:
    st.header("Registrar Saída do Estoque")
    if estoque_df.empty:
        st.warning("Nenhum item disponível para retirada.")
    else:
        with st.form("form_saida", clear_on_submit=True):
            item_selecionado = st.selectbox("Selecione o Item", options=sorted(estoque_df['Item'].unique()))
            if item_selecionado:
                max_qty = int(estoque_df.loc[estoque_df['Item'] == item_selecionado, 'Quantidade'].iloc[0])
                quantidade_saida = st.number_input("Quantidade a Retirar", min_value=1, max_value=max_qty, step=1)
            
            submitted = st.form_submit_button("Retirar do Estoque")
            if submitted and item_selecionado:
                nova_movimentacao = pd.DataFrame([{'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'Tipo': 'Saída','Item': item_selecionado,'Quantidade': quantidade_saida}])
                movimentacoes_df = pd.concat([movimentacoes_df, nova_movimentacao], ignore_index=True)
                
                item_idx = estoque_df[estoque_df['Item'] == item_selecionado].index[0]
                estoque_df.loc[item_idx, 'Quantidade'] -= quantidade_saida
                estoque_df = estoque_df[estoque_df['Quantidade'] > 0]
                
                # Atualizar planilha
                set_with_dataframe(spreadsheet.worksheet("Estoque"), estoque_df)
                set_with_dataframe(spreadsheet.worksheet("Movimentacoes"), movimentacoes_df)
                
                st.success(f"✔️ {quantidade_saida} unidade(s) de '{item_selecionado}' retiradas!")
                st.rerun()

# --- ABA 4: EDITAR NOME DO ITEM ---
with tab4:
    st.header("Editar Nome do Item")
    if estoque_df.empty:
        st.warning("Nenhum item disponível para edição.")
    else:
        opcoes_validas = sorted([item for item in estoque_df['Item'].unique() if pd.notna(item)])
        item_para_editar = st.selectbox("Selecione o Item para Editar", options=opcoes_validas, key="edit_select")
        
        if item_para_editar:
            with st.form("form_edicao"):
                st.write(f"Editando: **{item_para_editar}**")
                novo_nome = st.text_input("Novo Nome do Item", value=item_para_editar).strip()
                
                submitted_edicao = st.form_submit_button("Salvar Alterações")
                if submitted_edicao:
                    if not novo_nome:
                        st.error("O novo nome não pode ser vazio.")
                    elif novo_nome.lower() != item_para_editar.lower() and not estoque_df[estoque_df['Item'].astype(str).str.lower() == novo_nome.lower()].empty:
                        st.error(f"O item '{novo_nome}' já existe. Escolha um nome diferente.")
                    else:
                        # ESTA É A LINHA QUE FOI CORRIGIDA
                        idx_item = estoque_df[estoque_df['Item'] == item_para_editar].index[0]
                        estoque_df.loc[idx_item, 'Item'] = novo_nome
                        
                        # Atualizar o nome no histórico de movimentações
                        movimentacoes_df.loc[movimentacoes_df['Item'] == item_para_editar, 'Item'] = novo_nome
                        
                        # Salvar ambos na planilha
                        set_with_dataframe(spreadsheet.worksheet("Estoque"), estoque_df)
                        set_with_dataframe(spreadsheet.worksheet("Movimentacoes"), movimentacoes_df)
                        
                        st.success(f"Item '{item_para_editar}' atualizado para '{novo_nome}'!")
                        st.rerun()
