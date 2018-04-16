from hogwild.svm import SVM

mock_data = [{1: 0.1, 2: 0.2},
             {1: 0.2, 4: 0.9},
             {3: 0.9, 8: 1},
             {4: 0.4, 5: 0.7}]
mock_labels = [1, -1, 1, -1]

mock_delta_w = {1: 0.01, 2: 0.02, 3: 0.03, 4: 0.04, 5: 0.05, 6: 0, 7: 0, 8: 0.08}


def test_fit():
    svm = SVM(1, 1e-5, 9)
    expected_result = {1: -0.100001,
                       2: 0.2,
                       3: 0.9,
                       4: -1.29999199999,
                       5: -0.6999909999899999,
                       8: 1.0}

    result = svm.fit(mock_data, mock_labels)

    assert expected_result == result


def test_predict():
    svm = SVM(1, 1e-5, 9)
    svm.fit(mock_data, mock_labels)
    expected_result = [1]
    result = svm.predict([{2: 0.8, 3: 0.9}])

    assert expected_result == result
