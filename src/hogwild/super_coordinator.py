import grpc
import json
import random
import multiprocessing
from concurrent import futures
from datetime import datetime
from hogwild import hogwild_pb2, hogwild_pb2_grpc, ingest_data, utils
from hogwild import settings as s
from hogwild.EarlyStopping import EarlyStopping
from hogwild.HogwildServicer import HogwildServicer
from hogwild.svm import SVM, svm_subprocess
from time import time, sleep


if __name__ == '__main__':
    # Step 1: Load the data from the reuters dataset and create targets
    print('Data path:', s.TRAIN_FILE)
    dataset_size = sum(1 for line in open(s.TRAIN_FILE))
    val_indices = random.sample(range(dataset_size), int(s.validation_split * dataset_size))
    print('Whole dataset size: {}'.format(dataset_size))

    # Step 2: Startup the nodes
    # addresses of all nodes and coordinator and the dataset to all worker nodes
    stubs = {}

    for i, node_addr in enumerate(s.node_addresses):
        # Open a gRPC channel
        channel = grpc.insecure_channel(node_addr, options=[('grpc.max_message_length', 1024 * 1024 * 1024),
                                                            ('grpc.max_send_message_length', 1024 * 1024 * 1024),
                                                            ('grpc.max_receive_message_length', 1024 * 1024 * 1024)])
        # Create a stub (client)
        stub = hogwild_pb2_grpc.HogwildStub(channel)
        stubs[node_addr] = stub
        # Send to each node the list of all other nodes and the coordinator
        other_nodes = s.node_addresses.copy()
        other_nodes.remove(node_addr)
        info = hogwild_pb2.NetworkInfo(coordinator_address=s.coordinator_address, node_addresses=other_nodes,
                                       val_indices=val_indices, worker_idx=i)
        response = stub.GetNodeInfo(info)

    # Create queues for communication with the SVM process
    task_queue = multiprocessing.Queue()
    response_queue = multiprocessing.Queue()
    svm_proc = multiprocessing.Process(target=svm_subprocess, args=(task_queue, response_queue, val_indices)) # TODO: None
    svm_proc.start()

    # Step 3: Create a listener for the coordinator and send start command to all nodes
    # Create a gRPC server
    # TODO: Increase #threads?
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Use the generated function `add_HogwildServicer_to_server`
    # to add the defined class to the created server
    hws = HogwildServicer()
    hogwild_pb2_grpc.add_HogwildServicer_to_server(hws, server)

    # Listen on port defined in settings.py
    print('Starting coordinator server. Listening on port {}.'.format(s.port))
    server.add_insecure_port('[::]:{}'.format(s.port))
    server.start()

    # Send start message to all the nodes
    for stub in stubs.values():
        start = hogwild_pb2.StartMessage()
        response = stub.StartSGD(start)
    print('Start message sent to all nodes. SGD running...')

    # Early stopping
    early_stopping = EarlyStopping(s.persistence)
    stopping_crit_reached = False

    # Wait until SGD done and calculate prediction
    try:
        t0 = time()
        losses_val = []
        n_epochs = 1
        while hws.epochs_done != len(s.node_addresses) and not stopping_crit_reached:
            # If SYNC
            if s.synchronous:
                # Wait for the weight updates from all workers
                while not hws.wait_for_all_nodes_counter == len(s.node_addresses):
                    pass
                # Send accumulated weight update to all workers
                for stub in stubs.values():
                    weight_update = hogwild_pb2.WeightUpdate(delta_w=hws.all_delta_w)
                    response = stub.GetWeightUpdate(weight_update)
                # Use accumulated weight updates from other nodes to update own weights
                task_queue.put({'type': 'update_weights',
                                'all_delta_w': hws.all_delta_w})
                hws.all_delta_w = {}
                hws.wait_for_all_nodes_counter = 0
                # Wait for the ReadyToGo from all workers
                while not hws.ready_to_go_counter == len(s.node_addresses):
                    pass
                # Send ReadyToGo to all workers
                for stub in stubs.values():
                    rtg = hogwild_pb2.ReadyToGo()
                    response = stub.GetReadyToGo(rtg)
                hws.ready_to_go_counter = 0
                print('CEpoch {} done'.format(n_epochs))
                if n_epochs == s.epochs:
                    break
                n_epochs += 1

            # If ASYNC
            else:
                # Wait for sufficient number of weight updates
                while len(hws.all_delta_w) < s.subset_size * len(s.node_addresses):
                    if hws.epochs_done == len(s.node_addresses) or stopping_crit_reached:
                        break
                print(len(hws.all_delta_w))
                with hws.weight_lock:
                    # Use accumulated weight updates from workers to update own weights
                    task_queue.put({'type': 'update_weights',
                                    'all_delta_w': hws.all_delta_w})
                    hws.all_delta_w = {}

            # Calculate validation loss
            task_queue.put({'type': 'calculate_val_loss'})
            val_loss = response_queue.get()
            #response_queue.task_done()

            losses_val.append({'time': datetime.utcfromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S.%f"),
                               'loss_val': val_loss})
            print('Val loss: {:.4f}'.format(val_loss))

            # Check for early stopping
            stopping_crit_reached = early_stopping.stopping_criterion(val_loss)
            if stopping_crit_reached:
                for stub in stubs.values():
                    stop_msg = hogwild_pb2.StopMessage()
                    response = stub.GetStopMessage(stop_msg)

            print('Epochs done {}/{}'.format(hws.epochs_done, len(s.node_addresses)))

        print('All SGD epochs done!')

        # IF ASYNC, flush the weight buffer one last time
        if not s.synchronous:
            task_queue.put({'type': 'update_weights',
                            'all_delta_w': hws.all_delta_w})



        ### TEMP

        data, targets = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                            s.TOPICS_FILE,
                                                            s.TEST_FILES,
                                                            selected_cat='CCAT',
                                                            train=True)
        data_val = [data[x] for x in val_indices]
        targets_val = [targets[x] for x in val_indices]

        ### TEMP

        # Calculate the predictions on the validation set
        task_queue.put({'type': 'predict', 'values': data_val})
        prediction = response_queue.get()
        #response_queue.task_done()

        a = sum([1 for x in zip(targets_val, prediction) if x[0] == 1 and x[1] == 1])
        b = sum([1 for x in targets_val if x == 1])
        print('Val accuracy of Label 1: {:.2f}%'.format(a / b))

        c = sum([1 for x in zip(targets_val, prediction) if x[0] == -1 and x[1] == -1])
        d = sum([1 for x in targets_val if x == -1])
        print('Val accuracy of Label -1: {:.2f}%'.format(c / d))
        print('Val accuracy: {:.2f}%'.format(utils.accuracy(targets_val, prediction)))

        t1 = time()

        log = [{'start_time': datetime.utcfromtimestamp(t0).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'end_time': datetime.utcfromtimestamp(t1).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'running_time': t1 - t0,
                'n_workers': s.N_WORKERS,
                'running_mode': s.running_mode,
                'accuracy': utils.accuracy(targets_val, prediction),
                'accuracy_1': a / b,
                'accuracy_-1': c / d,
                'losses_val': losses_val,
                'losses_train': hws.train_losses}]

        with open('log.json', 'w') as outfile:
            json.dump(log, outfile)

        # Send poison pill to SVM process
        task_queue.put(None)

        # Close queues and join processes
        task_queue.close()
        task_queue.join_thread()
        response_queue.close()
        response_queue.join_thread()
        svm_proc.join()

    except KeyboardInterrupt:
        server.stop(0)
