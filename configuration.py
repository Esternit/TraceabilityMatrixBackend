import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

WORDS = [
    "ancient", "brave", "calm", "daring", "eager", "fierce", "gentle", "heroic",
    "icy", "jolly", "kind", "lucky", "mighty", "noble", "odd", "proud", "quick", "royal",
    "silent", "tough", "unique", "vast", "wild", "young", "zany", "smoke", "tree", "rock"
]