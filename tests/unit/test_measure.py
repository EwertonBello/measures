# -*- coding: utf-8 -*-

from unittest import TestCase
from measures import Measure
from mock import patch
import json
import socket

from nose_focus import focus

class MeasureTestCase(TestCase):

    def test_must_create_a_measure_object_with_correct_attributes(self):
        measure = Measure('myclient', ('localhost', 1984))
        self.assertEqual(measure.client, 'myclient')
        self.assertEqual(measure.addresses, [('localhost', 1984)])
        self.assertEqual(
            measure.socket.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE),
            socket.SOCK_DGRAM)
        # socket is non-blocking
        self.assertEqual(measure.socket.gettimeout(), 0.0)


class BaseMeasureTestCase(TestCase):

    def setUp(self):
        self.measure = Measure('myclient', ('localhost', 1984))


class MeasureCountTestCase(BaseMeasureTestCase):

    @patch('socket.socket.sendto')
    def test_must_send_a_packet_to_correct_address(self, mock_sendto):
        self.measure.count('mymetric')
        self.assertEqual(mock_sendto.call_count, 1)
        self.assertEqual(mock_sendto.call_args[0][1], ('localhost', 1984))

    @patch('socket.socket.sendto')
    def test_must_send_a_packet_with_counter_of_one(self, mock_sendto):
        self.measure.count('mymetric')

        self.assertEqual(mock_sendto.call_count, 1)

        expected_message = {'client': 'myclient', 'metric': 'mymetric', 'count': 1}
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertDictEqual(message, expected_message)

    @patch('socket.socket.sendto')
    def test_must_send_a_packet_with_metric_counter_of_ten(self, mock_sendto):
        self.measure.count('mymetric', counter=10)

        self.assertEqual(mock_sendto.call_count, 1)

        expected_message = {'client': 'myclient', 'metric': 'mymetric', 'count': 10}
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertDictEqual(message, expected_message)

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_dimensions(self, mock_sendto):
        self.measure.count('mymetric', dimensions={'name': 'john'})

        self.assertEqual(mock_sendto.call_count, 1)
        expected_message = {
            'client': 'myclient',
            'metric': 'mymetric',
            'count': 1,
            'name': 'john',
        }
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertDictEqual(message, expected_message)

    @patch('socket.socket.sendto')
    def test_dimensions_must_not_override_parameters(self, mock_sendto):
        self.measure.count('mymetric', dimensions={'client': 'otherclient', 'metric': 'othermetric', 'count': 10})

        self.assertEqual(mock_sendto.call_count, 1)
        expected_message = {
            'client': 'myclient',
            'metric': 'mymetric',
            'count': 1,
        }
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertDictEqual(message, expected_message)

    @patch('socket.socket.sendto')
    def test_must_not_change_dimensions_dict(self, mock_sendto):
        dimensions = {}
        self.measure.count('mymetric', dimensions=dimensions)
        self.assertFalse(dimensions)

    @patch('socket.socket.sendto', side_effect=socket.error)
    def test_must_not_throw_socket_exception(self, mock_sendto):
        try:
            self.measure.count('mymetric')
        except socket.error:
            self.fail('socket.error raised from count')

    @patch('socket.socket.sendto', side_effect=socket.error(80, 'error'))
    @patch('measures.logger.error')
    def test_must_log_socket_error(self, mock_warn, mock_sendto):
        self.measure.count('mymetric')
        mock_warn.assert_called_once_with('Error on sendto. [Errno 80 - error]')


