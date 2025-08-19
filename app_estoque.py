import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Controle de Estoque Avançado",
    page_icon="📦",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES ---

# Função para inicializar os arquivos CSV se eles não existirem
def inicializar_arquivos():
    if not os.path.exists('estoque.csv'):
        pd.DataFrame(columns=['Item', 'Quantidade', 'Preco_Unitario']).to_csv('estoque.csv', index=False)
    if not os.path.exists('movimentacoes.csv'):
        pd.DataFrame(columns=['Timestamp', 'Tipo', 'Item', 'Quantidade', 'Preco_Unitario']).to_csv('movimentacoes.csv', index=False)

# Função para carregar os dados dos arquivos CSV
def carregar_dados():
    try:
        estoque_df = pd.read_csv('estoque.csv')
        movimentacoes_df = pd.read_csv('movimentacoes.csv')
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver vazio, retorna um DataFrame vazio com as colunas certas
        estoque_df = pd.DataFrame(columns=['Item', 'Quantidade', 'Preco_Unitario'])
        movimentacoes_df = pd.DataFrame(columns=['Timestamp', 'Tipo', 'Item', 'Quantidade', 'Preco_Unitario'])
    return estoque_df, movimentacoes_df

# Função para converter DataFrame para CSV para download
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- INICIALIZAÇÃO ---
inicializar_arquivos()
estoque_df, movimentacoes_df = carregar_dados()

# --- TÍTULO DO APP ---
st.title("📦 Sistema de Gerenciamento de Estoque")
st.markdown("---")

# --- ABAS (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Estoque", 
    "📥 Adicionar Item (Entrada)", 
    "📤 Retirar Item (Saída)",
    "✏️ Editar Item"
])

# --- ABA 1: DASHBOARD ---
with tab1:
    st.header("Gráficos do Estoque")

    # Métricas principais
    total_itens = estoque_df['Quantidade'].sum()
    valor_total_estoque = (estoque_df['Quantidade'] * estoque_df['Preco_Unitario']).sum()
    itens_unicos = estoque_df['Item'].nunique()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Itens Únicos", value=f"{itens_unicos}")
    with col2:
        st.metric(label="Total de Itens no Estoque", value=f"{total_itens:,.0f}")
    with col3:
        st.metric(label="Valor Total do Estoque (R$)", value=f"R$ {valor_total_estoque:,.2f}")

    st.markdown("---")
    
    # --- GRÁFICOS DE VISUALIZAÇÃO ---
    st.subheader("Visualização do Estoque")
    if not estoque_df.empty:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.write("Quantidade por Item")
            chart_data_qty = estoque_df.set_index('Item')['Quantidade']
            st.bar_chart(chart_data_qty)
        
        with col_chart2:
            st.write("Valor Total (R$) por Item")
            estoque_df['Valor_Total'] = estoque_df['Quantidade'] * estoque_df['Preco_Unitario']
            chart_data_value = estoque_df.set_index('Item')['Valor_Total']
            st.bar_chart(chart_data_value)
    else:
        st.warning("Não há dados de estoque para exibir gráficos.")

    st.markdown("---")
    
    # --- BUSCA E FILTROS ---
    st.subheader("Estoque Atual")
    search_term = st.text_input("Buscar Item", placeholder="Digite o nome do item para buscar...")
    if search_term:
        filtered_stock = estoque_df[estoque_df['Item'].str.contains(search_term, case=False, na=False)]
    else:
        filtered_stock = estoque_df

    # Exibindo o DataFrame filtrado ou completo
    st.dataframe(filtered_stock, use_container_width=True, height=300)
    
    # --- EXPORTAÇÃO DE DADOS ---
    col_export1, col_export2 = st.columns(2)
    with col_export1:
        csv_estoque = convert_df_to_csv(estoque_df)
        st.download_button(
            label="📥 Baixar Estoque Atual (CSV)",
            data=csv_estoque,
            file_name='estoque_atual.csv',
            mime='text/csv',
        )
    with col_export2:
        csv_movimentacoes = convert_df_to_csv(movimentacoes_df)
        st.download_button(
            label="📥 Baixar Histórico de Movimentações (CSV)",
            data=csv_movimentacoes,
            file_name='historico_movimentacoes.csv',
            mime='text/csv',
        )

    st.subheader("Histórico de Movimentações Recentes")
    st.dataframe(movimentacoes_df.sort_values('Timestamp', ascending=False).head(10), use_container_width=True)

