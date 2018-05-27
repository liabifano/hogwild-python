import grpc
import json
import random
import multiprocessing
from concurrent import futures
from datetime import datetime
from hogwild import hogwild_pb2, hogwild_pb2_grpc, ingest_data
from hogwild import settings as s
from hogwild.EarlyStopping import EarlyStopping
from hogwild.HogwildServicer import HogwildServicer, create_servicer
from hogwild.svm import svm_subprocess
from hogwild.utils import calculate_accs
from time import time


def open_connections(val_indices, worker_addresses):
    stubs = {}
    for i, worker_addr in enumerate(worker_addresses):
        # Open a gRPC channel
        channel = grpc.insecure_channel(worker_addr)
        # Create a stub (client)
        stub = hogwild_pb2_grpc.HogwildStub(channel)
        stubs[worker_addr] = stub
        # Send to each worker the list of all other workers and the coordinator, the validation indices and a unique index
        other_workers = worker_addresses.copy()
        other_workers.remove(worker_addr)
        info = hogwild_pb2.NetworkInfo(other_workers=other_workers,
                                       val_indices=val_indices, worker_idx=i)
        response = stub.GetWorkerInfo(info)
    return stubs


if __name__ == '__main__':
    # Step 1: Calculate the indices reserved for the validation set
    dataset_size = sum(1 for line in open(s.TRAIN_FILE))
    val_indices = random.sample(range(dataset_size), int(s.validation_split * dataset_size))
    print('Data set size: {}, Train set size: {}, Validation set size: {}'.format(dataset_size,
                                                                                  dataset_size-len(val_indices),
                                                                                  len(val_indices)))

    # Step 2: Open connections to all workers
    stubs = open_connections(val_indices, s.worker_addresses)

    # Step 3: Start the coordinator SVM process
    task_queue = multiprocessing.Queue()
    response_queue = multiprocessing.Queue()
    svm_proc = multiprocessing.Process(target=svm_subprocess, args=(task_queue, response_queue, val_indices))
    svm_proc.start()

    # Step 4: Create a listener for the coordinator
    hws, server = create_servicer(s.port)

    # Step 5: Send start message to all the workers
    for stub in stubs.values():
        start = hogwild_pb2.StartMessage()
        response = stub.StartSGD(start)
    print('Start message sent to all workers. SGD running...')

    # Early stopping
    early_stopping = EarlyStopping(s.persistence)
    stopping_crit_reached = False

    try:
        start_time = time()
        losses_val = []
        n_epochs = 1
        # Run until SGD is done or stopping criterion was reached
        while hws.epochs_done != len(s.worker_addresses) and not stopping_crit_reached:
            # If SYNC
            if s.synchronous:
                # Wait for the weight updates from all workers
                while not hws.wait_for_all_workers_counter == len(s.worker_addresses):
                    pass
                # Send accumulated weight update to all workers
                for stub in stubs.values():
                    weight_update = hogwild_pb2.WeightUpdate(delta_w=hws.all_delta_w)
                    response = stub.GetWeightUpdate(weight_update)
                # Use accumulated weight updates to update own SVM weights
                task_queue.put({'type': 'update_weights',
                                'all_delta_w': hws.all_delta_w})
                hws.all_delta_w = {}
                hws.wait_for_all_workers_counter = 0
                # Wait for the ReadyToGo from all workers
                while not hws.ready_to_go_counter == len(s.worker_addresses):
                    pass
                # Send ReadyToGo to all workers
                for stub in stubs.values():
                    rtg = hogwild_pb2.ReadyToGo()
                    response = stub.GetReadyToGo(rtg)
                hws.ready_to_go_counter = 0
                print('Coordinator Epoch {} done'.format(n_epochs))
                # Stop when all epochs done
                if n_epochs == s.epochs:
                    break
                n_epochs += 1

            # If ASYNC
            else:
                # Wait for sufficient number of weight updates (Waiting for approximately
                # as much as in synchronous case.) to update own SVM weights every now and again
                while len(hws.all_delta_w) < s.subset_size * len(s.worker_addresses):
                    # Stop when all epochs done or stopping criterion reached
                    if hws.epochs_done == len(s.worker_addresses) or stopping_crit_reached:
                        break
                with hws.weight_lock:
                    # Use accumulated weight updates to update own weights
                    task_queue.put({'type': 'update_weights',
                                    'all_delta_w': hws.all_delta_w})
                    hws.all_delta_w = {}

            # Calculate validation loss
            task_queue.put({'type': 'calculate_val_loss'})
            val_loss = response_queue.get()
            losses_val.append({'time': datetime.utcfromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S.%f"),
                               'loss_val': val_loss})
            print('Val loss: {:.4f}'.format(val_loss))

            # Check for early stopping
            stopping_crit_reached = early_stopping.stopping_criterion(val_loss)
            if stopping_crit_reached:
                # Send stop message to all workers
                for stub in stubs.values():
                    stop_msg = hogwild_pb2.StopMessage()
                    response = stub.GetStopMessage(stop_msg)

        # IF ASYNC, flush the weight buffer one last time
        print('update_weights')
        if not s.synchronous:
            task_queue.put({'type': 'update_weights',
                            'all_delta_w': hws.all_delta_w})

        end_time = time()
        print('All SGD epochs done!')


        ### Calculating final accuracies on train, validation and test sets ###
        print('reading data')
        data_test, targets_test = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                            s.TOPICS_FILE,
                                                            s.TEST_FILES,
                                                            selected_cat='CCAT',
                                                            train=False)

        ### TEMP
        print('read_data')
        # Calculate the predictions on the validation set
        task_queue.put({'type': 'predict', 'values': data_test})
        prediction = response_queue.get()
        #response_queue.task_done()
        print('queues closed')

        a = sum([1 for x in zip(targets_test, prediction) if x[0] == 1 and x[1] == 1])
        b = sum([1 for x in targets_test if x == 1])
        print('Val accuracy of Label 1: {:.2f}%'.format(a / b))

        # Load the train dataset
        print('Loading train and validation sets to calculate final accuracies')
        data, targets = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                            s.TOPICS_FILE,
                                                            s.TEST_FILES,
                                                            selected_cat='CCAT',
                                                            train=True)
        data_train, targets_train, data_val, targets_val = ingest_data.train_val_split(data, targets, val_indices)

        # Calculate the predictions on the train set
        task_queue.put({'type': 'predict', 'values': data_train})
        preds_train = response_queue.get()
        acc_pos_train, acc_neg_train, acc_tot_train = calculate_accs(targets_train, preds_train)
        print('Train accuracy of Label 1: {:.2f}%'.format(acc_pos_train))
        print('Train accuracy of Label -1: {:.2f}%'.format(acc_neg_train))
        print('Train accuracy: {:.2f}%'.format(acc_tot_train))

        # Calculate the predictions on the validation set
        task_queue.put({'type': 'predict', 'values': data_val})
        preds_val = response_queue.get()
        acc_pos_val, acc_neg_val, acc_tot_val = calculate_accs(targets_val, preds_val)
        print('Val accuracy of Label 1: {:.2f}%'.format(acc_pos_val))
        print('Val accuracy of Label -1: {:.2f}%'.format(acc_neg_val))
        print('Val accuracy: {:.2f}%'.format(acc_tot_val))

        # Load the test dataset
        print('Loading test set')
        data_test, targets_test = ingest_data.load_large_reuters_data(s.TRAIN_FILE,
                                                                      s.TOPICS_FILE,
                                                                      s.TEST_FILES,
                                                                      selected_cat='CCAT',
                                                                      train=False)

        # Calculate the predictions on the test set
        task_queue.put({'type': 'predict', 'values': data_test})
        preds_test = response_queue.get()
        acc_pos_test, acc_neg_test, acc_tot_test = calculate_accs(targets_test, preds_test)
        print('Test accuracy of Label 1: {:.2f}%'.format(acc_pos_test))
        print('Test accuracy of Label -1: {:.2f}%'.format(acc_neg_test))
        print('Test accuracy: {:.2f}%'.format(acc_tot_test))


        # Save results in a log
        log = [{'start_time': datetime.utcfromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'end_time': datetime.utcfromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'running_time': end_time - start_time,
                'n_workers': s.N_WORKERS,
                'running_mode': s.running_mode,
                'sync_epochs': n_epochs-1,
                'accuracy_train': acc_tot_train,
                'accuracy_1_train': acc_pos_train,
                'accuracy_-1_train': acc_neg_train,
                'accuracy_val': acc_tot_val,
                'accuracy_1_val': acc_pos_val,
                'accuracy_-1_val': acc_neg_val,
                'accuracy_test': acc_tot_test,
                'accuracy_1_test': acc_pos_test,
                'accuracy_-1_test': acc_neg_test,
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
