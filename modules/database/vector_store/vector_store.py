import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_gigachat.embeddings import GigaChatEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

AUTH_KEY = os.environ.get("AUTH_KEY")

loader = PyPDFLoader("docs/doc.pdf")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200
)
all_splits = text_splitter.split_documents(docs)

print(docs)

embedding = GigaChatEmbeddings(
    credentials=AUTH_KEY,
    verify_ssl_certs=False
)

vector_store = Chroma(
    embedding_function=embedding,
    persist_directory=r'c:/apps/ai/data/pizza_store',
    collection_name='pizza_store'
)

if vector_store._collection.count() == 0:
    print("Коллекция пуста. Добавляем документы...")
    vector_store.add_documents(all_splits)
    print("Документы добавлены.")
else:
    print("В коллекции уже есть записи. Пропускаем добавление.")