"""
API для доступа к данным скрапинга
Библиотека: FastAPI
Документация: автоматическая (Swagger UI)

Запуск: uvicorn api:app --reload
Документация: http://localhost:8000/docs
"""

import os
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ============ КОНФИГУРАЦИЯ ============
DATA_FILE = os.getenv("DATA_FILE", "src/data/products.csv")
PLOT_FILE = "src/data/price_plot.png"

# ============ СОЗДАНИЕ ПРИЛОЖЕНИЯ ============
app = FastAPI(
    title="Books Scraping API",
    description="API для доступа к данным о книгах, собранным скрапером",
    version="2.0",
    contact={
        "name": "Scraping Project",
        "email": "student@example.com",
    },
    license_info={
        "name": "MIT",
    },
)


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def load_data() -> pd.DataFrame:
    """Загрузка данных из CSV"""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    return pd.read_csv(DATA_FILE)


def validate_limit(limit: int) -> int:
    """Проверка лимита (мин 1, макс 50)"""
    if limit > 50:
        return 50
    if limit < 1:
        return 10
    return limit


# ============ ЭНДПОИНТЫ ============

@app.get("/")
def root():
    """Главная страница с информацией об API"""
    return {
        "name": "Books Scraping API",
        "version": "2.0",
        "description": "API для доступа к данным о книгах",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "GET /": "Информация об API",
            "GET /stats": "Статистика по данным",
            "GET /products": "Список книг (фильтрация, сортировка, пагинация)",
            "GET /products/top": "Топ дорогих книг",
            "GET /products/cheap": "Топ дешёвых книг",
            "GET /products/search": "Поиск по названию",
            "GET /filters": "Доступные фильтры",
            "GET /plot": "График распределения цен (PNG)",
        }
    }


@app.get("/stats")
def get_stats():
    """
    Получение общей статистики по данным

    Возвращает:
    - total_books: общее количество книг
    - avg_price: средняя цена
    - min_price: минимальная цена
    - max_price: максимальная цена
    - avg_rating: средний рейтинг
    """
    df = load_data()

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="Нет данных. Запустите скрапер: python src/scrap.py"
        )

    return {
        "total_books": len(df),
        "avg_price": round(df['price'].mean(), 2),
        "min_price": round(df['price'].min(), 2),
        "max_price": round(df['price'].max(), 2),
        "avg_rating": round(df['rating'].mean(), 2),
        "in_stock": len(df[df['availability'] == 'in_stock']) if 'availability' in df else 0,
    }


@app.get("/products")
def get_products(
    # Фильтры
    min_price: Optional[float] = Query(None, ge=0, description="Минимальная цена (£)"),
    max_price: Optional[float] = Query(None, ge=0, description="Максимальная цена (£)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Минимальный рейтинг (0-5)"),
    availability: Optional[str] = Query(
        None,
        pattern="^(in_stock|out_of_stock|unknown)$",
        description="Наличие"
    ),

    # Сортировка
    sort_by: Optional[str] = Query(
        "price",
        pattern="^(price|rating|name)$",
        description="Поле для сортировки"
    ),
    order: Optional[str] = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Порядок сортировки (asc - по возрастанию, desc - по убыванию)"
    ),

    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    limit: int = Query(20, ge=1, le=50, description="Количество записей на странице (макс 50)")
):
    """
    Получение списка книг с фильтрацией, сортировкой и пагинацией

    **Фильтры:**
    - `min_price` / `max_price` — диапазон цен
    - `min_rating` — минимальный рейтинг
    - `availability` — наличие (in_stock/out_of_stock/unknown)

    **Сортировка:**
    - `sort_by` — поле (price / rating / name)
    - `order` — направление (asc / desc)

    **Пагинация:**
    - `page` — номер страницы (по умолчанию 1)
    - `limit` — записей на странице (макс 50)
    """
    df = load_data()

    if df.empty:
        raise HTTPException(status_code=404, detail="Нет данных")

    original_total = len(df)

    # ===== ФИЛЬТРАЦИЯ =====
    if min_price is not None:
        df = df[df['price'] >= min_price]

    if max_price is not None:
        df = df[df['price'] <= max_price]

    if min_rating is not None:
        df = df[df['rating'] >= min_rating]

    if availability is not None:
        df = df[df['availability'] == availability]

    # ===== СОРТИРОВКА =====
    if sort_by == "price":
        df = df.sort_values('price', ascending=(order == 'asc'))
    elif sort_by == "rating":
        df = df.sort_values('rating', ascending=(order == 'asc'))
    elif sort_by == "name":
        df = df.sort_values('name', ascending=(order == 'asc'))

    # ===== ПАГИНАЦИЯ =====
    total = len(df)
    offset = (page - 1) * limit

    if offset >= total and total > 0:
        total_pages = (total + limit - 1) // limit
        raise HTTPException(
            status_code=404,
            detail=f"Страница {page} не найдена. Всего страниц: {total_pages}"
        )

    result = df.iloc[offset:offset + limit][['name', 'price', 'rating', 'availability']].to_dict(orient='records')

    return {
        "success": True,
        "total_books_before_filter": original_total,
        "total_after_filter": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        "filters_applied": {
            "min_price": min_price,
            "max_price": max_price,
            "min_rating": min_rating,
            "availability": availability
        },
        "sorting": {
            "sort_by": sort_by,
            "order": order
        },
        "books": result
    }


