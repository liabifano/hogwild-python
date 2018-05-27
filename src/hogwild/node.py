import grpc
import random
import sys
from concurrent import futures
import settings as s
import multiprocessing

from hogwild import hogwild_pb2, hogwild_pb2_grpc
from hogwild.HogwildServicer import HogwildServicer
from hogwild.svm import SVM, svm_subprocess
from hogwild import ingest_data
from time import time
from datetime import datetime
import json


if __name__ == "__main__":
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

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

    # Create queues for communication with the SVM process
    task_queue = multiprocessing.Queue()
    response_queue = multiprocessing.Queue()
    svm_proc = multiprocessing.Process(target=svm_subprocess, args=(task_queue, response_queue, hws.val_indices))
    svm_proc.start()

    # Wait to receive the start command from the coordinator
    while not hws.ready_to_calculate:
        pass
    print('Starting SVM calculation.')

    try:
        epoch = 1
        while epoch <= s.epochs and not hws.stop_msg_received:
            print('Epoch {}'.format(epoch))

            # Send command to SVM process to calculate weight update and send
            # to coordinator (and all nodes if asynchronous)
            task_queue.put({'type': 'calculate_svm_update'})
            response = response_queue.get()
            delta_w = response['total_delta_w']
            train_loss = response['train_loss']
            timestamp = datetime.utcfromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S.%f")
            # Send current train loss to coordinator
            loss_msg = hogwild_pb2.LossMessage(loss=train_loss, timestamp=timestamp, worker_idx=hws.worker_idx)
            response = hws.stubs[hws.coordinator_address].GetLossMessage(loss_msg)

            # Send weight update to coordinator
            weight_update = hogwild_pb2.WeightUpdate(delta_w=delta_w)
            response = hws.stubs[hws.coordinator_address].GetWeightUpdate(weight_update)
            # If ASYNC, send weight update to all workers
            if not s.synchronous:
                for stub in [hws.stubs[node_addr] for node_addr in hws.node_addresses]:
                    weight_update = hogwild_pb2.WeightUpdate(delta_w=delta_w)
                    response = stub.GetWeightUpdate(weight_update)

            # If SYNC communicate only with coordinator
            if s.synchronous:
                # Wait for the accumulated weight update from the coordinator
                while not hws.wait_for_all_nodes_counter == 1:
                    pass
                hws.wait_for_all_nodes_counter = 0

                # Use accumulated weight updates from other nodes to update own weights
                task_queue.put({'type': 'update_weights',
                                'all_delta_w': hws.all_delta_w})
                hws.all_delta_w = {}

                # Send ReadyToGo to coordinator
                rtg = hogwild_pb2.ReadyToGo()
                response = hws.stubs[hws.coordinator_address].GetReadyToGo(rtg)
                # Wait for the ReadyToGo from coordinator
                while not hws.ready_to_go_counter == 1:
                    pass
                hws.ready_to_go_counter = 0

            # If ASYNC communicate with coordinator and all workers
            else:
                # Use accumulated weight updates from other nodes to update own weights
                with hws.weight_lock:
                    task_queue.put({'type': 'update_weights',
                                    'all_delta_w': hws.all_delta_w})
                    hws.all_delta_w = {}

            epoch += 1
            # with open('epochs_done.json', 'w') as outfile:
            #     json.dump([{'last_epoch': epoch}], outfile)

        # Send poison pill to SVM process
        task_queue.put(None)

        # Close queues and join processes
        task_queue.close()
        task_queue.join_thread()
        response_queue.close()
        response_queue.join_thread()
        svm_proc.join()

        # Send message to all nodes that SGD has finished
        for stub in hws.stubs.values():
            ep_done = hogwild_pb2.EpochsDone()
            response = stub.GetEpochsDone(ep_done)

        # with open('other_nodes_epochs1.json', 'w') as outfile:
        #     json.dump([{'last_epoch': hws.epochs_done,
        #                 'len_stubs': len(hws.stubs)}], outfile)


        # Wait for message of all nodes that they also finished before quitting
        while not hws.epochs_done == len(hws.stubs) - 1:
            # with open('other_nodes_epochs1.json', 'w') as outfile:
            #     json.dump([{'last_epoch': hws.epochs_done,
            #                 'len_stubs': len(hws.stubs)}], outfile)
            pass

    except KeyboardInterrupt:
        server.stop(0)
