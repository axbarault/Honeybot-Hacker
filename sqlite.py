import os
import sqlite3
from newbieUser import NewbieUser


class SQlite():
    def __init__(self, filename: str):
        self.filename = filename
        if not os.path.isfile(self.filename):
            print("La base de données est manquante -> python init_db.py")
            exit()

    def openConn(self):
        self.conn = sqlite3.connect(self.filename)
        return self.conn.cursor()

    def closeConn(self):
        self.conn.commit()
        self.conn.close()

    def addUser(self, discord_id: int, rules: bool = False):
        cursor = self.openConn()

        query = "SELECT COUNT(*) from discord_users where discord_id=?"
        values = (discord_id,)
        rep = cursor.execute(query, values).fetchall()
        if rep[0][0] == 0:
            query = "INSERT INTO discord_users (discord_id, rules) VALUES (?, ?)"
            values = (discord_id, rules)
            cursor.execute(query, values)

        self.closeConn()

    def updateRules(self, discord_id: int, value: bool):
        cursor = self.openConn()

        query = "UPDATE discord_users SET rules=? WHERE discord_id=?"
        values = (value, discord_id)
        cursor.execute(query, values)

        self.closeConn()

    def updateNewbie(self, newbieUser):
        cursor = self.openConn()

        query = "UPDATE discord_users SET newbie_id=? WHERE discord_id=?"
        values = (newbieUser.id, newbieUser.discord_id)
        cursor.execute(query, values)

        query = "SELECT COUNT(*) from newbie_users where newbie_id=?"
        values = (newbieUser.id,)
        rep = cursor.execute(query, values).fetchall()
        if rep[0][0] == 1:
            query = "UPDATE newbie_users SET login=?, points=?, position=? WHERE newbie_id=?"
            values = (newbieUser.login, newbieUser.points, newbieUser.position, newbieUser.id)
            cursor.execute(query, values)
        else:
            query = "INSERT INTO newbie_users (newbie_id, login, points, position) VALUES (?, ?, ?, ?)"
            values = (newbieUser.id, newbieUser.login, newbieUser.points, newbieUser.position)
            cursor.execute(query, values)

        self.closeConn()

    def getNewbieUsers(self):
        cursor = self.openConn()

        query = "SELECT discord_id, newbie_users.newbie_id, login, points, position FROM discord_users INNER JOIN newbie_users ON discord_users.newbie_id = newbie_users.newbie_id"
        rep = cursor.execute(query).fetchall()
        newbieUsers = []
        for row in rep:
            newbieUsers.append(NewbieUser(row[0], row[1], row[2], row[3], row[4]))

        self.closeConn()
        return newbieUsers


sqlite = SQlite('members.db')
