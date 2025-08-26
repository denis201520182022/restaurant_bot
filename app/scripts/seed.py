import asyncio
from app.db.session import get_session
from app.db.models import MenuItem

async def add_test_menu():
    async with get_session() as session:
        items = [
            MenuItem(title="Маргарита", description="Классическая пицца с сыром и томатным соусом", price=450),
            MenuItem(title="Цезарь", description="Салат с курицей, соусом Цезарь и гренками", price=350),
            MenuItem(title="Американо", description="Кофе черный, без молока", price=150),
        ]
        session.add_all(items)
        await session.commit()

async def main():
    await add_test_menu()

if __name__ == "__main__":
    asyncio.run(main())
