from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, ItemsDB, User

# Creates a session in the items database
engine = create_engine('sqlite:///ItemsDB.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Me as the admin
Me = User(name="admin", email="test@gmail.com")
session.add(Me)
session.commit()

print "Database populated"

# Begin adding random items

Item1 = ItemsDB(itemName="Hat",
                description="Wear it on your head",
                category="Clothing",
                user_id="1")
session.add(Item1)
session.commit()

Item2 = ItemsDB(itemName="Pants",
                description="Wear it on your legs",
                category="Clothing",
                user_id="1")
session.add(Item2)
session.commit()

Item3 = ItemsDB(itemName="Pizza",
                description="Now that's a spicy meatball",
                category="Food",
                user_id="1")
session.add(Item3)
session.commit()

Item4 = ItemsDB(itemName="Hawaii",
                description="Islands where the palm trees sway",
                category="Place",
                user_id="1")
session.add(Item4)
session.commit()

Item5 = ItemsDB(itemName="Canary eating a lollipop",
                description="A tweety with a sweetie",
                category="Misc",
                user_id="1")
session.add(Item5)
session.commit()
