from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base


#create an engine for your DB using sqlite and storing it in a file named reddit.sqlite
engine = create_engine('sqlite:///bird.sqlite')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db(): 
    from bird_classes import Location, Hotspot, Sighting, Bird

    # import your classes that represent tables in the DB and then create_all of the tables
    Base.metadata.create_all(bind=engine)

    

    # save the database
    db_session.commit()
