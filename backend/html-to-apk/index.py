import json
import base64
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from apk_builder import build_real_apk

def handler(event: dict, context) -> dict:
    """
    Конвертирует HTML ZIP-архив в APK приложение через WebView
    """
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        app_name = body.get('appName')
        app_version = body.get('appVersion')
        zip_content = body.get('zipFile')
        icon_content = body.get('iconFile')
        
        if not all([app_name, app_version, zip_content, icon_content]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields'}),
                'isBase64Encoded': False
            }
        
        zip_data = base64.b64decode(zip_content.split(',')[1] if ',' in zip_content else zip_content)
        icon_data = base64.b64decode(icon_content.split(',')[1] if ',' in icon_content else icon_content)
        
        has_index = validate_and_prepare_html(zip_data)
        if not has_index['valid']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': has_index['error']}),
                'isBase64Encoded': False
            }
        
        apk_result = build_webview_apk(app_name, app_version, zip_data, icon_data)
        
        if apk_result['success']:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'apkFile': apk_result['apk_base64'],
                    'fileName': f"{app_name.replace(' ', '_')}_v{app_version}.apk"
                }),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': apk_result['error']}),
                'isBase64Encoded': False
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Server error: {str(e)}'}),
            'isBase64Encoded': False
        }


def validate_and_prepare_html(zip_data: bytes) -> dict:
    """
    Проверяет наличие index.html в корне архива
    """
    try:
        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            has_index = any(
                name == 'index.html' or name.endswith('/index.html') and name.count('/') == 1
                for name in file_list
            )
            
            if not has_index:
                return {
                    'valid': False,
                    'error': 'Архив должен содержать файл index.html в корне'
                }
            
            return {'valid': True}
    
    except Exception as e:
        return {
            'valid': False,
            'error': f'Ошибка чтения архива: {str(e)}'
        }


def build_webview_apk(app_name: str, app_version: str, zip_data: bytes, icon_data: bytes) -> dict:
    """
    Генерирует настоящий подписанный APK с WebView
    """
    try:
        package_name = f"com.app.{app_name.lower().replace(' ', '').replace('-', '')}"
        
        apk_bytes = build_real_apk(
            app_name=app_name,
            app_version=app_version,
            package_name=package_name,
            html_data=zip_data,
            icon_data=icon_data
        )
        
        apk_base64 = base64.b64encode(apk_bytes).decode('utf-8')
        
        return {
            'success': True,
            'apk_base64': apk_base64
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Build failed: {str(e)}'
        }


