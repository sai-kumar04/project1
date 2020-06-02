from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import os

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

print("Opened database successfully")



with open('books.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter = ",")
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print("this is the header line")
            line_count += 1
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year);",{"isbn": row[0], "title": row[1], "author": row[2], "year": row[3]})
            print(f"book with title: { row[1] } successfully inserted")
            line_count += 1
db.commit()
print("records created successfully")
