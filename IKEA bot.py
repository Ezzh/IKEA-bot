import vk_api
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


# функция для загрузки фото в сообщение
def uploadphoto(photto):
    upload = VkUpload(vk)
    photo = upload.photo_messages(photto)
    owner_id = photo[0]['owner_id']
    photo_id = photo[0]['id']
    access_key = photo[0]['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    return attachment


# функция для написания сообщения
def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': get_random_id(),
                                'keyboard': keyboard.get_keyboard()})


# функция для преобразования id вк в имя пользователя
def fullname(user_id):
    user = vk.method("users.get", {"user_ids": user_id})  # вместо 1 подставляете айди нужного юзера
    fullname = user[0]['first_name'] + ' ' + user[0]['last_name']
    return fullname


# функция для коавиатуры работника
def klavarabotnik():
    global keyboard
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Пополнить склад / Поменять цену', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Подтвердить оплату', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Подтвержденные заказы', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Не подтвержденные заказы', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Доложить о готовности заказа', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Список товаров', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.NEGATIVE)


# клавиатура основного меню
def klavamenu():
    global keyboard
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Список товаров', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('FAQ', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Сделать заказ', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Функции для работников магазина', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Перейти к переписке с админом', color=VkKeyboardColor.SECONDARY)


# склад
def printsklad(event):
    result = ''
    for i in cur.execute("""SELECT * FROM tovari""").fetchall():
        result += f'№{i[0]} Товар: {i[1]} | Цена: {i[2]}\n'
    write_msg(event.user_id, result)


