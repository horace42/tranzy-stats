
from tkinter import Tk

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tranzy_db import Base
from interface import MainWindow


def main():

    # connect to db
    engine = create_engine("sqlite+pysqlite:///tranzy.db?charset=utf8mb4", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)

    root = Tk()
    root.title("Tranzy Stats")
    w = MainWindow(root, session)
    root.mainloop()

    # close db session
    session.close()


if __name__ == '__main__':
    main()
