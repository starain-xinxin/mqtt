import multiprocessing
from legacy.mqtt2 import server_process
from GUI import ui_process

if __name__ == "__main__":
    # 创建 Queue 用于进程间通信
    queue = multiprocessing.Queue()

    # 启动服务器进程
    server = multiprocessing.Process(target=server_process, args=(queue,))
    server.start()

    # 启动 UI 进程
    ui_process(queue)

    # 等待服务器进程结束
    server.join()
