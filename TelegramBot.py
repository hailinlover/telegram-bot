import telebot

# 创建机器人对象
bot = telebot.TeleBot("YOUR_BOT_TOKEN")

# 存储待审核的稿件信息
pending_posts = {}


# 欢迎信息
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "欢迎使用投稿机器人！请您开始投稿。")


# 收集投稿信息
@bot.message_handler(func=lambda message: message.text)
def collect_info(message):
    global name, image, description, file_size, tags

    if not name:
        name = message.text
        bot.send_message(message.chat.id, "请您提供图片。")
    elif not image:
        if message.photo:
            image = message.photo[-1].file_id
            bot.send_message(message.chat.id, "请您提供描述。")
        else:
            bot.send_message(message.chat.id, "请您发送图片。")
    elif not description:
        description = message.text
        bot.send_message(message.chat.id, "请您提供文件大小。")
    elif not file_size:
        file_size = message.text
        bot.send_message(message.chat.id, "请您提供标签。")
    elif not tags:
        tags = message.text
        confirm_message = f"确认投稿信息：\n\n名称：{name}\n图片：{image}\n描述：{description}\n文件大小：{file_size}\n标签：{tags}\n\n是否确认投稿？"
        bot.send_message(message.chat.id, confirm_message,
                         reply_markup=telebot.types.InlineKeyboardMarkup(inline_keyboard=[
                             [telebot.types.InlineKeyboardButton("确认", callback_data="confirm"),
                              telebot.types.InlineKeyboardButton("取消", callback_data="cancel")]
                         ]))
    else:
        bot.send_message(message.chat.id, "请您重新开始投稿。")


# 投稿确认
@bot.callback_query_handler(func=lambda call: call.data == "confirm")
def confirm(call):
    # 将信息整理成格式化的文本
    post_text = f"名称：{name}\n图片：{image}\n描述：{description}\n文件大小：{file_size}\n标签：{tags}"

    # 生成一个唯一的投稿 ID
    post_id = str(len(pending_posts) + 1)

    # 将投稿信息存储到 pending_posts 字典中
    pending_posts[post_id] = {
        "name": name,
        "image": image,
        "description": description,
        "file_size": file_size,
        "tags": tags
    }

    # 发送到指定的 Telegram 频道，并标记为“待审核”
    bot.send_message(YOUR_CHANNEL_ID, f"投稿 {post_id}：\n\n{post_text}",
                     reply_markup=telebot.types.InlineKeyboardMarkup(inline_keyboard=[
                         [telebot.types.InlineKeyboardButton("批准", callback_data=f"approve_{post_id}"),
                          telebot.types.InlineKeyboardButton("拒绝", callback_data=f"reject_{post_id}")]
                     ]))

    # 清空变量
    global name, image, description, file_size, tags
    name = image = description = file_size = tags = None

    bot.send_message(call.message.chat.id, f"投稿成功！您的投稿 ID 为 {post_id}，已提交审核。")


# 取消投稿
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel(call):
    bot.send_message(call.message.chat.id, "已取消投稿。")


# 审核功能
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve(call):
    post_id = call.data.split("_")[1]
    # 将投稿信息发送到指定的 Telegram 频道，并标记为“已发布”
    post_info = pending_posts[post_id]
    post_text = f"名称：{post_info['name']}\n图片：{post_info['image']}\n描述：{post_info['description']}\n文件大小：{post_info['file_size']}\n标签：{post_info['tags']}"
    bot.send_message(YOUR_CHANNEL_ID, f"投稿 {post_id} 已批准发布。\n\n{post_text}")
    # 回复到当前机器人
    bot.send_message(call.message.chat.id, f"您的投稿 {post_id} 已通过审核。")
    # 从 pending_posts 字典中删除已审核的稿件
    del pending_posts[post_id]


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):
    post_id = call.data.split("_")[1]
    # 发送消息给管理员，要求输入驳回原因
    bot.send_message(call.message.chat.id, "请输入驳回原因：")
    # 设置一个状态，用于记录当前正在处理的投稿 ID
    bot.set_state(call.message.chat.id, "rejecting", call.message.chat.id)


@bot.message_handler(state="rejecting")
def handle_reject_reason(message):
    post_id = bot.get_state(message.chat.id)
    reject_reason = message.text
    # 将投稿信息发送到指定的 Telegram 频道，并标记为“已拒绝”，并附上驳回原因
    post_info = pending_posts[post_id]
    post_text = f"名称：{post_info['name']}\n图片：{post_info['image']}\n描述：{post_info['description']}\n文件大小：{post_info['file_size']}\n标签：{post_info['tags']}"
    bot.send_message(YOUR_CHANNEL_ID, f"投稿 {post_id} 已拒绝。\n\n驳回原因：{reject_reason}\n\n{post_text}")
    # 回复到当前机器人
    bot.send_message(message.chat.id, f"您的投稿 {post_id} 已被驳回。\n\n驳回原因：{reject_reason}")
    # 从 pending_posts 字典中删除已审核的稿件
    del pending_posts[post_id]
    # 清除状态
    bot.delete_state(message.chat.id)


# 查看审核中的稿件
@bot.message_handler(commands=["view_pending"])
def view_pending(message):
    if pending_posts:
        pending_list = "\n".join(f"投稿 {post_id}: {post_info['name']}" for post_id, post_info in pending_posts.items())
        bot.send_message(message.chat.id, f"当前审核中的稿件：\n\n{pending_list}")
    else:
        bot.send_message(message.chat.id, "当前没有处于审核中的稿件。")


# 启动机器人
bot.polling()
