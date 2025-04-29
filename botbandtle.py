import telebot
from telebot import types
import smtplib
import threading
import time
import ssl
import os
# ====== إعدادات البوت ======
TOKEN = os.environ.get("TOKEN")
print(f"TOKEN VALUE: {TOKEN}")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
bot = telebot.TeleBot(TOKEN)

# ====== متغير رسالة الترحييب القابلة للتعديل ======
welcome_text = "مرحباً بك في بوت البلاغات!"  # يمكن تعديله عبر الزر

# ====== تخزين بيانات المستخدم وحقوق الاستخدام ======
user_data = {}  # بيانات الإرسال لكل مستخدم
allowed_users = [ADMIN_ID]  # قائمة المسموح لهم باستخدام البوت


# ====== إنشاء لوحة الأزرار الرئيسية ======
def get_main_menu(is_admin=False):
    menu = types.InlineKeyboardMarkup(row_width=2)
    # إعدادات الإرسال
    menu.add(
        types.InlineKeyboardButton("➕ إضافة بريد الإرسال",
                                   callback_data='add_email'),
        types.InlineKeyboardButton("🔑 إضافة كلمة مرور التطبيقات",
                                   callback_data='add_password'),
        types.InlineKeyboardButton("🎯 تحديد بريد الاستقبال",
                                   callback_data='set_target_email'),
        types.InlineKeyboardButton("📝 تحديد الموضوع",
                                   callback_data='set_subject'),
        types.InlineKeyboardButton("📄 تحديد نص الرسالة",
                                   callback_data='set_message'),
        types.InlineKeyboardButton("⏱️ تحديد وقت الانتظار",
                                   callback_data='set_delay'),
        types.InlineKeyboardButton("#️⃣ تحديد عدد البلاغات",
                                   callback_data='set_count'),
        types.InlineKeyboardButton("🚀 بدء الإرسال",
                                   callback_data='start_sending'),
        types.InlineKeyboardButton("🛑 إيقاف الإرسال",
                                   callback_data='stop_sending'))
    #  إدارة المستخدمين للمدير فقط والادمن
    if is_admin:
        menu.add(
            types.InlineKeyboardButton("📋 إدارة المستخدمين",
                                       callback_data='manage_users'),
            types.InlineKeyboardButton("✏️ تعديل رسالة الترحيب",
                                       callback_data='edit_welcome'))
    return menu


# ====== لوحة إدارة المستخدمين ======
managemenu = types.InlineKeyboardMarkup(row_width=2)
managemenu.add(
    types.InlineKeyboardButton("👥 عرض عدد المستخدمين",
                               callback_data='show_count'),
    types.InlineKeyboardButton("📜 عرض قائمة المستخدمين",
                               callback_data='show_list'),
    types.InlineKeyboardButton("➕ إضافة مستخدم", callback_data='add_user'),
    types.InlineKeyboardButton("➖ حذف مستخدم", callback_data='remove_user'),
    types.InlineKeyboardButton("🗑️ حذف جميع المستخدمين",
                               callback_data='clear_users'),
    types.InlineKeyboardButton("↩️ رجوع", callback_data='back_main'))


# ====== أوامر الروبوت ======
@bot.message_handler(commands=['start'])
def start_cmd(message):
    cid = message.chat.id
    if cid not in allowed_users:
        bot.send_message(
            cid,
            "🚫 أنت غير مصرح لك باستخدام هذا البوت. تواصل مع المالك لتفعيل حسابك: @uchcf"
        )
        return
    # تهيئة بيانات المستخدم
    user_data[cid] = {'stop': False}
    # إرسال رسالة الترحيب مع الأزرار
    menu = get_main_menu(is_admin=(cid == ADMIN_ID))
    bot.send_message(cid, welcome_text, reply_markup=menu)


# أمر لإظهار القائمة الرئيسية
@bot.message_handler(commands=['menu'])
def menu_cmd(message):
    cid = message.chat.id
    if cid not in allowed_users:
        bot.send_message(cid, "🚫 أنت غير مصرح لك.")
        return
    menu = get_main_menu(is_admin=(cid == ADMIN_ID))
    bot.send_message(cid, welcome_text, reply_markup=menu)


