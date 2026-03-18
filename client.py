import grpc
import kvstore_pb2 as pb2
import kvstore_pb2_grpc as pb2_grpc
import time


def run_tests():
    # Подключаемся к серверу
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.KeyValueStoreStub(channel)
    
    print("=== Тест 1: Put и Get ===")
    # Кладем значение
    stub.Put(pb2.PutRequest(key="user:1", value="Alice", ttl_seconds=5))
    print("Put: user:1 = Alice (TTL 5 сек)")
    
    # Читаем значение
    response = stub.Get(pb2.GetRequest(key="user:1"))
    print(f"Get user:1 -> {response.value}")
    
    print("\n=== Тест 2: Get несуществующего ключа ===")
    try:
        stub.Get(pb2.GetRequest(key="user:999"))
    except grpc.RpcError as e:
        print(f"Ожидаемая ошибка: {e.code()} - {e.details()}")
    
    print("\n=== Тест 3: Put и Get с разными ключами ===")
    stub.Put(pb2.PutRequest(key="user:2", value="Bob", ttl_seconds=0))
    stub.Put(pb2.PutRequest(key="user:3", value="Charlie", ttl_seconds=10))
    stub.Put(pb2.PutRequest(key="admin:1", value="Admin", ttl_seconds=0))
    
    for key in ["user:2", "user:3", "admin:1"]:
        resp = stub.Get(pb2.GetRequest(key=key))
        print(f"{key} -> {resp.value}")
    
    print("\n=== Тест 4: List с префиксом 'user:' ===")
    response = stub.List(pb2.ListRequest(prefix="user:"))
    print(f"Найдено {len(response.items)} элементов:")
    for item in response.items:
        print(f"  {item.key} = {item.value}")
    
    print("\n=== Тест 5: List с префиксом 'admin:' ===")
    response = stub.List(pb2.ListRequest(prefix="admin:"))
    print(f"Найдено {len(response.items)} элементов:")
    for item in response.items:
        print(f"  {item.key} = {item.value}")
    
    print("\n=== Тест 6: Delete ===")
    stub.Delete(pb2.DeleteRequest(key="user:2"))
    print("Удалили user:2")
    
    try:
        stub.Get(pb2.GetRequest(key="user:2"))
    except grpc.RpcError as e:
        print(f"user:2 после удаления: {e.code()}")
    
    print("\n=== Тест 7: TTL (ждем 6 секунд) ===")
    print("Ждем 6 секунд...")
    time.sleep(6)
    
    try:
        stub.Get(pb2.GetRequest(key="user:1"))
    except grpc.RpcError as e:
        print(f"user:1 после TTL: {e.code()} - {e.details()}")
    
    # user:3 еще должен жить (TTL 10 сек)
    resp = stub.Get(pb2.GetRequest(key="user:3"))
    print(f"user:3 еще жив: {resp.value}")
    
    print("\n=== Тест 8: LRU (max_size=10) ===")
    print("Добавляем 15 ключей...")
    for i in range(15):
        stub.Put(pb2.PutRequest(key=f"lru:{i}", value=f"val{i}", ttl_seconds=0))
    
    response = stub.List(pb2.ListRequest(prefix="lru:"))
    print(f"Осталось в хранилище: {len(response.items)} ключей")
    keys = [item.key for item in response.items]
    print(f"Ключи: {sorted(keys)}")
    
    print("\n=== Тест 9: List с пустым префиксом ===")
    response = stub.List(pb2.ListRequest(prefix=""))
    print(f"Всего ключей в хранилище: {len(response.items)}")


def interactive_mode():
    """Интерактивный режим для ручного тестирования"""
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.KeyValueStoreStub(channel)
    
    print("\n=== Интерактивный режим ===")
    print("Команды: put key value [ttl], get key, delete key, list [prefix], exit")
    
    while True:
        cmd = input("\n> ").strip().split()
        if not cmd:
            continue
        
        if cmd[0] == "exit":
            break
        
        try:
            if cmd[0] == "put" and len(cmd) >= 3:
                key = cmd[1]
                value = cmd[2]
                ttl = int(cmd[3]) if len(cmd) > 3 else 0
                stub.Put(pb2.PutRequest(key=key, value=value, ttl_seconds=ttl))
                print(f"OK: {key} = {value} (TTL {ttl})")
            
            elif cmd[0] == "get" and len(cmd) == 2:
                resp = stub.Get(pb2.GetRequest(key=cmd[1]))
                print(f"{cmd[1]} = {resp.value}")
            
            elif cmd[0] == "delete" and len(cmd) == 2:
                stub.Delete(pb2.DeleteRequest(key=cmd[1]))
                print(f"Удален: {cmd[1]}")
            
            elif cmd[0] == "list":
                prefix = cmd[1] if len(cmd) > 1 else ""
                resp = stub.List(pb2.ListRequest(prefix=prefix))
                print(f"Найдено {len(resp.items)} ключей:")
                for item in resp.items:
                    print(f"  {item.key} = {item.value}")
            
            else:
                print("Неизвестная команда")
                
        except grpc.RpcError as e:
            print(f"Ошибка: {e.code()} - {e.details()}")


if __name__ == "__main__":
    print("Запуск тестов...")
    run_tests()
    
    # Раскомментируй для интерактивного режима
    # interactive_mode()