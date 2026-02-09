import duckdb
from pathlib import Path

DB_PATH = Path("data/warehouse/electricity.duckdb")
STG_CSV = Path("data/processed/stg_prices.csv")

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))


    # Rebuild warehouse from scratch (simplest for G level)
    con.execute("DROP TABLE IF EXISTS fact_prices;")
    con.execute("DROP TABLE IF EXISTS dim_date;")
    con.execute("DROP TABLE IF EXISTS dim_country;")
    con.execute("DROP TABLE IF EXISTS dim_source;")

    # 1) Skapa staging view direkt från CSV
    con.execute(f"""
        CREATE OR REPLACE VIEW stg_prices AS
        SELECT
            source,
            country,
            area,
            CAST(date AS DATE) AS date,
            hour,
            CAST(price AS DOUBLE) AS price,
            currency,
            unit,
            granularity,
            ingested_at
        FROM read_csv_auto('{STG_CSV.as_posix()}', header=True);
    """)

    # 2) Skapa dimensions
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date_id INTEGER PRIMARY KEY,
            date DATE UNIQUE,
            year INTEGER,
            month INTEGER,
            day INTEGER
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_country (
            country_id INTEGER PRIMARY KEY,
            country TEXT UNIQUE
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_source (
            source_id INTEGER PRIMARY KEY,
            source TEXT UNIQUE
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_area (
            area_id INTEGER PRIMARY KEY,
            area TEXT UNIQUE
        );
    """)

    # 3) Fyll dimensions (enkelt sätt: skapa om varje gång för G-nivå)
    con.execute("""
        INSERT INTO dim_date
        SELECT
            ROW_NUMBER() OVER (ORDER BY date) AS date_id,
            date,
            EXTRACT(year FROM date) AS year,
            EXTRACT(month FROM date) AS month,
            EXTRACT(day FROM date) AS day
        FROM (SELECT DISTINCT date FROM stg_prices WHERE date IS NOT NULL)
        ORDER BY date;
    """)

    con.execute("""
        INSERT INTO dim_country
        SELECT
            ROW_NUMBER() OVER (ORDER BY country) AS country_id,
            country
        FROM (SELECT DISTINCT country FROM stg_prices WHERE country IS NOT NULL)
        ORDER BY country;
    """)

    con.execute("""
        INSERT INTO dim_source
        SELECT
            ROW_NUMBER() OVER (ORDER BY source) AS source_id,
            source
        FROM (SELECT DISTINCT source FROM stg_prices WHERE source IS NOT NULL)
        ORDER BY source;
    """)

    con.execute("""
        INSERT INTO dim_area
        SELECT
            ROW_NUMBER() OVER (ORDER BY area) AS area_id,
            area
        FROM (SELECT DISTINCT area FROM stg_prices WHERE area IS NOT NULL)
        ORDER BY area;
    """)

    # 4) Fact table
    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_prices (
            fact_id BIGINT PRIMARY KEY,
            date_id INTEGER,
            country_id INTEGER,
            source_id INTEGER,
            area_id INTEGER,
            price DOUBLE,
            currency TEXT,
            unit TEXT,
            granularity TEXT,
            FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
            FOREIGN KEY(country_id) REFERENCES dim_country(country_id),
            FOREIGN KEY(source_id) REFERENCES dim_source(source_id),
            FOREIGN KEY(area_id) REFERENCES dim_area(area_id)
        );
    """)
    con.execute("""
        INSERT INTO fact_prices
        SELECT
            ROW_NUMBER() OVER (ORDER BY d.date_id, c.country_id, s.source_id) AS fact_id,
            d.date_id,
            c.country_id,
            s.source_id,
            a.area_id,
            stg.price,
            stg.currency,
            stg.unit,
            stg.granularity
        FROM stg_prices stg
        JOIN dim_date d ON d.date = stg.date
        JOIN dim_country c ON c.country = stg.country
        JOIN dim_source s ON s.source = stg.source
        JOIN dim_area a ON a.area = stg.area
        WHERE stg.price IS NOT NULL;
    """)

    # 5) Snabb kontroll
    fact_count = con.execute("SELECT COUNT(*) FROM fact_prices;").fetchone()[0]
    print(f"✅ Warehouse built: {DB_PATH}")
    print(f"✅ fact_prices rows: {fact_count}")

    print("\nSample query (avg price per country):")
    print(con.execute("""
        SELECT c.country, AVG(f.price) AS avg_price
        FROM fact_prices f
        JOIN dim_country c ON c.country_id = f.country_id
        GROUP BY 1
        ORDER BY 2 DESC;
    """).fetchdf())

    con.close()

if __name__ == "__main__":
    main()
