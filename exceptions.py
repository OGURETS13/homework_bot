class EndpointException(Exception):
    def __str__(self):
        return 'Эндпоинт недоступен'
