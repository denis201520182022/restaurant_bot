# scripts/seed_menu.py

import asyncio
from sqlalchemy import select
from app.db.session import get_session
from app.db.models import MenuItem

# Вот здесь мы описываем наши блюда.
# image_id пока пустые, мы заполним их на следующем шаге.
MENU_ITEMS_DATA = [
    {
        "title": "Цезарь с курицей",
        "description": "куриная грудка гриль, салат айсберг, сыр грано падано, с хрустящими гренками",
        "price": 280,
        "image_id": "AgACAgIAAxkBAAE6KMdorYSdsJZOrpa_wxcIz6NTgOy_AwACy_AxG5o3cElFp8TQkdIG5wEAAwIAA3kAAzYE" 
    },
    {
        "title": "Харчо с бараниной",
        "description": "подаётся с чесночными гренками и сметаной",
        "price": 280,
        "image_id": "AgACAgIAAxkBAAE6KM9orYUo3fkzsx79LTfHHvK_bCPMDgACzPAxG5o3cEnwbIRe7KnbHgEAAwIAA3kAAzYE"
    },
    {
        "title": "Пицца Четыре сыра",
        "description": "моцарелла, дор блю, буффало моцарелла",
        "price": 360,
        "image_id": "AgACAgIAAxkBAAE6KNForYVoChBxeF7HtJxDUvQ-uw-s2wAC0PAxG5o3cEnvjhuhRAZmhwEAAwIAA3kAAzYE"
    },
    {
        "title": "Паста Карбонара",
        "description": "спагетти, бекон, помидор черри, сливочный соус, сыр грано падано, белое вино",
        "price": 260,
        "image_id": "AgACAgIAAxkBAAE6KNNorYWm4hABw5D3FKD04EtVeQY8_QAC0vAxG5o3cEkE5q91EucnqQEAAwIAA3gAAzYE"
    },
    {
        "title": "Крылышки BBQ",
        "description": "подаются с соусом BBQ, морковью и сельдереем", # Немного дополнил описание для красоты
        "price": 290,
        "image_id": "AgACAgIAAxkBAAE6KNporYXW6NIJ_daYUhRpzC5YchOphQAC1fAxG5o3cEkSNwhxSdef7QEAAwIAA3kAAzYE"
    },
    {
        "title": "Сельдь с картофелем",
        "description": "нежная сельдь с отварным молодым картофелем и луком", # Немного дополнил
        "price": 180,
        "image_id": "AgACAgIAAxkBAAE6KN9orYYk1cRxglzJImOIBJpa3JFJWAAC1_AxG5o3cEmnTMHftNJODgEAAwIAA3kAAzYE"
    },
    {
        "title": "Борщ украинский с говядиной",
        "description": "подаётся с чесночными гренками и сметаной",
        "price": 250,
        "image_id": "AgACAgIAAxkBAAE6KOhorYZ2g2K0RcZWDqPecvrlj2fI4QAC3PAxG5o3cEkEL_9PzYZKZgEAAwIAA3kAAzYE"
    },
    {
        "title": "Жюльен с курицей и грибами",
        "description": "классический жюльен под сырной корочкой",
        "price": 130,
        "image_id": "AgACAgIAAxkBAAE6KO5orYaxVP5VK7s_A---wxyBw5-fqQAC3fAxG5o3cEk8L1T3WFwMmAEAAwIAA3kAAzYE"
    },
]

async def seed_menu():
    print("Starting to seed menu items...")
    async with get_session() as session:
        # Сначала получим все существующие названия блюд
        result = await session.execute(select(MenuItem.title))
        existing_titles = {row[0] for row in result}

        items_to_add = []
        for item_data in MENU_ITEMS_DATA:
            if item_data["title"] not in existing_titles:
                items_to_add.append(MenuItem(**item_data))
            else:
                print(f"Skipping '{item_data['title']}', as it already exists.")
        
        if items_to_add:
            session.add_all(items_to_add)
            await session.commit()
            print(f"Successfully added {len(items_to_add)} new menu items.")
        else:
            print("No new menu items to add.")

if __name__ == "__main__":
    asyncio.run(seed_menu())