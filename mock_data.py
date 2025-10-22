"""
Заглушки для данных из базы данных и бэкенда
В будущем это будет заменено на реальные API-запросы к Go бэкенду
"""
import random


class MockDatabase:
    """Имитация работы с базой данных"""
    
    def __init__(self):
        self.candidates = {}
        self.interview_results = {}
    
    def save_candidate(self, user_id: int, data: dict) -> bool:
        """
        Сохранить данные кандидата
        В будущем: POST запрос к Go API endpoint /api/candidates
        """
        self.candidates[user_id] = data
        vacancy = data.get('vacancy_name', 'Не указана')
        print(f"[MOCK DB] Сохранены данные кандидата {user_id} на вакансию '{vacancy}': {data}")
        return True
    
    def get_screening_result(self, user_id: int) -> dict:
        """
        Получить результат скрининга резюме
        В будущем: GET запрос к Go API endpoint /api/screening/{user_id}
        """
        # Имитация работы нейросети - случайный результат
        passed = random.choice([True, False])
        print(f"[MOCK SCREENING] Результат для {user_id}: {'Прошел' if passed else 'Не прошел'}")
        return {
            'passed': passed,
            'score': random.randint(60, 95) if passed else random.randint(30, 59),
            'feedback': 'Ваше резюме соответствует требованиям вакансии' if passed else 'К сожалению, ваш опыт не соответствует требованиям'
        }
    
    def get_interview_questions(self, vacancy_name: str = None) -> list:
        """
        Получить вопросы для интервью по вакансии
        В будущем: GET запрос к Go API endpoint /api/vacancies/{vacancy_id}/questions
        """
        questions = [
            "Расскажите о своем опыте работы в данной области",
            "Какие технологии вы использовали в последнем проекте?",
            "Опишите самую сложную задачу, которую вам приходилось решать",
            "Почему вы хотите работать в нашей компании?",
            "Какие ваши сильные и слабые стороны?"
        ]
        print(f"[MOCK DB] Получены вопросы для вакансии '{vacancy_name}'")
        return questions
    
    def save_interview_answer(self, user_id: int, question_num: int, answer: str) -> bool:
        """
        Сохранить ответ на вопрос интервью
        В будущем: POST запрос к Go API endpoint /api/interview/answers
        """
        if user_id not in self.interview_results:
            self.interview_results[user_id] = {}
        
        self.interview_results[user_id][question_num] = answer
        print(f"[MOCK DB] Сохранен ответ {question_num} для кандидата {user_id}")
        return True
    
    def get_interview_result(self, user_id: int) -> dict:
        """
        Получить результат интервью
        В будущем: GET запрос к Go API endpoint /api/interview/{user_id}/result
        """
        # Имитация анализа ответов - случайный результат
        passed = random.choice([True, True, False])  # 66% шанс успеха
        print(f"[MOCK INTERVIEW] Результат интервью для {user_id}: {'Прошел' if passed else 'Не прошел'}")
        return {
            'passed': passed,
            'score': random.randint(70, 100) if passed else random.randint(40, 69),
            'feedback': 'Поздравляем! Вы прошли на следующий этап' if passed else 'К сожалению, по результатам интервью мы не можем продолжить процесс отбора'
        }
    
    def get_candidate_status(self, user_id: int) -> dict:
        """
        Получить статус кандидата
        В будущем: GET запрос к Go API endpoint /api/candidates/{user_id}/status
        """
        statuses = [
            {'status': 'new', 'text': 'Новый кандидат', 'description': 'Ваша заявка зарегистрирована'},
            {'status': 'resume_review', 'text': 'Проверка резюме', 'description': 'Ваше резюме проходит проверку'},
            {'status': 'interview_pending', 'text': 'Ожидание интервью', 'description': 'Готовимся к вашему интервью'},
            {'status': 'interview_completed', 'text': 'Интервью завершено', 'description': 'Анализируем ваши ответы'},
            {'status': 'hr_review', 'text': 'Проверка HR', 'description': 'HR-менеджер рассматривает вашу кандидатуру'},
            {'status': 'approved', 'text': 'Одобрено', 'description': 'Поздравляем! С вами свяжется HR'},
        ]
        
        # Случайный статус для заглушки
        status_data = random.choice(statuses)
        print(f"[MOCK DB] Статус кандидата {user_id}: {status_data['status']}")
        return status_data
    
    def get_timing_info(self) -> str:
        """
        Получить информацию о сроках
        В будущем: может быть частью конфига или API
        """
        return (
            "⏰ <b>Примерные сроки:</b>\n\n"
            "• Проверка резюме: 1-2 рабочих дня\n"
            "• Анализ интервью: 2-3 рабочих дня\n"
            "• Финальное решение HR: 3-5 рабочих дней\n\n"
            "Мы стараемся обрабатывать заявки как можно быстрее и обязательно уведомим вас о любых изменениях статуса."
        )
    
    def get_contact_info(self) -> str:
        """
        Получить контактную информацию
        В будущем: может быть из конфига или API
        """
        return (
            "📞 <b>Контактная информация:</b>\n\n"
            "• Email: hr@company.com\n"
            "• Телефон: +7 (495) 123-45-67\n"
            "• Рабочие часы: Пн-Пт, 9:00-18:00 (МСК)\n\n"
            "Если у вас возникли вопросы, вы можете написать нам на email или позвонить в рабочее время."
        )

#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⢀⢐⠀⣬⡄⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⣶⣴⣿⣷⡿⡿⢷⣦⣥⡄⢀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⢖⣴⠋⢩⣿⠻⣷⠀⠀⠉⠻⣿⣆⣠⣶⡷⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⢉⠀⢸⡟⠀⢹⣷⡄⣠⣴⣿⣿⢫⠘⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⣿⡷⢀⣴⣿⣿⣟⠉⠐⣻⡇⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠐⣿⡇⡇⣸⣿⣷⢟⠋⠁⠙⢿⣧⣀⣿⠁⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⢀⣭⣿⣿⣿⣾⠏⠀⠀⠀⠀⠈⣿⣿⣿⣷⠈⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠰⠿⠋⠁⢟⣿⣿⣤⣦⡠⣀⣴⣶⡟⣻⢿⣾⡇⠄⠠⠀⠀⠀⠀
#⠀⠀⠀⠐⠀⠀⠁⠀⠀⠀⠈⣿⡯⠟⠟⠛⡿⠋⠁⠄⢸⠀⠹⣿⣄⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⡿⠁⠀⠀⠀⠇⠀⠀⠀⢸⠀⠀⠘⠛⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⢰⠆⠀⠀⠀⠀⠀⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀


# Глобальный экземпляр (в продакшене это будет заменено на настоящий API клиент)
mock_db = MockDatabase()

