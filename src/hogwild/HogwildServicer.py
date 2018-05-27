import grpc
from concurrent import futures
from threading import Lock
from hogwild import hogwild_pb2, hogwild_pb2_grpc
from hogwild import settings as s
from datetime import datetime

def create_servicer(port):
    '''
    Creates a gRPC server and HogwildServicer
    '''
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) # TODO: Increase max_workers?

    # Use the generated function `add_HogwildServicer_to_server`
    # to add the defined class to the created server
    hws = HogwildServicer()
    hogwild_pb2_grpc.add_HogwildServicer_to_server(hws, server)

    # Listen on port defined in settings.py
    print('Starting server. Listening on port {}.'.format(port))
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()
    return hws, server


# Create a class to define the server functions
# derived from hogwild_pb2_grpc.HogwildServicer
class HogwildServicer(hogwild_pb2_grpc.HogwildServicer):
    def __init__(self):
        self.other_workers = []
        self.stubs = {}

        self.val_indices = []
        self.train_losses = []

        self.workerinfo_received = False
        self.ready_to_calculate = False
        self.all_delta_w = {}
        self.weight_lock = Lock()
        self.wait_for_all_workers_counter = 0

        self.ready_to_go_counter = 0
        self.epochs_done = 0
        self.stop_msg_received = False

    def GetWorkerInfo(self, request, context):
        self.other_workers = request.other_workers
        self.val_indices = request.val_indices
        self.worker_idx = request.worker_idx
        print('Other workers at {}'.format(self.other_workers))
        for worker_addr in list(self.other_workers) + [str(s.coordinator_address)]:
            channel = grpc.insecure_channel(worker_addr)
            stub = hogwild_pb2_grpc.HogwildStub(channel)
            self.stubs[worker_addr] = stub
        self.workerinfo_received = True
        response = hogwild_pb2.Empty()
        return response

    def StartSGD(self, request, context):
        self.ready_to_calculate = True
        response = hogwild_pb2.Empty()
        return response

    def GetWeightUpdate(self, request, context):
        with self.weight_lock:
            for k, v in dict(request.delta_w).items():
                if k in self.all_delta_w:
                    self.all_delta_w[k] += v
                else:
                    self.all_delta_w[k] = v
            self.wait_for_all_workers_counter += 1
        response = hogwild_pb2.Empty()
        return response

    def GetReadyToGo(self, request, context):
        self.ready_to_go_counter += 1
        response = hogwild_pb2.Empty()
        return response

    def GetEpochsDone(self, request, context):
        self.epochs_done += 1
        response = hogwild_pb2.Empty()
        return response

    def GetStopMessage(self, request, context):
        self.stop_msg_received = True
        response = hogwild_pb2.Empty()
        return response

    def GetLossMessage(self, request, context):
        loss_log = {'worker_idx': request.worker_idx,
                    'loss_train': request.loss,
                    'time': request.timestamp}
        self.train_losses.append(loss_log)
        response = hogwild_pb2.Empty()
        return response
