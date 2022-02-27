import sqlite3

conn = sqlite3.connect('members.db')

conn.execute("""CREATE TABLE newbie_users(
             newbie_id INT PRIMARY KEY NOT NULL,
             login TEXT NOT NULL,
             points INT NOT NULL,
             position INT NOT NULL
             );""")

conn.execute("""CREATE TABLE discord_users(
             discord_id INT PRIMARY KEY NOT NULL,
             rules BOOLEAN NOT NULL,
             newbie_id INT,
             rootme_id INT,
             FOREIGN KEY(newbie_id) REFERENCES newbie_users(newbie_id)
             );""")

conn.commit()
conn.close()