class MeasureTimeTestCase(BaseMeasureTestCase):

    @patch('socket.socket.sendto')
    def test_must_send_a_packet_to_correct_address(self, mock_sendto):
        with self.measure.time('mymetric'):
            pass

        self.assertEqual(mock_sendto.call_count, 1)
        self.assertEqual(mock_sendto.call_args[0][1], ('localhost', 1984))

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_time_spent(self, mock_sendto):
        with self.measure.time('mymetric'):
            pass

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertEqual(len(message), 5)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('time', message)
        self.assertIsInstance(message['time'], float)
        self.assertGreater(message['time'], 0)
        self.assertIn('error_type', message)
        self.assertEqual(message['error_type'], '')
        self.assertIn('error_value', message)
        self.assertEqual(message['error_value'], '')

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_dimensions(self, mock_sendto):
        with self.measure.time('mymetric') as dimensions:
            dimensions['name'] = 'john'

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertEqual(len(message), 6)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('time', message)
        self.assertIsInstance(message['time'], float)
        self.assertGreater(message['time'], 0)
        self.assertIn('error_type', message)
        self.assertEqual(message['error_type'], '')
        self.assertIn('error_value', message)
        self.assertEqual(message['error_value'], '')
        self.assertIn('name', message)
        self.assertEqual(message['name'], 'john')

    @patch('socket.socket.sendto')
    def test_dimensions_must_not_override_parameters(self, mock_sendto):
        with self.measure.time('mymetric') as dimensions:
            dimensions['client'] = 'otherclient'
            dimensions['metric'] = 'othermetric'
            dimensions['time'] = -1
            dimensions['error_type'] = 'othertype'
            dimensions['error_value'] = 'othervalue'

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertEqual(len(message), 5)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('time', message)
        self.assertIsInstance(message['time'], float)
        self.assertGreater(message['time'], 0)
        self.assertIn('error_type', message)
        self.assertEqual(message['error_type'], '')
        self.assertIn('error_value', message)
        self.assertEqual(message['error_value'], '')

    @patch('socket.socket.sendto')
    def test_must_not_change_dimensions_dict(self, mock_sendto):
        with self.measure.time('mymetric') as dimensions:
            dimensions = {}
        self.assertFalse(dimensions)

    @patch('socket.socket.sendto', side_effect=socket.error)
    def test_must_not_throw_socket_exception(self, mock_sendto):
        try:
            with self.measure.time('mymetric'):
                pass
        except socket.error:
            self.fail('socket.error raised from time')

    @patch('socket.socket.sendto', side_effect=socket.error(80, 'error'))
    @patch('measures.logger.error')
    def test_must_log_socket_error(self, mock_warn, mock_sendto):
        with self.measure.time('mymetric'):
            pass
        mock_warn.assert_called_once_with('Error on sendto. [Errno 80 - error]')

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_time_spent_on_error(self, mock_sendto):
        with self.assertRaises(ValueError):
            with self.measure.time('mymetric'):
                raise ValueError('foo')

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertEqual(len(message), 5)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('time', message)
        self.assertIsInstance(message['time'], float)
        self.assertGreater(message['time'], 0)
        self.assertIn('error_type', message)
        self.assertEqual(message['error_type'], str(ValueError))
        self.assertIn('error_value', message)
        self.assertEqual(message['error_value'], 'foo')

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_dimensions_on_error(self, mock_sendto):
        with self.assertRaises(ValueError):
            with self.measure.time('mymetric') as dimensions:
                dimensions['name'] = 'john'
                raise ValueError('foo')

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))
        self.assertIn('name', message)
        self.assertEqual(message['name'], 'john')


class MeasureSendTestCase(BaseMeasureTestCase):

    @patch('socket.socket.sendto')
    def test_must_send_a_packet_to_correct_address(self, mock_sendto):
        self.measure.send('mymetric', None)

        self.assertEqual(mock_sendto.call_count, 1)
        self.assertEqual(mock_sendto.call_args[0][1], ('localhost', 1984))

    @patch('socket.socket.sendto')
    def test_must_send_packet_with_dimensions(self, mock_sendto):
        d = {
            'count': 1,
            'name': 'john'
        }
        self.measure.send('mymetric', d)

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))

        self.assertEqual(len(message), 4)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('count', message)
        self.assertIsInstance(message['count'], int)
        self.assertEqual(message['count'], 1)
        self.assertIn('name', message)
        self.assertEqual(message['name'], 'john')

    @patch('socket.socket.sendto', side_effect=socket.error(80, 'error'))
    @patch('measures.logger.error')
    def test_must_log_socket_error(self, mock_warn, mock_sendto):
        self.measure.send('mymetric', None)
        mock_warn.assert_called_once_with('Error on sendto. [Errno 80 - error]')

    @patch('socket.socket.sendto')
    def test_dimensions_must_not_override_parameters(self, mock_sendto):
        d = {
            'client': 'otherclient',
            'metric': 'othermetric',
            'time': 1.1,
            'name': 'john'
        }
        self.measure.send('mymetric', d)

        self.assertEqual(mock_sendto.call_count, 1)
        message = json.loads(mock_sendto.call_args[0][0].decode('utf-8'))

        self.assertEqual(len(message), 4)
        self.assertIn('client', message)
        self.assertEqual(message['client'], 'myclient')
        self.assertIn('metric', message)
        self.assertEqual(message['metric'], 'mymetric')
        self.assertIn('time', message)
        self.assertIsInstance(message['time'], float)
        self.assertEqual(message['time'], 1.1)
        self.assertIn('name', message)
        self.assertEqual(message['name'], 'john')
