import eventlet
import ssl
import os
eventlet.monkey_patch()

from app import app, socketio
import eventlet.wsgi

if __name__ == '__main__':
    # 建立 SSL context
    certfile = 'fullchain.pem'
    keyfile = 'privkey.pem'

    # 設置適當的工作線程數
    os.environ['EVENTLET_THREADPOOL_SIZE'] = '30'

    # 建立一個 SSL socket
    listener = eventlet.listen(('0.0.0.0', 5000))
    wrapped_socket = eventlet.wrap_ssl(
        listener,
        certfile=certfile,
        keyfile=keyfile,
        server_side=True
    )

    # 使用 eventlet.wsgi.server 手動啟動，增加池大小
    eventlet.wsgi.server(wrapped_socket, app, max_size=1000)
