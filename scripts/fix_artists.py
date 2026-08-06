import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="radiodj"
)

cursor = conn.cursor()

cursor.execute("""
    UPDATE song 
    SET artist = CONCAT('RSDV Vol.', FLOOR(id/100)+1)
    WHERE artist = '' 
    OR artist = 'Unknown Artist'
    OR artist IS NULL
""")

conn.commit()
print(f"{cursor.rowcount} chansons mises a jour!")
cursor.close()
conn.close()
input("Appuie sur Enter pour fermer...")