# унаследованный класс для обхода ограничения вконтакте по времени чтения лонгпула
class MyVkLongPoll(VkLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print('error', e)


# база дынных
con = sqlite3.connect("IKEAbd.sqlite")
cur = con.cursor()
# api
with open('token.txt', 'r') as file:
    token = file.readline()
vk = vk_api.VkApi(token=token)
# если есть чат сотрудников, сюда ввести id
chat_id_sotrudnik = None
# создание клавиатуры
keyboard = VkKeyboard(one_time=True)
version = 1.3
longpoll = MyVkLongPoll(vk)
# координаты магазина
koordiIKEA = (3050, 3350)
# цена доставки за 1км
pricedostavki = 5


# основная функция
def main():
    global keyboard
    klavamenu()
    # списки, в которые заносится id пользователей для отслеживания на каком меню они находятся
    zakaz = []
    zdacha = []
    popolnenie = []
    proverka = []
    pod = []
    admin = []
    podzakaz = {}
    # Основной цикл
    for event in longpoll.listen():
        # Если пришло новое сообщение
        if event.type == VkEventType.MESSAGE_NEW:
            # Если оно имеет метку для меня(то есть бота)
            if event.to_me:
                # Сообщение от пользователя
                request = event.text
                # если пользователь заказывает
                if event.user_id in zakaz:
                    if request == 'Вернуться в основное меню':
                        zakaz.remove(event.user_id)
                        klavamenu()
                        write_msg(event.user_id, 'Главное меню')
                    else:
                        try:
                            vvod = request.split()
                            tovar = \
                                cur.execute(f"""SELECT tovar FROM tovari WHERE id = {int(vvod[0])}""").fetchall()[0][0]
                            kolvo = int(vvod[1])
                            price = \
                                round(cur.execute(f"""SELECT price FROM tovari WHERE id = {int(vvod[0])}""").fetchall()[
                                          0][
                                          0] * kolvo, 2)
                            koordi = (int(vvod[2]), int(vvod[3]))
                            dostavka = round(((koordi[0] - koordiIKEA[0]) ** 2 + (
                                    koordi[1] - koordiIKEA[1]) ** 2) ** 0.5 // 1000 * pricedostavki, 2)
                            fullprice = price + dostavka
                            podzakaz.update([(event.user_id, [tovar, kolvo, fullprice, f'x{koordi[0]}y{koordi[1]}'])])
                            if not koordi[0] > 30000 and not koordi[1] > 30000 and not koordi[0] < -30000 and not \
                                    koordi[1] < -30000:
                                if kolvo > 0:
                                    write_msg(event.user_id,
                                              f'Стоимость товара в заказе: {price}\nСтоимость доставки: {dostavka}\nИтоговая цена: {fullprice}\n\nОтправте подтверждение оплаты(скрин перевода монет)')
                                    proverka.append(event.user_id)
                                    keyboard = VkKeyboard(one_time=True)
                                    keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.POSITIVE)
                                    write_msg(event.user_id, 'Проверка оплаты...')
                                else:
                                    write_msg(event.user_id, 'Количество товара указано некорректно')
                                zakaz.remove(event.user_id)
                            else:
                                zakaz.remove(event.user_id)
                                klavamenu()
                                write_msg(event.user_id, 'Нет таких кардинат!')
                                write_msg(event.user_id, 'Главное меню')

                        except Exception:
                            zakaz.remove(event.user_id)
                            klavamenu()
                            write_msg(event.user_id, 'Неверный формат ввода')
                # если сотрудник магазина подтверждает оплату
                elif event.user_id in pod:
                    try:
                        if request == 'Вернуться в основное меню':
                            pod.remove(event.user_id)
                            klavamenu()
                            write_msg(event.user_id, 'Главное меню')
                        else:
                            if (int(request),) in cur.execute("""SELECT id FROM Zakazi WHERE oplata = 0"""):
                                klavarabotnik()
                                cur.execute(f"""UPDATE Zakazi SET oplata = 1 WHERE id = {int(request)}""")
                                z = cur.execute(f"""SELECT * FROM Zakazi WHERE id = {int(request)}""").fetchall()[0]
                                con.commit()
                                if chat_id_sotrudnik:
                                    vk.method('messages.send', {'chat_id': chat_id_sotrudnik,
                                                                'message': f'Новый заказ!\n{z[1]}\n{z[2]} штук\nКоординаты: {z[4]}\nЗаказ от @id{z[5]}({fullname(z[5])})',
                                                                'random_id': get_random_id()})

                                idvk = \
                                    cur.execute(f"""SELECT idvk FROM Zakazi WHERE id = {int(request)}""").fetchall()[0][
                                        0]
                                tovar = \
                                    cur.execute(f"""SELECT Tovar FROM Zakazi WHERE id = {int(request)}""").fetchall()[
                                        0][0]

                                klavamenu()
                                write_msg(idvk,
                                          f'Ваш заказ на товар {tovar} подтвержден!\nВ скором времени ваш заказ будет доставлен')
                                pod.remove(event.user_id)
                                klavarabotnik()
                                write_msg(event.user_id, f'Оплата товара подтверждена!')
                            else:
                                klavarabotnik()
                                pod.remove(event.user_id)
                                write_msg(event.user_id, 'Такого заказа нет!')
                    except Exception as er:
                        pod.remove(event.user_id)
                        klavarabotnik()
                        write_msg(event.user_id, 'Неверный формат ввода!')
                        print(er)
                # пользователь отправляет на проверку оплату
                elif event.user_id in proverka:
                    if request == 'Вернуться в основное меню':
                        proverka.remove(event.user_id)
                        klavamenu()
                        write_msg(event.user_id, 'Главное меню')
                    else:
                        try:
                            if event.attachments['attach1_type'] and event.attachments['attach1_type'] == 'photo':
                                url = vk.method('messages.getById', {'message_ids': event.message_id})['items'][0][
                                    'attachments'][0]['photo']['sizes'][-1]['url']
                                cur.execute(
                                    """INSERT INTO Zakazi(Tovar, Kolvo, Price, koordi, idvk, urloplati) VALUES (?, ?, ?, ?, ?, ?)""",
                                    (podzakaz[event.user_id][0], podzakaz[event.user_id][1], podzakaz[event.user_id][2],
                                     podzakaz[event.user_id][3], event.user_id, url))
                                con.commit()
                                klavamenu()
                                write_msg(event.user_id,
                                          'Ваша заявка принята!\nОжидание проверки оплаты администрацией...')
                                if chat_id_sotrudnik:
                                    vk.method('messages.send', {'chat_id': chat_id_sotrudnik,
                                                                'message': f'Новые не подтвержденные заказы!',
                                                                'random_id': get_random_id()})
                                proverka.remove(event.user_id)
                            else:
                                klavamenu()
                                write_msg(event.user_id, 'Неправильный формат')
                                proverka.remove(event.user_id)
                        except Exception as er:
                            klavamenu()
                            write_msg(event.user_id, 'Неправильный формат')
                            proverka.remove(event.user_id)
                            print(er)
                # сдача заказа сотрудником
                elif event.user_id in zdacha:
                    try:
                        if (int(request),) in cur.execute("""SELECT id FROM Zakazi"""):
                            klavarabotnik()
                            cur.execute(f"""DELETE FROM Zakazi WHERE id = {int(request)}""")
                            con.commit()
                            write_msg(event.user_id, f'Заказ №{request} выполнен!')
                            if chat_id_sotrudnik:
                                vk.method('messages.send', {'chat_id': chat_id_sotrudnik,
                                                            'message': f'Заказ №{request} выполнен сотрудником: {fullname(event.user_id)}!',
                                                            'random_id': get_random_id()})

                            zdacha.remove(event.user_id)
                        else:
                            klavarabotnik()
                            write_msg(event.user_id, 'Такого заказа нет!')
                            zdacha.remove(event.user_id)
                    except Exception:
                        klavarabotnik()
                        write_msg(event.user_id, 'Неверный формат ввода')
                        zdacha.remove(event.user_id)
                # сотрудник пополняет склад
                elif event.user_id in popolnenie:
                    if request == 'Вернуться в основное меню':
                        popolnenie.remove(event.user_id)
                        klavamenu()
                        write_msg(event.user_id, 'Главное меню')
                    else:
                        try:
                            klavarabotnik()
                            vod = request.split()
                            resurs = vod[0]
                            cena = vod[1]
                            if (resurs,) in cur.execute("""SELECT tovar FROM tovari""").fetchall():
                                cur.execute(
                                    f"""UPDATE tovari SET price = {cena} WHERE tovar = '{resurs}'""")
                                write_msg(event.user_id, f'Цена успешно обновлена')
                            else:
                                cur.execute(f"""INSERT INTO tovari(tovar, price) VALUES('{resurs}', {cena})""")
                                write_msg(event.user_id, f'Новый товар: {resurs} добавлен на склад!')
                            popolnenie.remove(event.user_id)
                        except Exception:
                            popolnenie.remove(event.user_id)
                            klavarabotnik()
                            write_msg(event.user_id, 'Неверный формат ввода')

                elif event.user_id in admin:
                    if request == 'Перейти к переписке с ботом':
                        klavamenu()
                        write_msg(event.user_id, 'Основное меню')
                        admin.remove(event.user_id)

                elif request == 'Не подтвержденные заказы':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        klavarabotnik()
                        result = ''
                        if cur.execute("""SELECT * FROM Zakazi WHERE oplata = 0""").fetchall():
                            for i in cur.execute("""SELECT * FROM Zakazi WHERE oplata = 0""").fetchall():
                                result += f'Заказ №{i[0]} Товар: {i[1]} Количество: {i[2]} Цена: {i[3]} Координаты: {i[4]} Вк: @id{i[5]}({fullname(i[5])})\nОплата:\n{i[7]}'
                            write_msg(event.user_id, result)
                        else:
                            write_msg(event.user_id, 'Заказов нет!')
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Подтвердить оплату':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        if cur.execute("""SELECT * FROM Zakazi WHERE oplata = 0""").fetchall():
                            result = ''
                            for i in cur.execute("""SELECT * FROM Zakazi WHERE oplata = 0""").fetchall():
                                result += f'Заказ №{i[0]} Товар: {i[1]} Количество: {i[2]} Цена: {i[3]} Координаты: {i[4]} Вк: @id{i[5]}({fullname(i[5])})\nОплата:\n{i[7]}'
                            keyboard = VkKeyboard(one_time=True)
                            keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.POSITIVE)
                            write_msg(event.user_id, result)
                            write_msg(event.user_id, 'Оплату какого товара вы хотите подтвердить?')
                            pod.append(event.user_id)
                        else:
                            klavarabotnik()
                            write_msg(event.user_id, 'Не подтвержденных заказов нет!')
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Вернуться в основное меню' or request == 'Меню' or request == 'меню' or request == 'Начать':
                    klavamenu()
                    write_msg(event.user_id, 'Главное меню')

                elif request == 'FAQ':
                    klavamenu()
                    write_msg(event.user_id,
                              f'Бот сделан для приема заказов на товары из сети магазинов IKEA\nТекущая версия бота: {version}\nО багах и предложениях писать в лс: https://vk.com/ezzh32')

                elif request == 'Список товаров':
                    klavamenu()
                    printsklad(event)

                elif request == 'Сделать заказ':
                    keyboard = VkKeyboard(one_time=True)
                    keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.POSITIVE)
                    printsklad(event)
                    write_msg(event.user_id, f'Стоимость доставки {pricedostavki} монет за 1 км')
                    write_msg(event.user_id,
                              'Выберите номер товара, количество,ваши координаты(X и Z)\nПример: 2 14 500 -200')
                    zakaz.append(event.user_id)

                elif request == 'Подтвержденные заказы':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        klavarabotnik()
                        result = ''
                        if cur.execute("""SELECT * FROM Zakazi WHERE oplata = 1""").fetchall():
                            for i in cur.execute("""SELECT * FROM Zakazi WHERE oplata = 1""").fetchall():
                                result += f'Заказ №{i[0]} Товар: {i[1]} Количество: {i[2]} Цена: {i[3]} Координаты: {i[4]} Вк: @id{i[5]}({fullname(i[5])})\n'
                            write_msg(event.user_id, result)
                        else:
                            write_msg(event.user_id, 'Заказов нет!')
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Доложить о готовности заказа':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        if cur.execute("""SELECT * FROM Zakazi WHERE oplata = 1""").fetchall():
                            keyboard = VkKeyboard(one_time=True)
                            keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.POSITIVE)
                            result = ''
                            for i in cur.execute("""SELECT * FROM Zakazi WHERE oplata = 1""").fetchall():
                                result += f'Заказ №{i[0]} Товар: {i[1]} Количество: {i[2]} Цена: {i[3]} Координаты: {i[4]} Вк: @id{i[5]}({fullname(i[5])})\n'
                            write_msg(event.user_id, result)
                            write_msg(event.user_id, "Какой номер заказа вы выполнили?")
                            zdacha.append(event.user_id)
                        else:
                            klavarabotnik()
                            write_msg(event.user_id, "Заказов нет!")
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Функции для работников магазина':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        klavarabotnik()
                        write_msg(event.user_id, "Меню работника")
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Пополнить склад / Поменять цену':
                    if (event.user_id,) in cur.execute("""SELECT idvk FROM Workers""").fetchall():
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button('Вернуться в основное меню', color=VkKeyboardColor.POSITIVE)
                        popolnenie.append(event.user_id)
                        printsklad(event)
                        write_msg(event.user_id,
                                  'Название товара(без пробелов)\nЦена за штуку\nПример: ЗолотыеЯблоки 200')
                    else:
                        klavamenu()
                        write_msg(event.user_id, "Нет доступа")

                elif request == 'Перейти к переписке с админом':
                    admin.append(event.user_id)
                    keyboard = VkKeyboard(one_time=True)
                    keyboard.add_button('Перейти к переписке с ботом', color=VkKeyboardColor.POSITIVE)
                    write_msg(event.user_id, 'Связываюсь с админом....\nМожете набирать сообщение')

                else:
                    klavamenu()
                    write_msg(event.user_id, "Несуществующая команда")


if __name__ == '__main__':
    main()
