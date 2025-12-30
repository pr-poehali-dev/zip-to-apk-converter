import json
import base64
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from io import BytesIO

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


def build_webview_apk(app_name: str, app_version: str, zip_data: bytes, icon_data: bytes) -> dict:
    """
    Генерирует простой APK-шаблон с WebView (симуляция сборки)
    """
    try:
        apk_template = create_minimal_apk_template(app_name, app_version, zip_data, icon_data)
        apk_base64 = base64.b64encode(apk_template).decode('utf-8')
        
        return {
            'success': True,
            'apk_base64': apk_base64
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Build failed: {str(e)}'
        }


def create_minimal_apk_template(app_name: str, app_version: str, zip_data: bytes, icon_data: bytes) -> bytes:
    """
    Создает минимальный APK-подобный архив с манифестом
    """
    
    apk_buffer = BytesIO()
    
    with zipfile.ZipFile(apk_buffer, 'w', zipfile.ZIP_DEFLATED) as apk_zip:
        manifest_content = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.app.{app_name.lower().replace(' ', '').replace('-', '')}"
    android:versionCode="1"
    android:versionName="{app_version}">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <application
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true">
        
        <activity android:name=".MainActivity"
            android:label="{app_name}"
            android:theme="@android:style/Theme.NoTitleBar.Fullscreen">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
        
        apk_zip.writestr('AndroidManifest.xml', manifest_content)
        
        apk_zip.writestr('assets/www.zip', zip_data)
        
        apk_zip.writestr('res/mipmap-xxxhdpi/ic_launcher.png', icon_data)
        
        readme_content = f'''APK Template for {app_name} v{app_version}

This is a template APK structure. For a real Android application:
1. Use Android Studio or Gradle build tools
2. Compile Java/Kotlin code with Android SDK
3. Sign the APK with a keystore
4. Optimize with zipalign and ProGuard

This file demonstrates the structure but is NOT a valid installable APK.
For production use, integrate with proper Android build pipeline.
'''
        apk_zip.writestr('README.txt', readme_content)
    
    apk_buffer.seek(0)
    return apk_buffer.read()
