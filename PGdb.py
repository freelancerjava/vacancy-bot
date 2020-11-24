import psycopg2


class PGdb:

    # users: id(autoinc), user_id, username, photo, phone
    # requests: id(autoinc), user_id, type_id, date, additional, status

    def __init__(self):
        self.connection = psycopg2.connect(user = "strapi",
                                  password = "strapi",
                                  host = "127.0.0.1",
                                  port = "5433",
                                  database="strapi")
        self.cursor = self.connection.cursor()

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()

    def print_messages(self):
        with self.connection:
            q = "SELECT * FROM messages"
            self.cursor.execute("SELECT * FROM messages")
            res = self.cursor.fetchall()
            for x in res:
                print(x)

    def print_help(self):
        with self.connection:
            q = "SELECT * FROM messages"
            self.cursor.execute(q)
            res = self.cursor.fetchall()
            for x in res:
                print(x)