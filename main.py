import json

with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as my_file:
    file_contents = my_file.read()
r = file_contents.split('\n\n')

questions = [i for i in r if 'Вопрос' in i]
answers = [i for i in r if 'Ответ' in i]

quiz = dict(zip(questions, answers))
print(quiz)
