import grpc
import random
import sys
from concurrent import futures
import settings as s
from threading import Lock

from hogwild import hogwild_pb2, hogwild_pb2_grpc
from hogwild.svm import SVM


# Create a class to define the server functions
# derived from hogwild_pb2_grpc.HogwildServicer
class HogwildServicer(hogwild_pb2_grpc.HogwildServicer):
    def __init__(self):
        self.coordinator_address = ''
        self.node_addresses = []
        self.stubs = {}

        self.data = []
        self.targets = []
        self.learning_rate = 0
        self.lambda_reg = 0
        self.epochs = 0
        self.subset_size = 0

        self.nodeinfo_received = False
        self.ready_to_calculate = False
        self.svm = None
        self.all_delta_w = {}
        self.weight_lock = Lock()
        self.wait_for_all_nodes_counter = 0

        self.ready_to_go_counter = 0
        self.epochs_done = 0
        self.stop_msg_received = False

    def GetNodeInfo(self, request, context):
        print('Received node network information!')
        self.coordinator_address = request.coordinator_address
        self.node_addresses = request.node_addresses
        self.val_indices = request.val_indices
        print('Coordinator at {}'.format(self.coordinator_address))
        print('Other nodes at {}'.format(self.node_addresses))
        for node_addr in list(self.node_addresses) + [str(self.coordinator_address)]:
            channel = grpc.insecure_channel(node_addr)
            stub = hogwild_pb2_grpc.HogwildStub(channel)
            self.stubs[node_addr] = stub
        self.nodeinfo_received = True
        response = hogwild_pb2.Empty()
        return response

    def StartSGD(self, request, context):
        self.learning_rate = request.learning_rate
        self.lambda_reg = request.lambda_reg
        self.epochs = request.epochs
        self.subset_size = request.subset_size
        dim = request.dim
        self.svm = SVM(learning_rate=self.learning_rate, lambda_reg=self.lambda_reg, dim=dim)
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


if __name__ == "__main__":
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), \
                         options=[('grpc.max_message_length', 1024 * 1024 * 1024), \
                                  ('grpc.max_send_message_length', 1024 * 1024 * 1024), \
                                  ('grpc.max_receive_message_length', 1024 * 1024 * 1024)])

    # Use the generated function `add_HogwildServicer_to_server`
    # to add the defined class to the created server
    hws = HogwildServicer()
    hogwild_pb2_grpc.add_HogwildServicer_to_server(hws, server)

    # Listen on the port specified in the command line argument
    print('Starting server. Listening on port {}.'.format(sys.argv[1]))
    server.add_insecure_port('[::]:{}'.format(sys.argv[1]))
    server.start()

    # Wait to receive node information
    while not hws.nodeinfo_received:
        pass
    print('Loading training data')
    data, targets = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                        s.TOPICS_FILE,
                                                        s.TEST_FILES,
                                                        selected_cat='CCAT',
                                                        train=True)
    data = [data[x] for x in range(len(targets)) if x not in request.val_indices]
    targets = [targets[x] for x in range(len(targets)) if x not in request.val_indices]
    print('Number of training datapoints: {}'.format(len(self.targets)))

    # Wait to receive the start command from the coordinator
    while not hws.ready_to_calculate:
        pass
    print('Starting SVM calculation.')

    try:
        epoch = 1
        while epoch < hws.epochs and not hws.stop_msg_received:
            print('Epoch {}'.format(epoch))
            # Select random subset and calculate weight updates for it
            subset_indices = random.sample(range(len(targets)), hws.subset_size)
            data_stoc = [data[x] for x in subset_indices]
            targets_stoc = [targets[x] for x in subset_indices]
            total_delta_w = hws.svm.fit(data_stoc, targets_stoc, update=not s.synchronous)

            # If SYNC send to coordinator
            if s.synchronous:
                #Send weight update to coordinator
                weight_update = hogwild_pb2.WeightUpdate(delta_w=total_delta_w)
                hws.stubs[hws.coordinator_address].GetWeightUpdate(weight_update)
                # Wait for the accumulated weight update from the coordinator
                while not hws.wait_for_all_nodes_counter == 1:
                    pass
                hws.wait_for_all_nodes_counter = 0
                # Use weight updates from all nodes to update own weights
                hws.svm.update_weights(hws.all_delta_w)
                hws.all_delta_w = {}
                hws.received_all_delta_w = False
                # Send ReadyToGo to coordinator
                rtg = hogwild_pb2.ReadyToGo()
                response = hws.stubs[hws.coordinator_address].GetReadyToGo(rtg)
                # Wait for the ReadyToGo from coordinator
                while not hws.ready_to_go_counter == 1:
                    pass
                hws.ready_to_go_counter = 0

            # If ASYNC send to all nodes
            else:
                # Send weight updates to all other nodes
                for stub in hws.stubs.values():
                    weight_update = hogwild_pb2.WeightUpdate(delta_w=total_delta_w)
                    response = stub.GetWeightUpdate(weight_update)
                # Use weight updates from other nodes to update own weights
                with hws.weight_lock:
                    hws.svm.update_weights(hws.all_delta_w)
                    hws.all_delta_w = {}

            epoch += 1
        # Send message to all nodes that SGD has finished
        for stub in hws.stubs.values():
            ep_done = hogwild_pb2.EpochsDone()
            response = stub.GetEpochsDone(ep_done)

        # Wait for message of all nodes that they also finished before quitting
        while not hws.epochs_done == len(hws.stubs) - 1:
            pass
    except KeyboardInterrupt:
        server.stop(0)
