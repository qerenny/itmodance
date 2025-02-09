#json_fun.py
import json
from utils.logging_utils import setup_logger, log_function_call

logger = setup_logger('json_fun', 'utils.log')

@log_function_call(logger)
def post_client_json_updater(tg_id, json_file_path, uuid, email, period, sub_id):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        for client in data['settings']['clients']:
            client['id'] = f"{uuid}"
            client['email'] = f"{email}"
            client['tgId'] = f"{tg_id}"
            client['expiryTime'] = period
            client['subId'] = f"{sub_id}"

        data['settings'] = json.dumps(data['settings'])
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in file: {json_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error in post_client_json_updater: {str(e)}")
        raise

@log_function_call(logger)
def receipt_creator(json_file_path, description, amount):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        data['receipt']['items'][0]['description'] = f"{description}"
        data['receipt']['items'][0]['amount']['value'] = f"{amount/100:.2f}"

        data = json.dumps(data)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in file: {json_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error in receipt_creator: {str(e)}")
        raise
