import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, CallbackContext

TOKEN = "7710466234:AAF0pgfBMT7eAweguOIO3xGkg7j9mVqZHto"

# Estados do cadastro
NOME, CPF, CEP, CONFIRMAR_ENDERECO, TELEFONE, NOME_ANIMAL, ESPECIE = range(7)

cadastros = {}

async def start(update: Update, context: CallbackContext):
    """Mostra o menu inicial."""
    keyboard = [
        [InlineKeyboardButton("🐶 Cadastrar meu animal", callback_data="cadastrar_animal")],
        [InlineKeyboardButton("💬 Falar com um veterinário", callback_data="falar_veterinario")],
        [InlineKeyboardButton("📋 Minhas informações", callback_data="minhas_info")],
        [InlineKeyboardButton("❓ Dúvidas", callback_data="duvidas")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma opção abaixo:", reply_markup=reply_markup)

async def button_click(update: Update, context: CallbackContext):
    """Inicia o cadastro ou responde a outras opções do menu."""
    query = update.callback_query
    await query.answer()

    if query.data == "cadastrar_animal":
        await query.message.reply_text("Vamos começar o cadastro. Qual é o seu nome completo?")
        return NOME
    else:
        responses = {
            "falar_veterinario": "Em breve, um veterinário entrará em contato com você.",
            "minhas_info": "Suas informações ainda não estão cadastradas. Use a opção 'Cadastrar meu animal'.",
            "duvidas": "Se tiver dúvidas, entre em contato pelo e-mail suporte@meuvet.com."
        }
        await query.message.reply_text(responses.get(query.data, "Opção inválida!"))
        return ConversationHandler.END

async def get_nome(update: Update, context: CallbackContext):
    """Recebe o nome do dono."""
    context.user_data["nome"] = update.message.text
    await update.message.reply_text("Ótimo! Agora informe seu CPF:")
    return CPF

async def get_cpf(update: Update, context: CallbackContext):
    """Recebe o CPF do dono."""
    context.user_data["cpf"] = update.message.text
    await update.message.reply_text("Agora informe seu CEP:")
    return CEP

async def get_cep(update: Update, context: CallbackContext):
    """Recebe o CEP, consulta o endereço e pede confirmação."""
    cep = update.message.text
    context.user_data["cep"] = cep

    # Consulta o endereço pelo ViaCEP
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url).json()

    if "erro" in response:
        await update.message.reply_text("CEP inválido! Tente novamente.")
        return CEP

    endereco = f"{response['logradouro']}, {response['bairro']}, {response['localidade']} - {response['uf']}"
    context.user_data["endereco"] = endereco

    keyboard = [
        [InlineKeyboardButton("✅ Sim", callback_data="confirmar_endereco")],
        [InlineKeyboardButton("❌ Não", callback_data="recusar_endereco")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Confirme seu endereço: {endereco}", reply_markup=reply_markup)
    return CONFIRMAR_ENDERECO

async def confirmar_endereco(update: Update, context: CallbackContext):
    """Confirma o endereço e pede o telefone."""
    query = update.callback_query
    await query.answer()

    # Solicita o telefone
    keyboard = [[KeyboardButton("📱 Enviar meu telefone", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await query.message.reply_text("Por favor, compartilhe seu telefone tocando no botão abaixo:", reply_markup=reply_markup)

    return TELEFONE

async def recusar_endereco(update: Update, context: CallbackContext):
    """Caso o endereço não esteja correto, pede para o usuário inserir um novo CEP."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Por favor, insira o CEP correto:")
    return CEP

async def get_telefone(update: Update, context: CallbackContext):
    """Recebe o telefone do usuário."""
    contato = update.message.contact
    context.user_data["telefone"] = contato.phone_number

    await update.message.reply_text("Agora, informe o nome do seu animal:")
    return NOME_ANIMAL

async def get_nome_animal(update: Update, context: CallbackContext):
    """Recebe o nome do animal."""
    context.user_data["nome_animal"] = update.message.text

    # Pergunta se é canino ou felino
    keyboard = [
        [InlineKeyboardButton("🐶 Canino", callback_data="canino")],
        [InlineKeyboardButton("🐱 Felino", callback_data="felino")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Seu pet é um Canino ou Felino?", reply_markup=reply_markup)
    return ESPECIE

async def get_especie(update: Update, context: CallbackContext):
    """Recebe se o pet é Canino ou Felino."""
    query = update.callback_query
    await query.answer()

    context.user_data["especie"] = "Canino" if query.data == "canino" else "Felino"

    user_id = query.from_user.id
    cadastros[user_id] = context.user_data.copy()

    await query.message.reply_text(
        f"✅ Cadastro concluído!\n\n"
        f"👤 **Dono:** {context.user_data['nome']}\n"
        f"📍 **Endereço:** {context.user_data['endereco']}\n"
        f"📞 **Telefone:** {context.user_data['telefone']}\n"
        f"🐾 **Pet:** {context.user_data['nome_animal']} ({context.user_data['especie']})\n"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Cancela o cadastro."""
    await update.message.reply_text("Cadastro cancelado.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern="^cadastrar_animal$")],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nome)],
            CPF: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cpf)],
            CEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cep)],
            CONFIRMAR_ENDERECO: [
                CallbackQueryHandler(confirmar_endereco, pattern="^confirmar_endereco$"),
                CallbackQueryHandler(recusar_endereco, pattern="^recusar_endereco$")
            ],
            TELEFONE: [MessageHandler(filters.CONTACT, get_telefone)],
            NOME_ANIMAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nome_animal)],
            ESPECIE: [CallbackQueryHandler(get_especie, pattern="^(canino|felino)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
