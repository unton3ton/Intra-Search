#!/usr/bin/env python3  
"""  
Прямой запуск Flask-приложения Intra-Search с созданием эмбеддингов  
"""  

# # http://127.0.0.1:8080

# # import platformdirs  
  # # # Для Intra-Search  
# # app_name = "intra-search"  
# # data_dir = platformdirs.user_data_dir(app_name)  
# # print(data_dir) ## '/home/van_rossum/.local/share/intra-search'


# import os  
# from uuid import uuid4  
# import glob
# from flask import request, jsonify
# import pickle
# from intra_search.server import app
# from intra_search.doc import Pdf  
# from intra_search.model import Model  
# from intra_search.store import Store  
# from intra_search.utils import sanitize_filename

import os  
import glob
import json
import pickle
from uuid import uuid4
from flask import request, jsonify
from intra_search.server import app
from intra_search.doc import Pdf  
from intra_search.model import Model  
from intra_search.store import Store  
from intra_search.utils import sanitize_filename

def create_embeddings(pdf_files, model_name="msmarco-distilbert-cos-v5", chunk_size=50):  
    """Создание эмбеддингов для PDF-файлов"""    
      
    store = Store()  
    completed = []  
      
    for file_path in pdf_files:  
        if not os.path.exists(file_path):  
            print(f"Файл не найден: {file_path}")  
            continue  
              
        doc = Pdf(file_path)  
          
        # Проверяем, существуют ли уже эмбеддинги  
        if store.exist(  
            file_path=doc.file_path,  
            model_name=model_name,  
            chunk_size=chunk_size,  
        ):  
            print(f"Эмбеддинги уже существуют для: {doc.file_name}")  
            continue  
          
        print(f"Обработка документа: {doc.file_name}")  
          
        model = Model(model_name=model_name)  
          
        embedding_file_name = (  
            sanitize_filename(  
                "_".join(map(str, [doc.file_name, model_name, chunk_size]))  
            )  
            + ".pkl"  
        )  
          
        embeddings_meta = {  
            "id": str(uuid4()),  
            "model": model_name,  
            "chunk_size": chunk_size,  
            "document_path": doc.file_path,  
            "document_name": doc.file_name,  
            "embedding_name": embedding_file_name,  
        }  
          
        store.save(  
            file_name=embedding_file_name,  
            meta=embeddings_meta,  
            item={  
                **embeddings_meta,  
                "embeddings": model.get_embeddings(  
                    doc.extract_text(chunk_size=chunk_size)  
                ),  
            },  
        )  
          
        completed.append(doc.file_name)  
      
    if completed:  
        print(f"Эмбеддинги созданы для документов: {', '.join(completed)}")  
      
    return completed  


# ➕ НОВАЯ ФУНКЦИЯ: Проверка и обработка новых PDF
def check_and_process_new_pdfs(pdf_directory, model_name="msmarco-distilbert-cos-v5", chunk_size=50):
    """Проверяет каталог на наличие новых PDF и обрабатывает их"""
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    if not pdf_files:
        return []
    # Фильтруем только те, для которых ещё нет эмбеддингов
    store = Store()  # Инициализируем Store для проверки
    new_files = []
    for file_path in pdf_files:
        doc = Pdf(file_path)
        if not store.exist(file_path=doc.file_path, model_name=model_name, chunk_size=chunk_size):
            new_files.append(file_path)
    if new_files:
        print(f"Найдено {len(new_files)} новых PDF для обработки.")
        return create_embeddings(new_files, model_name, chunk_size)
    else:
        print("Новых PDF для обработки не найдено.")
        return []


# ➕ Добавляем роут в приложение для принудительной проверки
@app.route('/check-new-pdfs', methods=['GET'])
def trigger_pdf_check():
    PDF_DIRECTORY = "/data/public/bioarticles/found/"
    processed = check_and_process_new_pdfs(PDF_DIRECTORY)
    return jsonify({
        "status": "success",
        "processed_files": processed,
        "count": len(processed)
    })


# ➕ Добавляем роут для очистки осиротевших эмбеддингов
@app.route('/cleanup-embeddings', methods=['GET'])
def trigger_cleanup():
    PDF_DIRECTORY = "/data/public/bioarticles/found/"
    removed = cleanup_orphaned_embeddings_manual(PDF_DIRECTORY)
    return jsonify({
        "status": "success",
        "removed_embeddings": removed,
        "count": len(removed)
    })


