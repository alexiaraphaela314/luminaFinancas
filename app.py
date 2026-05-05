import streamlit as st
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Configuração da página padrão MYCARD
st.set_page_config(page_title="MYCARD Atendimento", page_icon="💳")

# --- 1. TREINAMENTO DA IA (Reestruturado para Normalização) ---
@st.cache_resource
def treinar_modelo():
    try:
        # Carrega o perguntas.csv garantindo que não existam espaços nos nomes das colunas
        perguntas = pd.read_csv("perguntas.csv", skipinitialspace=True)
        
        # NORMALIZAÇÃO: Convertemos as frases de treino para minúsculas
        # Isso ensina a IA a ignorar se o usuário escreve com Shift ou Caps Lock
        frases = perguntas["frases"].astype(str).str.lower().tolist()
        categorias = perguntas["categoria"].astype(str).tolist()
        
        vetorizador = CountVectorizer()
        x = vetorizador.fit_transform(frases)
        modelo = MultinomialNB()
        modelo.fit(x, categorias)
        return vetorizador, modelo
    except Exception as e:
        st.error(f"Erro ao carregar perguntas.csv: {e}")
        return None, None

vetorizador, modelo = treinar_modelo()

# --- 2. BUSCA NO BANCO DE DADOS ---
def buscar_cliente(cpf):
    try:
        with sqlite3.connect('luminaFinanças.db') as conn:
            conn.row_factory = sqlite3.Row  # Crucial para acessar dados pelo nome da coluna
            cursor = conn.cursor()
            # CPF no seu banco é INTEGER, por isso convertemos o input
            cursor.execute('SELECT * FROM clientes WHERE cpf = ?', (int(cpf),))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
    except Exception:
        return None

# --- 3. INTERFACE VISUAL ---
st.markdown("<h1 style='text-align: center;'>Operadora de cartão de crédito MYCARD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Atendimento virtual para clientes</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Digite seu CPF para iniciar o atendimento."}]
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = None

# Botão Limpar Conversa
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("Limpar conversa"):
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Digite seu CPF para iniciar o atendimento."}]
        st.session_state.cliente_logado = None
        st.rerun()

# Renderização do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. FLUXO DE CONVERSA ---
if prompt := st.chat_input("Digite aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # LOGIN: Identificação por CPF
    if st.session_state.cliente_logado is None:
        cpf_limpo = "".join(filter(str.isdigit, prompt)) # Pega só os números
        cliente = buscar_cliente(cpf_limpo)
        
        if cliente:
            st.session_state.cliente_logado = cliente
            nome_cli = cliente['nome'].split()[0]
            resposta = f"Olá, {nome_cli}! No que posso te ajudar?"
        else:
            resposta = "CPF não encontrado. Digite apenas os números do seu CPF para logar."
            
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)
    
    # ATENDIMENTO: Respostas baseadas na IA e no Banco
    else:
        dados = st.session_state.cliente_logado
        nome = dados['nome'].split()[0]
        
        # NORMALIZAÇÃO DO INPUT: Transforma a fala do usuário em minúscula
        # Isso resolve o problema de "Cartão" vs "cartao" do seu print
        prompt_normalizado = prompt.lower().strip()
        
        # IA decide a categoria
        pergunta_vet = vetorizador.transform([prompt_normalizado])
        categoria = modelo.predict(pergunta_vet)[0]
        
        # Mapeamento das respostas com as colunas corretas do SQL
        if categoria == "Cartão":
            # Aqui buscamos explicitamente a coluna 'limite'
            resposta = f"{nome}, o seu limite disponível no cartão é R$ {dados['limite']:.2f}."
        elif categoria == "Extrato":
            # Aqui buscamos explicitamente a coluna 'saldo'[cite: 2, 3]
            resposta = f"{nome}, seu saldo atual em conta é de R$ {dados['saldo']:.2f}."
        elif categoria == "Faturamento":
            resposta = f"{nome}, sua fatura atual é de R$ {dados['fatura']:.2f}."
        elif categoria == "Emprestimo":
            status = "disponível" if dados['emprestimo'] == 1 else "indisponível"
            resposta = f"{nome}, o serviço de empréstimo está {status} para o seu perfil."
        elif categoria == "Conta":
            resposta = f"Dados bancários: Agência {dados['num_agencia']} | Conta {dados['num_conta']}."
        else:
            resposta = f"Ainda estou aprendendo sobre isso, {nome}. Tente perguntar sobre saldo, limite ou fatura."
            
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)