# --- ABA 2: ADICIONAR ITEM (ENTRADA) ---
with tab2:
    st.header("Registrar Entrada no Estoque")
    with st.form("form_entrada", clear_on_submit=True):
        nome_item = st.text_input("Nome do Item", key="add_name").strip()
        quantidade = st.number_input("Quantidade", min_value=1, step=1, key="add_qty")
        preco_unitario = st.number_input("Preço Unitário (R$)", min_value=0.01, format="%.2f", key="add_price")
        
        submitted = st.form_submit_button("Adicionar ao Estoque")
        if submitted:
            # Lógica de adição (mantida da versão anterior)
            if not nome_item:
                st.error("O nome do item é obrigatório.")
            else:
                estoque_df, movimentacoes_df = carregar_dados()
                nova_movimentacao = pd.DataFrame([{'Timestamp': datetime.now(),'Tipo': 'Entrada','Item': nome_item,'Quantidade': quantidade,'Preco_Unitario': preco_unitario}])
                movimentacoes_df = pd.concat([movimentacoes_df, nova_movimentacao], ignore_index=True)
                
                item_existente = estoque_df[estoque_df['Item'].str.lower() == nome_item.lower()]
                if not item_existente.empty:
                    idx = item_existente.index[0]
                    estoque_df.loc[idx, 'Quantidade'] += quantidade
                    estoque_df.loc[idx, 'Preco_Unitario'] = preco_unitario 
                else:
                    novo_item = pd.DataFrame([{'Item': nome_item,'Quantidade': quantidade,'Preco_Unitario': preco_unitario}])
                    estoque_df = pd.concat([estoque_df, novo_item], ignore_index=True)
                
                estoque_df.to_csv('estoque.csv', index=False)
                movimentacoes_df.to_csv('movimentacoes.csv', index=False)
                st.success(f"✅ {quantidade} unidade(s) de '{nome_item}' adicionadas!")
                st.rerun()

# --- ABA 3: RETIRAR ITEM (SAÍDA) ---
with tab3:
    st.header("Registrar Saída do Estoque")
    if estoque_df.empty:
        st.warning("Nenhum item disponível no estoque para retirada.")
    else:
        with st.form("form_saida", clear_on_submit=True):
            item_selecionado = st.selectbox("Selecione o Item", options=sorted(estoque_df['Item'].unique()), key="remove_item")
            max_qty = int(estoque_df.loc[estoque_df['Item'] == item_selecionado, 'Quantidade'].iloc[0])
            quantidade_saida = st.number_input("Quantidade a Retirar", min_value=1, max_value=max_qty, step=1, key="remove_qty")
            submitted_saida = st.form_submit_button("Retirar do Estoque")
            if submitted_saida:
                # Lógica de retirada (mantida da versão anterior)
                estoque_df, movimentacoes_df = carregar_dados()
                item_idx = estoque_df[estoque_df['Item'] == item_selecionado].index[0]
                preco_unitario_saida = estoque_df.loc[item_idx, 'Preco_Unitario']
                
                nova_movimentacao = pd.DataFrame([{'Timestamp': datetime.now(),'Tipo': 'Saída','Item': item_selecionado,'Quantidade': quantidade_saida,'Preco_Unitario': preco_unitario_saida}])
                movimentacoes_df = pd.concat([movimentacoes_df, nova_movimentacao], ignore_index=True)
                
                estoque_df.loc[item_idx, 'Quantidade'] -= quantidade_saida
                estoque_df = estoque_df[estoque_df['Quantidade'] > 0]
                
                estoque_df.to_csv('estoque.csv', index=False)
                movimentacoes_df.to_csv('movimentacoes.csv', index=False)
                st.success(f"✔️ {quantidade_saida} unidade(s) de '{item_selecionado}' retiradas!")
                st.rerun()

# --- ABA 4: EDITAR ITEM ---
with tab4:
    st.header("Editar Item do Estoque")
    if estoque_df.empty:
        st.warning("Nenhum item disponível no estoque para edição.")
    else:
        item_para_editar = st.selectbox("Selecione o Item para Editar", options=sorted(estoque_df['Item'].unique()), key="edit_select")
        
        if item_para_editar:
            dados_atuais = estoque_df[estoque_df['Item'] == item_para_editar].iloc[0]
            
            with st.form("form_edicao"):
                st.write(f"Editando: **{item_para_editar}**")
                
                novo_nome = st.text_input("Novo Nome do Item", value=dados_atuais['Item']).strip()
                novo_preco = st.number_input("Novo Preço Unitário (R$)", min_value=0.01, value=dados_atuais['Preco_Unitario'], format="%.2f")
                
                submitted_edicao = st.form_submit_button("Salvar Alterações")
                
                if submitted_edicao:
                    if not novo_nome:
                        st.error("O novo nome do item não pode ser vazio.")
                    else:
                        # Carregar dados mais recentes para a operação
                        estoque_df, movimentacoes_df = carregar_dados()
                        
                        # Atualizar o DataFrame de estoque
                        idx_item = estoque_df[estoque_df['Item'] == item_para_editar].index[0]
                        estoque_df.loc[idx_item, 'Item'] = novo_nome
                        estoque_df.loc[idx_item, 'Preco_Unitario'] = novo_preco
                        
                        # Atualizar o nome do item no histórico de movimentações para consistência
                        movimentacoes_df.loc[movimentacoes_df['Item'] == item_para_editar, 'Item'] = novo_nome
                        
                        # Salvar ambos os arquivos
                        estoque_df.to_csv('estoque.csv', index=False)
                        movimentacoes_df.to_csv('movimentacoes.csv', index=False)
                        
                        st.success(f"Item '{item_para_editar}' atualizado para '{novo_nome}' com sucesso!")
                        st.rerun()