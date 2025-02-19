import qrcode
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Estados da conversa
MENU, NAME, CPF, ADDRESS, PHONE, CONFIRM, FINAL_OPTIONS = range(7)

# Função para gerar QR Code
def gerar_qrcode(link):
    qr = qrcode.make(link)
    qr_path = "/tmp/perfil_qrcode.png"  # Caminho temporário para salvar a imagem
    qr.save(qr_path)
    return qr_path

# Função para iniciar o bot
def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [
        ["Quero cadastrar meu animal!", "Minhas informações"],
        ["Conversar com um veterinário", "QR Code"]
    ]
    update.message.reply_text(
        "Olá! Sou o CãoVersador, a IA do CastraMóvel! 🐾\n\n"
        "Como posso lhe ajudar?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MENU

# Lidar com as opções do menu
def handle_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update.message.chat.id
    
    if text == "Quero cadastrar meu animal!":
        update.message.reply_text("Ótimo! Vamos começar o cadastro. Por favor, informe o seu nome completo.")
        return NAME
    elif text == "Minhas informações":
        user_data = context.user_data.get(user_id)
        if user_data:
            update.message.reply_text(
                "Aqui estão as suas informações cadastradas:\n\n"
                f"Nome: {user_data['name']}\n"
                f"CPF: {user_data['cpf']}\n"
                f"Endereço: {user_data['address']}\n"
                f"Telefone: {user_data['phone']}\n"
            )
        else:
            update.message.reply_text(
                "Você ainda não possui um cadastro. Deseja começar agora?\n\n"
                "Selecione uma opção:",
                reply_markup=ReplyKeyboardMarkup(
                    [["Quero cadastrar meu animal!", "Voltar ao menu"]], 
                    one_time_keyboard=True, 
                    resize_keyboard=True
                )
            )
        return MENU
    elif text == "Conversar com um veterinário":
        update.message.reply_text("Por favor, descreva sua dúvida para que um veterinário possa ajudá-lo.")
        return ConversationHandler.END
    elif text == "QR Code":
        user_data = context.user_data.get(user_id)
        if user_data:
            # Gerar o link do perfil e QR Code
            link_do_perfil = f"https://www.meusite.com.br/perfil/{user_id}"
            qr_path = gerar_qrcode(link_do_perfil)
            
            # Enviar QR Code para o usuário
            update.message.reply_text("Aqui está o seu QR Code para acessar seu perfil:")
            update.message.reply_photo(photo=open(qr_path, 'rb'))
        else:
            # Informar que não há cadastro e voltar ao menu
            update.message.reply_text(
                "Você ainda não possui um cadastro. Por favor, escolha uma das opções abaixo para continuar:",
                reply_markup=ReplyKeyboardMarkup(
                    [["Quero cadastrar meu animal!", "Voltar ao menu"]], 
                    one_time_keyboard=True, 
                    resize_keyboard=True
                )
            )
        return MENU
    else:
        update.message.reply_text("Desculpe, não entendi. Por favor, selecione uma das opções.")
        return MENU

# Coletar o nome completo
def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text(f"Obrigado, {context.user_data['name']}! Agora, por favor, informe o seu CPF.")
    return CPF

# Coletar o CPF (verificação de números)
def get_cpf(update: Update, context: CallbackContext) -> int:
    cpf = update.message.text
    if cpf.isdigit() and len(cpf) == 11:  # Verifica se o CPF é composto apenas por números e tem 11 dígitos
        context.user_data['cpf'] = cpf
        update.message.reply_text("Obrigado! Agora informe o seu endereço completo.")
        return ADDRESS
    else:
        update.message.reply_text("Por favor, informe um CPF válido (somente números e 11 dígitos). Tente novamente.")
        return CPF

# Coletar o endereço
def get_address(update: Update, context: CallbackContext) -> int:
    context.user_data['address'] = update.message.text
    update.message.reply_text("Ótimo! Agora, por favor, informe o seu telefone para contato.")
    return PHONE

# Coletar o telefone (verificação de números)
def get_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    if phone.isdigit() and len(phone) >= 10:  # Verifica se o telefone é composto apenas por números e tem pelo menos 10 dígitos
        context.user_data['phone'] = phone
        update.message.reply_text(
            "Cadastro quase completo! Aqui estão os dados fornecidos:\n\n"
            f"Nome: {context.user_data['name']}\n"
            f"CPF: {context.user_data['cpf']}\n"
            f"Endereço: {context.user_data['address']}\n"
            f"Telefone: {context.user_data['phone']}\n\n"
            "Está tudo correto? (Sim/Não)"
        )
        return CONFIRM
    else:
        update.message.reply_text("Por favor, informe um telefone válido (somente números e com pelo menos 10 dígitos). Tente novamente.")
        return PHONE

# Confirmar ou reiniciar o cadastro
def confirm_data(update: Update, context: CallbackContext) -> int:
    text = update.message.text.lower()
    user_id = update.message.chat.id
    if text == "sim":
        # Salvar os dados no contexto
        context.user_data[user_id] = context.user_data.copy()
        
        # Gerar o link do perfil
        link_do_perfil = f"https://www.meusite.com.br/perfil/{user_id}"
        
        # Gerar QR Code com o link do perfil
        qr_path = gerar_qrcode(link_do_perfil)
        
        # Enviar o QR Code para o usuário
        update.message.reply_text(
            "Cadastro finalizado com sucesso! Aqui está o seu QR Code para acessar seu perfil no aplicativo:"
        )
        update.message.reply_photo(photo=open(qr_path, 'rb'))
        
        # Perguntar se o usuário deseja fazer mais alguma coisa
        reply_keyboard = [["Voltar ao menu", "Finalizar conversa"]]
        update.message.reply_text(
            "Posso ajudar com algo mais?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return FINAL_OPTIONS
    elif text == "não":
        update.message.reply_text("Vamos reiniciar o cadastro. Por favor, informe o seu nome completo.")
        return NAME
    else:
        update.message.reply_text("Por favor, responda apenas com 'Sim' ou 'Não'.")
        return CONFIRM

# Função de opções finais (voltar ao menu ou finalizar conversa)
def final_options(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == "Voltar ao menu":
        return start(update, context)  # Reinicia a conversa a partir do menu
    elif text == "Finalizar conversa":
        return cancel(update, context)  # Finaliza a conversa
    else:
        update.message.reply_text(
            "Opção inválida. Por favor, escolha entre 'Voltar ao menu' ou 'Finalizar conversa'."
        )
        return FINAL_OPTIONS

# Cancelar o cadastro
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Conversa encerrada. Até mais!")
    return ConversationHandler.END

# Configuração principal do bot
def main():
    TOKEN = "TOKEN"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Configuração do fluxo de conversa
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [MessageHandler(Filters.text & ~Filters.command, handle_menu)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            CPF: [MessageHandler(Filters.text & ~Filters.command, get_cpf)],
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, get_address)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            CONFIRM: [MessageHandler(Filters.text & ~Filters.command, confirm_data)],
            FINAL_OPTIONS: [MessageHandler(Filters.text & ~Filters.command, final_options)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Inicia o bot
    print("Bot está rodando... Pressione Ctrl+C para sair.")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
