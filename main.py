import telebot
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

bot = telebot.TeleBot(os.environ.get('TOKEN'))
print(bot.get_me())

alibigshop_id = str(-1001201269123)
ali_toy_id = str(-1001475664667)
xiaomiacc_id = str(-1001438676034)
aliexpress_cars_id = str(-1001453028896)
op7acc_id = str(-1001290739042)
iphoneacc_id = str(-1001419650223)
sgsacc_id = str(-1001183912718)
huaweiacc_id = str(-1001331199379)

# hash от ePN для создания партнерской ссылки
deeplink_hash = os.environ.get('DEEPLINK')

# url = input('Give Me URL: ').split(' ')[0]
# Коды смайлов для вставки в сообщение
star_smile = u'\U00002B50'
dollar_bag_smile = u'\U0001F4B0'
review_smile = u'\U0001F4AC'
box_smile = u'\U0001F4E6'
link_smile = u'\U0001F449'

PATTERN_SCLICK_MSG = re.compile('https://s.click.aliexpress.com/[A-Za-z].*/[_A-Za-z0-9].*')
PATTERN_HTML_MSG = re.compile('/item/[\\-0-9/A-Za-z].*.html')
PATTERN_ALIPUB_MSG = re.compile('http://ali.pub/[0-9A-Za-z].*')
PATTERN_PROD_ID = re.compile('[0-9].*.html')


def get_id_alipub(link):
    req = requests.get(link)
    soup = BeautifulSoup(req.text, "lxml")
    try:
        product_id = soup.find(property='al:android:url')['content'].split('productId=')[1].split('&')[0] + '.html'
    except TypeError:
        product_id = PATTERN_PROD_ID.findall(soup.get_text())
        if product_id:
            product_id = product_id[0]
    return product_id


def get_id_sclick(link):
    req = requests.get(link)
    soup = BeautifulSoup(req.text, "lxml")
    try:
        product_id_1 = soup.find(property='al:android:url')['content'].split('https://')[1].split('?')[0].split('/')[-1]
    except Exception:
        product_id_1 = ''
    try:
        product_id_2 = soup.find(rel='alternate', hreflang='ru')['href'].split('/')[-1]
    except Exception:
        product_id_2 = ''
    try:
        product_id_3 = soup.find(property='og:url')['content'].split("rdtUrl=")[1].split('%3Fsrc')[0].split('2F')[-1]
    except Exception:
        product_id_3 = ''
    if product_id_1:
        return product_id_1
    elif product_id_2:
        return product_id_2
    elif product_id_3:
        return product_id_3
    else:
        return "maintain.html"


def get_id_html(link):
    splitted_link = link.split('/')[-1]
    product_id = splitted_link
    return product_id


def get_usd_price(m_url):
    cookie = {'aep_usuc_f': 'site=rus&c_tp=USD&region=RU&b_locale=ru_RU', 'intl_locale': 'ru_RU',
              'xman_us_f': 'x_locale=ru_RU&x_l=0'}
    m_req = requests.get(m_url, cookies=cookie)
    m_soup = BeautifulSoup(m_req.text, "lxml")
    try:
        data_json = json.loads(m_soup.find('script').text.strip())
    except Exception:
        current_price = ''
    try:
        current_price = data_json['offers']['price'] + ' ' + data_json['offers']['priceCurrency']
    except KeyError:
        try:
            current_price = data_json['offers']['lowPrice'] + ' - ' + data_json['offers']['highPrice'] + \
                            ' ' + data_json['offers']['priceCurrency']
        except KeyError:
            current_price = ''
    return current_price


# Преобразовываем ссылку в мобильную версию, переходим по ней и забираем информацию о товаре
def get_prod_info(html_id):
    m_url = 'https://m.ru.aliexpress.com/item/' + html_id
    pc_url = 'https://ru.aliexpress.com/item/' + html_id
    cookie = {'aep_usuc_f': 'site=rus&c_tp=RUB&region=RU&b_locale=ru_RU', 'intl_locale': 'ru_RU',
              'xman_us_f': 'x_locale=ru_RU&x_l=0'}
    m_req = requests.get(m_url, cookies=cookie)
    m_soup = BeautifulSoup(m_req.text, "lxml")
    sss = m_soup.find('script').text.strip()
    print('Нужная строка джсон', sss)
    data_json = json.loads(sss)
    try:
        img_url = data_json['image']
    except KeyError:
        img_url = ''
    try:
        rus_title = data_json['name']
    except KeyError:
        rus_title = ''
    try:
        user_count = str(data_json['aggregateRating']['ratingCount'])
    except KeyError:
        user_count = 'Нет Отзывов'
    try:
        user_rating = str(data_json['aggregateRating']['ratingValue'])
    except KeyError:
        user_rating = 'Нет Рейтинга'
    try:
        current_price = data_json['offers']['price'] + ' ' + data_json['offers']['priceCurrency']
    except KeyError:
        try:
            current_price = data_json['offers']['lowPrice'] + ' - ' + data_json['offers']['highPrice'] + \
                            ' ' + data_json['offers']['priceCurrency']
        except KeyError:
            current_price = ''
    usd_price = get_usd_price(m_url)
    return user_count, user_rating, img_url, rus_title, pc_url, current_price, usd_price


