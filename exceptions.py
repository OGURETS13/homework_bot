class EndpointException(Exception):
    def __str__(self):
        return 'Эндпоинт недоступен'


class MessageException(Exception):
    pass


class MainException(Exception):
    pass
