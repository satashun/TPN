# utils/data_loader.py
import json
import os
from models.solution import Solution
from models.additive import Additive
import logging

def load_solutions(file_path='data/base_solutions.json'):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, '..', file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            solutions_data = json.load(f)
        solutions = [Solution(**sol) for sol in solutions_data]
        logging.debug("ベース製剤データのロードに成功しました。")
        return solutions
    except FileNotFoundError:
        logging.error(f"ベース製剤データファイルが見つかりません: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"ベース製剤データファイルのJSON解析エラー: {e}")
        return []

def load_additives(file_path='data/additives.json'):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, '..', file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            additives_data = json.load(f)
        additives = {add['name']: Additive(**add) for add in additives_data}
        logging.debug("添加剤データのロードに成功しました。")
        return additives
    except FileNotFoundError:
        logging.error(f"添加剤データファイルが見つかりません: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"添加剤データファイルのJSON解析エラー: {e}")
        return {}
