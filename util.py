import re


def is_valid_phone(phone: str) -> bool:
    """
    Валидация номера телефона.
    Поддерживает форматы: +79991234567
    """
    cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Проверяем соответствие паттернам
    patterns = [
        r'^\+7\d{10}$',  # +79991234567
    ]

    return any(re.match(pattern, cleaned_phone) for pattern in patterns)
