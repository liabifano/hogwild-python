import grpc
import random
import sys
from concurrent import futures

# Import the automatically generated classes
import hogwild_pb2
import hogwild_pb2_grpc
from svm import SVM


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
        self.batch_size = 0

        self.dataset_received = False
        self.ready_to_calculate = False
        self.svm = None
        self.all_delta_w = {}
        self.wait_for_all_nodes_counter = 0

        self.ready_to_go_counter = 0
        self.epochs_done = 0

    def GetNodeInfo(self, request, context):
        print('Received node network information!')
        self.coordinator_address = request.coordinator_address
        self.node_addresses = request.node_addresses
        print('Coordinator at {}'.format(self.coordinator_address))
        print('Other nodes at {}'.format(self.node_addresses))
        for node_addr in list(self.node_addresses) + [str(self.coordinator_address)]:
            channel = grpc.insecure_channel(node_addr)
            stub = hogwild_pb2_grpc.HogwildStub(channel)
            self.stubs[node_addr] = stub
        response = hogwild_pb2.Empty()
        return response

    def GetDataSet(self, request, context):
        datapoints = request.datapoints
        for d in datapoints:
            self.data.append(dict(d.datapoint))
            self.targets.append(d.target)
        print('Received dataset!')
        print('Dataset length = {}'.format(len(self.data)))
        print('Targets length = {}'.format(len(self.targets)))
        self.dataset_received = True
        response = hogwild_pb2.Empty()
        return response

    def StartSGD(self, request, context):
        self.learning_rate = request.learning_rate
        self.lambda_reg = request.lambda_reg
        self.epochs = request.epochs
        self.batch_size = request.batch_size
        dim = max([max(k) for k in self.data]) + 1
        self.svm = SVM(learning_rate=self.learning_rate, lambda_reg=self.lambda_reg, dim=dim)
        self.ready_to_calculate = True
        response = hogwild_pb2.Empty()
        return response

    def GetWeightUpdate(self, request, context):
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

    try:
        # Wait to receive the dataset and start command from the coordinator
        while not (hws.dataset_received and hws.ready_to_calculate):
            pass
        print('Starting SVM calculation.')
        epoch = 1
        while epoch < hws.epochs:
            print('Epoch {}'.format(epoch))
            # Select random minibatch and calculate weight updates for it
            batch_indices = random.sample(range(len(hws.targets)), hws.batch_size)
            data_stoc = [hws.data[x] for x in batch_indices]
            targets_stoc = [hws.targets[x] for x in batch_indices]
            total_delta_w = hws.svm.fit(data_stoc, targets_stoc)
            # Send weight updates to all other nodes
            for stub in hws.stubs.values():
                weight_update = hogwild_pb2.WeightUpdate(delta_w=total_delta_w)
                response = stub.GetWeightUpdate(weight_update)
            # Wait for the weight updates from all other nodes
            while not hws.wait_for_all_nodes_counter == len(hws.node_addresses):
                pass
            # Use weight updates from other nodes to update own weights
            hws.svm.update_weights(hws.all_delta_w)
            hws.all_delta_w = {}
            hws.wait_for_all_nodes_counter = 0
            # Send ReadyToGo to all other nodes
            for stub in hws.stubs.values():
                rtg = hogwild_pb2.ReadyToGo()
                response = stub.GetReadyToGo(rtg)
            if epoch < hws.epochs:
                # Wait for the ReadyToGo from all other nodes
                while not hws.ready_to_go_counter == len(hws.node_addresses):
                    pass
                hws.ready_to_go_counter = 0
            epoch += 1
        # Send message to coordinator that SGD has finished
        ep_done = hogwild_pb2.EpochsDone()
        response = hws.stubs[hws.coordinator_address].GetEpochsDone(ep_done)
    except KeyboardInterrupt:
        server.stop(0)
