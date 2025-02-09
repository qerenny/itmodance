#const/const_bot.py
CURRENCY = 'RUB'
MAIN_MENU = '🏠 В главное меню'
DONATION = '🎁 Пожертвования'
SUBSCRIPTION = '🎫 Подписки'

R100_DICT = {'label' : 'Пожертвование - 100 РУБ', 'amount' : 100*100,
          'description': 'Пожертвование в 100 РУБ',
          'payload' : 'D100'}
R300_DICT = {'label' : 'Пожертвование - 300 РУБ', 'amount' : 300*100,
          'description': 'Пожертвование в 300 РУБ',
          'payload' : 'D300'}
R500_DICT = {'label' : 'Пожертвование - 500 РУБ', 'amount' : 500*100,
          'description': 'Пожертвование в 500 РУБ',
          'payload' : 'D500'}
R1000_DICT = {'label' : 'Пожертвование - 1000 РУБ', 'amount' : 1000*100,
         'description': 'Пожертвование в 1000 РУБ',
         'payload' : 'D1000'}

SUB1_DICT = {'label' : 'Подписка на 1 месяц занятий', 'amount' : 1300*100,
          'description': '4 занятия с даты покупки в течение 1 месяца',
          'payload' : 'S1'}
SUB2_DICT = {'label' : 'Подписка на 2 месяца занятий', 'amount' : 2100*100,
          'description': '8 занятий с даты покупки в течение 2 месяцев',
          'payload' : 'S2'}
SUB3_DICT = {'label' : 'Подписка на 3 месяца занятий', 'amount' : 2900*100,
          'description': '12 занятий с даты покупки в течение 3 месяцев',
          'payload' : 'S3'}
