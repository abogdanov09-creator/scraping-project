#!/usr/bin/env python3
"""
Точка входа для запуска скрапера

Запуск:
    python scripts/run_scraper.py
    python scripts/run_scraper.py --pages 5
"""

import sys
import os
import argparse

# Добавляем корневую папку в путь
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.scrap import SimpleScraper


def main():
    parser = argparse.ArgumentParser(description='Скрапер для сбора данных о книгах')
    parser.add_argument('--pages', '-p', type=int, default=3,
                        help='Количество страниц для парсинга (по умолчанию: 3)')

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("🕷️  WEB SCRAPER - Сбор данных")
    print("=" * 50)
    print(f"📚 Источник: books.toscrape.com")
    print(f"📄 Страниц: {args.pages}")
    print("=" * 50 + "\n")

    # Создаём экземпляр скрапера
    scraper = SimpleScraper()

    # Запускаем сбор данных (передаём количество страниц)
    products = scraper.scrape_books(max_pages=args.pages)

    if products:
        scraper.save_to_csv()
        scraper.analyze_and_plot()

        print("\n" + "=" * 50)
        print("📊 ИТОГИ")
        print("=" * 50)
        print(f"✅ Собрано товаров: {len(products)}")
        print(f"📁 Данные: data/products.csv")
        print(f"📄 Отчет: data/report.txt")
        print(f"📈 График: data/price_plot.png")
        print("=" * 50)
        print("\n✅ СКРАПИНГ УСПЕШНО ЗАВЕРШЕН!")
    else:
        print("\n❌ НЕ УДАЛОСЬ СОБРАТЬ ДАННЫЕ")


if __name__ == "__main__":
    main()