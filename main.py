import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# --- 1. CONFIGURAÇÃO DA IA ---
# Usamos skipinitialspace=True para evitar erros com espaços invisíveis no CSV
perguntas = pd.read_csv(r"C:\Users\fabia\OneDrive\Área de Trabalho\BancoDigitalIA\perguntas.csv", skipinitialspace=True)

# Pegando as colunas conforme sua última imagem
frases = perguntas["frases"].astype(str).tolist()
categorias = perguntas["categoria"].astype(str).tolist()

vetorizador = CountVectorizer()
x = vetorizador.fit_transform(frases)
modelo = MultinomialNB()
modelo.fit(x, categorias)

# --- 2. FUNÇÃO DE BUSCA NO BANCO ---
def buscar_dados_cliente(cpf):
    try:
        with sqlite3.connect('luminaFinanças.db') as conexao:
            cursor = conexao.cursor()
            cursor.execute('SELECT nome, fatura, saldo, limite FROM clientes WHERE cpf = ?', (cpf,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erro ao acessar banco: {e}")
        return None

# --- 3. LOGICA DO CHATBOT ---
print("="*40)
print("🏦 LUMINA FINANÇAS - ASSISTENTE VIRTUAL")
print("="*40)

user_cpf = input("Por favor, digite seu CPF para começar: ")
dados = buscar_dados_cliente(user_cpf)

if dados:
    nome_cliente, valor_fatura, saldo_conta, limite_total = dados
    print(f"\nOlá, {nome_cliente}! Como posso ajudar você hoje?")
    
    while True:
        pergunta = input("\nVocê: ").lower()

        if pergunta == "sair":
            print("Chatbot: A Lumina Finanças agradece seu contato. Até logo!")
            break

        # IA prevendo a intenção
        pergunta_vet = vetorizador.transform([pergunta])
        categoria = modelo.predict(pergunta_vet)[0]

        # IMPORTANTE: Os nomes aqui devem ser IGUAIS aos da coluna 'categoria' do seu CSV
        if categoria == "Faturamento":
            print(f"Chatbot: Sua fatura atual é de R$ {valor_fatura:.2f}. Deseja o boleto por e-mail?")
        
        elif categoria == "Extrato":
            print(f"Chatbot: Seu saldo disponível é de R$ {saldo_conta:.2f}.")
        
        elif categoria == "Cartão":
            print(f"Chatbot: Vi aqui que seu limite total é R$ {limite_total:.2f}.")
            
        elif categoria == "Investimento":
            print(f"Chatbot: Você possui R$ {saldo_conta:.2f} disponíveis para investir em CDB ou Poupança.")
            
        elif categoria == "Atendimento":
            print("Chatbot: Vou te transferir para um especialista. Aguarde um momento.")
        
        elif categoria == "Segurança":
            print("Chatbot: Entendido. Por segurança, seu cartão foi bloqueado. Deseja solicitar uma nova via?")

        else:
            print(f"Chatbot: Desculpe, não entendi (Categoria: {categoria}). Pode repetir?")
else:
    print("Chatbot: CPF não encontrado em nossa base de dados.")