# ====== معالجة الأزرار ======
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    if cid not in allowed_users:
        bot.answer_callback_query(call.id, "🚫 غير مصرح لك.")
        return
    data = call.data
    # إدارة المستخدمين
    if data == 'manage_users' and cid == ADMIN_ID:
        bot.edit_message_text("📋 إدارة المستخدمين:",
                              chat_id=cid,
                              message_id=call.message.message_id,
                              reply_markup=managemenu)
        return
    if data == 'back_main':
        menu = get_main_menu(is_admin=True)
        bot.edit_message_text(welcome_text,
                              chat_id=cid,
                              message_id=call.message.message_id,
                              reply_markup=menu)
        return
    # عرض عدد المستخدمين
    if data == 'show_count' and cid == ADMIN_ID:
        bot.send_message(cid, f"👥 عدد المستخدمين: {len(allowed_users)}")
        return
    # عرض قائمة المستخدمين
    if data == 'show_list' and cid == ADMIN_ID:
        bot.send_message(
            cid, f"📜 قائمة المستخدمين ({len(allowed_users)}):\n" +
            "\n".join(str(u) for u in allowed_users))
        return
    # إضافة مستخدم
    if data == 'add_user' and cid == ADMIN_ID:
        msg = bot.send_message(cid, "✍️ أرسل معرف المستخدم (ID) لإضافته:")
        bot.register_next_step_handler(msg, do_add_user)
        return
    # حذف مستخدم
    if data == 'remove_user' and cid == ADMIN_ID:
        msg = bot.send_message(cid, "✍️ أرسل معرف المستخدم (ID) لحذفه:")
        bot.register_next_step_handler(msg, do_remove_user)
        return
    # حذف جميع المستخدمين
    if data == 'clear_users' and cid == ADMIN_ID:
        allowed_users.clear()
        allowed_users.append(ADMIN_ID)
        bot.send_message(cid, "🗑️ تم حذف جميع المستخدمين.")
        return
    # تعديل رسالة الترحيب
    if data == 'edit_welcome' and cid == ADMIN_ID:
        msg = bot.send_message(cid, "✍️ أرسل نص رسالة الترحيب الجديد:")
        bot.register_next_step_handler(msg, save_welcome)
        return
    # أوامر الإرسال
    if data == 'add_email':
        msg = bot.send_message(cid, "📩 أرسل الآن بريد الإرسال:")
        bot.register_next_step_handler(msg, save_email)
        return
    if data == 'add_password':
        msg = bot.send_message(cid, "🔑 أرسل الآن كلمة مرور التطبيقات:")
        bot.register_next_step_handler(msg, save_password)
        return
    if data == 'set_target_email':
        msg = bot.send_message(cid, "🎯 أرسل الآن البريد المستهدف:")
        bot.register_next_step_handler(msg, save_target_email)
        return
    if data == 'set_subject':
        msg = bot.send_message(cid, "📝 أرسل الآن الموضوع:")
        bot.register_next_step_handler(msg, save_subject)
        return
    if data == 'set_message':
        msg = bot.send_message(cid, "📄 أرسل الآن نص الرسالة:")
        bot.register_next_step_handler(msg, save_message)
        return
    if data == 'set_delay':
        msg = bot.send_message(cid, "⏱️ أرسل الوقت بالثواني بين البلاغات:")
        bot.register_next_step_handler(msg, save_delay)
        return
    if data == 'set_count':
        msg = bot.send_message(cid, "#️⃣ أرسل عدد البلاغات:")
        bot.register_next_step_handler(msg, save_count)
        return
    if data == 'stop_sending':
        user_data[cid]['stop'] = True
        bot.answer_callback_query(call.id, "🛑 تم إيقاف الإرسال.")
        return
    if data == 'start_sending':
        threading.Thread(target=start_sending_process,
                         args=(cid, call.message.message_id)).start()
        return


# ====== دوال إدارة المستخدمين ======
def do_add_user(message):
    try:
        uid = int(message.text)
        if uid not in allowed_users:
            allowed_users.append(uid)
            bot.send_message(message.chat.id, "✅ تم إضافة المستخدم.")
        else:
            bot.send_message(message.chat.id, "⚠️ المستخدم موجود بالفعل.")
    except:
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقمًا.")


