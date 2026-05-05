import sqlite3

def gerenciar_banco():
    with sqlite3.connect('luminaFinanças.db') as conexao:
        cursor = conexao.cursor()
        
        # 1. Coletando dados pelo terminal
        print("\n--- Cadastro de Novo Cliente ---")
        nome = input("Digite o nome: ")
        idade = int(input("Digite a idade: "))
        cpf = int(input("Digite o CPF (apenas números): "))
        fatura = float(input("Valor da fatura atual: "))
        limite = float(input("Limite total: "))
        saldo = float(input("Saldo em conta: "))
        
        # Para o booleano, vamos simplificar para o usuário digitar S ou N
        tem_emp = input("Possui empréstimo? (S/N): ").upper()
        emprestimo = 1 if tem_emp == 'S' else 0
        
        num_conta = int(input("Número da conta: "))
        num_agencia = int(input("Número da agência: "))

        # 2. Inserindo no Banco
        novo_usuario = (nome, idade, cpf, fatura, limite, saldo, emprestimo, num_conta, num_agencia)
        
        cursor.execute('''
            INSERT INTO clientes (nome, idade, cpf, fatura, limite, saldo, emprestimo, num_conta, num_agencia) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', novo_usuario)
        
        conexao.commit()
        print(f"\nUsuário {nome} cadastrado com sucesso!")

        # 3. Consultar para ver se ele entrou mesmo
        cursor.execute('SELECT * FROM clientes')
        for linha in cursor.fetchall():
            print(linha)

if __name__ == "__main__":
    gerenciar_banco()