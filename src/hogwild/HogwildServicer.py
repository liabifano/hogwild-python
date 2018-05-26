import grpc
from threading import Lock
from hogwild import hogwild_pb2, hogwild_pb2_grpc
from datetime import datetime


# Create a class to define the server functions
# derived from hogwild_pb2_grpc.HogwildServicer
class HogwildServicer(hogwild_pb2_grpc.HogwildServicer):
    def __init__(self):
        self.coordinator_address = ''
        self.node_addresses = []
        self.stubs = {}

        self.val_indices = []
        self.train_losses = []

        self.nodeinfo_received = False
        self.ready_to_calculate = False
        self.all_delta_w = {}
        self.weight_lock = Lock()
        self.wait_for_all_nodes_counter = 0

        self.ready_to_go_counter = 0
        self.epochs_done = 0
        self.stop_msg_received = False

    def GetNodeInfo(self, request, context):
        print('Received node network information!!!!')
        self.coordinator_address = request.coordinator_address
        self.node_addresses = request.node_addresses
        self.val_indices = request.val_indices
        self.worker_idx = request.worker_idx
        print('Coordinator at {}'.format(self.coordinator_address))
        print('Other nodes at {}'.format(self.node_addresses))
        # TODO: Remove it when it is asyncronous. But fix it in the epochs_done
        for node_addr in list(self.node_addresses) + [str(self.coordinator_address)]:
            channel = grpc.insecure_channel(node_addr)
            stub = hogwild_pb2_grpc.HogwildStub(channel)
            self.stubs[node_addr] = stub
        self.nodeinfo_received = True
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
            self.wait_for_all_nodes_counter += 1
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
        print('Got loss {} from worker {}'.format(request.loss, request.worker_idx))
        loss_log = {'worker_idx': request.worker_idx,
                    'loss_train': request.loss,
                    'time': datetime.utcfromtimestamp(request.timestamp).strftime("%Y-%m-%d %H:%M:%S")}
        self.train_losses.append(loss_log)
        response = hogwild_pb2.Empty()
        return response
