from modules import run_cycle
from modules.database import create_tables, init_db
from modules.seed.products import init_products

if __name__ == "__main__":
    init_db()
    create_tables()
    init_products()
    run_cycle()