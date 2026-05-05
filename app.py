import streamlit as st
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Configuração da página Web
st.set_page_config(page_title="Lumina Finanças", page_icon="🏦")

# --- 1. TREINAMENTO DA IA (MESMA LÓGICA ANTERIOR) ---
@st.cache_resource
def treinar_modelo():
    try:
        perguntas = pd.read_csv("perguntas.csv", skipinitialspace=True)
        frases = perguntas["frases"].astype(str).tolist()
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

# --- 2. FUNÇÃO DO BANCO DE DADOS ---
def buscar_cliente(cpf):
    try:
        with sqlite3.connect('luminaFinanças.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, fatura, saldo, limite FROM clientes WHERE cpf = ?', (cpf,))
            return cursor.fetchone()
    except Exception:
        return None

# --- 3. INTERFACE (SIDEBAR / LOGIN) ---
st.sidebar.title("🏦 Lumina Finanças")
cpf_raw = st.sidebar.text_input("Digite seu CPF para acessar:", placeholder="000.000.000-00")

# LIMPEZA: Remove pontos e traços caso o usuário digite
# Isso garante que '123.456.789-01' vire '12345678901'
cpf_limpo = cpf_raw.replace(".", "").replace("-", "").strip()

# Agora fazemos a busca usando a variável limpa
cliente = buscar_cliente(cpf_limpo)

if cliente:
    nome, fatura, saldo, limite = cliente
    st.sidebar.success(f"Conectado como: {nome}")
    st.sidebar.metric("Saldo em Conta", f"R$ {saldo:.2f}")
    st.sidebar.metric("Limite Disponível", f"R$ {limite:.2f}")
    
    # --- 4. LÓGICA DO CHAT ---
    st.title("Assistente Virtual Lumina")
    
    # Inicializa o histórico do chat na sessão web
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibe as mensagens do histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Campo de entrada do chat
    if prompt := st.chat_input("Como posso ajudar hoje?"):
        # Adiciona mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Processamento da IA
        pergunta_vet = vetorizador.transform([prompt.lower()])
        probs = modelo.predict_proba(pergunta_vet)[0]
        confianca = max(probs)
        categoria = modelo.predict(pergunta_vet)[0]

        # Resposta do Bot
        with st.chat_message("assistant"):
            if confianca > 0.55: # Filtro de estabilidade
                if categoria == "Faturamento":
                    resposta = f"Sua fatura atual é de R$ {fatura:.2f}."
                elif categoria == "Extrato":
                    resposta = f"O saldo atual da sua conta é R$ {saldo:.2f}."
                elif categoria == "Cartão":
                    遭到 = f"Seu limite total de crédito é R$ {limite:.2f}."
                elif categoria == "Investimento":
                    resposta = f"Vi aqui que você tem R$ {saldo:.2f} para investir. Qual modalidade prefere?"
                else:
                    resposta = "Entendi seu interesse, mas ainda estou aprendendo sobre esse assunto."
            else:
                resposta = "Desculpe, não entendi. Pode repetir? Tente algo sobre saldo ou fatura."
            
            st.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})

else:
    st.info("Aguardando acesso... Insira um CPF válido na barra lateral.")