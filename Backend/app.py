from app import create_app
import ssl
import os
import logging

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    logging.info("正在启动电力资产缺陷识别API服务...")
    
    # SSL 配置
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    # 检查证书是否存在，如果不存在，尝试生成或以非SSL模式运行
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        logging.warning("未找到SSL证书。正在检查生成脚本...")
        if os.path.exists('scripts/generate_cert.py'):
            logging.info("正在生成自签名证书...")
            os.system('python scripts/generate_cert.py')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logging.info("找到SSL证书。正在以HTTPS模式启动...")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        app.run(
            host='0.0.0.0',
            port=8090,
            debug=True,
            threaded=True,
            ssl_context=context
        )
    else:
        logging.warning("无法找到或生成SSL证书。正在以HTTP模式启动...")
        app.run(
            host='0.0.0.0',
            port=8090,
            debug=True,
            threaded=True
        )
