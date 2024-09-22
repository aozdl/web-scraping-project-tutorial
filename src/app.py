import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

resource_url = "https://ycharts.com/companies/TSLA/revenues"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class Scraping:
    def __init__(self, resource_url, headers):
        self.resource_url = resource_url
        self.html = None
        self.headers = headers

    def download(self):
        self.html = requests.get(self.resource_url, headers=self.headers)
        print("Status Code:", self.html.status_code)
        print("HTML Content Snippet:", self.html.text[:2000])

    def parse_html(self):
        if self.html is None:
            raise ValueError("HTML content is not downloaded.")
        parsed_html = BeautifulSoup(self.html.text, "html.parser")
        tables = parsed_html.find_all("table")
        print(f"Found {len(tables)} tables.")
        if not tables:
            raise ValueError("No tables found in the HTML.")
        return tables

    def extract_table_data(self, table):
        columns = []
        data = []

        headers = table.find_all("th")
        columns = [header.get_text(strip=True) for header in headers]
        print(f"Columns found: {columns}")

        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            data.append([cell.get_text(strip=True) for cell in cells])
        
        print(f"Number of rows extracted: {len(data)}")
        return columns, data

    def to_dataframe(self):
        tables = self.parse_html()
        if tables:
            columns, data = self.extract_table_data(tables[0])
            df = pd.DataFrame(data, columns=columns)
            print("DataFrame head:\n", df.head())
            return df
        else:
            raise ValueError("No tables found on the page.")

    def clean_dataframe(self, df):
        print("Raw DataFrame before cleaning:\n", df.head())

        df['Value'] = df['Value'].replace('[\$,B]', '', regex=True)
        df['Value'] = df['Value'].str.replace(',', '')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        
        print("DataFrame after removing $, B, and commas:\n", df.head())

        df.dropna(inplace=True)

        print("Cleaned DataFrame head:\n", df.head())

        df.rename(columns={'Value': 'Revenue'}, inplace=True)

        return df

    def store_data_in_sqlite(self, df, db_name='tesla_revenues.db'):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            create_table_query = '''
            CREATE TABLE IF NOT EXISTS revenues (
                Date TEXT,
                Revenue REAL
            )
            '''
            cursor.execute(create_table_query)
            df.to_sql('revenues', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

    def plot_visualizations(self, df):
        try:
            plt.figure(figsize=(15, 5))
            
            plt.subplot(1, 3, 1)
            plt.plot(pd.to_datetime(df['Date']), df['Revenue'], marker='o')
            plt.title('Revenue Trend Over Time')
            plt.xlabel('Date')
            plt.ylabel('Revenue')
            plt.xticks(rotation=45)

            plt.subplot(1, 3, 2)
            df_sorted = df.sort_values(by='Revenue', ascending=False)
            sns.barplot(x='Date', y='Revenue', data=df_sorted)
            plt.title('Revenue by Quarter')
            plt.xlabel('Date')
            plt.ylabel('Revenue')
            plt.xticks(rotation=45)

            plt.subplot(1, 3, 3)
            plt.hist(df['Revenue'], bins=20, edgecolor='k')
            plt.title('Distribution of Revenue')
            plt.xlabel('Revenue')
            plt.ylabel('Frequency')
            
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Error during visualization: {e}")

sc = Scraping(resource_url, headers)
sc.download()
df = sc.to_dataframe()


df_cleaned = sc.clean_dataframe(df)
print("Cleaned DataFrame head:\n", df_cleaned.head())

sc.store_data_in_sqlite(df_cleaned)

sc.plot_visualizations(df_cleaned)