def do_remove_user(message):
    try:
        uid = int(message.text)
        if uid in allowed_users and uid != ADMIN_ID:
            allowed_users.remove(uid)
            bot.send_message(message.chat.id, "✅ تم حذف المستخدم.")
        else:
            bot.send_message(message.chat.id, "⚠️ لا يمكن حذف هذا المعرف.")
    except:
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يكون رقمًا.")


# ====== دوال حفظ رسالة الترحيب ======
def save_welcome(message):
    global welcome_text
    welcome_text = message.text
    bot.send_message(message.chat.id, "✅ تم تحديث رسالة الترحيب بنجاح.")


# ====== دوال حفظ بيانات الإرسال ======
def save_email(message):
    user_data[message.chat.id]['email'] = message.text
    bot.send_message(message.chat.id, "✅ تم حفظ البريد بنجاح.")


def save_password(message):
    user_data[message.chat.id]['password'] = message.text
    bot.send_message(message.chat.id, "✅ تم حفظ كلمة المرور بنجاح.")


def save_target_email(message):
    user_data[message.chat.id]['target_email'] = message.text
    bot.send_message(message.chat.id, "✅ تم حفظ البريد المستهدف بنجاح.")


def save_subject(message):
    user_data[message.chat.id]['subject'] = message.text
    bot.send_message(message.chat.id, "✅ تم حفظ الموضوع بنجاح.")


def save_message(message):
    user_data[message.chat.id]['message'] = message.text
    bot.send_message(message.chat.id, "✅ تم حفظ نص الرسالة بنجاح.")


# ====== دوال حفظ الوقت والعدد ======
def save_delay(message):
    try:
        user_data[message.chat.id]['delay'] = int(message.text)
        bot.send_message(message.chat.id, "✅ تم حفظ وقت الانتظار بنجاح.")
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ الرجاء إدخال رقم صالح لوقت الانتظار.")


def save_count(message):
    try:
        user_data[message.chat.id]['count'] = int(message.text)
        bot.send_message(message.chat.id, "✅ تم حفظ عدد البلاغات بنجاح.")
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ الرجاء إدخال رقم صالح لعدد البلاغات.")


# ====== تنفيذ الإرسال مع دعم الإيقاف ======
def start_sending_process(chat_id, message_id):
    data = user_data.get(chat_id, {})
    email = data.get('email')
    password = data.get('password')
    target = data.get('target_email')
    subject = data.get('subject')
    body = data.get('message')
    delay = data.get('delay', 5)
    count = data.get('count', 1)
    if not all([email, password, target, subject, body]):
        bot.send_message(chat_id, "⚠️ تأكد من إدخال جميع البيانات قبل البدء.")
        return
    success = 0
    failed = 0
    batch_size = 5
    bot.edit_message_text(
        f"🚀 جاري بدء الإرسال...\n\n✅ البلاغات الناجحة: {success}\n❌ البلاغات الفاشلة: {failed}",
        chat_id=chat_id,
        message_id=message_id)
    for i in range(0, count, batch_size):
        if user_data[chat_id].get('stop'):
            break
        current = min(batch_size, count - i)
        for _ in range(current):
            if user_data[chat_id].get('stop'):
                break
            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls(context=ssl.create_default_context())
                    server.login(email, password)
                    msg = f"Subject: {subject}\n\n{body}"
                    server.sendmail(email, target, msg.encode('utf-8'))
                success += 1
            except:
                failed += 1
            bot.edit_message_text(
                f"🚀 جاري الإرسال...\n\n✅ البلاغات الناجحة: {success}\n❌ البلاغات الفاشلة: {failed}",
                chat_id=chat_id,
                message_id=message_id)
        if i + batch_size < count and not user_data[chat_id].get('stop'):
            time.sleep(delay)
    final_text = f"🏁 {'تم الإيقاف.' if user_data[chat_id].get('stop') else 'تم الانتهاء!'}\n\n✅ البلاغات الناجحة: {success}\n❌ البلاغات الفاشلة: {failed}"
    bot.edit_message_text(final_text, chat_id=chat_id, message_id=message_id)
    user_data[chat_id]['stop'] = False


# ====== تشغيل البوت ======
bot.remove_webhook()
bot.polling(non_stop=True)