# Сокращаем промо ссылку
def get_short_link(long_link):
    get_url_link = 'http://save.ali.pub/get-url.php'
    form_data = {
        'url': long_link,
        'submit': 'submit',
    }
    response = requests.post(get_url_link, data=form_data)
    soap = BeautifulSoup(response.text, "lxml")
    try:
        result = soap.find('div', {'class': 'result'}).text.split('Сокращение: ')[1].strip()
    except AttributeError:
        result = long_link
    return result


def create_button(btn_text, btn_ch_id, filename):
    btn = telebot.types.InlineKeyboardButton(text=btn_text,
                                             callback_data=btn_text + '::' + btn_ch_id + '::' + filename)
    return btn


def inline_markup_keyboard(filename):
    keyboard = telebot.types.InlineKeyboardMarkup()
    toy_channel_button = create_button('@ali_toy', ali_toy_id, filename)
    bigshop_channel_button = create_button('@alibigshop', alibigshop_id, filename)
    xiaomi_channel_button = create_button('@xiaomiacc', xiaomiacc_id, filename)
    car_channel_button = create_button('@aliexpress_cars', aliexpress_cars_id, filename)
    op7_channel_button = create_button('@oneplus7acc', op7acc_id, filename)
    iphone_channel_button = create_button('@iphoneacc', iphoneacc_id, filename)
    sgs_channel_button = create_button('@sgsacc', sgsacc_id, filename)
    huawei_channel_button = create_button('@huaweiacc', huaweiacc_id, filename)
    edit_button = telebot.types.InlineKeyboardButton(text='Изменить описание', callback_data='edit::' + filename)
    keyboard.row(bigshop_channel_button, toy_channel_button, car_channel_button)
    keyboard.row(iphone_channel_button, sgs_channel_button, huawei_channel_button)
    keyboard.row(xiaomi_channel_button, op7_channel_button)
    keyboard.row(edit_button)
    return keyboard


def send_parsed_message(message, html_prod_id):
    product_reviews, product_rating, product_img_url, title, product_full_url, price, usd_price = get_prod_info(
        html_prod_id)
    if title and product_img_url and price:
        # Получаем числовой ID Товара для создания промо ссылки
        prod_id = html_prod_id.split('.')[0]
        # Создаем промо ссылку для последующего укорачивания
        promo_link = 'http://alipromo.com/redirect/product/' + deeplink_hash + '/' + prod_id + '/ru'
        short_link = get_short_link(promo_link)
        product_data = json.dumps({'img': product_img_url,
                                   'title': title,
                                   'price': price,
                                   'rating': product_rating,
                                   'reviews': product_reviews,
                                   'short_url': short_link,
                                   'promo_url': promo_link,
                                   'usd_price': usd_price})
        filename = short_link.split('/')[-1] + '.txt'
        file = open(filename, 'w')
        file.write(product_data)
        file.close()
        keyboard = inline_markup_keyboard(filename)
        bot.send_photo(message.chat.id, product_img_url, box_smile + ' ' + title + '\n'
                       + dollar_bag_smile + ' ' + price + '\n'
                       + dollar_bag_smile + ' ' + usd_price + '\n'
                       + star_smile + ' ' + product_rating + '\n'
                       + review_smile + ' ' + product_reviews + '\n'
                       + link_smile + ' ' + short_link + '\n'
                       + promo_link, parse_mode="markdown", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Не могу достать данные о товаре, попробуйте другой товар.')


@bot.message_handler(commands=['start'])
def handle_start(message):
    line1 = 'Привет, заходи на мои каналы с подборками товаров с Aliexpress!\n'
    line2 = '@alibigshop - Разные товары\n'
    line3 = '@ali_toy - Игрушки и товары для детей\n'
    line4 = '@aliexpress_cars - Всё для автомобилей\n'
    line5 = '@xiaomiacc - Аксессуары для Xiaomi\n'
    line6 = '@iphoneacc - Аксессуары для iPhone\n'
    line7 = '@sgsacc - Аксессуары для Samsung\n'
    line8 = '@oneplus7acc - Аксессуары для OnePlus 7/T/Pro series\n'
    line9 = '@huaweiacc - Аксессуары для Huawei и Honor'
    msg = line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8 + line9
    remover = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.from_user.id, msg, reply_markup=remover)