@app.get("/products/top")
def get_top_products(
    limit: int = Query(5, ge=1, le=20, description="Количество (макс 20)")
):
    """Топ N самых дорогих книг"""
    df = load_data()

    if df.empty:
        raise HTTPException(status_code=404, detail="Нет данных")

    limit = validate_limit(limit)
    top = df.nlargest(limit, 'price')[['name', 'price', 'rating', 'availability']]

    return {
        "success": True,
        "total_shown": len(top),
        "books": top.to_dict(orient='records')
    }


@app.get("/products/cheap")
def get_cheap_products(
    limit: int = Query(5, ge=1, le=20, description="Количество (макс 20)")
):
    """Топ N самых дешёвых книг"""
    df = load_data()

    if df.empty:
        raise HTTPException(status_code=404, detail="Нет данных")

    limit = validate_limit(limit)
    cheap = df.nsmallest(limit, 'price')[['name', 'price', 'rating', 'availability']]

    return {
        "success": True,
        "total_shown": len(cheap),
        "books": cheap.to_dict(orient='records')
    }


@app.get("/products/search")
def search_products(
    q: str = Query(..., min_length=1, max_length=100, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=50, description="Максимум результатов (макс 50)")
):
    """Поиск книг по названию (частичное совпадение, без учёта регистра)"""
    df = load_data()

    if df.empty:
        raise HTTPException(status_code=404, detail="Нет данных")

    result = df[df['name'].str.contains(q, case=False, na=False)]

    limit = validate_limit(limit)
    result = result.head(limit)[['name', 'price', 'rating', 'availability']]

    return {
        "success": True,
        "query": q,
        "found": len(result),
        "books": result.to_dict(orient='records')
    }


@app.get("/filters")
def get_available_filters():
    """Информация о доступных значениях для фильтрации"""
    df = load_data()

    if df.empty:
        return {"error": "Нет данных"}

    return {
        "success": True,
        "price_range": {
            "min": round(df['price'].min(), 2),
            "max": round(df['price'].max(), 2)
        },
        "rating_range": {
            "min": df['rating'].min(),
            "max": df['rating'].max()
        },
        "availability_values": df['availability'].unique().tolist() if 'availability' in df else []
    }


@app.get("/plot")
def get_plot():
    """
    Получение графика распределения цен
    Возвращает PNG изображение
    """
    if not os.path.exists(PLOT_FILE):
        raise HTTPException(
            status_code=404,
            detail="График не найден. Запустите скрапер: python src/scrap.py"
        )

    return FileResponse(PLOT_FILE, media_type="image/png")