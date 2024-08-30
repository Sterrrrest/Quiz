import json


def get_quiz(file='1vs1200.txt'):
    with open(f'quiz-questions/{file}', 'r', encoding='KOI8-R') as my_file:
        file_contents = my_file.read()
    r = file_contents.split('\n\n')

    questions = [i for i in r if 'Вопрос' in i]
    answers = [i for i in r if 'Ответ' in i]

    quiz = dict(zip(questions, answers))

    return quiz

# for k, v in get_quiz().items():
#     print(k)