def edit_about(message, filename, m_id):
    file = open(filename, 'r')
    product_data = json.loads(file.read())
    file.close()
    product_data['title'] = message.text
    file = open(filename, 'w')
    file.write(json.dumps(product_data))
    file.close()
    keyboard = inline_markup_keyboard(filename)
    bot.edit_message_caption(chat_id=message.chat.id, message_id=m_id,
                             caption=box_smile + ' ' + product_data['title'] + '\n'
                                     + dollar_bag_smile + ' ' + product_data['price'] + '\n'
                                     + dollar_bag_smile + ' ' + product_data['usd_price'] + '\n'
                                     + star_smile + ' ' + product_data['rating'] + '\n'
                                     + review_smile + ' ' + product_data['reviews'] + '\n'
                                     + link_smile + ' ' + product_data['short_url'] + '\n'
                                     + product_data['promo_url'], parse_mode="markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message.chat.id == 109964287 or call.message.chat.id == 39089088 or call.message.chat.id == 101065511 or call.message.chat.id == 27825292:
        data_list = call.data.split('::')
        if data_list[0] == 'edit':
            filename = data_list[1]
            bot.send_message(call.message.chat.id, 'Введи новое описание')
            bot.register_next_step_handler(call.message, edit_about, filename, call.message.message_id)
        else:
            channel_name = data_list[0]
            channel_id = data_list[1]
            filename = data_list[2]
            file = open(filename, 'r')
            product_data = json.loads(file.read())
            file.close()
            bot.send_photo(int(channel_id), product_data['img'], box_smile + ' ' + product_data['title'] + '\n'
                           + dollar_bag_smile + ' ' + product_data['price'] + '\n'
                           + dollar_bag_smile + ' ' + product_data['usd_price'] + '\n'
                           + star_smile + ' ' + product_data['rating'] + '\n'
                           + review_smile + ' ' + product_data['reviews'] + '\n'
                           + link_smile + ' ' + product_data['short_url'], parse_mode="markdown")
            bot.send_message(call.message.chat.id, 'Отправил сообщение в канал ' + channel_name)

    else:
        bot.send_message(call.message.chat.id, 'Ненененене')


@bot.message_handler(content_types=['text'])
def handle_command(message):
    if message.chat.id == 109964287 or message.chat.id == 39089088 or message.chat.id == 101065511 or message.chat.id == 27825292:
        if PATTERN_SCLICK_MSG.findall(message.text):
            print(str(message.chat.id) + ':' + message.text + ' 1')
            url = PATTERN_SCLICK_MSG.findall(message.text)
            print(url)
            for i in url:
                html_id = get_id_sclick(i)
                try:
                    send_parsed_message(message, html_id)
                except Exception:
                    prod_id = html_id.split('.')[0]
                    # Создаем промо ссылку для последующего укорачивания
                    promo_link = 'http://alipromo.com/redirect/product/' + deeplink_hash + '/' + prod_id + '/ru'
                    short_link = get_short_link(promo_link)
                    bot.send_message(message.chat.id, short_link)
        elif PATTERN_HTML_MSG.findall(message.text):
            print(str(message.chat.id) + ':' + message.text + ' 2')
            url = PATTERN_HTML_MSG.findall(message.text)
            for i in url:
                html_id = get_id_html(i)
                send_parsed_message(message, html_id)
        elif PATTERN_ALIPUB_MSG.findall(message.text):
            print(str(message.chat.id) + ':' + message.text + ' 3')
            url = PATTERN_ALIPUB_MSG.findall(message.text)
            for i in url:
                html_id = get_id_alipub(i)
                send_parsed_message(message, html_id)
        elif PATTERN_PROD_ID.findall(message.text):
            print(str(message.chat.id) + ':' + message.text + ' 4')
            if re.match(".*aliexpress.*", PATTERN_PROD_ID.findall(message.text)[0]):
                product_id = PATTERN_PROD_ID.findall(message.text)[0].split('2F')[-1]
                send_parsed_message(message, product_id)
            else:
                send_parsed_message(message, message.text)
        else:
            bot.send_message(message.chat.id, 'Кривая ссылка')
            print(str(message.chat.id) + ':' + message.text + ' Кривая ссылка')
    else:
        bot.send_message(message.chat.id, 'Я не понимаю о чем ты')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as err:
            print(err)
            time.sleep(10)
