import mysql.connector
from werkzeug.security import generate_password_hash

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="877011",
    database="mini_erp"
)
cursor = db.cursor()

name = "Pratham Sen"
email = "pratham@test.com"
password = generate_password_hash("test123")

cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
db.commit()
cursor.close()
db.close()
print("Test user created!")