EMBEDDING_DIR = "/home/van_rossum/.local/share/intra-search" #"/home/leo/.local/share/intra-search/"

def cleanup_orphaned_embeddings_manual(pdf_directory, embedding_dir=EMBEDDING_DIR):
    """Удаляет .pkl файлы и обновляет manifest.json для которых нет соответствующих PDF"""
    removed = []    
    # Путь к manifest.json
    manifest_path = os.path.join(embedding_dir, "manifest.json")
    
    # Читаем текущий manifest
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Ошибка чтения manifest.json: {e}")
            manifest = []
    else:
        manifest = []
    
    # Получаем список всех существующих PDF файлов
    existing_pdfs = set(glob.glob(os.path.join(pdf_directory, "*.pdf")))    
    # Фильтруем manifest - оставляем только записи с существующими PDF
    updated_manifest = []
    
    for entry in manifest:
        doc_path = entry.get("document_path")        
        # Если PDF существует и находится в нужной директории
        if doc_path and os.path.exists(doc_path) and doc_path in existing_pdfs:
            updated_manifest.append(entry)
        else:
            # Удаляем .pkl файл
            pkl_filename = entry.get("embedding_name")
            if pkl_filename:
                pkl_path = os.path.join(embedding_dir, pkl_filename)
                if os.path.exists(pkl_path):
                    try:
                        os.remove(pkl_path)
                        print(f"Удалён файл эмбеддинга: {pkl_path}")
                    except Exception as e:
                        print(f"Ошибка удаления {pkl_path}: {e}")
            
            removed.append(entry.get("document_name", "unknown"))
            print(f"PDF отсутствует: {doc_path} → удалена запись из manifest")
    
    # Сохраняем обновлённый manifest
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(updated_manifest, f, ensure_ascii=False, indent=4)
        print(f"Обновлён manifest.json: осталось {len(updated_manifest)} записей")
    except Exception as e:
        print(f"Ошибка записи manifest.json: {e}")    
    if removed:
        print(f"Удалено {len(removed)} осиротевших эмбеддингов: {', '.join(removed)}")
    else:
        print("Нет осиротевших эмбеддингов для удаления.")        
    return removed


# ➕ Улучшенная автоматическая проверка
@app.before_request
def auto_check_pdfs():
    # Проверяем только для главной страницы по пути
    if request.path == '/':
        print("Выполняем автоматическую проверку для главной страницы")
        PDF_DIRECTORY = "/home/van_rossum/Документы/bioarticles/found/" #"/data/public/bioarticles/found/"
        # Сначала очищаем осиротевшие эмбеддинги
        removed = cleanup_orphaned_embeddings_manual(PDF_DIRECTORY)
        # Затем проверяем новые PDF
        processed = check_and_process_new_pdfs(PDF_DIRECTORY)
        
        if removed:
            print(f"Очищено {len(removed)} эмбеддингов")
        if processed:
            print(f"Обработано {len(processed)} новых PDF")

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Возвращает список доступных PDF-документов"""
    pdf_directory = "/home/van_rossum/Документы/bioarticles/found/" #"/data/public/bioarticles/found/"
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    
    # Извлекаем только имена файлов без пути
    documents = [os.path.basename(f) for f in pdf_files]
    
    return jsonify({
        "status": "success",
        "documents": sorted(documents)  # отсортированный список
    })

if __name__ == "__main__":
    PDF_DIRECTORY = "/home/van_rossum/Документы/bioarticles/found/" #"/data/public/bioarticles/found/"

    # Очистка "осиротевших" эмбеддингов при запуске
    print("Очистка осиротевших эмбеддингов при запуске...")
    cleanup_orphaned_embeddings_manual(PDF_DIRECTORY)

    # Обработка новых PDF
    print("Проверка новых PDF при запуске...")
    PDF_FILES = glob.glob(os.path.join(PDF_DIRECTORY, "*.pdf"))
    if not PDF_FILES:
        print(f"PDF-файлы не найдены в директории: {PDF_DIRECTORY}")
    else:
        print(f"Найдено {len(PDF_FILES)} PDF-файлов")
        check_and_process_new_pdfs(PDF_DIRECTORY)  # обрабатываем только новые

    # Запуск приложения
    print("Запуск Flask приложения...")
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )