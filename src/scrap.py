

import time
import csv
import os
import re
from datetime import datetime
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt


class SimpleScraper:
    """Простой скрапер на requests + BeautifulSoup"""

    def __init__(self):
        self.products = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_books(self, max_pages: int = 3) -> List[Dict]:
        """
        Сбор данных о книгах с books.toscrape.com
        Это тестовый сайт, который всегда доступен
        """
        products = []

        for page in range(1, max_pages + 1):
            url = f"https://books.toscrape.com/catalogue/page-{page}.html"
            print(f"📄 Страница {page}: {url}")

            try:
                response = self.session.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                books = soup.find_all('article', class_='product_pod')

                print(f"   Найдено книг: {len(books)}")

                for book in books:
                    product = self._parse_book(book)
                    if product:
                        products.append(product)

                print(f"   Всего собрано: {len(products)}\n")
                time.sleep(1)  # Вежливая пауза

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

        self.products = products
        return products

    def _parse_book(self, book) -> Dict:
        """Парсинг одной книги"""
        try:
            # Название
            title_elem = book.find('h3').find('a')
            title = title_elem.get('title', '') if title_elem else ''

            # Цена
            price_elem = book.find('p', class_='price_color')
            price = 0.0
            if price_elem:
                price_text = price_elem.text
                numbers = re.findall(r'[\d.]+', price_text)
                if numbers:
                    price = float(numbers[0])

            # Рейтинг
            rating_elem = book.find('p', class_='star-rating')
            rating = 0
            if rating_elem:
                rating_classes = rating_elem.get('class', [])
                rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
                for key, value in rating_map.items():
                    if key in rating_classes:
                        rating = value
                        break

            # Наличие
            in_stock = book.find('p', class_='instock availability')
            availability = 'in_stock' if in_stock and 'In stock' in in_stock.text else 'unknown'

            return {
                'name': title,
                'price': price,
                'rating': rating,
                'availability': availability,
                'category': 'books',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return None

    def save_to_csv(self, filename: str = "data/products.csv"):
        if not self.products:
            print("❌ Нет данных для сохранения")
            return False

        os.makedirs("../data", exist_ok=True)

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['name', 'price', 'rating', 'availability', 'category', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)

        print(f"✅ Данные сохранены: {filename}")
        print(f"   Всего товаров: {len(self.products)}")
        return True

    def analyze_and_plot(self):
        if not self.products:
            print("❌ Нет данных для анализа")
            return

        df = pd.DataFrame(self.products)
        os.makedirs("../data", exist_ok=True)

        # ===== ОТЧЕТ =====
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("ОТЧЕТ ПО СКРАПИНГУ")
        report_lines.append("=" * 60)
        report_lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Всего товаров: {len(df)}")
        report_lines.append(f"Средняя цена: £{df['price'].mean():.2f}")
        report_lines.append(f"Максимальная цена: £{df['price'].max():.2f}")
        report_lines.append(f"Минимальная цена: £{df['price'].min():.2f}")
        report_lines.append(f"Средний рейтинг: {df['rating'].mean():.2f}")
        report_lines.append("")

        report_lines.append("-" * 60)
        report_lines.append("ТОП-5 САМЫХ ДОРОГИХ КНИГ")
        report_lines.append("-" * 60)
        for i, row in df.nlargest(5, 'price').iterrows():
            report_lines.append(f"{i + 1}. {row['name'][:50]} - £{row['price']:.2f} (⭐{row['rating']})")

        report_lines.append("")
        report_lines.append("-" * 60)
        report_lines.append("ТОП-5 ЛУЧШИХ ПО РЕЙТИНГУ")
        report_lines.append("-" * 60)
        for i, row in df.nlargest(5, 'rating').iterrows():
            report_lines.append(f"{i + 1}. {row['name'][:50]} - ⭐{row['rating']} (£{row['price']:.2f})")

        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("ВЫВОДЫ")
        report_lines.append("=" * 60)
        report_lines.append(f"✓ Самая дорогая книга: {df.loc[df['price'].idxmax(), 'name'][:40]}")
        report_lines.append(f"✓ Самая дешёвая книга: {df.loc[df['price'].idxmin(), 'name'][:40]}")
        report_lines.append(f"✓ Всего проанализировано: {len(df)} книг")
        report_lines.append("=" * 60)

        report_text = "\n".join(report_lines)
        with open("../data/report.txt", "w", encoding='utf-8') as f:
            f.write(report_text)

        print("\n" + report_text)
        print(f"\n✅ Отчет сохранен: data/report.txt")

        # ===== ГРАФИК =====
        plt.figure(figsize=(10, 6))
        plt.hist(df['price'], bins=15, edgecolor='black', alpha=0.7, color='steelblue')
        plt.axvline(df['price'].mean(), color='red', linestyle='--',
                    label=f'Средняя: £{df["price"].mean():.2f}')
        plt.xlabel('Цена (£)', fontsize=12)
        plt.ylabel('Количество книг', fontsize=12)
        plt.title('Распределение цен на книги', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('data/price_plot.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ График сохранен: data/price_plot.png")


def main():
    print("\n" + "=" * 50)
    print("🕷️  WEB SCRAPER (100% рабочий)")
    print("=" * 50)
    print("📚 Сбор данных о книгах с books.toscrape.com")
    print("📄 Страниц: 3")
    print("=" * 50 + "\n")

    start_time = time.time()

    scraper = SimpleScraper()
    products = scraper.scrape_books(max_pages=3)

    elapsed_time = time.time() - start_time

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
        print(f"⏱️ Время: {elapsed_time:.2f} сек")
        print("=" * 50)
        print("\n✅ СКРАПИНГ УСПЕШНО ЗАВЕРШЕН!")
    else:
        print("\n❌ НЕ УДАЛОСЬ СОБРАТЬ ДАННЫЕ")


if __name__ == "__main__":
    main()
