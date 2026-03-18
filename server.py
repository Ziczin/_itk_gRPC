import grpc
from concurrent import futures

import kvstore_pb2 as pb2
import kvstore_pb2_grpc as pb2_grpc
import time


class KeyValueStoreServicer(pb2_grpc.KeyValueStoreServicer):
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.storage: dict[str, str] = {}

    def List(
        self, request: pb2.ListRequest, context: grpc.ServicerContext
    ) -> pb2.ListResponse:
        items = []
        for key, value in list(self.storage.items()):
            if value["ttl"] > 0 and time.time() > value["last_used"] + value["ttl"]:
                del self.storage[key]

            if key.startswith(request.prefix):
                items.append(pb2.KeyValue(key=key, value=value["value"]))

        return pb2.ListResponse(items=items)

    def Get(
        self, request: pb2.GetRequest, context: grpc.ServicerContext
    ) -> pb2.GetResponse:
        try:
            obj = self.storage[request.key]

            if obj["ttl"] > 0 and time.time() > obj["last_used"] + obj["ttl"]:
                del self.storage[request.key]
                raise KeyError

            obj["last_used"] = time.time()

            return pb2.GetResponse(value=obj["value"])

        except KeyError:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Key not found")
            return pb2.GetResponse()

    def Put(
        self, request: pb2.PutRequest, context: grpc.ServicerContext
    ) -> pb2.PutResponse:
        self.storage[request.key] = {
            "value": request.value,
            "ttl": request.ttl_seconds,
            "last_used": time.time(),
        }
        if len(self.storage) > 10:
            del self.storage[
                min(self.storage, key=lambda key: self.storage[key]["last_used"])
            ]
        return pb2.PutResponse()

    def Delete(
        self, request: pb2.DeleteRequest, context: grpc.ServicerContext
    ) -> pb2.DeleteResponse:
        try:
            del self.storage[request.key]

        except KeyError:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Key not found")

        return pb2.DeleteResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStoreServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
